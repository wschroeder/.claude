"""Tests for session_budget.

Run: python3 -m unittest discover -s ~/.claude/skills/session-loop/scripts
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import session_budget as sb


_NEXT_ID = [0]


def assistant(ts, model="claude-opus-5", inp=0, cw=0, cr=0, out=0, msg_id=None):
    """One assistant record shaped like a real transcript line.

    Claude Code writes one record per content block — a turn that thinks and
    then calls four tools lands as five records carrying the SAME message id
    and the SAME usage. Records default to a fresh id here so a test that does
    not care about blocks gets one turn per record.
    """
    if msg_id is None:
        _NEXT_ID[0] += 1
        msg_id = "msg_%d" % _NEXT_ID[0]
    return {
        "type": "assistant",
        "timestamp": ts,
        "sessionId": "s1",
        "cwd": "/repo",
        "requestId": "req_for_" + msg_id,
        "message": {
            "id": msg_id,
            "model": model,
            "usage": {
                "input_tokens": inp,
                "cache_creation_input_tokens": cw,
                "cache_read_input_tokens": cr,
                "output_tokens": out,
            },
        },
    }


class OneTurnManyBlocks(unittest.TestCase):
    """The bug this guards: usage repeated per block, counted per block."""

    def test_blocks_of_one_turn_are_counted_once(self):
        recs = [assistant("2026-08-09T00:00:00Z", inp=1, cw=10, cr=100, out=5, msg_id="msg_a")
                for _ in range(5)]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.turns, 1)
        self.assertEqual(stats.output_tokens, 5)
        self.assertEqual(stats.cache_read, 100)

    def test_a_turn_that_thinks_then_calls_four_tools_is_one_turn(self):
        recs = ([assistant("2026-08-09T00:00:00Z", cr=40_000, out=500, msg_id="msg_a")] * 5
                + [assistant("2026-08-09T00:01:00Z", cr=60_000, out=200, msg_id="msg_b")] * 2)
        stats = sb.session_stats(recs)
        self.assertEqual(stats.turns, 2)
        self.assertEqual(stats.output_tokens, 700)
        self.assertEqual(stats.ctx_start, 40_000)
        self.assertEqual(stats.ctx_peak, 60_000)

    def test_records_with_no_id_fall_back_to_the_request_id(self):
        a = assistant("2026-08-09T00:00:00Z", out=7, msg_id="msg_a")
        b = assistant("2026-08-09T00:00:00Z", out=7, msg_id="msg_a")
        del a["message"]["id"], b["message"]["id"]
        self.assertEqual(sb.session_stats([a, b]).output_tokens, 7)

    def test_records_with_neither_id_are_each_their_own_turn(self):
        a = assistant("2026-08-09T00:00:00Z", out=7)
        b = assistant("2026-08-09T00:01:00Z", out=7)
        for r in (a, b):
            del r["message"]["id"], r["requestId"]
        stats = sb.session_stats([a, b])
        self.assertEqual(stats.turns, 2)
        self.assertEqual(stats.output_tokens, 14)


class ReadRecords(unittest.TestCase):
    def test_skips_blank_and_malformed_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as fh:
            fh.write(json.dumps(assistant("2026-08-09T00:00:00Z")) + "\n")
            fh.write("\n")
            fh.write("{not json\n")
            fh.write(json.dumps(assistant("2026-08-09T00:01:00Z")) + "\n")
            path = fh.name
        try:
            self.assertEqual(len(sb.read_records(path)), 2)
        finally:
            os.unlink(path)


class SessionStats(unittest.TestCase):
    def test_context_is_input_plus_both_cache_fields(self):
        recs = [assistant("2026-08-09T00:00:00Z", inp=2, cw=22808, cr=21637, out=244)]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.ctx_start, 44447)
        self.assertEqual(stats.ctx_peak, 44447)

    def test_ramp_tracks_start_peak_and_end_across_turns(self):
        recs = [
            assistant("2026-08-09T00:00:00Z", cr=40_000, out=100),
            assistant("2026-08-09T00:10:00Z", cr=300_000, out=100),
            assistant("2026-08-09T00:20:00Z", cr=180_000, out=100),
        ]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.turns, 3)
        self.assertEqual(stats.ctx_start, 40_000)
        self.assertEqual(stats.ctx_peak, 300_000)
        self.assertEqual(stats.ctx_end, 180_000)

    def test_totals_sum_each_token_class(self):
        recs = [
            assistant("2026-08-09T00:00:00Z", inp=1, cw=10, cr=100, out=5),
            assistant("2026-08-09T00:01:00Z", inp=2, cw=20, cr=200, out=7),
        ]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.input_tokens, 3)
        self.assertEqual(stats.cache_write, 30)
        self.assertEqual(stats.cache_read, 300)
        self.assertEqual(stats.output_tokens, 12)

    def test_records_without_usage_do_not_count_as_turns(self):
        recs = [
            {"type": "user", "timestamp": "2026-08-09T00:00:00Z", "message": {"content": "hi"}},
            assistant("2026-08-09T00:01:00Z", cr=1000, out=5),
        ]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.turns, 1)

    def test_timestamps_come_from_any_record_not_only_assistant_ones(self):
        recs = [
            {"type": "user", "timestamp": "2026-08-09T00:00:00Z", "message": {"content": "hi"}},
            assistant("2026-08-09T00:05:00Z", cr=1000, out=5),
        ]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.started, "2026-08-09T00:00:00Z")
        self.assertEqual(stats.ended, "2026-08-09T00:05:00Z")

    def test_an_empty_transcript_yields_zeroed_stats_not_an_error(self):
        stats = sb.session_stats([])
        self.assertEqual(stats.turns, 0)
        self.assertEqual(stats.ctx_peak, 0)
        self.assertIsNone(stats.started)


class ContextTokens(unittest.TestCase):
    """The size of a session, with no prices involved.

    Every turn re-pays the whole context it was handed, so context summed
    across turns is what a session consumed. Output is counted separately
    because it is what the session produced, not what it re-read.
    """

    def test_context_tokens_are_input_plus_both_cache_classes(self):
        recs = [assistant("2026-08-09T00:00:00Z", inp=1, cw=10, cr=100, out=1000)]
        self.assertEqual(sb.session_stats(recs).context_tokens, 111)

    def test_context_tokens_accumulate_across_turns(self):
        recs = [
            assistant("2026-08-09T00:00:00Z", cr=1_000),
            assistant("2026-08-09T00:01:00Z", cr=3_000),
        ]
        self.assertEqual(sb.session_stats(recs).context_tokens, 4_000)

    def test_every_model_in_a_mixed_session_is_counted(self):
        recs = [
            assistant("2026-08-09T00:00:00Z", model="a", cr=100),
            assistant("2026-08-09T00:01:00Z", model="b", cr=200),
        ]
        self.assertEqual(sb.session_stats(recs).context_tokens, 300)


class Collect(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.proj = os.path.join(self.root, "-repo")
        os.makedirs(os.path.join(self.proj, "sess-1", "subagents"))
        self._write(os.path.join(self.proj, "sess-1.jsonl"),
                    [assistant("2026-08-09T00:00:00Z", cr=40_000, out=100),
                     assistant("2026-08-09T01:00:00Z", cr=400_000, out=100)])
        self._write(os.path.join(self.proj, "sess-1", "subagents", "agent-abc.jsonl"),
                    [assistant("2026-08-09T00:30:00Z", cr=30_000, out=50)])
        self._write(os.path.join(self.proj, "sess-0.jsonl"),
                    [assistant("2026-08-01T00:00:00Z", cr=10_000, out=10)])

    def _write(self, path, recs):
        with open(path, "w") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")

    def test_a_session_carries_its_own_subagents(self):
        [report] = sb.collect(self.proj, since="2026-08-05")
        self.assertEqual(report.session_id, "sess-1")
        self.assertEqual(len(report.subagents), 1)
        self.assertEqual(report.subagents[0].name, "abc")

    def test_since_excludes_sessions_that_started_earlier(self):
        ids = [r.session_id for r in sb.collect(self.proj, since="2026-08-05")]
        self.assertEqual(ids, ["sess-1"])
        ids = [r.session_id for r in sb.collect(self.proj, since="2026-07-01")]
        self.assertEqual(ids, ["sess-0", "sess-1"])

    def test_reports_come_back_oldest_first(self):
        ids = [r.session_id for r in sb.collect(self.proj, since="2026-07-01")]
        self.assertEqual(ids, sorted(ids))


class RunReport(unittest.TestCase):
    def test_a_session_reports_its_own_tokens_and_its_subagents_separately(self):
        main = sb.session_stats([assistant("2026-08-09T00:00:00Z", cr=1_000)])
        sub = sb.session_stats([assistant("2026-08-09T00:05:00Z", cr=2_000)])
        payload = sb.as_dict(sb.SessionReport("s1", main, [sb.Subagent("agent", sub)]))
        self.assertEqual(payload["tokens"]["context"], 1_000)
        self.assertEqual(payload["subagents"][0]["tokens"]["context"], 2_000)
        self.assertAlmostEqual(payload["fanout"], 2.0)


class NoMoney(unittest.TestCase):
    """Pacing is by context. A price creeping back in is the bug, not a feature.

    Dollars came from a rate table the tool could not verify, so its numbers
    moved with the table rather than with the work, and a fixed dollar cap cut
    an expensive session at half the work of a cheap one.
    """

    def setUp(self):
        with open(sb.__file__) as fh:
            self.source = fh.read()

    def test_no_rate_table_and_no_pricing_survive(self):
        for gone in ("RATES", "class Rate", "def cost(", "def run_total(",
                     "def load_rates("):
            # assertNotIn would print the whole file as the failure message.
            self.assertFalse(gone in self.source, "%s should be gone" % gone)

    def test_no_money_flags_survive(self):
        for gone in ("--rates", "--ceiling\"", "--ceiling'"):
            self.assertFalse(gone in self.source, "%s should be gone" % gone)



class FindingItself(unittest.TestCase):
    """A worker deciding when to hand off has to be able to read its own context."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.env)

    def _write(self, name, recs):
        path = os.path.join(self.root, name)
        with open(path, "w") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        return path

    def test_the_session_id_in_the_environment_names_the_transcript(self):
        want = self._write("abc.jsonl", [assistant("2026-08-10T00:00:00Z")])
        self._write("other.jsonl", [assistant("2026-08-10T00:00:00Z")])
        os.environ["CLAUDE_CODE_SESSION_ID"] = "abc"
        self.assertEqual(sb.current_session_path(self.root), want)

    def test_without_the_variable_it_falls_back_to_the_newest_transcript(self):
        old = self._write("old.jsonl", [assistant("2026-08-10T00:00:00Z")])
        new = self._write("new.jsonl", [assistant("2026-08-10T00:00:00Z")])
        os.utime(old, (1, 1))
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.assertEqual(sb.current_session_path(self.root), new)

    def test_a_session_id_naming_no_file_falls_back_and_says_so(self):
        new = self._write("new.jsonl", [assistant("2026-08-10T00:00:00Z")])
        os.environ["CLAUDE_CODE_SESSION_ID"] = "not-on-disk"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(sb.current_session_path(self.root), new)
        self.assertIn("not-on-disk", err.getvalue())

    def test_an_empty_directory_has_no_current_session(self):
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.assertIsNone(sb.current_session_path(self.root))


class HandoffPoint(unittest.TestCase):
    def test_context_now_is_the_last_completed_turn(self):
        recs = [assistant("2026-08-10T00:00:00Z", cr=40_000),
                assistant("2026-08-10T00:05:00Z", cr=210_000),
                assistant("2026-08-10T00:06:00Z", cr=214_000)]
        self.assertEqual(sb.session_stats(recs).ctx_end, 214_000)

    def test_over_the_threshold_is_decided_on_the_latest_context_not_the_peak(self):
        recs = [assistant("2026-08-10T00:00:00Z", cr=250_000),
                assistant("2026-08-10T00:05:00Z", cr=100_000)]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.ctx_peak, 250_000)
        self.assertFalse(sb.past_handoff_point(stats, 200_000))

    def test_at_the_threshold_is_not_yet_past_it(self):
        recs = [assistant("2026-08-10T00:00:00Z", cr=200_000)]
        self.assertFalse(sb.past_handoff_point(sb.session_stats(recs), 200_000))
        recs.append(assistant("2026-08-10T00:01:00Z", cr=200_001))
        self.assertTrue(sb.past_handoff_point(sb.session_stats(recs), 200_000))


class SelfCheck(unittest.TestCase):
    """The verdict a worker acts on after every commit.

    Two strings and two exit codes are the whole contract: the driver's
    protocol block quotes them, and a worker decides whether to keep working
    or write the handoff by reading them. Inverting them silently restores
    the behaviour — one unit of work, then stop — that this tool exists to
    replace, so they are pinned exactly rather than matched loosely.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SESSION_ID", None)

    def write(self, session_id, context):
        path = os.path.join(self.dir, session_id + ".jsonl")
        with open(path, "w") as fh:
            fh.write(json.dumps(assistant("2026-08-10T00:00:00Z", cr=context)) + "\n")
        os.environ["CLAUDE_CODE_SESSION_ID"] = session_id
        return path

    def run_check(self, threshold=200_000, as_json=False):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sb.self_check(self.dir, threshold, as_json)
        return code, out.getvalue(), err.getvalue()

    def test_a_session_under_the_threshold_is_told_to_keep_going(self):
        self.write("s-small", 30_000)
        code, out, _ = self.run_check()
        self.assertIn("keep going", out)
        self.assertNotIn("hand off", out)
        self.assertEqual(code, 0)

    def test_a_session_over_the_threshold_is_told_to_hand_off(self):
        self.write("s-big", 250_000)
        code, out, _ = self.run_check()
        self.assertIn("hand off", out)
        self.assertNotIn("keep going", out)
        self.assertEqual(code, 3)

    def test_the_line_carries_the_turn_the_context_and_the_threshold(self):
        self.write("s-small", 30_000)
        _, out, _ = self.run_check()
        self.assertEqual(out.strip(), "s-small: turn 1, context 30,000 of 200,000 — keep going")

    def test_the_threshold_is_the_one_passed_not_the_default(self):
        self.write("s-mid", 100_000)
        self.assertEqual(self.run_check(threshold=50_000)[0], 3)
        self.assertEqual(self.run_check(threshold=150_000)[0], 0)

    def test_the_output_names_the_session_it_measured(self):
        # The fallback can land on a different session's transcript, and a
        # verdict with no name attached gives a worker no way to notice.
        self.write("s-small", 30_000)
        self.assertIn("s-small", self.run_check()[1])

    def test_json_mode_carries_the_same_verdict_as_a_field(self):
        self.write("s-big", 250_000)
        code, out, _ = self.run_check(as_json=True)
        payload = json.loads(out)
        self.assertEqual(payload["session"], "s-big")
        self.assertEqual(payload["context"], 250_000)
        self.assertTrue(payload["past_handoff_point"])
        self.assertEqual(code, 3)

    def test_a_project_directory_with_no_transcripts_is_an_error_not_a_verdict(self):
        # Reachable when the project directory exists but the session has not
        # written its first turn yet. A verdict here would be invented.
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        empty = os.path.join(self.dir, "empty-project")
        os.makedirs(empty)
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        os.makedirs(os.path.join(root, "empty-project"))
        with mock.patch.object(sb, "PROJECTS_ROOT", root):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = sb.self_check(empty, 200_000, False)
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("no transcript", err.getvalue())

    def test_an_id_that_names_no_file_says_so_rather_than_answering_silently(self):
        # Falling back without a word is how a worker ends up acting on some
        # other session's context and nobody finds out.
        self.write("s-real", 30_000)
        os.environ["CLAUDE_CODE_SESSION_ID"] = "not-a-session"
        _, out, err = self.run_check()
        self.assertIn("not-a-session", err)
        self.assertIn("s-real", out)


def limit_notice(ts):
    """What Claude Code appends when the run is cut off: zero usage, one line."""
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "id": "msg_limit",
            "model": "claude-opus-5",
            "stop_reason": "stop_sequence",
            "content": [{"type": "text",
                         "text": "You've hit your session limit · resets 12:40pm (America/Chicago)"}],
            "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0,
                      "cache_read_input_tokens": 0, "output_tokens": 0},
        },
    }


class CutOffByTheLimit(unittest.TestCase):
    def test_the_limit_notice_does_not_become_the_current_context(self):
        recs = [assistant("2026-08-10T00:00:00Z", cr=210_000),
                limit_notice("2026-08-10T00:01:00Z")]
        stats = sb.session_stats(recs)
        self.assertEqual(stats.ctx_end, 210_000)
        self.assertTrue(sb.past_handoff_point(stats, 200_000))

    def test_the_notice_is_not_counted_as_a_turn(self):
        recs = [assistant("2026-08-10T00:00:00Z", cr=1000), limit_notice("2026-08-10T00:01:00Z")]
        self.assertEqual(sb.session_stats(recs).turns, 1)

    def test_the_report_marks_a_session_the_limit_cut_off(self):
        # A run that stopped because the usage limit hit looks, in every other
        # column, like a run that chose to stop. Without this it reads as a
        # session that handed off early.
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        proj = os.path.join(root, "-repo")
        os.makedirs(proj)
        for name, recs in (
            ("cut", [assistant("2026-08-10T00:00:00Z", cr=90_000), limit_notice("2026-08-10T00:01:00Z")]),
            ("fine", [assistant("2026-08-10T01:00:00Z", cr=90_000)]),
        ):
            with open(os.path.join(proj, name + ".jsonl"), "w") as fh:
                for rec in recs:
                    fh.write(json.dumps(rec) + "\n")

        by_id = {r.session_id: r for r in sb.collect(proj)}
        self.assertTrue(by_id["cut"].hit_limit)
        self.assertFalse(by_id["fine"].hit_limit)
        self.assertTrue(sb.as_dict(by_id["cut"])["cut_off_by_usage_limit"])

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sb.print_table([by_id["cut"], by_id["fine"]], verbose=False)
        cut_row = [l for l in out.getvalue().splitlines() if l.startswith("2026-08-10T00:00")][0]
        fine_row = [l for l in out.getvalue().splitlines() if l.startswith("2026-08-10T01:00")][0]
        self.assertIn("limit", cut_row)
        self.assertNotIn("limit", fine_row)

    def test_a_session_cut_off_by_the_limit_is_recognised(self):
        self.assertTrue(sb.hit_session_limit([assistant("2026-08-10T00:00:00Z"),
                                              limit_notice("2026-08-10T00:01:00Z")]))

    def test_a_session_that_finished_normally_is_not(self):
        self.assertFalse(sb.hit_session_limit([assistant("2026-08-10T00:00:00Z")]))


class Verdict(unittest.TestCase):
    """The one judgement the driver reads: is delegation paying for itself?"""

    def test_fanout_is_subagent_context_over_the_session_s_own(self):
        self.assertAlmostEqual(sb.fanout_overhead(main_tokens=100, sub_tokens=163), 1.63)

    def test_a_session_with_no_subagents_has_no_overhead(self):
        self.assertEqual(sb.fanout_overhead(main_tokens=100, sub_tokens=0), 0.0)

    def test_overhead_is_undefined_rather_than_infinite_when_the_session_read_nothing(self):
        self.assertIsNone(sb.fanout_overhead(main_tokens=0, sub_tokens=5))


class HookCheck(unittest.TestCase):
    """The check that fires whether or not the session decides to look.

    Measured across the last two runs: every worker committed once, near the
    end, and the one budget check it ran landed a turn or two later at 145,000
    to 204,000 — so 29% of one run went on turns already past the line. The
    three moments the contract names are all milestones in the work cycle, and
    a session doing one piece of work reaches them once. This runs from a
    PostToolUse hook instead, which fires on every tool call and needs no
    cooperation from the session.

    Two properties carry the whole design. It is SILENT under the line, because
    anything it prints is context re-paid on every later turn — an announcement
    per tool call would cost more than the overshoot it prevents. And it exits 0
    on every kind of bad input, because a hook that fails loudly injects noise
    into a tool call the session was right to make.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

    def transcript(self, *contexts):
        path = os.path.join(self.dir, "live.jsonl")
        with open(path, "w") as fh:
            for c in contexts:
                fh.write(json.dumps(assistant("2026-08-17T00:00:00Z", cr=c)) + "\n")
        return path

    def run_hook(self, payload, threshold=170_000):
        text = payload if isinstance(payload, str) else json.dumps(payload)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with mock.patch.object(sb.sys, "stdin", io.StringIO(text)):
                code = sb.hook_check(threshold)
        return code, out.getvalue(), err.getvalue()

    def test_under_the_line_it_says_nothing_at_all(self):
        path = self.transcript(40_000, 90_000)
        code, out, err = self.run_hook({"transcript_path": path})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_over_the_line_it_exits_2_so_the_session_cannot_skim_past_it(self):
        # Probed: a hook writing to plain stdout is invisible to the model, and
        # exit 2 with stderr arrives as a blocking error it reads. Exit 0 with a
        # message would be advice the session is free to ignore, which is the
        # failure this replaces.
        path = self.transcript(40_000, 180_000)
        code, out, err = self.run_hook({"transcript_path": path})
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("180,000", err)
        self.assertIn("170,000", err)

    def test_it_reads_the_latest_turn_not_the_peak(self):
        # A session that compacted is genuinely cheaper again, and telling it to
        # hand off on a number it no longer carries would retire a context that
        # has room left.
        path = self.transcript(40_000, 250_000, 60_000)
        self.assertEqual(self.run_hook({"transcript_path": path})[0], 0)

    def test_the_message_says_to_commit_and_rewrite_the_handoff(self):
        # A worker told only that it is over stops where it stands, leaving a
        # dirty tree — which trips the driver's dirty-tree gate and halts the
        # whole run. Naming the two steps is what makes this a handoff rather
        # than an abort.
        path = self.transcript(180_000)
        err = self.run_hook({"transcript_path": path})[2]
        self.assertIn("commit", err)
        self.assertIn("HANDOFF.md", err)

    def test_the_message_names_the_skill_that_writes_the_handoff(self):
        # Measured on the run that prompted this: two work sessions wrote
        # HANDOFF.md with a heredoc rather than through clear-task, one of them
        # saying at 160,121 context that loading the skill "would not leave
        # enough room to finish the file". A peer loaded it from 150,721 and
        # finished the whole handoff at 172,071, so the skill and the file
        # together cost 21,350 against a window of a million. This line is the
        # instruction in the room at that moment, and it named no skill.
        path = self.transcript(180_000)
        err = self.run_hook({"transcript_path": path})[2]
        self.assertIn("clear-task", err)

    def test_the_message_says_the_handoff_point_is_not_a_limit(self):
        # A session reading the number as a wall spends its last turns
        # economising, which is how one of those two talked itself out of
        # loading the skill that owns handoffs.
        path = self.transcript(180_000)
        err = self.run_hook({"transcript_path": path})[2]
        self.assertIn("not a limit", err)

    def test_the_threshold_passed_is_the_one_used(self):
        path = self.transcript(100_000)
        self.assertEqual(self.run_hook({"transcript_path": path}, threshold=90_000)[0], 2)
        self.assertEqual(self.run_hook({"transcript_path": path}, threshold=150_000)[0], 0)

    def test_a_payload_that_is_not_json_is_silently_ignored(self):
        code, out, err = self.run_hook("not json at all")
        self.assertEqual((code, out, err), (0, "", ""))

    def test_a_payload_with_no_transcript_path_is_silently_ignored(self):
        code, out, err = self.run_hook({"tool_name": "Bash"})
        self.assertEqual((code, out, err), (0, "", ""))

    def test_a_transcript_path_that_does_not_exist_is_silently_ignored(self):
        code, out, err = self.run_hook({"transcript_path": os.path.join(self.dir, "gone.jsonl")})
        self.assertEqual((code, out, err), (0, "", ""))

    def test_a_transcript_with_no_usage_yet_is_silently_ignored(self):
        # The first tool call of a session can land before any turn carrying
        # usage has been written. There is no number to judge, so there is no
        # verdict to give.
        path = os.path.join(self.dir, "empty.jsonl")
        open(path, "w").close()
        code, out, err = self.run_hook({"transcript_path": path})
        self.assertEqual((code, out, err), (0, "", ""))

    def test_a_half_written_last_line_does_not_break_the_verdict(self):
        # Transcripts are appended to live, so the hook routinely opens one
        # mid-write. The turns already complete still have to be read.
        path = self.transcript(40_000, 180_000)
        with open(path, "a") as fh:
            fh.write('{"type": "assistant", "message": {"usa')
        self.assertEqual(self.run_hook({"transcript_path": path})[0], 2)


class LoopStateFiles(unittest.TestCase):
    """What a session cost is in the loop's state files, not in its transcript.

    NoMoney forbids a rate table this tool would have to maintain. These files
    carry a price Claude Code itself computed and wrote, so reading one is not
    that — and reading it is the only way to compare an Opus session against a
    Sonnet one, which counting tokens alone gets wrong.
    """

    def state_dir(self, files):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        for name, body in files.items():
            with open(os.path.join(directory, name), "w") as fh:
                json.dump(body, fh)
        return directory

    def test_run_files_are_work_eval_files_are_review_and_order_is_chronological(self):
        directory = self.state_dir({
            "run-20260821T024950-4.json": {
                "session_id": "aaa",
                "total_cost_usd": 6.09,
                "terminal_reason": "completed",
                "modelUsage": {"claude-opus-5": {"costUSD": 6.08}},
            },
            "eval-20260821T025914-3.json": {
                "session_id": "bbb",
                "total_cost_usd": 0.94,
                "terminal_reason": "completed",
                "modelUsage": {"claude-sonnet-5": {"costUSD": 0.94}},
            },
        })
        found = sb.read_loop_sessions(directory)
        self.assertEqual(
            [(s.session_id, s.kind, s.reported_usd) for s in found.sessions],
            [("aaa", "work", 6.09), ("bbb", "review", 0.94)],
        )

    def test_files_without_a_session_id_are_counted_not_silently_dropped(self):
        """The loop's own test suite leaves thousands of these in the real
        state directory: run-shaped, priced 1.25, no session to join them to.
        Dropping them quietly would report a fraction of a run as the whole.
        """
        directory = self.state_dir({
            "run-20260817T003455-1.json": {
                "is_error": False,
                "num_turns": 7,
                "terminal_reason": "completed",
                "total_cost_usd": 1.25,
            },
            "run-20260817T003456-2.json": {
                "session_id": "real",
                "total_cost_usd": 3.0,
                "terminal_reason": "completed",
            },
        })
        found = sb.read_loop_sessions(directory)
        self.assertEqual([s.session_id for s in found.sessions], ["real"])
        self.assertEqual(found.unjoinable, 1)

    def test_a_run_that_ended_on_429_is_recorded_as_cut_off_by_the_limit(self):
        """The 429 is in the run record the loop already writes, so nothing has
        to open a transcript to know a session was cut off rather than choosing
        to stop. Everything the round grouping does rests on this flag.
        """
        directory = self.state_dir({
            "run-20260823T020130-3.json": {
                "session_id": "finished",
                "total_cost_usd": 4.85,
                "terminal_reason": "completed",
            },
            "run-20260823T022107-4.json": {
                "session_id": "cut",
                "total_cost_usd": 1.26,
                "terminal_reason": "api_error",
                "api_error_status": 429,
                "result": "You've hit your session limit · resets 12:30am",
            },
            # An overload is an API error too, and the run it ends can be
            # started again straight away. Reading it as the usage limit would
            # close a round that never ended.
            "run-20260823T023000-5.json": {
                "session_id": "overloaded",
                "total_cost_usd": 0.2,
                "terminal_reason": "api_error",
                "api_error_status": 529,
                "result": "Overloaded",
            },
        })
        found = sb.read_loop_sessions(directory)
        self.assertEqual(
            [(s.session_id, s.cut_off_by_the_limit) for s in found.sessions],
            [("finished", False), ("cut", True), ("overloaded", False)],
        )

    def test_an_unknown_project_stops_rather_than_matching_a_neighbour(self):
        """A wrong-project read is worse than no read. The loop's own test
        fixtures sit in a sibling directory named repo; a fuzzy match that
        reached them would price a run against somebody else's numbers.
        """
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.mkdir(os.path.join(root, "repo"))
        os.mkdir(os.path.join(root, "repo-a"))
        with mock.patch.object(sb, "SESSION_LOOP_ROOT", root):
            self.assertEqual(
                sb.loop_state_dir("/Users/anyone/projects/repo-a"),
                os.path.join(root, "repo-a"),
            )
            with self.assertRaises(SystemExit):
                sb.loop_state_dir("/Users/anyone/projects/repo-b")

    def test_spend_joins_price_to_transcript_and_splits_totals_by_kind(self):
        """Tokens alone rank a Sonnet review beside an Opus session as though
        they cost the same. Splitting by kind is what shows they do not.
        """
        state = self.state_dir({
            "run-20260821T020000-1.json": {
                "session_id": "aaa",
                "total_cost_usd": 6.0,
                "terminal_reason": "completed",
                "modelUsage": {"claude-opus-5": {"costUSD": 6.0}},
            },
            "eval-20260821T021000-1.json": {
                "session_id": "bbb",
                "total_cost_usd": 1.0,
                "terminal_reason": "completed",
                "modelUsage": {"claude-sonnet-5": {"costUSD": 1.0}},
            },
        })
        transcripts = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, transcripts)
        for name, records in (
            ("aaa", [assistant("2026-08-21T02:00:01Z", cr=50000),
                     assistant("2026-08-21T02:05:00Z", cr=120000)]),
            ("bbb", [assistant("2026-08-21T02:10:01Z", model="claude-sonnet-5", cr=60000)]),
        ):
            with open(os.path.join(transcripts, name + ".jsonl"), "w") as fh:
                for record in records:
                    fh.write(json.dumps(record) + "\n")

        report = sb.spend_report(state, transcripts)
        self.assertEqual(
            [(r.session.session_id, r.requests, r.ctx_peak) for r in report.rows],
            [("aaa", 2, 120000), ("bbb", 1, 60000)],
        )
        self.assertEqual(report.usd_by_kind, {"work": 6.0, "review": 1.0})
        self.assertEqual(report.usd_by_model,
                         {"claude-opus-5": 6.0, "claude-sonnet-5": 1.0})

    def test_transcripts_the_loop_did_not_run_are_counted_but_not_priced(self):
        """An interactive session in the same repo leaves a transcript and no
        state file. It spent against the same limit, and nothing here can price
        it, so the count is the only honest thing to report about it.
        """
        state = self.state_dir({
            "run-20260821T020000-1.json": {
                "session_id": "aaa",
                "total_cost_usd": 6.0,
                "terminal_reason": "completed",
            },
        })
        transcripts = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, transcripts)
        for name in ("aaa", "typed-by-hand"):
            with open(os.path.join(transcripts, name + ".jsonl"), "w") as fh:
                fh.write(json.dumps(assistant("2026-08-21T02:00:01Z", cr=1000)) + "\n")

        report = sb.spend_report(state, transcripts)
        self.assertEqual([r.session.session_id for r in report.rows], ["aaa"])
        self.assertEqual(report.not_run_by_the_loop, 1)

    def test_since_filters_the_unpriced_transcripts_too(self):
        """A window's report that counts every interactive session this repo
        ever had reads as though the window contained them.
        """
        state = self.state_dir({
            "run-20260821T020000-1.json": {
                "session_id": "aaa", "total_cost_usd": 6.0,
                "terminal_reason": "completed",
            },
        })
        transcripts = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, transcripts)
        for name, ts in (("aaa", "2026-08-21T02:00:01Z"),
                         ("in-window", "2026-08-21T03:00:00Z"),
                         ("months-ago", "2026-08-01T03:00:00Z")):
            with open(os.path.join(transcripts, name + ".jsonl"), "w") as fh:
                fh.write(json.dumps(assistant(ts, cr=1000)) + "\n")

        report = sb.spend_report(state, transcripts, since="2026-08-21")
        self.assertEqual(report.not_run_by_the_loop, 1)

    def test_the_band_figure_is_a_median_not_the_upper_middle_value(self):
        """Two sessions at $0.10 and $0.20 sit in one band. Reporting $0.20
        rounds a run's headline up, which is the kind of quiet wrong number
        this whole mode exists to stop.
        """
        rows = [
            sb.SpendRow(session=sb.LoopSession("a", "work", 1.0, "20260821T020000"),
                        requests=10, ctx_peak=110_000),
            sb.SpendRow(session=sb.LoopSession("b", "work", 2.0, "20260821T021000"),
                        requests=10, ctx_peak=120_000),
        ]
        [(kind, label, count, median)] = sb.usd_per_request_by_band(rows)
        self.assertEqual((kind, label, count), ("work", "100k-140k", 2))
        self.assertAlmostEqual(median, 0.15)

    def test_work_and_review_sessions_are_banded_separately(self):
        """Reviews run on Sonnet and stop lower, so pooling them with work
        sessions drags the cheap bands down and makes handing off earlier look
        better than it is. That comparison is the only thing this table is for.
        """
        rows = [
            sb.SpendRow(session=sb.LoopSession("w", "work", 5.0, "20260821T020000"),
                        requests=10, ctx_peak=90_000),
            sb.SpendRow(session=sb.LoopSession("r", "review", 1.0, "20260821T021000"),
                        requests=10, ctx_peak=90_000),
        ]
        self.assertEqual(
            [(kind, label, count) for kind, label, count, _ in
             sb.usd_per_request_by_band(rows)],
            [("work", "0k-100k", 1), ("review", "0k-100k", 1)],
        )

    def test_a_session_id_cannot_reach_outside_the_transcript_directory(self):
        """Ids come from JSON in a tree the loop's own tests write into."""
        state = self.state_dir({
            "run-20260821T020000-1.json": {
                "session_id": "../../../etc/passwd",
                "total_cost_usd": 1.0,
                "terminal_reason": "completed",
            },
        })
        transcripts = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, transcripts)
        report = sb.spend_report(state, transcripts)
        self.assertEqual(report.rows, [])
        self.assertEqual(report.unjoinable, 1)

    def test_pacing_never_reads_a_price(self):
        """The moduledoc promises --self and --hook do not look at money.
        NoMoney bans a rate table; this bans the new reader from the decision.
        """
        source = open(sb.__file__).read()
        for name in ("def self_check", "def hook_check", "def past_handoff_point"):
            start = source.index(name)
            body = source[start:source.index("\ndef ", start + 1)]
            for priced in ("reported_usd", "spend_report", "read_loop_sessions",
                           "usd_by_kind", "total_usd"):
                self.assertNotIn(priced, body, "%s must not read %s" % (name, priced))



class WhereTheContextCameFrom(unittest.TestCase):
    """Which content a session re-read, and how many turns re-read it.

    Cache reads are almost all of what a loop run spends, and a total cannot
    say which of them was worth paying. What an addition costs is its own size
    times the number of turns that came after it, so the same paragraph is
    cheap at the end of a session and expensive at the start.
    """

    def test_what_the_turn_wrote_and_what_its_tools_returned_are_charged_apart(self):
        """The turn's own output tokens are the only part of its growth that
        anybody can read off the usage block; the rest came back from the tools
        it called. Charging the whole delta to either one is what makes the
        report say the model wrote 90,000 tokens of prose, or that Bash did.
        """
        thinker = assistant("2026-08-23T00:00:00Z", cw=100, out=40)
        thinker["message"]["usage"]["output_tokens_details"] = {
            "thinking_tokens": 30}
        thinker["message"]["content"] = [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}]
        found = sb.attribute([
            thinker,
            assistant("2026-08-23T00:01:00Z", cr=100, cw=940, out=10),
            assistant("2026-08-23T00:02:00Z", cr=1040, out=10),
        ])
        # 940 arrived: 40 the turn wrote (30 of it thinking), 900 from Bash.
        self.assertEqual(found.by_cause[sb.THINKING], 30)
        self.assertEqual(found.by_cause[sb.ANSWER], 10)
        self.assertEqual(found.by_cause["Bash"], 900)

    def test_the_opening_context_is_charged_once_for_every_later_turn(self):
        found = sb.attribute([
            assistant("2026-08-23T00:00:00Z", cw=100, out=10),
            assistant("2026-08-23T00:01:00Z", cr=100, cw=50, out=10),
            assistant("2026-08-23T00:02:00Z", cr=150, out=10),
        ])
        self.assertEqual(found.total, 250)
        self.assertEqual(found.by_cause[sb.OPENING_CONTEXT], 200)


class FloorAndHandoff(unittest.TestCase):
    """Splitting the opening context into the part a handoff can shrink and
    the part it cannot.

    Both are paid on every turn, so together they are about half of a run — but
    only one of them answers to anything the operator writes. Nothing can
    tokenise the handoff here, so the split is read off how the opening context
    moves as the handoff's length changes across the run's sessions.
    """

    def test_the_floor_is_where_a_handoff_of_no_length_would_land(self):
        found = sb.floor_and_handoff([(10000, 38000), (20000, 42000), (30000, 46000)])
        self.assertEqual(found.floor, 34000)
        self.assertAlmostEqual(found.tokens_per_char, 0.4)

    def test_handoffs_that_never_changed_length_give_no_split_rather_than_a_guess(self):
        """Dividing by a zero spread would either raise or invent a number, and
        an invented floor reads exactly like a measured one.
        """
        self.assertIsNone(sb.floor_and_handoff([(20000, 42000), (20000, 42000)]))

    def test_one_session_is_not_enough_to_read_a_slope_from(self):
        self.assertIsNone(sb.floor_and_handoff([(20000, 42000)]))

    def test_the_handoff_is_the_first_prompt_and_not_the_tool_results_after_it(self):
        """Every later user record is a tool result, and they are much the
        larger share of the file. Measuring the wrong one would put the slope
        on content the operator does not write.
        """
        records = [
            {"type": "user", "message": {"role": "user", "content": "handoff"}},
            {"type": "user", "message": {"role": "user", "content": [
                {"type": "tool_result", "content": "a much longer tool result"}]}},
            {"type": "user", "message": {"role": "user", "content": "later prompt"}},
        ]
        self.assertEqual(sb.opening_prompt_chars(records), len("handoff"))

    def test_a_transcript_with_no_prompt_measures_nothing_rather_than_zero(self):
        self.assertIsNone(sb.opening_prompt_chars(
            [{"type": "user", "message": {"role": "user", "content": []}}]))


def commit_call(tool_id, command="git commit -m x", failed=False):
    """A git-commit tool call and the result that came back, as two records."""
    return [
        {"type": "assistant", "message": {"id": "msg_" + tool_id, "usage": {
            "input_tokens": 1, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0, "output_tokens": 1},
            "content": [{"type": "tool_use", "id": tool_id, "name": "Bash",
                         "input": {"command": command}}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_id,
             "is_error": failed, "content": "out"}]}},
    ]


class DidTheCutOffSessionKeepAnything(unittest.TestCase):
    """Whether a session that ran out of usage left its work behind.

    Nothing else can answer it. The loop writes an iteration record only after
    a session finishes, so the one killed mid-flight has none — and reading git
    instead cannot tell a session that did nothing from one that amended, since
    the commit the amend replaced is reachable from no branch.
    """

    def test_a_commit_that_came_back_clean_counts_as_kept(self):
        self.assertTrue(sb.landed_a_commit(commit_call("t1")))

    def test_a_session_that_never_tried_to_commit_kept_nothing(self):
        records = [assistant("2026-08-24T02:30:00Z", cr=16120, out=800)]
        self.assertFalse(sb.landed_a_commit(records))

    def test_a_commit_that_came_back_an_error_did_not_land(self):
        """The session was cut off, so its last call is exactly the one likely
        to have failed. Counting the attempt would report work that is gone.
        """
        self.assertFalse(sb.landed_a_commit(commit_call("t2", failed=True)))

    def test_reading_the_diff_is_not_committing_it(self):
        self.assertFalse(sb.landed_a_commit(
            commit_call("t3", command="git log -1 --format=%B")))


class Rounds(unittest.TestCase):
    """The work between one usage-limit cutoff and the next.

    This is the unit the operator lives in — "it ran until the credits went,
    then I continued it" — and no single session is that unit. Every session
    report before this one made the operator group the rows by eye.
    """

    def sessions(self, *spec):
        return [
            sb.LoopSession(session_id=sid, kind=kind, reported_usd=0.0,
                           stamp=stamp, cut_off_by_the_limit=cut)
            for sid, kind, stamp, cut in spec
        ]

    def test_a_round_ends_at_the_cutoff_and_the_next_session_opens_a_new_one(self):
        found = sb.rounds(self.sessions(
            ("a", "work", "20260823T003939", False),
            ("b", "work", "20260823T005735", True),
            ("c", "work", "20260823T011647", False),
        ))
        self.assertEqual(
            [[s.session_id for s in r.sessions] for r in found],
            [["a", "b"], ["c"]],
        )

    def test_data_ending_on_a_cutoff_leaves_no_empty_round_behind(self):
        """Every round in the logs so far ends this way — the last session ran
        out of usage and nothing has run since. An empty trailing round would
        divide by zero on every per-round figure.
        """
        found = sb.rounds(self.sessions(
            ("a", "work", "20260825T052445", False),
            ("b", "work", "20260825T054352", True),
        ))
        self.assertEqual([r.number for r in found], [1])
        self.assertEqual([s.session_id for s in found[0].sessions], ["a", "b"])


class WhereARoundWent(unittest.TestCase):
    """The whole report, over the unit the operator actually runs in."""

    def dirs(self, state_files, transcripts):
        state = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, state)
        for name, body in state_files.items():
            with open(os.path.join(state, name), "w") as fh:
                json.dump(body, fh)
        where = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, where)
        for name, records in transcripts.items():
            with open(os.path.join(where, name + ".jsonl"), "w") as fh:
                for record in records:
                    fh.write(json.dumps(record) + "\n")
        return state, where

    def test_a_round_reports_what_it_read_and_what_the_cutoff_threw_away(self):
        state, where = self.dirs(
            {
                "run-20260823T003939-1.json": {
                    "session_id": "kept", "total_cost_usd": 6.0,
                    "terminal_reason": "completed",
                },
                "run-20260823T005735-2.json": {
                    "session_id": "lost", "total_cost_usd": 1.0,
                    "terminal_reason": "api_error", "api_error_status": 429,
                },
                "iter-20260823T003939-1.json": {
                    "head_before": "a" * 40, "head_after": "b" * 40,
                    "commits": 1, "findings_in": None,
                },
            },
            {
                "kept": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 10000}}]
                    + [assistant("2026-08-23T00:39:00Z", cw=38000, out=10)]
                    + commit_call("c1")
                    + [assistant("2026-08-23T00:41:00Z", cr=38100, out=10)]),
                "lost": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 30000}}]
                    + [assistant("2026-08-23T00:57:00Z", cw=46000, out=10)]
                    + [assistant("2026-08-23T00:58:00Z", cr=46000, cw=100, out=10)]),
            },
        )
        rounds = sb.waste_report(state, where)
        self.assertEqual(len(rounds), 1)
        found = rounds[0]
        self.assertEqual((found.number, found.work_sessions, found.commits),
                         (1, 2, 1))
        self.assertTrue(found.cut_off)
        # The cut-off session committed nothing, so everything it read is
        # gone — both its turns, not just what the second one re-read.
        self.assertEqual(found.thrown_away, 46000 + 46100)
        # The breakdown has to add up to what the round read, or it is a story
        # about the tokens rather than an account of them.
        self.assertEqual(sum(found.by_cause.values()), found.total)

    def test_the_opening_context_splits_into_the_floor_and_the_handoff(self):
        """Two sessions whose handoffs differ in length are the whole of what
        separates the fixed part from the part an operator can shrink.
        """
        state, where = self.dirs(
            {
                "run-20260823T003939-1.json": {
                    "session_id": "small", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "run-20260823T005735-2.json": {
                    "session_id": "big", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
            },
            {
                "small": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 10000}}]
                    + [assistant("2026-08-23T00:39:00Z", cw=38000, out=10),
                       assistant("2026-08-23T00:41:00Z", cr=38000, out=10)]),
                "big": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 20000}}]
                    + [assistant("2026-08-23T00:57:00Z", cw=42000, out=10),
                       assistant("2026-08-23T00:58:00Z", cr=42000, out=10)]),
            },
        )
        found = sb.waste_report(state, where)[0]
        self.assertEqual(found.floor, 34000)
        self.assertNotIn(sb.OPENING_CONTEXT, found.by_cause)
        self.assertEqual(found.by_cause[sb.FIXED_FLOOR], 68000)
        self.assertEqual(found.by_cause[sb.HANDOFF], 4000 + 8000)

    def test_a_round_still_running_still_counts_its_last_commits(self):
        """The driver writes an iteration record after the session it is about,
        so the last one in a round carries a later stamp than any session in it.
        Bounding the window at the last session drops that record, and a round
        that has not hit the limit yet reports no commits at all.
        """
        state, where = self.dirs(
            {
                "run-20260826T010000-1.json": {
                    "session_id": "s1", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "iter-20260826T011500-1.json": {
                    "head_before": "a" * 40, "head_after": "b" * 40,
                    "commits": 3, "findings_in": None,
                },
            },
            {"s1": ([{"type": "user", "message": {
                "role": "user", "content": "h" * 10000}}]
                + [assistant("2026-08-26T01:00:00Z", cw=38000, out=10),
                   assistant("2026-08-26T01:10:00Z", cr=38000, out=10)])},
        )
        self.assertEqual(sb.waste_report(state, where)[0].commits, 3)

    def test_a_finished_round_does_not_claim_the_next_rounds_commits(self):
        """The other half of the same window. Opening the last round's upper
        bound must not let a closed one reach past its own cutoff.
        """
        state, where = self.dirs(
            {
                "run-20260826T010000-1.json": {
                    "session_id": "s1", "total_cost_usd": 1.0,
                    "terminal_reason": "api_error", "api_error_status": 429,
                },
                "run-20260826T030000-2.json": {
                    "session_id": "s2", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "iter-20260826T011500-1.json": {
                    "head_before": "a" * 40, "head_after": "b" * 40,
                    "commits": 3, "findings_in": None,
                },
                "iter-20260826T031500-2.json": {
                    "head_before": "b" * 40, "head_after": "c" * 40,
                    "commits": 5, "findings_in": None,
                },
            },
            {
                "s1": [assistant("2026-08-26T01:00:00Z", cw=38000, out=10),
                       assistant("2026-08-26T01:10:00Z", cr=38000, out=10)],
                "s2": [assistant("2026-08-26T03:00:00Z", cw=38000, out=10),
                       assistant("2026-08-26T03:10:00Z", cr=38000, out=10)],
            },
        )
        self.assertEqual([r.commits for r in sb.waste_report(state, where)],
                         [3, 5])

    def test_a_handoff_that_grew_while_the_opening_shrank_is_not_split(self):
        """The floor is not really fixed within a run — a skill added or
        dropped moves it. When it moves enough that a longer handoff opens
        smaller, the fit puts the floor above the opening context and the
        handoff line goes negative, which is not a measurement of anything.
        """
        state, where = self.dirs(
            {
                "run-20260823T010000-1.json": {
                    "session_id": "a", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "run-20260823T020000-2.json": {
                    "session_id": "b", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
            },
            {
                "a": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 10000}}]
                    + [assistant("2026-08-23T01:00:00Z", cw=50000, out=10),
                       assistant("2026-08-23T01:10:00Z", cr=50000, out=10)]),
                "b": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 40000}}]
                    + [assistant("2026-08-23T02:00:00Z", cw=42000, out=10),
                       assistant("2026-08-23T02:10:00Z", cr=42000, out=10)]),
            },
        )
        found = sb.waste_report(state, where)[0]
        self.assertIsNone(found.floor)
        self.assertEqual(found.by_cause[sb.OPENING_CONTEXT], 92000)
        self.assertNotIn(sb.FIXED_FLOOR, found.by_cause)
        self.assertTrue(all(tokens >= 0 for tokens in found.by_cause.values()),
                        found.by_cause)

    def test_a_session_whose_transcript_is_gone_is_counted_not_ignored(self):
        """Its price is in the state file and its tokens are not anywhere. A
        round that stays silent about it reports a fraction of itself as the
        whole, which is the same failure read_loop_sessions counts unjoinable
        files for.
        """
        state, where = self.dirs(
            {
                "run-20260823T010000-1.json": {
                    "session_id": "present", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "run-20260823T020000-2.json": {
                    "session_id": "gone", "total_cost_usd": 9.0,
                    "terminal_reason": "completed",
                },
            },
            {"present": ([{"type": "user", "message": {
                "role": "user", "content": "h" * 10000}}]
                + [assistant("2026-08-23T01:00:00Z", cw=38000, out=10),
                   assistant("2026-08-23T01:10:00Z", cr=38000, out=10)])},
        )
        self.assertEqual(sb.waste_report(state, where)[0].unaccounted_sessions, 1)

    def test_the_flag_prints_a_round_and_its_json_carries_the_same_numbers(self):
        """--spend and --value are both exercised through main(); this one was
        not, which left the printer and the JSON shape able to break without a
        test noticing.
        """
        state, where = self.dirs(
            {
                "run-20260823T010000-1.json": {
                    "session_id": "a", "total_cost_usd": 6.0,
                    "terminal_reason": "api_error", "api_error_status": 429,
                },
            },
            {"a": ([{"type": "user", "message": {
                "role": "user", "content": "h" * 10000}}]
                + [assistant("2026-08-23T01:00:00Z", cw=38000, out=10),
                   assistant("2026-08-23T01:10:00Z", cr=38000, out=10)])},
        )
        with mock.patch.object(sb, "loop_state_dir", lambda _: state), \
                mock.patch.object(sb, "transcript_dir", lambda _: where):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(sb.main(["anywhere", "--waste"]), 0)
            printed = out.getvalue()
            self.assertIn("round 1", printed)
            self.assertIn("committed nothing", printed)

            shaped = io.StringIO()
            with contextlib.redirect_stdout(shaped):
                self.assertEqual(sb.main(["anywhere", "--waste", "--json"]), 0)
        payload = json.loads(shaped.getvalue())["rounds"][0]
        self.assertEqual(payload["round"], 1)
        self.assertTrue(payload["cut_off"])
        self.assertEqual(payload["thrown_away"], 76000)
        self.assertEqual(sum(payload["by_cause"].values()), payload["total"])

    def test_the_reviewer_does_not_drag_the_workers_floor_around(self):
        """The reviewer opens on a different footing — a prompt of a few
        hundred characters and, measured on the real logs, an opening context
        some nine thousand tokens above the worker's floor. Fitting one line
        through both populations reads a floor that neither of them has.
        """
        state, where = self.dirs(
            {
                "run-20260823T003939-1.json": {
                    "session_id": "small", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "run-20260823T005735-2.json": {
                    "session_id": "big", "total_cost_usd": 1.0,
                    "terminal_reason": "completed",
                },
                "eval-20260823T010000-1.json": {
                    "session_id": "reader", "total_cost_usd": 0.5,
                    "terminal_reason": "completed",
                },
            },
            {
                "small": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 10000}}]
                    + [assistant("2026-08-23T00:39:00Z", cw=38000, out=10),
                       assistant("2026-08-23T00:41:00Z", cr=38000, out=10)]),
                "big": ([{"type": "user", "message": {
                    "role": "user", "content": "h" * 20000}}]
                    + [assistant("2026-08-23T00:57:00Z", cw=42000, out=10),
                       assistant("2026-08-23T00:58:00Z", cr=42000, out=10)]),
                "reader": ([{"type": "user", "message": {
                    "role": "user", "content": "r" * 1500}}]
                    + [assistant("2026-08-23T01:00:00Z", cw=44000, out=10),
                       assistant("2026-08-23T01:01:00Z", cr=44000, out=10)]),
            },
        )
        found = sb.waste_report(state, where)[0]
        self.assertEqual(found.floor, 34000)
        self.assertEqual(found.by_cause[sb.FIXED_FLOOR], 68000)
        self.assertEqual(found.by_cause[sb.HANDOFF], 12000)
        self.assertEqual(found.by_cause[sb.REVIEW_OPENING], 44000)


class WhatASessionBought(unittest.TestCase):
    """Cost alone says a run got cheaper; it cannot say it got better.

    The loop writes an iteration record naming the commit range each session
    produced, so the price of a session can be put beside what came out of it.
    Counting commits from `git log` instead is wrong: an amend leaves the
    commit it replaced unreachable, and the session that did the work then
    reads as having produced nothing.
    """

    def state_dir(self, files):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        for name, body in files.items():
            with open(os.path.join(directory, name), "w") as fh:
                json.dump(body, fh)
        return directory

    def test_a_day_carries_its_sessions_its_price_and_what_it_committed(self):
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 2, "findings_in": None,
            },
            "run-20260821T031717-5.json": {
                "session_id": "bbb", "total_cost_usd": 4.0,
                "terminal_reason": "completed",
            },
            "iter-20260821T031717-5.json": {
                "head_before": "c" * 40, "head_after": "d" * 40,
                "commits": 4, "findings_in": None,
            },
        })
        rows = sb.value_report(directory)
        self.assertEqual(
            [(r.day, r.sessions, r.usd, r.commits) for r in rows],
            [("20260809", 1, 30.0, 2), ("20260821", 1, 4.0, 4)],
        )

    def test_what_a_commit_cost_includes_the_review_it_was_read_by(self):
        """The reviewer runs once per iteration and is about a fifth to a
        quarter of what a round spends. Counting only the worker prints a cost
        per commit that no round has ever actually paid.
        """
        directory = self.state_dir({
            "run-20260823T003939-1.json": {
                "session_id": "worker", "total_cost_usd": 6.0,
                "terminal_reason": "completed",
            },
            "eval-20260823T005527-1.json": {
                "session_id": "reader", "total_cost_usd": 1.0,
                "terminal_reason": "completed",
            },
            "iter-20260823T003939-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 1, "findings_in": None,
            },
        })
        row = sb.value_report(directory)[0]
        self.assertEqual((row.sessions, row.usd, row.review_usd), (1, 6.0, 1.0))
        self.assertEqual(row.usd_per_commit, 7.0)

    def test_since_drops_the_iterations_as_well_as_the_sessions(self):
        """Filtering only the sessions would leave a day priced at nothing and
        credited with every commit before it, which reads as free work."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 2, "findings_in": None,
            },
            "run-20260821T031717-5.json": {
                "session_id": "bbb", "total_cost_usd": 4.0,
                "terminal_reason": "completed",
            },
            "iter-20260821T031717-5.json": {
                "head_before": "c" * 40, "head_after": "d" * 40,
                "commits": 4, "findings_in": None,
            },
        })
        rows = sb.value_report(directory, since="2026-08-21")
        self.assertEqual(
            [(r.day, r.sessions, r.usd, r.commits) for r in rows],
            [("20260821", 1, 4.0, 4)],
        )

    def test_a_record_that_will_not_parse_leaves_the_day_unknown(self):
        """A half-written record must not read as a day that committed less than
        it did. The driver truncates the file before writing it, so a run killed
        mid-write leaves exactly this shape behind."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
        })
        with open(os.path.join(directory, "iter-20260809T161303-1.json"), "w") as fh:
            fh.write('{"head_before": "aaa", "commits":')
        rows = sb.value_report(directory)
        self.assertEqual([(r.day, r.commits) for r in rows], [("20260809", None)])

    def test_a_record_whose_count_is_not_a_number_leaves_the_day_unknown(self):
        """Guarding the file that will not parse but not the one that parses to
        the wrong shape leaves the worse failure uncovered: a report that raises
        part-way through says nothing about any day, not just the bad one."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": {"not": "a number"}, "findings_in": None,
            },
        })
        self.assertEqual(
            [(r.day, r.commits) for r in sb.value_report(directory)],
            [("20260809", None)],
        )

    def test_a_count_written_as_a_string_is_read_rather_than_discarded(self):
        """The driver writes this field as a number, so a quoted one means some
        other hand wrote the file — and a quoted 2 still says two commits.
        Discarding it would lose a day's work over punctuation."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": "2", "findings_in": None,
            },
        })
        self.assertEqual(
            [(r.day, r.commits) for r in sb.value_report(directory)],
            [("20260809", 2)],
        )

    def test_the_json_shape_carries_what_the_table_shows(self):
        """--spend builds its JSON through a named function; reading a dataclass
        with vars() instead makes the contract whatever the fields happen to be,
        and drops usd/commit because a property is not a field."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 2, "findings_in": None,
            },
        })
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sb.main([directory, "--value", "--json"]), 0)
        self.assertEqual(
            json.loads(out.getvalue())["days"],
            [{"day": "20260809", "sessions": 1, "usd": 30.0, "review_usd": 0.0,
              "commits": 2, "usd_per_commit": 15.0}],
        )

    def test_the_json_shape_says_null_where_the_table_says_unknown(self):
        """A day with spend and no record is the only shape where the two
        usd/commit branches diverge, so it is the only one that pins them."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
        })
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sb.main([directory, "--value", "--json"]), 0)
        self.assertEqual(
            json.loads(out.getvalue())["days"],
            [{"day": "20260809", "sessions": 1, "usd": 30.0, "review_usd": 0.0,
              "commits": None, "usd_per_commit": None}],
        )

    def test_the_flag_prints_a_day_with_what_its_commits_cost(self):
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "iter-20260809T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 2, "findings_in": None,
            },
        })
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sb.main([directory, "--value"]), 0)
        printed = out.getvalue()
        self.assertIn("20260809", printed)
        self.assertIn("15.00", printed)

    def test_a_day_with_no_record_is_unknown_rather_than_zero(self):
        """Every day before the driver started recording has sessions and no
        iteration files. Printing 0 there says the loop committed nothing, which
        is a claim about the work; the truth is that nothing was written down.
        """
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
            "run-20260810T161303-1.json": {
                "session_id": "bbb", "total_cost_usd": 10.0,
                "terminal_reason": "completed",
            },
            "iter-20260810T161303-1.json": {
                "head_before": "a" * 40, "head_after": "b" * 40,
                "commits": 0, "findings_in": None,
            },
        })
        self.assertEqual(
            [(r.day, r.commits) for r in sb.value_report(directory)],
            [("20260809", None), ("20260810", 0)],
        )

    def test_a_day_that_committed_nothing_is_not_priced_per_commit(self):
        """Dividing by a commit count of zero is the shape that would crash, and
        printing 0.00 would read as a day whose work cost nothing."""
        directory = self.state_dir({
            "run-20260809T161303-1.json": {
                "session_id": "aaa", "total_cost_usd": 30.0,
                "terminal_reason": "completed",
            },
        })
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sb.main([directory, "--value"]), 0)
        day_row = out.getvalue().strip().split("\n")[1]
        self.assertTrue(day_row.startswith("20260809"), day_row)
        self.assertEqual(day_row.split()[-1], "-", day_row)
        self.assertEqual(day_row.split()[-2], "?", day_row)


if __name__ == "__main__":
    unittest.main()
