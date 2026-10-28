# Measurements behind spec-task's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why a case that breaks an earlier card's path belongs in that card

Measured (2026-10-13): a review noted a refresh rollback "Until abc-0m9 lands", and abc-0m9 depended on abc-a3y.

## Why a sentence a user reads goes through writing-prose at spec time

Measured on 2026-10-27: a build session rewrote an explanatory paragraph on a page while loading five skills, none of them `writing-prose`, and the operator called the result's grammar horrendous at the demo. The fix put the rule in `writing-code`.

Measured on 2026-10-28: a build session loaded `writing-code`, committed a new warning sentence and a new explanatory sentence without loading `writing-prose`, and copied both word for word from the cards' acceptance criteria. The spec session that wrote those cards loaded neither `writing-prose` nor any skill that names it. The wording was settled at spec time, so the rule moved here.

## Why help text is checked against the screen it explains

Measured (2026-10-27): a slice wrote a help manual for an app's screens. It passed the spec, twelve build sessions, and review, and the operator rejected it at the demo because most of it restated what the screens already showed. Nothing in the spec had asked whether a passage told the reader anything new.
