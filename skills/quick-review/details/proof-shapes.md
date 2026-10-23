# Proof-shape catalog — the artifact that licenses each clean bill

```
Assertion strength /   RECEIPT. Quote the tdd-cycle 4a mutation receipt for each
test coverage          assertion the diff adds, from the card note, the handoff,
                       or this session. Do not mutate again here.
                       Receipt present and "caught" → DEMONSTRATED clean.
                       Receipt missing, or "survived" with no tightened
                       assertion after it → FINDING, fixed by running 4a.
                       Never judge an assertion "specific enough" by reading it.
                       No receipt exists, as on a branch this session did
                       not build: run these mutations yourself, one at a
                       time, over each new or changed function, and print
                       each result. Each survivor is a FINDING.
                       - put the base version back (git show <base>:<path>)
                       - delete each guard's call, one call site at a time
                       - loosen a validation pattern one constraint at a
                         time (length, character set, anchor)
                       - swap an argument for its sibling (otherField for
                         field), and give the test fixture two different
                         values so the swap shows
                       - make a value built from several inputs take a
                         property (sureness, source, status) from the first
                       - drop the first or the last element of a span

Injection / untrusted  Feed the adversarial input through the REAL entry point and
input                  show it rejected/escaped, OR quote the exact line that
                       parameterizes/neutralizes and show the value cannot reach a
                       raw sink. "No literal DROP found" is NOT proof.

Authorization scope    Construct the row the new gate should exclude; run the
                       query/resolver AS the unprivileged subject; show it is absent
                       from the result. "The gate looks correct" is NOT proof.

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
