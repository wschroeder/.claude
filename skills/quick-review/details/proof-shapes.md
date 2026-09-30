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

Atomicity / TOCTOU     Show the single-transaction boundary in the code (one call /
                       advisory lock / CAS). Two separate calls with a read between
                       them is a FINDING, not a clean bill.

Error-return shape     Trigger the error path (probe or test); show the return is the
                       {:error, _} callers destructure, not a raise that aborts the
                       surrounding transaction.
```
