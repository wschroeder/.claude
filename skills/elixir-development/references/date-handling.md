# Dates, times, and timezones

## Derive from the input, never from "now"

When processing a timestamp, derive every dependent value from that timestamp — not
from `DateTime.utc_now()` or `Date.utc_today()`. Otherwise a backdated record
processed through an admin tool or a data migration silently gets today's date.

```elixir
# Bad — uses current time instead of the input
def process_timestamp(timestamp) do
  date = Date.utc_today()
  ...
end

# Good — derives from the actual input
def process_timestamp(timestamp) do
  date = DateTime.to_date(timestamp)
  ...
end
```

## Match the timezone handling of the functions around you

Before converting a timestamp, read how the neighbouring functions in the same
pipeline convert theirs, including what they fall back to when no timezone is
given. A function that converts in UTC while its callers and siblings convert
through a project utility with a non-UTC fallback produces dates that disagree by a
day near midnight.

Where a project has its own date utility with a defined fallback, use it rather than
`DateTime.to_date/1`, so the fallback stays consistent across the codebase.

## Respect the owning user's timezone

When a date is derived from a timestamp on behalf of a person — an assignment's due
date, a report boundary, a streak — use that person's timezone when it is known, and
the project's defined fallback when it is not.

```elixir
case record.created_by do
  %User{timezone: tz} when is_binary(tz) -> to_date(timestamp, tz)
  _ -> to_date(timestamp, nil)
end
```
