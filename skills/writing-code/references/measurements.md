# Measurements behind writing-code's rules

The skill body states each rule. This file holds the run that prompted it, for a reader who disputes one.

## Why the report quotes the view whose pattern it copied

Measured: 20 build sessions in a row edited views without opening the UX reference, and the two that did were both told to by their handoff. On the next run three sessions read it, and a bare view name in a report could not show whether the read changed anything.

## Why a stored value is read rather than worked out again

Measured: a preview fetched every selected PDF to count its pages, with that reason, while the query behind it already selected each file's stored page count, and a review then flagged the fetches as slow rather than as unneeded.

## Why you run the change the way a person would before the reviews

Measured: no build session in one run started the app, and the demo's first drive found two bugs.

Measured again on the next run: four build sessions reached the reviews, none started the app, and the demo's first drive found a refusal that showed nothing on the page.

## Why security-review runs only when the diff touches its list

Measured on 2026-09-26 across four repositories: of ten sampled security reviews run on every card regardless, one found an issue, and no path in the shipped code reached it.

## Why help text states facts only, and why any change to on-screen text loads this skill

Measured on 2026-10-28: a slice wrote one-sentence definitions for every figure on two screens. The spec sessions wrote the wording into a design document, and none of them opened the interface reference: no session in the run loaded this skill, and the two that wrote the wording mention the reference zero times. spec-task's help-text check told the writer to keep what the reader should do about a figure, so several definitions shipped carrying advice and predictions. The operator caught them at the demo and said help states facts only.
