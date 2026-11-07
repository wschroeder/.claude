# Destructive-recommendation gate (irreversibility ratchet)

1. Apply this gate to any finding that proposes DELETE / UPDATE / DROP / TRUNCATE / schema rewrite / data migration to "cleanse"/"reject"/"purge" rows / any other IRREVERSIBLE operation on USER-AUTHORED data.
2. Require the finding to name the specific invariant the existing rows violate and to cite evidence that those rows actually violate it.
3. Accept only these as invariants: NOT NULL violation, unique-key violation, FK dangling reference, content-validation rule (regex/length/format), schema-type mismatch, referential-integrity break.
4. Never accept a new filter, authorization predicate, visibility scope, ABAC subject narrowing, or ownership column added to a query as an invariant, because rows a filter excludes are legitimate data outside the caller's view.
5. If the finding cannot name a violated invariant and cite the affected rows, then drop the destructive recommendation entirely, or downgrade it to a Flag that says: "the diff filters X; rows excluded by the filter are NOT recommended for deletion, only for visibility scoping."
6. Default to preserving and flagging user data, never to recommending deletion from a pattern match.
