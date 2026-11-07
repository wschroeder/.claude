# Dates, times, and timezones

## Derive from the input, never from "now"

1. Derive every value that depends on a timestamp from that timestamp, such as `DateTime.to_date(timestamp)`, never from `DateTime.utc_now()` or `Date.utc_today()`.

## Match the timezone handling of the functions around you

1. Before converting a timestamp, read how the neighbouring functions in the same pipeline convert theirs, including their fallback when no timezone is given, and convert the same way.
2. Where the project has its own date utility with a defined fallback, use it rather than `DateTime.to_date/1`.

## Respect the owning user's timezone

1. When you derive a date from a timestamp on behalf of a person, such as a due date, a report boundary, or a streak, use that person's timezone when it is known and the project's defined fallback when it is not:

```elixir
case record.created_by do
  %User{timezone: tz} when is_binary(tz) -> to_date(timestamp, tz)
  _ -> to_date(timestamp, nil)
end
```
