# Proof-shape catalog — the artifact that licenses each clean bill

```
Assertion strength /   RECEIPT. Quote the tdd-cycle 4a mutation receipt for each
test coverage          assertion the diff adds, from the card note, the handoff,
                       or this session. Do not mutate again here.
                       Receipt present and "caught" → DEMONSTRATED clean.
                       Receipt missing, or "survived" with no tightened
                       assertion after it → FINDING, fixed by running 4a.
                       Never judge an assertion "specific enough" by reading it.

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

Error-return shape     Trigger the error path (probe or test); show the return is the
                       {:error, _} callers destructure, not a raise that aborts the
                       surrounding transaction.
```
