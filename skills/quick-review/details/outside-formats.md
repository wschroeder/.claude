# Outside formats and outside input

1. Read this file now, before Pass 1, when the diff parses a format that comes from outside (a file, a model's reply, a third-party payload) or takes input from outside the process. Angle 4.26, every variant the format allows, stays in the body.
2. Walk each angle below in the pass its number names, give it a disposition, and print its line in the Checklist under that pass.

### 4.24 CWE-20 input validation

1. Flag any input whose shape, type, or range is trusted without a check, including a raw outside value that travels past the edge or is coerced where it lands, and give the fix as parsing it at the edge.
2. Treat this as the one security angle quick-review keeps; `writing-code` says which diffs also owe `security-review`.

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

1. For a check that two things fit together, such as one config naming another's files, a schema checked against a reader, or a source borrowing another source's inputs, list every field the consumer reads from each, from the consumer's code.
2. Quote where the check compares each field, and report each field it skips as a finding.

### 4.25 Linked-input normalization

1. When outside data, such as model output, an uploaded file, or a form, links its own records through parent ids, references, or next pointers, build a two-record loop `a → b → a` by hand and run it through the normalizer and the check that consumes it.
2. Count clearing missing and self links as no defense against longer loops.
3. For each loop that survives, say what the downstream code computes, such as a tree walk that hangs or a sum over top-level records that sees none.
