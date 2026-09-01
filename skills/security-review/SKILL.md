---
name: security-review
description: Security review of a code change, scoped the same way the other review commands scope things — working tree, staged, branch, last commit, or a named ref. Use when asked for a security review, to check a diff for vulnerabilities, or when the change-then-review workflow calls for one.
activation:
  - "security-review"
  - "security review"
  - "review for vulnerabilities"
  - "check this for security issues"
---

# Security Review

You are a senior security engineer reviewing a code change for vulnerabilities
that a real attacker could exploit.

This skill replaces the built-in `/security-review`, which hardcoded
`git diff origin/HEAD...` into four shell commands that ran before its
instructions loaded. In a repository with no `origin` remote every one of them
failed with `fatal: ambiguous argument 'origin/HEAD...'` and the skill aborted
before it started. It also never looked at uncommitted work, so the usual case —
"I just changed this, review it" — was outside what it could see.

## Step 1 — Resolve the scope (do this first, with Bash)

Run the commands yourself. Nothing here is embedded in frontmatter, so no git
failure can stop the skill from loading. If a command fails, fall through to the
next option and say which one you landed on.

**Argument vocabulary.** Same as the `quick-review` skill, so the two are asked
for a scope the same way:

```
(no argument)     branch changes plus everything uncommitted   <- default
all               same as no argument
working           uncommitted only: unstaged, staged, untracked
staged            git diff --staged
branch            committed branch changes only, no working tree
last              git show HEAD
<ref>             git show <ref>
<ref>..<ref>      git diff <ref>..<ref>
<PR number>       gh pr diff <number>
```

**Finding the base commit.** Try these in order and stop at the first that
works. Never assume `origin` exists:

1. `git remote` — if it lists a remote, get the default branch from
   `git symbolic-ref --quiet refs/remotes/origin/HEAD`, falling back to
   `git remote show origin | sed -n 's/.*HEAD branch: //p'`. Fetch it, then use
   `git merge-base HEAD origin/<default>`.
2. No remote, or step 1 failed: look for a local `main` then `master` with
   `git rev-parse --verify --quiet <name>`. If one exists and is not HEAD, use
   `git merge-base HEAD <name>`.
3. Neither exists, or HEAD *is* the default branch: there is no branch to diff.
   Review the working tree, plus `git show HEAD` if the working tree is clean.
   Say plainly that this is what you did and why.

**Untracked files are part of the diff.** `git diff` does not show a file git has
never seen, so a brand-new module is invisible to every diff command above. This
is the single most common way a security review silently covers nothing:

```
git status --porcelain          # '??' entries are untracked
```

Read every untracked source file in the scope IN FULL and review it as added
lines. A new file is usually the most security-relevant thing in a change, not
the least.

**Confirm the scope before reviewing.** State in one line what you are reviewing
and how you resolved it — "no remote configured, so: merge-base with local main
(51203bc)..HEAD plus 2 untracked files". If the resolved scope is empty, say so
and stop. Do not review the whole repository because the diff came back blank.

## Step 2 — Read everything in scope

Read the complete diff, no truncation and no `| head -N`, plus every untracked
file. Read surrounding context for each touched file — callers, callees, sibling
functions — because a vulnerability is usually a mismatch between what a function
assumes and what its callers actually pass.

## Objective

Identify HIGH-CONFIDENCE security vulnerabilities with real exploitation
potential. This is not a general code review. Focus ONLY on security
implications newly introduced by this change. Do not comment on pre-existing
security concerns except where the change interacts with them.

1. **Minimize false positives.** Only flag issues where you are >80% confident of
   actual exploitability.
2. **Avoid noise.** Skip theoretical issues, style concerns, and low-impact
   findings.
3. **Focus on impact.** Prioritize what could lead to unauthorized access, data
   exposure, or system compromise.
4. **Exclusions.** Do not report denial of service or resource exhaustion,
   secrets stored on disk that are otherwise secured, or rate limiting.

## Security categories to examine

**Input validation**
- SQL injection via unsanitized input
- Command injection in system calls or subprocesses
- XXE in XML parsing
- Template injection
- NoSQL injection
- Path traversal in file operations

**Authentication and authorization**
- Authentication bypass logic
- Privilege escalation paths
- Session management flaws
- JWT vulnerabilities
- Authorization logic bypasses

**Crypto and secrets**
- Hardcoded API keys, passwords, or tokens
- Weak cryptographic algorithms or implementations
- Improper key storage or management
- Insufficient cryptographic randomness
- Certificate validation bypasses

**Injection and code execution**
- Remote code execution via deserialization
- Pickle injection in Python
- YAML deserialization
- Eval injection in dynamic code execution
- XSS in web applications: reflected, stored, and DOM-based

**Data exposure**
- Sensitive data logging or storage
- PII handling violations
- API endpoint data leakage
- Debug information exposure

Something exploitable only from the local network can still be HIGH severity.

## Methodology

**Phase 1, repository context.** Identify the security frameworks and libraries
already in use, the established secure-coding patterns, and the existing
sanitization and validation helpers. Understand the project's threat model — a
local single-player game and a multi-tenant web service do not have the same one.

**Phase 2, comparative analysis.** Compare the change against those existing
patterns. Deviations from a pattern the codebase already uses are the highest
signal findings available.

**Phase 3, vulnerability assessment.** Trace data flow from untrusted input to
sensitive operations. Look for privilege boundaries crossed unsafely, injection
points, and unsafe deserialization.

## False-positive filtering

Read the code to determine whether a finding is real. You do not need to build an
exploit.

**Hard exclusions.** Automatically drop findings matching these:

1. Denial of service, resource exhaustion, memory or CPU consumption.
2. Secrets on disk that are otherwise secured.
3. Rate limiting or service overload.
4. Missing input validation on non-security-critical fields with no proven
   security impact.
5. Missing hardening. Code is not expected to implement every best practice —
   flag concrete vulnerabilities only.
6. Theoretical race conditions or timing attacks. Report a race only when it is
   concretely problematic.
7. Outdated third-party libraries; these are managed separately.
8. Memory safety issues in memory-safe languages.
9. Files that are only tests or only used to run tests.
10. Log spoofing. Unsanitized input in logs is not a vulnerability.
11. SSRF that controls only the path — SSRF matters when it controls host or
    protocol.
12. User-controlled content in AI system prompts.
13. Regex injection and regex denial of service.
14. Findings in documentation files.
15. Missing audit logs.
16. GitHub Action workflow input sanitization, unless clearly triggerable by
    untrusted input.

**Precedents.**

1. Logging high-value secrets in plaintext is a vulnerability. Logging URLs is
   assumed safe. Logging non-PII data is not a vulnerability even when the data
   feels sensitive.
2. UUIDs are unguessable and need no validation.
3. Environment variables and CLI flags are trusted values. Any attack requiring
   control of them is invalid.
4. Memory and file descriptor leaks are not valid findings.
5. Tabnabbing, XS-Leaks, prototype pollution, and open redirects only count at
   extremely high confidence.
6. React and Angular are generally XSS-safe; do not report XSS in their
   components unless `dangerouslySetInnerHTML`, `bypassSecurityTrustHtml`, or a
   similar escape hatch is used.
7. Most GitHub Action workflow findings are not exploitable in practice. Require
   a specific attack path.
8. Missing permission or authentication checks in client-side code are not
   vulnerabilities — the server is responsible for validating everything it
   receives.
9. Include MEDIUM findings only when they are obvious and concrete.
10. Command injection in shell scripts requires a concrete path for untrusted
    input to reach it.
11. Notebook (`*.ipynb`) findings require a concrete path from untrusted input.

**Signal quality.** For each surviving finding ask: is there a concrete
exploitable path? Is this a real risk or a theoretical best practice? Are there
specific code locations? Would a security team act on it?

## Output

Markdown. One section per finding, most severe first:

```
# Vuln 1: XSS: `foo.py:42`

* Severity: High
* Description: User input from the `username` parameter is interpolated into
  HTML without escaping, allowing reflected XSS.
* Exploit Scenario: An attacker sends /bar?q=<script>alert(document.cookie)</script>,
  executing JavaScript in the victim's browser and enabling session hijacking.
* Recommendation: Escape the value, or render it through a template with
  auto-escaping enabled.
```

**Severity.** HIGH is directly exploitable and leads to remote code execution, a
data breach, or authentication bypass. MEDIUM requires specific conditions but
has significant impact. LOW is defense-in-depth.

**Confidence**, 1 to 10. Report nothing below 8.

State the resolved scope in one line above the findings. When there are no
findings, say so plainly and name what you reviewed — a clean report has to be
distinguishable from a review that looked at nothing, which is the exact failure
this skill was rewritten to prevent.

## Running it

1. Resolve the scope and read everything in it, including untracked files.
2. Use a sub-task to identify vulnerabilities, passing it the categories,
   methodology, and full diff.
3. For each candidate, launch a parallel sub-task to filter false positives,
   passing it the hard exclusions and precedents above.
4. Drop anything the filter scored below 8.

For a small change — a handful of files with no auth, network, or database
surface — do the analysis directly rather than spawning sub-tasks, and say that
is what you did. Spawning three agents to review a forty-line value object costs
more than it finds. The general rule, and the prompt contract for the cases
where delegating does pay, is in `subagents`.
