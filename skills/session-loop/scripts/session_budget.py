#!/usr/bin/env python3
"""How big a run of Claude Code sessions got, and where each one handed off.

Reads the transcripts Claude Code writes to ~/.claude/projects/<cwd-slug>/,
including the ones headless `claude -p` runs leave behind, and reports per
session: how many assistant turns it took, how its context grew from the
first turn to the last, and how much context its subagents read beside it.

Pacing is by context. A session's context is what decides its size, every turn
re-pays the whole of it, and that number is in the transcript. No rate table
lives here: --self and --hook never look at money.

Reporting is by price, where a price exists. The loop writes what Claude Code
charged for each session into ~/.claude/session-loop/<project>/, and --spend
reads it. Comparing an Opus session against a Sonnet one on tokens alone gets
the answer wrong by roughly five times.

Usage:
    session_budget.py                          # the repo you are standing in
    session_budget.py ~/projects/your-repo --since 2026-08-07
    session_budget.py ~/projects/your-repo --json
    session_budget.py ~/projects/your-repo --waste   # where each round's tokens
                                               # went, by round rather than by
                                               # session
    session_budget.py . --self                 # am I past my handoff point?
    session_budget.py --hook                   # the same question, asked by a
                                               # PostToolUse hook instead of by
                                               # the session itself
"""

import argparse
import glob
import json
import os
import re
import statistics
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

PROJECTS_ROOT = os.path.expanduser("~/.claude/projects")
SESSION_LOOP_ROOT = os.path.expanduser("~/.claude/session-loop")


@dataclass
class Tokens:
    inp: int = 0
    cache_write: int = 0
    cache_read: int = 0
    out: int = 0


@dataclass
class SessionStats:
    turns: int = 0
    ctx_start: int = 0
    ctx_peak: int = 0
    ctx_end: int = 0
    started: Optional[str] = None
    ended: Optional[str] = None
    by_model: Dict[str, Tokens] = field(default_factory=dict)

    @property
    def input_tokens(self) -> int:
        return sum(t.inp for t in self.by_model.values())

    @property
    def cache_write(self) -> int:
        return sum(t.cache_write for t in self.by_model.values())

    @property
    def cache_read(self) -> int:
        return sum(t.cache_read for t in self.by_model.values())

    @property
    def output_tokens(self) -> int:
        return sum(t.out for t in self.by_model.values())

    @property
    def context_tokens(self) -> int:
        """Context summed over every turn — the size of the session.

        Each turn is handed the whole context again, so this is the total the
        session read, and the number a subagent has to be compared against.
        """
        return self.input_tokens + self.cache_write + self.cache_read


@dataclass
class Subagent:
    name: str
    stats: SessionStats


@dataclass
class SessionReport:
    session_id: str
    stats: SessionStats
    subagents: List[Subagent] = field(default_factory=list)
    # Whether the usage limit ended this session rather than the session
    # choosing to stop. Every other column looks identical either way.
    hit_limit: bool = False


@dataclass
class LoopSession:
    """One session the loop ran, as its own state file records it."""

    session_id: str
    kind: str
    reported_usd: float
    stamp: str
    terminal_reason: str = ""
    by_model_usd: Dict[str, float] = field(default_factory=dict)
    # A session that stopped because the account ran out of usage, not because
    # it decided it was done. On a subscription the only 429 is that one.
    cut_off_by_the_limit: bool = False


@dataclass
class LoopSessions:
    sessions: List["LoopSession"] = field(default_factory=list)
    # State files with no session id cannot be joined to a transcript, so they
    # carry a price and nothing to attribute it to. Reporting the count keeps a
    # partial read from looking like a whole one.
    unjoinable: int = 0


STATE_FILE = re.compile(r"^(run|eval)-(\d{8}T\d{6})-\d+\.json$")

KIND_BY_PREFIX = {"run": "work", "eval": "review"}

ITER_FILE = re.compile(r"^iter-(\d{8}T\d{6})-\d+\.json$")


@dataclass
class SpendRow:
    session: "LoopSession"
    requests: int = 0
    ctx_peak: int = 0


@dataclass
class SpendReport:
    rows: List["SpendRow"] = field(default_factory=list)
    unjoinable: int = 0
    without_transcript: int = 0
    # Transcripts in the same repo that no state file names — an interactive
    # session, typically. It spent against the same limit and nothing here can
    # price it, so the count is all this report can honestly say about it.
    not_run_by_the_loop: int = 0
    usd_by_kind: Dict[str, float] = field(default_factory=dict)
    usd_by_model: Dict[str, float] = field(default_factory=dict)

    @property
    def total_usd(self) -> float:
        return sum(self.usd_by_kind.values())


def stamp_to_iso(stamp: str) -> str:
    """The timestamp in a state file's name, in the shape --since is written in."""
    return "%s-%s-%sT%s:%s:%s" % (
        stamp[0:4], stamp[4:6], stamp[6:8], stamp[9:11], stamp[11:13], stamp[13:15],
    )


def loop_state_dir(target: str) -> str:
    """Where run-loop.sh keeps one project's state files.

    Matches the directory's name exactly. transcript_dir falls back to a
    substring match when nothing else fits; this one does not, because the
    neighbours here include scratch directories left by the loop's own tests
    and pricing a run against those would look like a normal result.
    """
    if os.path.isdir(target) and glob.glob(os.path.join(target, "run-*.json")):
        return target

    name = os.path.basename(os.path.realpath(os.path.expanduser(target)).rstrip(os.sep))
    candidate = os.path.join(SESSION_LOOP_ROOT, name)
    if os.path.isdir(candidate):
        return candidate

    present = sorted(
        os.path.basename(d)
        for d in glob.glob(os.path.join(SESSION_LOOP_ROOT, "*"))
        if os.path.isdir(d)
    )
    raise SystemExit(
        "No loop state directory named %r under %s.%s"
        % (name, SESSION_LOOP_ROOT,
           (" Present: " + ", ".join(present)) if present else "")
    )


def read_loop_sessions(state_dir: str) -> LoopSessions:
    """Every session the loop recorded in one project's state directory.

    Ordered by the timestamp in the filename, which is when the session that
    wrote the file started rather than when the file landed.
    """
    found = []
    unjoinable = 0
    for path in sorted(glob.glob(os.path.join(state_dir, "*.json"))):
        match = STATE_FILE.match(os.path.basename(path))
        if not match:
            continue
        try:
            with open(path, "r", errors="replace") as fh:
                record = json.load(fh)
        except (IOError, OSError, ValueError):
            continue
        prefix, stamp = match.group(1), match.group(2)
        session_id = record.get("session_id")
        # An id is used to name a transcript file, so anything that is not a
        # bare filename would read somewhere else entirely. These files come
        # from a tree the loop's own tests write into.
        if not session_id or os.path.basename(session_id) != session_id:
            unjoinable += 1
            continue
        by_model = {
            model: usage.get("costUSD") or 0.0
            for model, usage in (record.get("modelUsage") or {}).items()
        }
        found.append(
            LoopSession(
                session_id=session_id,
                kind=KIND_BY_PREFIX[prefix],
                reported_usd=record.get("total_cost_usd") or 0.0,
                stamp=stamp,
                terminal_reason=record.get("terminal_reason") or "",
                by_model_usd=by_model,
                cut_off_by_the_limit=record.get("api_error_status") == 429,
            )
        )
    found.sort(key=lambda session: session.stamp)
    return LoopSessions(sessions=found, unjoinable=unjoinable)


@dataclass
class Turn:
    """One API call, with the content blocks that arrived as separate records."""

    context: int = 0
    out: int = 0
    thinking: int = 0
    tools: List[str] = field(default_factory=list)


def turns(records: List[dict]) -> List[Turn]:
    """The assistant turns in a transcript, one per API call.

    Claude Code writes one record per content block and repeats the turn's
    usage on every one, so a turn that thinks and then calls four tools arrives
    as five records. The blocks are folded back into the turn they came from.
    """
    found: List[Turn] = []
    by_id: Dict[str, Turn] = {}
    for record in records:
        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        inp = usage.get("input_tokens", 0) or 0
        cache_write = usage.get("cache_creation_input_tokens", 0) or 0
        cache_read = usage.get("cache_read_input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0
        # The cut-off notice carries a usage block of all zeroes and is not a
        # turn; reading its zero as the context would understate every charge.
        if inp + cache_write + cache_read + out == 0:
            continue

        turn_id = message.get("id") or record.get("requestId")
        turn = by_id.get(turn_id) if turn_id is not None else None
        if turn is None:
            details = usage.get("output_tokens_details") or {}
            turn = Turn(
                context=inp + cache_write + cache_read,
                out=out,
                thinking=details.get("thinking_tokens", 0) or 0,
            )
            found.append(turn)
            if turn_id is not None:
                by_id[turn_id] = turn
        for block in message.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                turn.tools.append(block.get("name") or "?")
    return found


OPENING_CONTEXT = "opening context"
THINKING = "thinking"
ANSWER = "answers and tool calls"


@dataclass
class Attribution:
    """Weighted tokens by what put them in the context."""

    by_cause: Dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.by_cause.values())

    def charge(self, cause: str, tokens: int) -> None:
        self.by_cause[cause] = self.by_cause.get(cause, 0) + tokens


def attribute(records: List[dict]) -> Attribution:
    """What a session's cache reads paid for, and how often each was re-read.

    A turn re-reads everything before it, so the opening context is charged
    once per later turn and an addition made at turn N is charged for the turns
    after N. The charges come to what the session read, within the turns where
    the context only grew: a turn that shrank it — after a compaction — carries
    no charge, and the total falls short of the session's cache reads by what
    those turns read. Measured across six real rounds the shortfall ran 0.3% to
    0.5%.
    """
    walked = turns(records)
    found = Attribution()
    if len(walked) < 2:
        return found
    last = len(walked) - 1
    found.charge(OPENING_CONTEXT, walked[0].context * last)
    for index in range(1, last + 1):
        added = walked[index].context - walked[index - 1].context
        if added <= 0:
            continue
        for cause, share in causes_of(walked[index - 1], added):
            found.charge(cause, share * (last - index))
    return found


def causes_of(turn: Turn, added: int) -> List[tuple]:
    """How one turn's growth divides between the assistant and its tools.

    The turn's own output tokens are what it wrote; whatever else arrived came
    back from the tools it called. Tool results are not in the transcript's
    usage, so the remainder is split evenly between the calls rather than by
    how much each one returned.
    """
    spoken = min(turn.out, added)
    from_tools = added - spoken
    divided = []
    if spoken:
        thinking = spoken * turn.thinking // turn.out if turn.out else 0
        if thinking:
            divided.append((THINKING, thinking))
        if spoken - thinking:
            divided.append((ANSWER, spoken - thinking))
    if not turn.tools:
        if from_tools:
            divided.append((ANSWER, from_tools))
        return divided
    each = from_tools // len(turn.tools)
    for position, name in enumerate(turn.tools):
        # The division's remainder goes to the first call rather than being
        # dropped, so the charges still add up to what the session read.
        extra = from_tools - each * len(turn.tools) if position == 0 else 0
        divided.append((name, each + extra))
    return divided


@dataclass
class Floor:
    """The opening context split into the fixed part and the handoff."""

    floor: int
    tokens_per_char: float

    def handoff_tokens(self, handoff_chars: int) -> int:
        return int(round(handoff_chars * self.tokens_per_char))


COMMIT_CALL = re.compile(r"\bgit\s+(?:-\S+\s+\S+\s+)*commit\b")


def landed_a_commit(records: List[dict]) -> bool:
    """Whether a session got a commit in before it stopped.

    Reads the result rather than the attempt: a session cut off by the usage
    limit stops wherever it happens to be, and the commit is often the call
    that never came back. Compound commands are taken at their word — a shell
    line that commits and then does something else reports the whole line's
    status, so a commit that failed inside a line that succeeded reads as
    landed.
    """
    committed = set()
    for record in records:
        if record.get("type") == "assistant":
            message = record.get("message") or {}
            for block in message.get("content") or []:
                if (isinstance(block, dict) and block.get("type") == "tool_use"
                        and COMMIT_CALL.search(
                            str((block.get("input") or {}).get("command", "")))):
                    committed.add(block.get("id"))
        elif record.get("type") == "user":
            message = record.get("message") or {}
            for block in message.get("content") or []:
                if (isinstance(block, dict) and block.get("type") == "tool_result"
                        and block.get("tool_use_id") in committed
                        and not block.get("is_error")):
                    return True
    return False


def opening_prompt_chars(records: List[dict]) -> Optional[int]:
    """How long the prompt was that started a session.

    Inside the loop that prompt is the handoff plus the protocol, which is the
    one part of the opening context anybody writes. Every later user record is
    a tool result, and those are much the larger share of the file.
    """
    for record in records:
        if record.get("type") != "user" or record.get("isSidechain"):
            continue
        content = (record.get("message") or {}).get("content")
        if isinstance(content, str) and content:
            return len(content)
    return None


def floor_and_handoff(openings: List[tuple]) -> Optional[Floor]:
    """What a session pays before its handoff, read off the run itself.

    Each session opens with the same system prompt, tool schemas and skill
    listing, plus a handoff of its own length. Fitting opening context against
    handoff length across the run separates the two: the intercept is what a
    handoff of no length would still cost. Measuring it per run rather than
    holding a constant keeps it true as Claude Code's own prompt changes.

    Returns None rather than a number when the run cannot answer — one session,
    or a handoff that never changed length, leaves no slope to read.
    """
    if len(openings) < 2:
        return None
    lengths = [float(chars) for chars, _ in openings]
    contexts = [float(context) for _, context in openings]
    mean_length = sum(lengths) / len(lengths)
    spread = sum((length - mean_length) ** 2 for length in lengths)
    if spread == 0:
        return None
    mean_context = sum(contexts) / len(contexts)
    slope = sum(
        (length - mean_length) * (context - mean_context)
        for length, context in zip(lengths, contexts)
    ) / spread
    return Floor(floor=int(round(mean_context - slope * mean_length)),
                 tokens_per_char=slope)


@dataclass
class Round:
    """The sessions between one usage-limit cutoff and the next."""

    number: int
    sessions: List["LoopSession"] = field(default_factory=list)


def rounds(sessions: List["LoopSession"]) -> List[Round]:
    """The loop's sessions grouped into the stretches the operator ran them in.

    Closing on the cutoff rather than opening on it puts the session that ran
    out of usage in the round whose usage it spent.
    """
    found: List[Round] = []
    current = Round(number=1)
    for session in sessions:
        current.sessions.append(session)
        if session.cut_off_by_the_limit:
            found.append(current)
            current = Round(number=len(found) + 1)
    if current.sessions:
        found.append(current)
    return found


@dataclass
class ValueRow:
    day: str
    sessions: int = 0
    usd: float = 0.0
    # What the second reader spent on the same commits. Held apart from the
    # worker's own spend because it answers to different changes, and summed
    # into the cost per commit because the commits were paid for by both.
    review_usd: float = 0.0
    # Zero is a claim about the work; None says nobody wrote it down, which
    # is every day before the driver began recording.
    commits: Optional[int] = None

    @property
    def total_usd(self) -> float:
        return self.usd + self.review_usd

    @property
    def usd_per_commit(self) -> Optional[float]:
        return self.total_usd / self.commits if self.commits else None


def read_iteration_commits(
    state_dir: str, since: Optional[str] = None
) -> Dict[str, int]:
    """Commits each day's iterations produced, from the driver's own records.

    Counting from `git log` instead credits an amended commit to whichever
    session amended it, because the one it replaced is unreachable.
    """
    by_day: Dict[str, int] = {}
    for stamp, counted in read_iteration_commits_by_stamp(
            state_dir, since=since).items():
        by_day[stamp[:8]] = by_day.get(stamp[:8], 0) + counted
    return by_day


FIXED_FLOOR = "fixed prompt floor"
HANDOFF = "handoff, re-read every turn"
REVIEW_OPENING = "reviewer's own opening context"


@dataclass
class RoundReport:
    """One round: what it read, what it produced, what it threw away."""

    number: int
    started: str = ""
    ended: str = ""
    work_sessions: int = 0
    review_sessions: int = 0
    usd: float = 0.0
    commits: Optional[int] = None
    by_cause: Dict[str, int] = field(default_factory=dict)
    # None when the round's handoffs never changed length, which leaves no
    # slope to read the floor off. The opening context stays undivided then.
    floor: Optional[int] = None
    cut_off: bool = False
    # Sessions the state files price and no transcript accounts for — the
    # file is missing, or it holds no assistant turn. Their tokens are absent
    # from every line above, so a round that stayed quiet about them would
    # report a fraction of itself as the whole.
    unaccounted_sessions: int = 0
    # What the session that ran out of usage read without committing anything.
    # Zero when it committed, or when the round has not hit the limit yet.
    thrown_away: int = 0

    @property
    def total(self) -> int:
        return sum(self.by_cause.values())


def waste_report(
    state_dir: str, transcripts_dir: str, since: Optional[str] = None
) -> List[RoundReport]:
    """Where each round's tokens went, and what its last session lost.

    A round's cache reads are almost all of what it spends, so the breakdown is
    over those rather than over price: price is per session and cannot say
    which part of a session was worth paying for.
    """
    commits = read_iteration_commits_by_stamp(state_dir, since=since)
    every = read_loop_sessions(state_dir).sessions
    grouped = rounds([
        session for session in every
        if not (since and stamp_to_iso(session.stamp) < since)])
    found = []
    for group in grouped:
        report = RoundReport(
            number=group.number,
            started=stamp_to_iso(group.sessions[0].stamp),
            ended=stamp_to_iso(group.sessions[-1].stamp),
            commits=commits_between(
                commits, group.sessions[0].stamp,
                session_after(every, group.sessions[-1].stamp)),
        )
        charges = Attribution()
        openings = []
        for session in group.sessions:
            path = os.path.join(transcripts_dir, session.session_id + ".jsonl")
            records = read_records(path)
            walked = turns(records)
            if not walked:
                report.unaccounted_sessions += 1
            report.usd += session.reported_usd
            if session.kind == "work":
                report.work_sessions += 1
            else:
                report.review_sessions += 1
            prompt = opening_prompt_chars(records)
            if walked and prompt:
                openings.append(Opening(kind=session.kind, chars=prompt,
                                        context=walked[0].context,
                                        turns=len(walked)))
            for cause, tokens in attribute(records).by_cause.items():
                charges.charge(cause, tokens)
            if session.cut_off_by_the_limit:
                report.cut_off = True
                if not landed_a_commit(records):
                    # What it read, not what later turns re-read: a session
                    # cut off on its first turn re-read nothing and still paid
                    # for the whole context once.
                    report.thrown_away = session_stats(records).context_tokens
        report.by_cause = dict(charges.by_cause)
        split_the_opening(report, openings)
        found.append(report)
    return found


@dataclass
class Opening:
    """How one session started: its prompt, its context, and its length."""

    kind: str
    chars: int
    context: int
    turns: int

    @property
    def charge(self) -> int:
        """What its opening cost over the session, re-read once per later turn."""
        return self.context * max(self.turns - 1, 0)


def split_the_opening(report: RoundReport, openings: List[Opening]) -> None:
    """Divide the workers' opening context into the fixed floor and the handoff.

    Only the workers. The reviewer opens on a different footing — a prompt of a
    few hundred characters, a narrowed tool set, and measured on the real logs
    an opening some nine thousand tokens above the worker's floor. Fitting one
    line through both reads a floor that neither of them has, so the reviewer's
    opening is reported as its own line instead of being divided.
    """
    charged = report.by_cause.pop(OPENING_CONTEXT, 0)
    if not charged:
        return
    working = [o for o in openings if o.kind == "work"]
    reviewing = [o for o in openings if o.kind != "work"]
    fit = floor_and_handoff([(o.chars, o.context) for o in working])
    # A floor above an opening it is supposed to sit under means something
    # other than the handoff moved that opening — a skill added mid-run, a
    # Claude Code release. The fit is then measuring that instead, and dividing
    # by it puts a negative number on the handoff line. Leave the opening whole
    # and say nothing rather than that.
    if fit is None or any(fit.floor > o.context for o in working):
        report.by_cause[OPENING_CONTEXT] = charged
        return
    report.floor = fit.floor
    read_by_reviews = sum(o.charge for o in reviewing)
    on_the_floor = sum(fit.floor * max(o.turns - 1, 0) for o in working)
    report.by_cause[FIXED_FLOOR] = on_the_floor
    report.by_cause[HANDOFF] = charged - on_the_floor - read_by_reviews
    if read_by_reviews:
        report.by_cause[REVIEW_OPENING] = read_by_reviews


def read_iteration_commits_by_stamp(
    state_dir: str, since: Optional[str] = None
) -> Dict[str, int]:
    """Commits each iteration produced, kept at the iteration's own timestamp.

    read_iteration_commits sums these by day, which is the right grain for a
    daily report and the wrong one for a round: several rounds can run in one
    day, and each would claim the whole day's commits.
    """
    by_stamp: Dict[str, int] = {}
    for path in sorted(glob.glob(os.path.join(state_dir, "iter-*.json"))):
        match = ITER_FILE.match(os.path.basename(path))
        if not match:
            continue
        try:
            with open(path, "r", errors="replace") as fh:
                record = json.load(fh)
            counted = int(record.get("commits") or 0)
        except (IOError, OSError, ValueError, TypeError):
            continue
        if since and stamp_to_iso(match.group(1)) < since:
            continue
        stamp = match.group(1)
        by_stamp[stamp] = by_stamp.get(stamp, 0) + counted
    return by_stamp


def session_after(sessions: List["LoopSession"], stamp: str) -> Optional[str]:
    """The stamp of the first session that started after the one named.

    Read from every session the loop recorded, not from the ones --since kept.
    A round's upper bound is a fact about the run; taking it from the filtered
    list would leave the last surviving round open at the top and let it claim
    every commit made after it.
    """
    later = [s.stamp for s in sessions if s.stamp > stamp]
    return min(later) if later else None


def commits_between(
    by_stamp: Dict[str, int], first: str, before: Optional[str]
) -> Optional[int]:
    """Commits from the iterations that ran inside one round.

    The window runs from the round's first session up to, but not including,
    the session that started after its last. `before` is None only when nothing
    has run since, which leaves the window open at the top — an iteration
    record is written after the session it is about, so a top bounded at the
    round's own last session would drop the final record every time.
    """
    counted = [n for stamp, n in by_stamp.items()
               if first <= stamp and (before is None or stamp < before)]
    return sum(counted) if counted else None


def value_report(
    state_dir: str, since: Optional[str] = None
) -> List[ValueRow]:
    """What each day of the run cost and what came out of it."""
    commits = read_iteration_commits(state_dir, since=since)
    rows: Dict[str, ValueRow] = {}
    for session in read_loop_sessions(state_dir).sessions:
        if since and stamp_to_iso(session.stamp) < since:
            continue
        row = rows.setdefault(session.stamp[:8], ValueRow(day=session.stamp[:8]))
        if session.kind == "work":
            row.sessions += 1
            row.usd += session.reported_usd
        else:
            row.review_usd += session.reported_usd
    for day, count in commits.items():
        rows.setdefault(day, ValueRow(day=day)).commits = count
    return [rows[day] for day in sorted(rows)]


def read_records(path: str) -> List[dict]:
    """Every JSON object in a transcript, skipping lines that are not one.

    Transcripts are appended to live, so the last line of a session that is
    still running is routinely half-written.
    """
    records = []
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
    except (IOError, OSError):
        return []
    return records


def session_stats(records: List[dict]) -> SessionStats:
    """Turn counts, the context ramp, and token totals for one transcript.

    Context is what the model was handed on a turn: fresh input plus both
    cache classes. It is the number that decides how big a turn is, because
    every later turn re-pays the whole of it.
    """
    stats = SessionStats()
    seen = set()
    for record in records:
        timestamp = record.get("timestamp")
        if timestamp:
            if stats.started is None:
                stats.started = timestamp
            stats.ended = timestamp

        message = record.get("message") or {}
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue

        # Claude Code writes one record per content block, and repeats the
        # turn's usage on every one of them. A turn that thinks and then calls
        # four tools arrives as five records with identical usage; counting
        # each would count the turn five times over.
        turn_id = message.get("id") or record.get("requestId")
        if turn_id is not None:
            if turn_id in seen:
                continue
            seen.add(turn_id)

        inp = usage.get("input_tokens", 0) or 0
        cache_write = usage.get("cache_creation_input_tokens", 0) or 0
        cache_read = usage.get("cache_read_input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0

        # The notice Claude Code appends when a run is cut off carries a usage
        # block of all zeroes. It is not a turn, and treating its zero as the
        # current context would tell a session it had room left.
        if inp + cache_write + cache_read + out == 0:
            continue

        model = message.get("model") or "default"
        totals = stats.by_model.setdefault(model, Tokens())
        totals.inp += inp
        totals.cache_write += cache_write
        totals.cache_read += cache_read
        totals.out += out

        context = inp + cache_write + cache_read
        if stats.turns == 0:
            stats.ctx_start = context
        stats.ctx_end = context
        stats.ctx_peak = max(stats.ctx_peak, context)
        stats.turns += 1
    return stats


def fanout_overhead(main_tokens: int, sub_tokens: int) -> Optional[float]:
    """Context the subagents read, as a multiple of what the session read.

    0.0 means the session never delegated. 1.0 means delegating doubled the
    reading. None means the session read nothing itself, so there is no ratio
    to take.
    """
    if main_tokens <= 0:
        return None
    return sub_tokens / main_tokens


def collect(project_dir: str, since: Optional[str] = None) -> List[SessionReport]:
    """Every session transcript in one project directory, oldest first.

    A session's subagents live in <session-id>/subagents/agent-*.jsonl beside
    it, and are reported under the session that launched them.
    """
    reports = []
    for path in glob.glob(os.path.join(project_dir, "*.jsonl")):
        records = read_records(path)
        stats = session_stats(records)
        if since and (stats.started is None or stats.started < since):
            continue
        session_id = os.path.basename(path)[: -len(".jsonl")]

        subagents = []
        pattern = os.path.join(project_dir, session_id, "subagents", "*.jsonl")
        for sub_path in sorted(glob.glob(pattern)):
            name = os.path.basename(sub_path)[: -len(".jsonl")]
            if name.startswith("agent-"):
                name = name[len("agent-") :]
            subagents.append(Subagent(name=name, stats=session_stats(read_records(sub_path))))

        reports.append(SessionReport(session_id=session_id, stats=stats,
                                     subagents=subagents,
                                     hit_limit=hit_session_limit(records)))

    reports.sort(key=lambda r: (r.stats.started or "", r.session_id))
    return reports


# Where a session hands off. The default is 225,000, and the honest reason to
# record here is that this number matters far less than it looks like it should.
#
# Measured over 29 sessions across repo-a and repo-b. Cost per turn of actual
# work — total context spent, divided by the turns after that session's own first
# Edit or Write — barely moves with where the session stopped: r = -0.07. What it
# does track is when the session starts working: r = +0.62. Sessions that first
# touch a file below 90,000 context cost a median 144,049 per working turn and
# get 51 working turns out of their life; sessions that first touch one above
# 130,000 cost 264,826 and get 20. That first-change point ranged from 60,016 to
# 187,085 across the same 29 sessions, and it is where the money actually is.
#
# An earlier version of this comment carried a fitted curve claiming a cheapest
# stopping point near 163,000 and a 4.3% penalty for stopping at 200,000. The fit
# assumed one re-orientation cost for every session. The measurement above says
# that cost varies threefold between sessions, which swamps the curve entirely.
#
# So do not tune this expecting a saving. It is a safety rail, and lower is the
# dangerous direction: 4 of those 29 sessions had not yet changed a single file
# at 150,000 context, so a ceiling there would have retired them before they did
# any work at all.
#
# 225,000 is where the operator set it, between two measured numbers. A turn
# taken in the session you already have costs exactly its own context; a turn of
# work from a fresh session costs a median 195,813 once that session's whole
# re-orientation is charged to it, so below about 195,813 carrying on is the
# cheaper move and above it handing off is. The quartiles on that figure are
# 153,681 and 251,450 — the same threefold spread again — so a ceiling somewhat
# above the median buys margin against drawing a slow-starting successor. The
# upper bound is accuracy: the operator measured answers starting to degrade past
# 250,000. If answers go wrong late in a session, lower this before assuming the
# work itself was at fault.
DEFAULT_HANDOFF_AT = 225_000


def spend_report(
    state_dir: str, transcripts_dir: str, since: Optional[str] = None
) -> SpendReport:
    """What each session the loop ran cost, joined to how big it got.

    The price comes from the state file, the size from the transcript. Neither
    file holds both, and comparing sessions on size alone ranks a Sonnet review
    beside an Opus session as though they cost the same.
    """
    found = read_loop_sessions(state_dir)
    report = SpendReport(unjoinable=found.unjoinable)
    for session in found.sessions:
        if since and stamp_to_iso(session.stamp) < since:
            continue
        path = os.path.join(transcripts_dir, session.session_id + ".jsonl")
        if not os.path.exists(path):
            report.without_transcript += 1
            continue
        stats = session_stats(read_records(path))
        report.rows.append(
            SpendRow(session=session, requests=stats.turns, ctx_peak=stats.ctx_peak)
        )
        report.usd_by_kind[session.kind] = (
            report.usd_by_kind.get(session.kind, 0.0) + session.reported_usd
        )
        for model, usd in session.by_model_usd.items():
            report.usd_by_model[model] = report.usd_by_model.get(model, 0.0) + usd

    priced = {session.session_id for session in found.sessions}
    for path in glob.glob(os.path.join(transcripts_dir, "*.jsonl")):
        if os.path.basename(path)[: -len(".jsonl")] in priced:
            continue
        started = session_stats(read_records(path)).started
        if since and (started is None or started < since):
            continue
        report.not_run_by_the_loop += 1
    return report


def current_session_path(project_dir: str) -> Optional[str]:
    """The transcript of the session asking the question.

    Claude Code puts the running session's id in CLAUDE_CODE_SESSION_ID, and
    names the transcript after it. Falls back to the most recently written
    transcript, which is the same file whenever one session is running.

    An id that names no file is a different situation from no id at all: the
    caller said who it was and this directory does not have it, so the answer
    is about to be about somebody else. Falling back is still the best guess,
    but it is said out loud rather than done quietly.
    """
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if session_id:
        named = os.path.join(project_dir, session_id + ".jsonl")
        if os.path.exists(named):
            return named
        sys.stderr.write(
            "warning: session %s has no transcript in %s; "
            "answering from the most recent one instead\n" % (session_id, project_dir)
        )

    transcripts = glob.glob(os.path.join(project_dir, "*.jsonl"))
    if not transcripts:
        return None
    return max(transcripts, key=os.path.getmtime)


SESSION_LIMIT_NOTICE = "hit your session limit"


def hit_session_limit(records: List[dict]) -> bool:
    """Whether the run was cut off by the usage limit rather than finishing."""
    for record in records:
        content = (record.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (isinstance(block, dict) and block.get("type") == "text"
                    and SESSION_LIMIT_NOTICE in block.get("text", "")):
                return True
    return False


def past_handoff_point(stats: SessionStats, threshold: int) -> bool:
    """Whether the session has grown past where it should hand off.

    Reads the latest context, not the peak: the question is what the next turn
    will cost, and a session that compacted is genuinely cheaper again.
    """
    return stats.ctx_end > threshold


def transcript_dir(target: str) -> str:
    """Where Claude Code keeps the transcripts for a working directory.

    Accepts the repo itself, the transcript directory, or the slug. Raises
    rather than guessing, because analysing the wrong project silently is
    worse than stopping.
    """
    if os.path.isdir(target) and glob.glob(os.path.join(target, "*.jsonl")):
        return target

    real = os.path.realpath(os.path.expanduser(target))
    slug = real.replace(os.sep, "-")
    candidate = os.path.join(PROJECTS_ROOT, slug)
    if os.path.isdir(candidate):
        return candidate

    candidate = os.path.join(PROJECTS_ROOT, os.path.basename(target))
    if os.path.isdir(candidate):
        return candidate

    matches = [
        d
        for d in sorted(glob.glob(os.path.join(PROJECTS_ROOT, "*")))
        if os.path.isdir(d) and os.path.basename(real) in os.path.basename(d)
    ]
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(
        "No transcript directory for %r. Looked for %s.%s"
        % (
            target,
            slug,
            (" Candidates: " + ", ".join(os.path.basename(m) for m in matches)) if matches else "",
        )
    )


def token_counts(stats: SessionStats) -> dict:
    return {
        "context": stats.context_tokens,
        "input": stats.input_tokens,
        "cache_write": stats.cache_write,
        "cache_read": stats.cache_read,
        "output": stats.output_tokens,
    }


def as_dict(report: SessionReport) -> dict:
    sub_tokens = sum(s.stats.context_tokens for s in report.subagents)
    return {
        "session_id": report.session_id,
        "started": report.stats.started,
        "ended": report.stats.ended,
        "turns": report.stats.turns,
        "context": {
            "start": report.stats.ctx_start,
            "peak": report.stats.ctx_peak,
            "end": report.stats.ctx_end,
        },
        "tokens": token_counts(report.stats),
        "fanout": fanout_overhead(report.stats.context_tokens, sub_tokens),
        "cut_off_by_usage_limit": report.hit_limit,
        "subagents": [
            {
                "name": s.name,
                "turns": s.stats.turns,
                "peak_context": s.stats.ctx_peak,
                "tokens": token_counts(s.stats),
            }
            for s in report.subagents
        ],
    }


def as_value_dict(rows: List[ValueRow]) -> dict:
    return {
        "days": [
            {
                "day": row.day,
                "sessions": row.sessions,
                "usd": round(row.usd, 2),
                "review_usd": round(row.review_usd, 2),
                "commits": row.commits,
                "usd_per_commit": (None if row.usd_per_commit is None
                                   else round(row.usd_per_commit, 2)),
            }
            for row in rows
        ]
    }


def as_spend_dict(report: SpendReport) -> dict:
    return {
        "total_usd": round(report.total_usd, 2),
        "usd_by_kind": {k: round(v, 2) for k, v in sorted(report.usd_by_kind.items())},
        "usd_by_model": {k: round(v, 2) for k, v in sorted(report.usd_by_model.items())},
        "unjoinable_state_files": report.unjoinable,
        "sessions_without_a_transcript": report.without_transcript,
        "transcripts_not_run_by_the_loop": report.not_run_by_the_loop,
        "sessions": [
            {
                "session": row.session.session_id[:8],
                "kind": row.session.kind,
                "started": stamp_to_iso(row.session.stamp),
                "requests": row.requests,
                "ctx_peak": row.ctx_peak,
                "usd": round(row.session.reported_usd, 2),
                "ended": row.session.terminal_reason,
            }
            for row in report.rows
        ],
    }


PEAK_BANDS = ((0, 100_000), (100_000, 140_000), (140_000, 180_000),
              (180_000, 220_000), (220_000, None))


def usd_per_request_by_band(rows: List["SpendRow"]) -> List[tuple]:
    """Median cost of a request, per session kind, by how big the session got.

    This is what says whether handing off earlier is worth it, so two things
    have to hold. The middle value has to be the middle: on an even count the
    upper-middle reports a band as dearer than any typical session in it. And
    work and review are counted apart, because reviews run on a cheaper model
    and stop lower, so pooling them makes the low bands look cheaper than
    handing off earlier would actually make them.
    """
    bands = []
    for kind in KIND_BY_PREFIX.values():
        usable = [row for row in rows if row.requests and row.session.kind == kind]
        for low, high in PEAK_BANDS:
            in_band = [
                row for row in usable
                if low <= row.ctx_peak and (high is None or row.ctx_peak < high)
            ]
            if not in_band:
                continue
            label = ("%3dk+" % (low // 1000) if high is None
                     else "%3dk-%3dk" % (low // 1000, high // 1000)).strip()
            per_request = [row.session.reported_usd / row.requests for row in in_band]
            bands.append((kind, label, len(in_band), statistics.median(per_request)))
    return bands


def print_spend(report: SpendReport) -> None:
    print("%-17s %-6s %8s %10s %9s  %s"
          % ("started", "kind", "requests", "ctx_peak", "usd", "ended"))
    for row in report.rows:
        print("%-17s %-6s %8d %10s %9s  %s"
              % (stamp_to_iso(row.session.stamp)[:16], row.session.kind,
                 row.requests, "{:,}".format(row.ctx_peak),
                 "${:,.2f}".format(row.session.reported_usd),
                 row.session.terminal_reason))

    print("\n%d sessions, $%.2f" % (len(report.rows), report.total_usd))
    for kind, usd in sorted(report.usd_by_kind.items(), key=lambda kv: -kv[1]):
        share = 100 * usd / report.total_usd if report.total_usd else 0
        print("  %-8s $%9.2f  %5.1f%%" % (kind, usd, share))
    for model, usd in sorted(report.usd_by_model.items(), key=lambda kv: -kv[1]):
        share = 100 * usd / report.total_usd if report.total_usd else 0
        print("  %-34s $%9.2f  %5.1f%%" % (model, usd, share))

    # Silence here would read as "this is the whole run" when it is not.
    if report.unjoinable:
        print("\n  %d state file(s) carried a price but no session id, so nothing "
              "could be joined to them." % report.unjoinable)
    if report.without_transcript:
        print("  %d session(s) had no transcript and are not counted above."
              % report.without_transcript)
    if report.not_run_by_the_loop:
        print("  %d transcript(s) in this repo were not run by the loop, carry no "
              "price, and are not counted above." % report.not_run_by_the_loop)

    bands = usd_per_request_by_band(report.rows)
    if bands:
        print("\ncost per request, by where the session peaked:")
        for kind, label, count, median in bands:
            print("  %-6s %-10s %3d sessions  median $%.3f/request"
                  % (kind, label, count, median))


def print_value(rows: List[ValueRow]) -> None:
    print("%-10s %8s %10s %10s %8s %12s"
          % ("day", "sessions", "work", "review", "commits", "usd/commit"))
    for row in rows:
        print("%-10s %8d %10s %10s %8s %12s"
              % (row.day, row.sessions, "${:,.2f}".format(row.usd),
                 "${:,.2f}".format(row.review_usd),
                 "?" if row.commits is None else row.commits,
                 "-" if row.usd_per_commit is None
                 else "${:,.2f}".format(row.usd_per_commit)))


def as_waste_dict(rounds_found: List[RoundReport]) -> dict:
    return {
        "rounds": [
            {
                "round": report.number,
                "started": report.started,
                "ended": report.ended,
                "work_sessions": report.work_sessions,
                "review_sessions": report.review_sessions,
                "usd": round(report.usd, 2),
                "commits": report.commits,
                "cut_off": report.cut_off,
                "unaccounted_sessions": report.unaccounted_sessions,
                "thrown_away": report.thrown_away,
                "floor": report.floor,
                "total": report.total,
                "by_cause": report.by_cause,
            }
            for report in rounds_found
        ]
    }


def print_waste(rounds_found: List[RoundReport]) -> None:
    if not rounds_found:
        print("no rounds to report")
        return
    for report in rounds_found:
        total = report.total
        print("\nround %d  %s -> %s  %d working session(s), %d review(s), "
              "%s commit(s)%s"
              % (report.number, report.started, report.ended,
                 report.work_sessions, report.review_sessions,
                 "?" if report.commits is None else report.commits,
                 "" if report.cut_off else "  (still running)"))
        print("  %-32s %13s %7s" % ("what was read", "tokens", "share"))
        for cause, tokens in sorted(report.by_cause.items(),
                                    key=lambda pair: -pair[1]):
            print("  %-32s %13s %6.1f%%"
                  % (cause, "{:,}".format(tokens),
                     100.0 * tokens / total if total else 0.0))
        print("  %-32s %13s" % ("total", "{:,}".format(total)))
        if report.floor is not None:
            print("  the floor measured %s tokens a turn from this round's own "
                  "sessions" % "{:,}".format(report.floor))
        if report.unaccounted_sessions:
            print("  %d session(s) here are priced with no transcript to "
                  "account for their tokens, so every line above is short by "
                  "whatever they read" % report.unaccounted_sessions)
        if report.thrown_away:
            print("  %s tokens went to the session the limit cut off, which "
                  "committed nothing" % "{:,}".format(report.thrown_away))


def print_table(reports: List[SessionReport], verbose: bool) -> None:
    # ctx_end is where the session actually stopped, which is the column that
    # says whether it handed off near its threshold or ran far past it.
    print(
        "%-16s %-16s %5s %9s %9s %9s %11s %6s"
        % ("started", "session", "turns", "ctx_start", "ctx_end", "ctx_peak",
           "tokens", "fanout")
    )
    run_tokens = 0
    for report in reports:
        sub_tokens = sum(s.stats.context_tokens for s in report.subagents)
        overhead = fanout_overhead(report.stats.context_tokens, sub_tokens)
        run_tokens += report.stats.context_tokens + sub_tokens
        print(
            "%-16s %-16s %5d %9s %9s %9s %11s %6s"
            % (
                (report.stats.started or "")[:16],
                report.session_id[:16],
                report.stats.turns,
                "{:,}".format(report.stats.ctx_start),
                "{:,}".format(report.stats.ctx_end),
                "{:,}".format(report.stats.ctx_peak),
                "{:,}".format(report.stats.context_tokens + sub_tokens),
                "-" if overhead is None else ("%.2fx" % overhead),
            )
            + ("  <- cut off by the usage limit" if report.hit_limit else "")
        )
        if verbose:
            for s in report.subagents:
                print(
                    "      - %-40s turns=%4d peak=%9s  %11s"
                    % (
                        s.name[:40],
                        s.stats.turns,
                        "{:,}".format(s.stats.ctx_peak),
                        "{:,}".format(s.stats.context_tokens),
                    )
                )
    print("\n%d sessions, %s context tokens" % (len(reports), "{:,}".format(run_tokens)))


def self_check(project: str, threshold: int, as_json: bool) -> int:
    """Answer one question, for the session that is asking: keep going, or hand off?

    Exits 3 when the session is past the point where continuing costs more than
    starting fresh would, so a script can branch on it.
    """
    path = current_session_path(transcript_dir(project))
    if path is None:
        sys.stderr.write("no transcript found for the current session\n")
        return 1

    stats = session_stats(read_records(path))
    over = past_handoff_point(stats, threshold)
    # The in-flight turn is not written until it completes, so this reads the
    # last finished one.
    verdict = "hand off" if over else "keep going"

    if as_json:
        print(json.dumps({
            "session": os.path.basename(path)[: -len(".jsonl")],
            "turns": stats.turns,
            "context": stats.ctx_end,
            "peak_context": stats.ctx_peak,
            "handoff_at": threshold,
            "past_handoff_point": over,
        }, indent=2))
    else:
        # The session id is here because the lookup above can land on a
        # neighbour's transcript, and a verdict with no name on it gives the
        # reader no way to notice that it did.
        print("%s: turn %d, context %s of %s — %s"
              % (os.path.basename(path)[: -len(".jsonl")], stats.turns,
                 "{:,}".format(stats.ctx_end), "{:,}".format(threshold), verdict))
    return 3 if over else 0


def hook_check(threshold: int) -> int:
    """The same verdict as --self, but nobody had to decide to ask for it.

    The contract names three moments to check: after each commit, before the
    reviews a piece of work owes, and after the probing that opens one. All
    three are milestones in the work cycle, and a session that spends its whole
    life on one piece of work reaches them once. Measured over the last two
    runs: every worker committed exactly once, between turn 27 and turn 86, and
    the one check it ran landed a turn or two later at 145,000 to 204,000 —
    after which 29% of one run's tokens went on turns already past the line.

    Claude Code runs this from a PostToolUse hook, which fires on every tool
    call and hands the hook the path to the session's own transcript. So the
    number gets looked at whether or not the session thought to look.

    Silence is deliberate. Anything written here enters the session's context
    and is re-paid by every later turn, so an announcement per tool call would
    cost more than the overshoot it prevents. Exit 2 with a line on stderr is
    the one channel a session cannot skim past — probed: plain stdout from a
    hook never reaches the model at all.

    Every kind of bad input returns 0. A hook that fails loudly turns a tool
    call the session was right to make into an error it has to explain.
    """
    try:
        payload = json.loads(sys.stdin.read())
        path = payload.get("transcript_path")
        if not path:
            return 0
        stats = session_stats(read_records(path))
    except (ValueError, TypeError, AttributeError, IOError, OSError):
        return 0

    # No turns means no number to judge — the first tool call of a session can
    # land before any turn carrying usage has been written.
    if stats.turns == 0 or not past_handoff_point(stats, threshold):
        return 0

    # Naming both steps is what makes this a handoff rather than an abort. A
    # worker told only that it is over stops where it stands, and the dirty tree
    # it leaves trips the driver's dirty-tree gate, halting the whole run.
    sys.stderr.write(
        "You are at %s context against a handoff point of %s. Stop here rather "
        "than finishing the piece of work: commit what you have with a subject "
        "that says it is unfinished, then rewrite HANDOFF.md as the continuation "
        "prompt for the next fresh session.\n"
        % ("{:,}".format(stats.ctx_end), "{:,}".format(threshold)))
    return 2


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project", nargs="?", default=".",
                        help="repo path, transcript directory, or slug (default: cwd)")
    parser.add_argument("--since", help="ISO timestamp prefix, e.g. 2026-08-07")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--verbose", action="store_true", help="list each subagent")
    parser.add_argument("--self", dest="self_check", action="store_true",
                        help="report the CURRENT session's context and whether it should hand off")
    parser.add_argument("--spend", action="store_true",
                        help="what each session the loop ran cost, from the prices "
                             "Claude Code wrote into ~/.claude/session-loop/<project>/")
    parser.add_argument("--waste", action="store_true",
                        help="where each round's tokens went, and what the "
                             "session the limit cut off threw away")
    parser.add_argument("--value", action="store_true",
                        help="what each day of the run cost and how many "
                             "commits came out of it")
    parser.add_argument("--hook", dest="hook_check", action="store_true",
                        help="read a PostToolUse hook payload on stdin and exit 2 if the "
                             "session it names is past its handoff point")
    parser.add_argument("--handoff-at", type=int, default=DEFAULT_HANDOFF_AT,
                        help="context to hand off at, for --self and --hook (default: %d)"
                             % DEFAULT_HANDOFF_AT)
    args = parser.parse_args(argv)

    if args.hook_check:
        return hook_check(args.handoff_at)

    if args.self_check:
        return self_check(args.project, args.handoff_at, args.json)

    if args.spend:
        report = spend_report(
            loop_state_dir(args.project), transcript_dir(args.project), since=args.since
        )
        if args.json:
            print(json.dumps(as_spend_dict(report), indent=2))
        else:
            print_spend(report)
        return 0

    if args.waste:
        rounds_found = waste_report(
            loop_state_dir(args.project), transcript_dir(args.project),
            since=args.since,
        )
        if args.json:
            print(json.dumps(as_waste_dict(rounds_found), indent=2))
        else:
            print_waste(rounds_found)
        return 0

    if args.value:
        rows = value_report(loop_state_dir(args.project), since=args.since)
        if args.json:
            print(json.dumps(as_value_dict(rows), indent=2))
        else:
            print_value(rows)
        return 0

    reports = collect(transcript_dir(args.project), since=args.since)

    if args.json:
        print(json.dumps({"sessions": [as_dict(r) for r in reports]}, indent=2))
    else:
        print_table(reports, args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
