# Register — how much distance to write from

Two other places own the rest, and this file never restates them.
`~/.claude/CLAUDE.md` "Communication Style" owns the sentence: the actor and the
verb, commas, invented labels, where the ask goes. The skill body owns
composition: what gets said, in what order, under what headings. Neither one
says how formal to be, how warm, or how much of the reader's own world to
explain back to them. That gap is register, and it is what this file holds.

Read this before writing as the operator to someone they have written to before
— a Slack message, a DM, a short email to a colleague. A first contact with a
stranger defaults formal, and so does anything a wider audience reads; this file
does not apply to either.

## What is in here

- [Stand level with the reader](#stand-level-with-the-reader) — narrate the
  attempt, open the premise before you diagnose, stack the softeners for an ask
  and drop them for a finding, refuse to explain their system back to them.
- [Cut what the reader can supply](#cut-what-the-reader-can-supply) — one code
  block holding the earliest surprise, no escape hatch, the identifier inside
  the ask and the grants in bullets, no locator they already know, and none of
  the operator's personal material.
- [Write as you would say it](#write-as-you-would-say-it) — no em-dashes, no
  imagery, contractions, fragments allowed.
- [Let the thread set the frame](#let-the-thread-set-the-frame) — the greeting
  and the emoji.
- [What holds in the formal register too](#what-holds-in-the-formal-register-too)
- [Extending this file](#extending-this-file)

## Stand level with the reader

**Narrate the attempt.** "I was trying to run X, starting with Y" tells the
reader what you did and lets them locate the failure inside it. "I want to run
X" asks them to grant something, which turns a message between peers into a
ticket.

**Leave the premise open, and open it before you diagnose.** When the reader owns
the system you are asking about, they know things you do not, and your diagnosis
may be answering the wrong question. Ask the open question first, then offer what
you think is happening. The open question says what you did and leaves room for a
different answer: you used the only X you had access to, and you wonder whether
there is a different one you should be using. The diagnosis comes after it and
stays a guess: you believe the real problem might just be Y. Stack the softeners
on the diagnosis. The reader can promote a guess to a fact in one line, and
talking you out of an assertion costs them a paragraph.

**Count the softeners by hand, because no band measures them.** The words doing
this work are "I wonder whether", "I believe", "might just be", and "if I am
reading this right". Measured on one pair against the same reader: the operator's
diagnosis carried four of them and a model draft of the same request carried two,
and the two-softener version read as a grant request. `scripts/voice_stats.py`
has a `hedges` band with a floor of 8.0, and it does not measure this: its
vocabulary is approximation words like "a bit" and "roughly". On that pair its
only match sat inside the closing personal aside this file tells you not to
write, and with the aside stripped both texts score 0.0 and both miss the band.
The band also inverts on this. Measured on a second pair in the same channel, a
rejected draft scored 16.7 and passed while the sent message scored 0.0 and
missed, and the draft's only matching token was one approximation word inside a
clause the operator cut. A passing `hedges` score is not evidence the register is
right. Grep your own draft for the four phrases above.

**The softeners belong to the ask, not to the reader.** Stack them when you are
asking the reader to give you something: a grant, an action, their time. Drop
them to zero when you are reporting what you found and asking what they meant by
it, because nothing is being requested and softening a factual question turns it
back into one. Measured across three messages to one reader in one channel, the
two asking for a grant carried four softeners each and the one asking about
intent carried none, and the operator's rewrite of a model draft of that third
message cut both softeners the draft had put in.

**Never explain the reader's own system back to them.** Working out why a
permission is missing feels like diligence, and writing that up for the person
who built the thing reads as a lecture. Name what you need and stop, and leave
the mechanism for the reader to supply, because it is usually theirs to explain.

## Cut what the reader can supply

**Quote only evidence they cannot infer.** One code block, holding the output
that surprised you. An error your previous sentence already predicted is
padding, and padding is what makes a short message read as a memo. When a chain
of commands failed, the useful output is the earliest one that surprised you, and
it is rarely the loudest one at the end. Measured: a model draft quoted a
three-line authorization failure carrying a request id and a timestamp, then
spent its next paragraph explaining that failure away, while the operator's
message quoted one line from the check upstream of it and never mentioned the
failure at all. A request id looks like evidence and buys the reader nothing once
the diagnosis is right.

**Ask for the thing, and drop the escape hatch.** Offering an easier alternative
— "or you could just do it yourself and send me the output" — feels generous and
lands as a message unsure whether it is asking for anything. If you would
genuinely rather they took the other path, then ask for that path instead.

**Put the identifier inside the sentence that asks.** An object id, an account
name, or a principal introduced in its own paragraph under the ask reads as a
fact appended to the message. Name it in the clause that introduces the list, so
the list reads as things to grant that principal. Give one identifier, not two:
an object id makes the email address redundant. Put the list in bullets, one
role-and-scope pair per bullet. CLAUDE.md owns the general rule; the failure
worth naming here is that a draft obeying every other rule in this file will
still run three pairs into one sentence with two "and"s.

**Cut the locator the reader already knows.** A path to the code, a directory
name, or a repository-relative reference tells a reader who works in that
repository nothing. "in `dev`" carries everything "drifted from what's in
`infra/envs/dev`" carries.

**Leave the operator's personal material to the operator.** A closing aside about
your own history — an approach you used years ago, a tool you have since
dropped — is not yours to write, because you do not hold the material and you
will invent it. Measured: one draft closed on a fabricated anecdote about a setup
script the operator had never carried, and the operator's own message closed on a
real one from years earlier that no model could have known. End the draft at the
ask. Leave no placeholder inviting one either: the operator adds these unprompted
when they have something to add.

## Write as you would say it

Measured on one pair against the same reader: the operator's sent message ran 127
words with no em-dashes, and the model's draft of the same request ran 266 with
two.

**No em-dashes.** They mark a sentence as written, and a message to a colleague is
a spoken one. A comma, a full stop, or a colon does the same work.

**No imagery, and no performing verbs.** "I was poking at the dev environment
this morning", "before it stopped me", "before I sit and watch a refresh time
out" — each of those acts the attempt out instead of reporting it. Say what you
ran and what came back.

**Use contractions.** Measured on one pair against the same reader: the
operator's sent message carried three and the model's draft of the same request
carried none, reaching for "cannot" where a contraction would do. "Whether" for
"if" and "there is" for "there's" are the same tell. A draft can obey every other
rule here and still read formal on this alone.

**A fragment is a complete move.** Two or three words closing a thought reads as
speech, and reaching for a full clause to carry the same content adds distance.

## Let the thread set the frame

**A greeting resets a thread.** A conversation that was live within the day
usually carries its own opening, so start cold. Open with a greeting after a
long gap. Open with one mid-thread and the reader reads it as a new
conversation.

**Let the thread decide the emoji.** Warmth already established elsewhere in the
channel needs no re-establishing inside a working message. A request carrying
its own emoji is asking to be liked while it asks for something else.

## What holds in the formal register too

These say nothing about register, and they apply to a design document as much as
to a DM: narrate the attempt, leave the premise open, refuse to explain the
reader's system to them, quote only what they cannot infer, ask for the thing
without an escape hatch, put the identifier inside the sentence that asks, cut
the locator the reader already knows, and leave the operator's personal material
to the operator.

The rest depend on the thread's state or on how the two of them already write to
each other: the greeting, the emoji, and everything under writing as you would
say it. Read the channel before you apply them.

## Extending this file

Every rule above came from reading the operator's own sent messages in a channel
and comparing them against a draft they had rejected as verbose. Do that again
before adding anything: read what they actually sent to that reader, and name
the difference. If you cannot point at a sent message for a rule, then you
invented it.

Run `scripts/voice_stats.py` over both the sent message and the rejected draft
before you write the rule, then look at which tokens produced each score. A band
that one passes and the other misses looks like it has named the difference, and
what it has named is whatever its own vocabulary matched, which may be a phrase
sitting in the part of the message this file tells you to cut. One rule here was
written from a 16.7 against a 0.0 before anyone checked that the 16.7 came from
two words in a closing aside, and it claimed a gate that does not exist.

A rule you cannot follow without inventing content does not belong here at all.
The closing personal aside was one: it called for an anecdote out of the
operator's own history, so every model following it made one up, and the invented
version got the operator wrong. If a candidate rule needs material only the
operator holds, then leave that slot out of the draft and let them fill it.

Add nothing here that names a person or quotes a message. This file publishes.
