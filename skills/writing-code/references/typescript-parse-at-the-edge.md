# Parse at the edge, in TypeScript

1. Apply SKILL.md's "Parse at the edge, don't validate inside" in TypeScript with these rules.
2. Parse with a schema library the project already uses, such as Zod, at the route, the file reader, the model-reply reader, or the row mapper, export the parsed type from the schema, and have inside code take that type.
3. Read the edge's own declared type before writing the schema, such as Hono's `string | File` for `c.req.parseBody()` values, and parse what it declares.
4. Allow `unknown` only at the edge, as the input to the parse; treat an inside `unknown`, or a `String(value)`, `Number(value)`, or `as` cast on one, as a missing parse, and parse it where it entered.
5. Never answer a linter rule such as `no-base-to-string` with a helper that coerces wherever the value lands.
6. Use `safeParse` at an HTTP edge and return the refusal yourself, because a thrown `ZodError` usually becomes a 500.
7. On the way out, convert the internal type into what the interface expects, such as decimal strings in a DTO, escaped text in a view, or the column's type in a query parameter.
