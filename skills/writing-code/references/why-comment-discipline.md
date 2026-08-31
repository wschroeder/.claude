# Why comment discipline is a rule and not a preference

The evidence behind the **Comments** section of `writing-code`. Read when the rule
is disputed, or when deciding whether a particular comment is worth its cost.

- Comments do not measurably improve correctness. Nielebock, Krolikowski, Krüger,
  Leich and Ortmeier (*Empirical Software Engineering* 24(3), 2019) put 277
  mostly-professional developers on bug-fixing and extension tasks under three
  conditions — no comments, implementation comments, documentation comments — and
  found no meaningful difference in accuracy; documentation comments raised the
  variance in completion time. Participants believed comments helped more than the
  results showed, and rated proper identifiers as more helpful than comments.
- Comments go stale by default. Wen, Nagy, Bavota and Lanza (*ICPC* 2019), across
  1,500 Java projects and 3.3 million commits, found only 13–20% of code changes
  trigger a comment update.
- The cost falls on every read. A comment is written once and read by every later
  session. In this codebase file contents are about 40% of everything a session
  loads, and about half of the source lines are comments.
