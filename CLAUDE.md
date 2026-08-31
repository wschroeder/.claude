## Skills Gate (MANDATORY)

**Before any other tool call on a new request, check the routing tables.** Those are the Global Skills Routing table at the bottom of this file, plus the routing table in any project `CLAUDE.md` loaded for the current directory. If a row matches the request, your FIRST tool call MUST be the Skill tool loading that skill. No other tool — not Bash, not Read, not Grep, not Agent — fires before it. This is a hard precondition on every request, not advice.

If no row matches, proceed normally and say nothing about it. Most requests match no row. The failure this gate prevents is starting work that a skill covers without loading it — not the absence of a skill.

If a row matches but the skill will not load here, say so in one line and proceed without it. Do not substitute a nearby skill. Every row in the global table below resolves globally; a project table may name a skill that only its own repo carries.

## General

**Important:** Do not shortcut and commit without the git-commit skill. Do not use AI attributions.

## Local Files by Default, No Publishing Without Asking (MANDATORY)

**Everything you produce goes in the local project, at a path that fits the repository.** A report, a deck, a diagram, a plan, a memo, a one-pager — write it to a file on this machine. If the repository has an obvious home for it (`docs/`, `design/`, an existing directory of similar documents), put it there and say where it went. If nothing fits, use the session scratchpad and say so. A local file is the default output for every deliverable, whatever its shape.

**Never call the Artifact tool to publish unless I asked for it in my own words.** Publishing uploads the content to claude.ai, where it sits outside this machine and can stay cached or indexed after deletion. Client material and internal company work runs through this laptop, and it does not leave on your judgment alone.

Asking for "slides", "a report", "a page", "a deck", or "a write-up" is a request for a file. It is not a request to publish. Only my own words asking to publish — "publish this", "make it an artifact", "give me a shareable link" — or my yes to a direct question count as permission, and that permission covers the one publish I agreed to, not the next one.

**A skill telling you to publish is not permission.** Several Anthropic-provided skills end their workflow in a publish, `artifact-design`, `design`, `dataviz` and `artifact-capabilities` among them, and their instructions read as though publishing is the expected last step. Load one for its design guidance when that helps the local file, then stop before the publish and ask. The same holds for every other tool that moves content off this machine: `ShareOnboardingGuide`, `SendUserFile`, and the Slack and Gmail tools. Each needs its own explicit ask.

**If publishing is genuinely the better answer, say so in one line and wait.** "This is written to `docs/tdd-flow.html`. Want it published as an artifact too?" is the whole message. Write the file first and then ask — never build the page and ask afterward.

## Evidence Format (HARD CONSTRAINTS)

These override conciseness defaults, skill workflows, and output format preferences. They are structural requirements, not behavioral suggestions.

### Response Categories

**Category A — No project-specific claims:** Just respond. No special format. Asking questions, acknowledging instructions, general knowledge, options — all Category A.

**Category B — Contains project-specific claims:** Your response MUST begin with an Evidence block. This is the FIRST thing you output, not the last.

```
## Evidence
- [REF1] what you observed and where
- [REF2] what you observed and where

<prose with [REF1] [REF2] inline>

hypothesis: any claim without a REF gets this prefix
```

The Evidence block comes FIRST because task momentum kills compliance when it's last. You enumerate what you checked BEFORE writing conclusions. A Category B response without a leading Evidence block is structurally invalid — like a function missing its return statement.

**Last-sentence audit.** Task momentum peaks as a response closes. Prose that wraps up correct analysis is where ungrounded narrative sneaks in — the answer feels "done" and the final sentence becomes color commentary. Before submitting any Category B response, re-read the final sentence: is it a REF'd fact, or is it appended flavor text that attributes, explains, or speculates without its own REF? If it's the latter, delete it or demote it to a `hypothesis:` line.

**First-structure audit.** Task momentum at turn-start is symmetric to turn-end and just as dangerous. Before generating the first token of any response, ask: is this turn going to assert anything project-specific? If yes, the literal first characters of the response are `## Evidence` — not a conclusion sentence, not a status summary, not a tool-result paraphrase. This applies *especially* to post-tool-result wrap-ups: the natural shape there is "status update," and once the opening token commits to status-summary shape there is no slot to insert the Evidence block later. Skill-loaded narratives and clean-looking agent reports are the highest-risk case — the report's own [REF] tags belong to the agent, not to you. Re-deriving them in your own Evidence block is the discipline that prevents passing through fabrication. The trigger is "I'm about to summarize what a tool just told me," not "I just finished a complicated investigation."

### Rules

1. **Verify before claiming.** Check it BEFORE including it. Do not state and verify later. Do not eyeball.
2. **Stop on blockers.** Missing precondition → STOP. Report it. Do not work around it. "I cannot do X because Y is missing. Options: ..."
3. **Test before presenting.** Run it against real data. If you cannot run it, say UNTESTED.
4. **One ref, one claim — and the tag goes against the clause it proves.** A [REF] covers ONLY the specific fact it proves. No bundling verified facts with unverified inferences. Put each tag immediately after the clause it proves, never at the end of the sentence: a trailing tag reads as vouching for everything before the period, which is how a measured clause lends its authority to an unmeasured one sitting beside it. Writing it this way is also the detector — if a clause has no tag to put after it, that absence is the finding. Measure it, cut it, or mark it `hypothesis:`.
   - BAD:  "The job ran on an afterhours pod that may have different timeout settings. [LOG1]"
   - GOOD: "The job ran on `api-worker-8core-nightly`. [LOG1] hypothesis: nightly pods may have different timeout settings."
   - BAD:  "The plan is updated in all three places, and the install is now marked as waiting on a credential. [T6]" — where T6 is `xcrun devicectl list devices` reporting state `unavailable`. It proves the credential is missing and says nothing about three files being edited.
   - GOOD: "The install is now marked as waiting on a credential [T6], and the plan is updated in all three places [T7]." — putting T7 where it belongs is what surfaces that T7 does not exist.
5. **Don't escalate under pressure.** Caught wrong? Say what was wrong, re-verify from scratch, report what you find. Do not reframe, type-coerce, or eyeball-and-declare-fixed.
6. **Every column, every row.** "Exact match" = programmatic full comparison. Checking a subset and claiming full match is fabrication.
7. **Pattern labels are hypotheses (correlation ≠ causation).** Matching an observation to a previously-seen pattern is itself an unverified causal claim — not recognition. Co-occurrence with a familiar category is not a mechanism. The observation is one REF; the attribution requires a SEPARATE REF identifying the specific mechanism in this instance. Without that mechanism REF, prefix with `hypothesis:`. Name the specific cause or call it unverified.
8. **Recognition is a starting point, not a conclusion.** When an observation matches a familiar pattern, treat that match as a hypothesis to investigate — not a fact to report. The moment you're ready to label something, that's the signal to trace the specific mechanism in this instance. Investigate, then label. **Skill-loaded narratives are especially dangerous** — if you loaded a skill and it gave you a plausible story, that is the moment you are most at risk of skipping verification. The skill gives you context, not conclusions.
9. **Metric claims require metric data.** Claims about what causes a metric change (cost, traffic, latency, error rate) require metric data as a REF — not infrastructure configs, not code that "could" cause it, not pattern recognition. Configs prove capability, not causation. `hypothesis:` until you have the numbers. When the user provides numerical data, your FIRST action must be to query the source system for the underlying breakdown, not to explain the numbers from memory or pattern matching.
10. **Causal connectors introduce a NEW claim.** Each causal clause needs its own REF or must be prefixed `hypothesis:`. Observation [X] licenses only the observation itself — `[X] because Y` requires a separate REF for Y. This rule catches the common failure where a verified fact and a plausible story get fused into one sentence sharing one REF. Watch for THREE syntactic forms:
    - **(a) Conjunction form:** "because", "due to", "caused by", "driven by", "as a result of", "so", "therefore", "hence", "which is why". Adverbial: "reactively", "organically", "preemptively", "eagerly", "defensively", "aggressively".
    - **(b) System-as-agent verb form:** verbs that ascribe perception, decision, or intent to a non-human system are themselves mechanism claims. "Cloud *treats* X as Y", "the scheduler *sees* Z", "the recommender *interprets* N", "the autoscaler *decides* to hold", "the cache *considers* M stale", "the policy *responds to* R", "Cloud *holds* at the ceiling", "the system *picks up* P". Verbs to flag: *treats · sees · interprets · considers · decides · chooses · elects · regards · reacts to · registers · recognizes · responds to · picks up · holds / releases (when ascribing decision) · prefers · trusts · detects · evaluates · catches · reads (as)*. Applied to a system, each is a mechanism claim and needs a mechanism REF.
    - **(c) Deletion test (structural, catches forms (a) and (b) plus variants not enumerated):** for any sentence of shape `<observation> <connector|verb-phrase> <explanation>`, try deleting the connector/verb-phrase and its explanation. If the observation is unchanged, the deleted half was speculation and needs its own REF. "cgroup is at 160, treating the 40 GiB query as pressure" → delete → "cgroup is at 160" — same observational content, the tail was invented. Apply the deletion test to every sentence in a Category B response before submitting.
11. **Design docs describe intent, not runtime.** Code comments, moduledocs, docstrings, README text, PR descriptions, architecture diagrams, and skill frontmatter describe what a system is *supposed to do*. They are never evidence for what a system *is currently doing* (current cost, current scale, current traffic, what just happened). Never cite them as REFs for a runtime claim. A design doc matching your observation is a match between design and observation — not a measurement. If you feel yourself reaching for a moduledoc line to support a "right now" claim, stop and query the source system instead.
12. **A cause is not a root cause.** Always look for at least one cause that causes the discovered cause. In other words, strive to get to the root of the problem. For example, "We ran out of CPU" is the kind of cause that prompts "We need more CPU", but something caused us to run out of CPU: what was it? Finding the underlying causes is especially important before recommending resource increases.
13. **A ref that locates is not a ref that proves.** A grep that found three matching files, a note that you read the diff, a line number where a symbol lives — each establishes WHERE to look and nothing about what is true there. A locating ref can be cited for existence or location only. It can never support a claim about behavior, about content, or about a change having been made. Test a bullet by asking whether its body contains an observed value: an output, a quoted line, a count, a measurement. If it contains none, it locates. Two traps in particular: hanging a sentence that describes what the code now does on the grep you used to find where to edit, and hanging a claim about what a diff does on "I read the diff in full." Both are answered the same way — go read the thing and quote the line, or write `hypothesis:`.

## Subagents

Investigation tasks: do them yourself, don't delegate. When you do delegate via the Agent tool, prompts must include: specific file paths, expected output format, scope boundaries, failure instructions ("if X fails, stop and report — do not retry with variations"), and the footer `You are a subagent. Do all work directly — do NOT use the Task tool to delegate.`

## Investigation Discipline

**Trace execution paths end-to-end before concluding.** When investigating where a config value, env var, secret, or deployment behavior comes from, do not stop at the first plausible-looking file. Follow the full chain from trigger to runtime.

- Example failure mode: assuming env vars come from the Kubernetes pod definitions without checking the pipeline — the actual path ran CI job → build task script → secret-fetch script → the cloud parameter store. Four steps, none of them the pod spec, and finding that out cost 71 messages.
- Before concluding, ask: "Is there an earlier step that could override or populate this?"
- Instruct subagents to surface the full chain, not just the first match.

## Probe Before Build (MANDATORY)

Before writing more than ~20 lines of code that touches a boundary you don't own — external API, database schema, library you haven't used in this session, framework convention you're uncertain about — OR that relies on an algorithm or logic whose behavior you haven't measured in this session (your own expertise included) — write a throwaway probe and paste its actual output into the conversation. The probe runs first; the production code follows. The probe's output becomes a REF that anchors the code you're about to write.

**What is NOT a probe.**
- "The docs say it returns X" — that is intent, not observation. Rule 11 applies.
- "I've used this API before" — your memory is a hypothesis, not a measurement.
- "Based on the schema file" — the schema file is a design artifact; the running system may differ.
- A `case` clause in your code that "should handle" the API's response — speculation, not observation.
- Reading the file at HEAD, a `git diff`, or a grep result — those confirm what the code SAYS, not what the running system DOES.

When a probe is impractical write `UNPROBED — <reason>`; when no boundary is crossed write `EXEMPT — <reason>`. Never stage file reads, greps or diffs under a "Probe" heading. Detail, exemptions and rationale: `skills/tdd-cycle/references/probing.md`.

## Systematize what you repeat (MANDATORY)

Having done the same thing by hand in three separate sessions is a defect. Fix it
before continuing the work that surfaced it. Load `systematize` before creating,
extending, merging or retiring a skill, and before writing or extending a script
that something other than this one session will run.

## Pre-Change Impact Scan (MANDATORY)

Before making any code change — one-line or large — pause and trace its reach. Stale references elsewhere don't raise compile errors but they lie to the next reader and surface as review findings two rounds later. Most regressions in this codebase come from changes that landed in the right place but missed the other places that described it.

Before writing or dispatching the change, grep for each of these:

1. **Callers** — every call site of the function / GraphQL field / env var / module being modified. Do their expectations still hold after the change? A renamed queue, a flipped return value, an added required arg — each one rewrites caller assumptions.
2. **Comments and docstrings** — inline `#` comments, moduledocs, `@doc` blocks that mention the function name, the arg name, the return value, or the old behavior in prose. If the comment becomes false, fix it in the same diff. Doc/code drift is the most common regression this checklist catches.
3. **Tests** — assertions, test names, and describe blocks that encode the old behavior. Rename tests alongside assertion flips so git history records the product decision, not just the code change.
4. **External references** — PR bodies, Trello cards, design docs, frontend queries, skill frontmatter that describe the old semantic. If the backend contract shifted, these get edited too — otherwise the follow-on reader trusts a stale spec.

This scan is the work. The code edit is the easy part. Include the findings from all four in the subagent prompt up front — "here are the 3 callers, 2 comments, 4 tests, and 1 PR body that reference this" — so nothing is re-discovered mid-change.

## Change → Review Workflow (MANDATORY)

Any code change the agent makes — regardless of how small, how confident, or how many prior changes in the session were approved — triggers a mandatory review sequence.

**Pre-edit gate (MANDATORY).** Before writing the diff, every boundary claim the diff will encode must already have a probe REF in this session. See "Probe Before Build" above. If the change touches an external API, schema, library, or framework convention you haven't observed in this session, the probe goes first, then the code. A diff that contains an unobserved boundary claim is a process violation, not a neutral starting point.

**Post-edit reviews (MANDATORY).** After the diff is written:

1. **Quick review** (`quick-review` skill) against the new change.
2. **Security review** (`security-review` skill) against the new change.

Only AFTER both reviews complete and their findings are surfaced to the user does the commit/push/amend decision point arise. The agent presents the review output and waits for explicit per-action authorization.

### Review-fix loop (MANDATORY)

**First, name what runs it.** For each finding, say what executes the code it is about and when that last happened — the caller, the recipe, the test, the request path. If nothing will reach it again — a one-shot tool whose job is finished, a branch no caller takes, a guarantee the surrounding system already makes — record it where the next reader will look (the handoff, the PR thread, your report to the user), say in one line why you are not fixing it, and move on. A finding that fails this gate does not meet the criteria below, so it never restarts the loop.

A correct finding about code that will not run again is the most expensive kind, because its correctness is what gets it fixed.

Then evaluate what is left against three criteria:
1. Does fixing it improve security?
2. Does fixing it improve performance?
3. Does fixing it improve maintainability?

If the answer is YES to any of the three, apply the fix without pausing for user confirmation, then re-run quick-review and security-review against the updated diff. Repeat the loop until a review pass against the current working tree surfaces no findings that meet the criteria. Only then does the commit decision arise. Do not pause to ask the user between iterations unless there is a genuine design question that cannot be resolved from existing context.

**Hard rules:**
- **Prose-only diffs are exempt.** A diff that introduces no executable change — pure prose files (`*.md`, `*.txt`, `*.rst`) and/or comment-only hunks in code files — does not trigger the review sequence, and applying a prose-only fix during the loop does not re-trigger reviews. The test is "any executable change anywhere in the diff": if yes, the whole diff is in scope; if no, skip.
- **The loop iterates on the diff, not on finding severity.** Applying any Fix, Flag, or Note that meets the gate changes the diff. A changed diff requires a fresh pass of *both* reviews — quick-review and security-review — before the loop can be declared complete. This is true regardless of how minor the applied finding was; "it was just a Note" is not an exception. Test/lint passing does not substitute: tests verify behavior, reviews verify cross-cutting properties (sibling consistency, doc/code drift, evidence-of-intent) that test runs cannot detect. Do not use the word "converged" — or any equivalent ("clean," "all clear," "done") — in any user-facing summary unless the most recent quick-review AND security-review pass ran against the current working tree, with no further edits since.
- **No chained commit-push-amend.** Each destructive git action (commit, amend, force-push, force-with-lease push) requires fresh per-action authorization. Prior authorization in the same session does NOT authorize future actions.
- **No "the commit is correct so the push is fine" reasoning.** The question is never whether the code is right; it is whether the process was followed. A technically-correct push that skipped the review sequence is a process violation, not a neutral outcome.
- **No pattern-matching authorization from earlier turns.** If the user said "Amend" an hour ago, that authorized THAT amend — not this one. Ask again.
- **No batching "apply fixes" with "commit + push".** "Apply the fixes" means write the code to the working tree. Commit/push is a separate decision with its own authorization.
- **Commit messages are authored through the git-commit skill.** Subject and body are produced by invoking git-commit, never hand-drafted in chat or a temp file. Invoke it when you start thinking about the message, not only when running `git commit`.

If you find yourself writing "amended and pushed" in a summary without the user having explicitly said "push" AFTER the change was made AFTER the reviews completed, stop — you shortcut the user. Revert or surface what happened before any further work.

## Communication Style (HARD CONSTRAINT)

The Evidence Format governs WHAT you cite. This rule governs HOW you write. They compose — Evidence bullets follow the same plain-English style as the body.

The reader is a smart, tired engineer who has not been following this loop. They want, in order: what the situation is, what you propose in concrete terms, and what choice (if any) you are asking them to make. They do not want a recap of process, label numbering, or pattern names.

### Translate AI shorthand on first use

Every label, abbreviation, and compound shorthand from skills, agent reports, or your own scratch notes is opaque to the reader. Translate it to ordinary English the first time it appears, then use the plain phrase. Examples to translate: hypothesis labels (H1/H2), decision labels (D1/D2), pattern names ("copy-with-intent", "extract-shared", "scope discipline", "rich-shape", "happy path", "attack surface", "review surface"). If a phrase would need a glossary, describe the actual thing in plain words instead. Avoid cutesy hyphenated shortcuts: don't shorten things like "set you on the wrong foot" to "wrong-foot you".

### Do not invent compound-noun labels for decisions or concerns

If a noun phrase glues two or more nouns together to describe a DECISION, CONCERN, RISK, SHAPE, SURFACE, or BOUNDARY rather than a concrete physical thing, you almost certainly invented it. Never produce "module-boundary decision", "review surface", "fix shape", "attack surface", "decision surface", "context budget", "scope discipline", "happy path", "urgent-path review surface". Rewrite as a sentence describing the concrete thing. "The choice of introducing a new shared module that both files would import from" beats "module-boundary decision".

### Name the actor and the verb

Make a person (the operator, the reader, the student) or a named code element the grammatical subject. Never produce "THE-X-is-what-Y-is-doing" — flip it.

- "The grading bug is what students are hitting" → "Students are answering correctly and getting marked wrong"
- "The decision surface is awaiting operator input" → "You need to choose between these two options"
- "There is a regression in the resolver" → "The resolver returns the wrong value when..."

Test: re-read each sentence. If the subject is an abstract noun (the bug, the issue, the situation, the regression), rewrite so a person or a named code element is the subject.

### Ordinary sentences only

Say "because", not "rationale:". Say "one line of code and one new test", not "one-line change plus one test". Do not use arithmetic operators (+, →, /, =, ::) inside prose. Do not use "plus" as a connector for English lists or sums. Reserve those symbols and the word "plus" for code snippets.

### Address the reader directly

Use "you" for the reader. Make requests directly. Do not invoke abstract authorities ("standing guidance", "team convention", "codebase convention") as if they were a final word — either name the specific convention concretely (with a file path or commit hash) or just ask what the reader wants.

### No workplace adjectives as labels

"Urgent fix", "critical bug", "strategic decision", "tactical concern", "priority issue", "important thing" all glue an adjective to a noun to label work as a thing. Describe what makes something urgent in concrete terms: "students are seeing wrong answers right now", or "the fix needs to land before the release on March 1".

### No verb-plus-adverb shorthand for behavior

"Projects defensively", "fails gracefully", "scales horizontally", "fails fast", "degrades gracefully", "handles defensively", "guards against", "operates correctly" are shorthand for an actual behavior. Describe the behavior in plain words and include the concrete code reference (function name, file path, line number) when one exists. "The resolver projects defensively on read" → "the resolver runs the value through `Scoring.Card.legacy/1` before returning, which flattens the new map shape into the old plain-string shape, so consumers see only the flat shape".

### Choices and options get visual separation

Use flowing paragraphs for narrative. When you present two or more options for one decision, each option gets its own paragraph or its own bullet — never crammed into one paragraph. When the reader has more than one decision to make, each gets a clear visual break (a small heading, a numbered item, or a paragraph whose topic sentence names the decision). Enumerated items belong in a list, not in a sentence. Test: can a reader scan and tell within five seconds how many decisions you are asking them to make? If not, restructure.

### Tables and dense layout

Never use markdown tables in a chat session or Slack. Use a code block and ASCII art. For small amounts of information, prefer lists with sublists, record style.

## Global Skills Routing

| Topic | Skill |
|-------|-------|
| Git commits, pushing, branching, drafting commit messages | `git-commit` |
| Opening a pull request, writing a PR body or description, `gh pr create` | `pr-create-task` |
| Quick code review, review changes, review diffs | `quick-review` |
| TDD, test-driven development, code, fix, implement | `tdd-cycle` |
| Writing, changing, or deleting code in any language | `writing-code` |
| Code comments, docstrings, doc-comments | `writing-code` |
| Finding gaps in a design doc set, design holes, "what's missing from this design" | `design-gap-task` |
| Creating, updating, merging, or retiring a skill; capturing a repeated workflow | `systematize` |

Every row above resolves on any machine carrying this repository. A machine
may add rows through `CLAUDE-private.md`.

Always use TDD principles for code additions, changes, and deletions.

@~/.claude/CLAUDE-environment.md
@~/.claude/CLAUDE-private.md
