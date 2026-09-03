#!/usr/bin/env python3
"""Tests for voice_stats.py. Run: python3 test_voice_stats.py"""
import os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voice_stats as vs


def main():
    # bare "not" is not the habit; "is not X. It is Y" is, and is counted below
    m = vs.measure("It has not run. The docs do not say.")
    assert m["sentences"] == 2, m
    assert m["not_uses"] == 100.0, m
    assert m["inversions"] == 0.0, m

    # the construction, counted by shape rather than by the word "not" --
    # a synonym rewrite must not slip the same habit past the gate
    for text in ("The test was wrong, not the code.",
                 "The test was wrong rather than the code.",
                 "Observe it instead of assuming it.",
                 "It is not slowness. It is invention.",
                 "Not the code but the test."):
        assert vs.measure(text)["inversions"] > 0, text

    m = vs.measure("It is pretty much done. Hopefully that works.")
    assert m["hedges"] == 100.0, m

    # sentence-initial capitals are not named specifics; mid-sentence ones are
    m = vs.measure("Bill asked Brandi about Bizinta.")
    assert m["named_specifics"] == 200.0, m
    m = vs.measure("The agent wrote a test.")
    assert m["named_specifics"] == 0.0, m
    # identifier-shaped tokens count too
    assert vs.measure("We load tdd-cycle first.")["named_specifics"] == 100.0

    long_one = "word " * 25
    m = vs.measure(long_one.strip() + ". Short.")
    assert m["long_sentences_pct"] == 50.0, m
    assert m["short_sentences_pct"] == 50.0, m

    m = vs.measure("A measurement nobody prints is a measurement nobody makes.")
    assert m["maxim_candidates"] == ["A measurement nobody prints is a measurement nobody makes."], m
    m = vs.measure("Run the count. Do not estimate it.")
    assert m["maxim_candidates"] == [], m

    m = vs.measure("Alpha — beta — gamma.")
    assert m["em_dashes"] == 2, m
    # an unknown band name must be a clear refusal, not a traceback
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write("A sentence about nothing.")
    try:
        proc = subprocess.run([sys.executable, os.path.join(HERE, "voice_stats.py"),
                               path, "--band", "bogus=1:2"],
                              capture_output=True, text=True)
        assert proc.returncode != 0, proc
        assert "unknown band" in (proc.stdout + proc.stderr), proc
        assert "Traceback" not in (proc.stdout + proc.stderr), proc
        proc = subprocess.run([sys.executable, os.path.join(HERE, "voice_stats.py"),
                               path, "--band", "hedges=x:y"],
                              capture_output=True, text=True)
        assert "needs MIN:MAX" in (proc.stdout + proc.stderr), proc
    finally:
        os.unlink(path)

    print("test_voice_stats: 22 assertions passed")


if __name__ == "__main__":
    main()
