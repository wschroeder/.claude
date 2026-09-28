# Destructive-recommendation gate (irreversibility ratchet)

Any finding that proposes DELETE / UPDATE / DROP / TRUNCATE / schema rewrite / data migration to "cleanse"/"reject"/"purge" rows / any other IRREVERSIBLE operation on USER-AUTHORED data must clear an additional precondition:

The finding MUST name the SPECIFIC invariant the existing rows violate AND cite the evidence those rows actually violate it. Acceptable invariants: NOT NULL violation, unique-key violation, FK dangling reference, content-validation rule (regex/length/format), schema-type mismatch, referential-integrity break.

NOT acceptable as "invariant": a new filter, a new authorization predicate, a new visibility scope, an ABAC subject narrowing, an ownership column added to a query. Rows excluded by a filter are legitimate data outside the caller's view — not "leaked," not "invalid," not "stale," not "orphaned."

If the finding cannot name a violated invariant AND cite specific affected rows: **DROP the destructive recommendation entirely**, OR downgrade to Flag with explicit caveats: "the diff filters X; rows excluded by the filter are NOT recommended for deletion, only for visibility scoping."

The default for any irreversible operation on user data is **preserve-and-flag**, never **recommend-deletion-from-pattern-match**.
