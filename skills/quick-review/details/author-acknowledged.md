# Author-acknowledged deviation is not exempt

When a moduledoc, comment, docstring, commit message, PR body, the review's own Notes, or the session's handoff acknowledges a deviation from spec / security / best practice — "we accept the LB-collapse here", "scope-down on refresh is not supported", "intentionally non-strict", "matches library posture", "known limitation upstream", "forward-flag for P6.5", "Q1=A pending column rekey", "silent zero-row until X lands" — the acknowledgment is the TRIGGER to flag, NOT a reason to skip.

A later card is an acknowledgment too. "Until abc-0m9 lands" or "abc-0m9 is the card that fixes this" says the commit ships the failure, so the finding is a Fix or a Flag in this commit, not a Note. Measured (2026-10-13): a review put a sync rollback under its own "## Notes" as "Until abc-0m9 lands … abc-0m9 is the card that fixes this", and that card was queued behind another.

The Yes-to-any gate has no "author already knew about it" exemption. Run the gate against the deviation itself; if it fires on any axis, the finding stands. Flag it, and let the developer escalate if the team's prior decision should hold.

Acknowledgment language is a SEARCH TERM, not an absolution. Grep for these in the diff and verify each is gate-clean:

```
# acknowledged   # known            # intentionally    # tradeoff
# TODO           # FIXME            not supported      accepted
we accept        forward-flag       forward flag       pinned to
deferred         defer to           silent zero-row    Q1=A
documented placeholder              intentional placeholder
transitional     pre-P\d            until P\d          for now
until <card> lands                  the card that fixes this
```

Such a comment is the signal to evaluate the gate, not a license to skip it.
