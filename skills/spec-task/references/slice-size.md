# What a slice holding four features cost

The rule in Section 1 — one slice, one feature — comes from a slice that held
four. This is what that looked like from the operator's side.

## The slice

S4 on the SEVEN project, "reach it with your thumb", shipped sixteen closed
cards. Its `a person can` line joined every one of them: tap a building's door
to walk over and go inside, tap the road out to leave, tap a tab to turn
straight to a page of the character sheet, tap a card and then tap the slot it
goes into, and touch nothing smaller than a thumb.

Read as capabilities a player would think of separately, the sixteen cards fall
into four groups:

```
  navigating between areas
    walk the party to a tapped door and take them inside
    drop a routed walk when the player does something else
    leave the party standing when a door has no route
    make the road out of a town a tap target
    settle the town's one control on BUILD

  swapping the cards in a build
    put three tabs across the character sheet
    swap a card by tapping the card and then the slot
    let a chosen card go when it is tapped again
    hold as many lines as fit, and map the number keys to them

  making every target big enough for a thumb
    ask every screen for its tap targets, and raise every one to 48 units
    name the tap before the key in every hint

  driving the game without a person at the keyboard
    send a click at a point from a drive script
    hold a key down for a count of frames
    refuse a drive script that cannot be read
    print the screen a drive finished on, and walk into a lurker
    teach just test to take the name of a single test
```

## What it cost

The first card landed at 11:48 on a Friday. The operator saw the result at
08:19 on the Saturday, twenty hours and thirty-one minutes and fourteen commits
later, and two of their three pieces of feedback were about that first card.

Their words at the demo, on the two features that shared the slice:

> I also noticed that once I was inside a building, the only way to leave it
> was with a LEAVE button, which is inconsistent. We need one way to do this
> stuff, consistent.

> For the card swaps, why is there still the TAKE option? Why is there a
> currently selected equipped card instead of my swap selection only? We need
> just one way to do it, not competing approaches. It was very confusing.

And their words at the retro that followed, which is where the rule comes from:

> Card swaps for builds is a different feature from navigation between areas,
> so that could have been separate slices. I wasn't too concerned about testing
> both, but a coherent story of features is usually nicer to keep in mind when
> opening the project.

## What the rule is not

It is not a card count. The slices before this one closed six cards and nine
cards, and the number was never what made them readable. A slice of nine cards
that a person can describe in one sentence passes; a slice of four that needs
two sentences does not.

Tooling a slice needs in order to prove itself rides along with that slice. The
five cards above that built a way to drive the game came from the operator
asking to be able to test without a person at the keyboard, and they belong to
whichever slice first needs them — not to a story of their own, and not spread
across a slice that was already carrying three other stories.
