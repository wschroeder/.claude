# Parse at the edge, in TypeScript

The rule is in SKILL.md, "Parse at the edge, don't validate inside". This file
says how it looks in TypeScript.

- Parse with a schema library the project already uses (Zod in most of ours)
  at the route, the file reader, the model-reply reader, or the row mapper.
  Export the parsed type from the schema and have inside code take that type.
- Read the edge's own declared type before writing the schema. A framework's
  types usually say exactly what arrives: Hono types `c.req.parseBody()` values
  as `string | File`, so the schema parses a string and refuses a file.
- `unknown` belongs only at the edge, as the input to the parse. An `unknown`
  inside the code, or a `String(value)`, `Number(value)`, or `as` cast applied
  to it, is a missing parse. Trace the value back to where it entered and parse
  it there. Do not answer a linter rule such as `no-base-to-string` with a
  helper that coerces wherever the value lands.
- Use `safeParse` at an HTTP edge and return the refusal yourself. A thrown
  `ZodError` reaches the app's error handler, which usually maps anything that
  is not an HTTP error to a 500.
- On the way out, convert the internal type into what the interface expects:
  decimal strings in a DTO, escaped text in a view, the column's type in a
  query parameter.

Measured (2026-10-14): a lint pass found 13 production `String()`
calls on values typed `unknown`. The session offered three ways to coerce them
inside each function. The operator objected to the premise: the types come from
the call chain, and Hono already declared them.
