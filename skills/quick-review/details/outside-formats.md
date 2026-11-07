# Outside formats and outside input

Read this file now, before Pass 1, when the diff parses a format that comes from outside (a file, a model's reply, a third-party payload) or takes input from outside the process. Angle 4.26, every variant the format allows, stays in the body.

Each angle below belongs to the pass its number names. Walk it in that pass, give it a disposition, and print its line in the Checklist under that pass.

### 4.24 CWE-20 input validation

Trusting the shape, type, or range of an input without a check. A raw outside value that travels past the edge, or is coerced where it lands, is a finding: parse it at the edge. This is the one security angle quick-review keeps; `writing-code` says which diffs also owe `security-review`.

## Checklist lines

```
Pass 2:
  2.22  Partial compatibility check      a check that two things fit: every field
                                          the consumer reads from each is compared
Pass 4:
  4.24  CWE-20 input validation          trust shape/type/range without check;
                                          a raw outside value past the edge, or
                                          coerced where it lands → parse at the edge
  4.25  Linked-input normalization       outside data that links its own records:
                                          loops of any length, not only self-links
```

### 2.22 Partial compatibility check

A check that two things fit together, such as one config naming another's files, a schema checked against a reader, or a source borrowing another source's inputs, has to compare every field the consumer reads from each. List those fields from the consumer's code, then quote where the check compares each one. A field the consumer reads and the check skips lets a pair through that fails later, away from the check that should have named it.

Worked example: `fileCheck` in a client repository refused a source whose named role had a different primary file kind. If the named role had a CSV alternative or `multiFile`, the picker would offer it and `runLocal` would then throw, because the check never compared either. The subagent arm of the 2026-10-22 review trial found it by probing both; the single session did not.

### 4.25 Linked-input normalization

When data from outside the system (model output, an uploaded file, a form) carries links between its own records, such as parent ids, references, or next pointers, check what the normalizer does with a loop. Clearing a link to a missing record and clearing a self-link handle loops of length zero and one, and `a → b → a` survives both. For each loop that survives, ask what the downstream code computes: a tree walk may hang, and a sum or check over "top-level" records may silently see none.

Worked example: extracted section totals named a parent section. The importer cleared unknown parents and self-parents, so a model result with two sections naming each other survived. It left no top-level totals, and each section's check passed by summing the other's printed value while unrelated line items still matched the total. A review had noticed the possible loop but asked only whether rendering could hang. The fix follows each parent chain and makes every section on a loop top-level, so each is checked against its line items on its own.

**Discovery method:** for each linked field in outside input, build the two-record loop by hand and run it through the normalizer and the check that consumes it.
