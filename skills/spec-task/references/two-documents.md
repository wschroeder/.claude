# Why the design documents and the plan are separate files

- [The rule](#the-rule)
- [Why prose may not point at code](#why-prose-may-not-point-at-code)
- [What the research supports, and what it does not](#what-the-research-supports-and-what-it-does-not)
- [The run that produced this rule](#the-run-that-produced-this-rule)
- [The edge nobody has settled yet](#the-edge-nobody-has-settled-yet)

## The rule

A design document describes the product: the rules of the game or the
business logic of the application, the aesthetic, and the main ideas. A
reader finishes it knowing how the thing behaves. It carries no formulae
and no code, and it leaves only the fuzziness that does not matter.

It says nothing about how any of that is built — no source file, no
function, no test, no engine setting, no configuration key — and it carries
no slice, ticket or card, because those describe a schedule rather than a
product. One exception stands on purpose: a tag on an element saying the
build holds it, so a reader can tell what exists now from what is coming.

A plan describes what is being built next: problem, definition of released,
solution, slices, requirements, test seams, implementation decisions, out
of scope. It holds exactly what a design document may not, it goes stale on
purpose, and it is rewritten every slice.

## Why prose may not point at code

The reason is maintenance, not taste.

Somebody renaming a function has the code open and the design document
closed. A pointer running from prose to code is therefore maintained by
nobody, and it is wrong within weeks — confidently wrong, which is worse
than absent, because a reader trusts it.

A pointer running the other way survives. A doc comment naming the design
section it implements is updated by the same person in the same commit that
renames the thing. So design documents may be pointed at, and they do not
point.

That asymmetry is the whole rule. Reach for it whenever a case is unclear:
ask who would have to open this file to keep the sentence true, and whether
they have any reason to.

## What the research supports, and what it does not

EARS is researched. Alistair Mavin and colleagues at Rolls-Royce published
it at the IEEE Requirements Engineering conference in 2009, out of work on
airworthiness regulations for jet engine controls, reporting reductions
across eight named defect types in requirements. It has since been taken up
at Airbus, Bosch, NASA and Siemens. What it establishes is narrow: a small
set of sentence patterns removes ambiguity, vagueness and incompleteness.
It says nothing about whether a document may name a file, so nothing in
this reference bears on Section 4's use of it.

The separation above is the mainstream practitioner position rather than an
experimental result. Cyrille Martraire's *Living Documentation* is the
book-length treatment of documentation that is generated or verified rather
than hand-duplicated. Gojko Adzic's *Specification by Example* is the other
lineage, and its answer to the same problem is to make the specification
executable, so the link to the code is a test run rather than a citation.
Both distil case studies. Neither is a controlled trial.

The opposite practice exists and is mandated: DO-178C in avionics, and its
equivalents in medical devices and automotive software, require traceability
from requirement to design to code to test. Those regimes maintain the
matrix in tooling, with a compliance budget. Nobody maintains it by hand in
prose, which is the case this rule is about.

## The run that produced this rule

Measured, on a game project in September 2026. The operator asked for a
one-time comparison of the design documents against the code — "we may need
to audit". The session answered itself four minutes later with "the audit is
not a document to write once. It is a missing gate step", specified a
permanent checker over every file path cited in prose, and spent a whole
slice building it and restructuring the documents around it.

Every question put to the operator after that moment took the checker as
settled; none asked whether the thing should be permanent. At the demo they
rejected the premise: design documents are a living description of the
product and never assume implementation, because nobody will maintain a
document full of file paths and nobody will read one.

The measurement that settled it: the entire design set held 39 file
references, and most of the checker's work fell on a survey that a later
slice was already scheduled to delete. The checker, its gate step and the
file references were removed together.

## The edge nobody has settled yet

The done tags are the one implementation-related thing a design document
carries, and nothing yet verifies them. A tag saying the build holds an
element rots exactly the way a file path rots, and a counter that reads the
tag's own words counts claims rather than measuring the build.

No template here writes those tags, either. `spec-task` may not write to a
design document at all, and `demo-task` reconciles the plan's requirement
statuses rather than the product's. Whoever settles this should decide who
writes a done tag and what checks it, before the tags spread.
