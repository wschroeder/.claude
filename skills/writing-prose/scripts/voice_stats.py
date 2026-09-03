#!/usr/bin/env python3
"""Measure the prose habits the operator's voice rules are stated in terms of.

Rates are per 100 sentences so a short deliverable and a long one compare.
Bands are seeded from a measured comparison against the operator's own writing;
override with --band name=min:max. Exits 1 when a band is missed.
"""
import argparse, json, re, statistics, sys

BANDS = {           # name: (min, max) rate per 100 sentences, None = unbounded
    "inversions": (None, 2.0),
    "hedges": (8.0, None),
    "long_sentences_pct": (20.0, None),
}
# Reported but NOT gated: the detector counts any mid-sentence capitalised token,
# so a deliverable's own step labels ("Probe", "Green", "Red") inflate it and it
# scores well on prose that names nothing concrete. Read the number, do not trust
# it as a gate until it distinguishes proper nouns from capitalised labels.
ADVISORY = ("not_uses", "named_specifics", "short_sentences_pct", "em_dashes")
HEDGES = (r"pretty much|a bit|I'm sure|hopefully|a little|roughly|about|mostly|"
          r"usually|often|tends to|and so on|so far|for now|in practice")
# Saying what a thing is NOT before saying what it is. Counting the bare word
# "not" instead lets the same habit through under a synonym ("rather than") and
# pushes a rewrite toward swapping words rather than restructuring the sentence.
INVERSIONS = (r",\s*not\b|\bis not\b[^.]{0,80}\.\s*It is\b|\brather than\b|"
              r"\binstead of\b|\bas opposed to\b|\bnot\b[^.]{0,40}\bbut\b")
MAXIM = re.compile(r"^(?:A|An|The|One)\s+\S+(?:\s+\S+){0,8}\s+is\s+(?:\S+\s*){1,6}\.$")


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+", text) if s.strip()]


def load(path, is_json):
    if not is_json:
        return open(path, encoding="utf-8").read()
    data = json.load(open(path, encoding="utf-8"))
    parts = []
    for unit in data["units"]:
        parts.append(unit.get("headline", ""))
        parts += [p["text"] for p in unit.get("prose", [])]
    return re.sub(r"\s+", " ", " ".join(parts))


def measure(text):
    sents = sentences(text)
    n = len(sents) or 1
    words = [len(s.split()) for s in sents]
    rate = lambda count: round(100.0 * count / n, 1)
    named = [t for s in sents for t in s.split()[1:]
             if re.match(r"^[A-Z][a-z]{2,}", t) or re.search(r"[a-z][._-][a-z]", t)]
    return {
        "sentences": len(sents),
        "median_words": statistics.median(words) if words else 0,
        "inversions": rate(len(re.findall(INVERSIONS, text, re.I))),
        "not_uses": rate(len(re.findall(r"\bnot\b", text, re.I))),
        "hedges": rate(len(re.findall(HEDGES, text, re.I))),
        "named_specifics": rate(len(named)),
        "long_sentences_pct": round(100.0 * sum(1 for w in words if w >= 20) / n, 1),
        "short_sentences_pct": round(100.0 * sum(1 for w in words if w <= 5) / n, 1),
        "em_dashes": len(re.findall("—", text)),
        "maxim_candidates": [s for s in sents if MAXIM.match(s)],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="path is the outline extractor's JSON output")
    ap.add_argument("--band", action="append", default=[], metavar="NAME=MIN:MAX")
    args = ap.parse_args()
    bands = dict(BANDS)
    for spec in args.band:
        name, _, pair = spec.partition("=")
        if name not in BANDS:
            raise SystemExit("unknown band %r; known: %s"
                             % (name, ", ".join(sorted(BANDS))))
        low, _, high = pair.partition(":")
        try:
            bands[name] = (float(low) if low else None, float(high) if high else None)
        except ValueError:
            raise SystemExit("band %s needs MIN:MAX numbers, got %r" % (name, pair))

    m = measure(load(args.path, args.json))
    print("%d sentences, median %g words" % (m["sentences"], m["median_words"]))
    print("%-22s %8s  %s" % ("measure", "rate", "band"))
    failed = []
    for name, (low, high) in bands.items():
        value = m[name]
        ok = (low is None or value >= low) and (high is None or value <= high)
        window = "%s to %s" % (low if low is not None else "-", high if high is not None else "-")
        print("%-22s %8.1f  %-12s %s" % (name, value, window, "" if ok else "MISSED"))
        if not ok:
            failed.append(name)
    print("\nreported, not gated:")
    for name in ADVISORY:
        print("%-22s %8.1f" % (name, m[name]))
    print("\nmaxim candidates (%d) -- mark each keep or cut, none may pass unmarked:"
          % len(m["maxim_candidates"]))
    for s in m["maxim_candidates"]:
        print("  " + s)
    if failed:
        print("\n%d band(s) missed: %s" % (len(failed), ", ".join(failed)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
