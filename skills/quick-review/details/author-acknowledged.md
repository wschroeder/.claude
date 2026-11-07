# Author-acknowledged deviation is not exempt

1. When a moduledoc, comment, docstring, commit message, PR body, the review's own Notes, or the session's handoff acknowledges a deviation from spec, security, or best practice, such as "scope-down on refresh is not supported" or "known limitation upstream", flag it; the acknowledgment is the trigger, never a reason to skip.
2. Treat a later card named as the fix, such as "until <card> lands", as an acknowledgment that this commit ships the failure, and class the finding a Fix or a Flag in this commit, never a Note.
3. Run the Yes-to-any gate against the deviation itself, with no "author already knew" exemption, and let the developer escalate if the team's prior decision should hold.
4. Grep the diff for these acknowledgment terms and check each hit against the gate:

```
# acknowledged   # known            # intentionally    # tradeoff
# TODO           # FIXME            not supported      accepted
we accept        forward-flag       forward flag       pinned to
deferred         defer to           silent zero-row    Q1=A
documented placeholder              intentional placeholder
transitional     pre-P\d            until P\d          for now
until <card> lands                  the card that fixes this
```
