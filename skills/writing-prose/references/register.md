# Register — how much distance to write from

Read this before writing as the operator to someone they have written to before, such as a Slack message, a DM, or a short email to a colleague. It holds register: how formal to be, how warm, and how much of the reader's own world to explain back to them. `~/.claude/CLAUDE.md` "Communication Style" owns the sentence, and the skill body owns composition; this file restates neither. A first contact with a stranger, and anything a wider audience reads, defaults formal, and this file does not apply to either.

## What is in here

- [Stand level with the reader](#stand-level-with-the-reader)
- [Cut what the reader can supply](#cut-what-the-reader-can-supply)
- [Write as you would say it](#write-as-you-would-say-it)
- [Let the thread set the frame](#let-the-thread-set-the-frame)
- [What holds in the formal register too](#what-holds-in-the-formal-register-too)
- [Extending this file](#extending-this-file)

## Stand level with the reader

1. Narrate the attempt, as "I was trying to run X, starting with Y", never as "I want to run X", which turns a message between peers into a ticket.
2. When the reader owns the system you are asking about, ask the open question first, saying what you did and leaving room for a different answer, and only then offer your diagnosis as a guess.
3. Stack the softeners on that diagnosis: "I wonder whether", "I believe", "might just be", and "if I am reading this right".
4. Count the softeners by hand by grepping your draft for those four phrases, because the `hedges` band of `scripts/voice_stats.py` measures approximation words, not these, and a passing score says nothing about register.
5. Stack softeners only when you ask the reader to give you something, such as a grant, an action, or their time; use none when you report what you found and ask what they meant by it.
6. Inside a finding, state a measured number bare, give one softener such as "looks like" to a claim that the measured parts explain the total, and report the measured period in the past tense rather than projecting a trend.
7. Never explain the reader's own system back to them: name what you need and stop.

## Cut what the reader can supply

1. Quote only evidence the reader cannot infer: one code block, holding the earliest output that surprised you, never an error your previous sentence already predicted.
2. In a post that asks nothing, state what the data shows and stop; cut what held steady, what you could not check, guesses about the cause, a next step nobody asked for, and a number restated in other units.
3. Keep a guess only when the message asks someone who can confirm it.
4. Give each item's number and its explanation together on one bullet, after a ` - `, and never return to items in later paragraphs under bold labels.
5. Ask for the thing and offer no easier alternative; if you would rather they took the other path, then ask for that path instead.
6. Name the identifier, such as an object id, an account name, or a principal, in the clause that introduces the list of things to grant, giving one identifier rather than two.
7. Put that list in bullets, one role-and-scope pair per bullet, never run together in one sentence.
8. Cut a locator the reader already knows, such as a path to the code, a directory name, or a repository-relative reference.
9. Never write a closing aside about the operator's own history, and leave no placeholder for one; end the draft at the ask.

## Write as you would say it

1. Use no em-dashes; a comma, a full stop, or a colon does the same work.
2. Use no imagery and no performing verbs, such as "poking at" or "before it stopped me"; say what you ran and what came back.
3. Use contractions, and prefer "if" to "whether" and "there's" to "there is".
4. Let two or three words close a thought as a fragment.
5. Type a Slack bullet as `* `, never `•`.

## Let the thread set the frame

1. Start cold in a conversation that was live within the day, open with a greeting after a long gap, and never greet mid-thread, because a greeting reads as a new conversation.
2. Let the thread decide the emoji, and add none to a request just to be liked.

## What holds in the formal register too

1. Apply these in a design document as much as in a DM: narrate the attempt, leave the premise open, refuse to explain the reader's system to them, quote only what they cannot infer, ask for the thing without an escape hatch, put the identifier inside the sentence that asks, cut the locator the reader already knows, and leave the operator's personal material to the operator.
2. Read the channel before you apply the rest: the greeting, the emoji, and everything under writing as you would say it.

## Extending this file

1. Before adding a rule, read what the operator actually sent to that reader, compare it against a draft they rejected, and name the difference; if you cannot point at a sent message for a rule, then you invented it.
2. Run `scripts/voice_stats.py` over both the sent message and the rejected draft, then look at which tokens produced each score before you trust a band's difference.
3. Add no rule that needs material only the operator holds; leave that slot out of the draft and let them fill it.
4. Add nothing here that names a person or quotes a message, because this file publishes.
