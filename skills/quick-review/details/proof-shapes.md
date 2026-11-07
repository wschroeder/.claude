# Proof-shape catalog — the artifact that licenses each clean bill

```
Assertion strength /   MUTATIONS THIS REVIEW RAN. Never judge an assertion
test coverage          "specific enough" by reading it, and never cite a
                       mutation an earlier session says it ran.
                       Run one mutation per item below, one at a time, re-run
                       the tests that cover it, and print each result. A
                       mutation a test catches → DEMONSTRATED clean for that
                       item only. Each survivor is a FINDING.
                       - each clause of each acceptance criterion: each
                         bound, count, quantifier, and condition ("ten or
                         fewer", "every", "none covering"), and each member
                         of a list a condition names; a bound over a random
                         or repeated process gets a mutation that breaks it
                         on some runs, not all of them
                       - each constraint of a validation pattern: its
                         length, its character set, and each anchor
                         (`/^[0-9a-f]{40}$/` gets `{7,40}`, `[0-9a-fA-F]`,
                         and a dropped `$`)
                       - each operand of a condition joined by && or ||,
                         dropped alone, and the whole condition forced on
                         and off (`set && !isHash(v)` gets `!isHash(v)`,
                         `true`, and `false`)
                       - each arm of a ladder of fallbacks (a SQL case, a
                         coalesce chain, an if / else if run), and each
                         condition inside an arm
                       - a mutation the card names its test must catch
                       Over each other new or changed function:
                       - put the base version back (git show <base>:<path>)
                       - delete each guard's call, one call site at a time
                       - swap an argument for its sibling (otherField for
                         field), and give the test fixture two different
                         values so the swap shows
                       - serve a cached value without its freshness check,
                         and drop each line that evicts or invalidates an
                         entry
                       - make a value built from several inputs take a
                         property (sureness, source, status) from the first
                       - drop the first or the last element of a span
                       Copy each file aside before you mutate it and restore
                       from that copy, never with git checkout or git
                       restore: both restore from the index, which lacks
                       whatever is not yet staged.
                         cp <path> /tmp/<name>.keep   # before the first
                         cp /tmp/<name>.keep <path>   # after the last
                       Print each one as:
                         clause "<clause>"  mutated <file>:<line>
                           <original> -> <mutated>   <run result>  caught

Atomicity / TOCTOU     Owes two artifacts.
                       AGAINST ITSELF (2.7): run two copies of the path at once
                       and show what each one wrote, OR quote the lock both
                       copies take before their first write (select … for
                       update / advisory lock / CAS whose row count is checked).
                       A transaction boundary alone is NOT proof: under read
                       committed two copies of one transaction interleave.
                       Neither is a grep of a later step that "claims only the
                       newest". Two separate calls with a read between them is
                       a FINDING, not a clean bill.
                       AGAINST OTHER WRITERS (2.18): list every other writer of
                       the same rows and of the parents its foreign keys name,
                       and show the lock or constraint that orders each pair.
                       The self-race run covers only the first artifact and
                       never stands in for this one.
                       BOTH runs assert the invariant the code promises
                       ("at most 30 rows"), counted on the rows afterwards.
                       "No errors" over any number of calls is NOT proof.
                       Run at least replicas × pool size copies at once.
                       READ SKEW (2.19): a path that queries twice, read-only
                       ones included. Run the real writer between the two
                       reads and assert what the path reports. "Read-only,
                       no writes" is NOT an N/A.

Error-return shape     Trigger the error path (probe or test); show the return is the
                       {:error, _} callers destructure, not a raise that aborts the
                       surrounding transaction.
```
