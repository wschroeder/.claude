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

    # a Slack post: each bullet is a sentence, and so is the lead-in that ends
    # in a colon, and the marker is not a word
    m = vs.measure("Two steps got slower:\n* seed: 48s to 58s\n- app scan\n"
                   "• migrate scan\n1. build")
    assert m["sentences"] == 5, m
    assert m["median_words"] == 2, m
    m = vs.measure("* a bullet with no stop\n  wrapped onto two lines\n\nNext paragraph here.")
    assert m["sentences"] == 2, m
    m = vs.measure("## Heading\n\nBody.")
    assert m["sentences"] == 1, m

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

    # a clause that ends on what nobody did, in place of the actor who did it
    for text in ("A detail row drops out of the read, and nothing reports it.",
                 "The report was skipped, and nobody was told.",
                 "The line slipped past without a word.",
                 "It read 51 of 52 lines with nothing said.",
                 "A blank group would be counted without anyone being told.",
                 "Nothing warns the reviewer."):
        assert vs.measure(text)["silent_tails"] == [text], text
    for text in ("The parser skips the row and raises no error.",
                 "Nothing changed in the schema.",
                 "It reads the file, and nothing else."):
        assert vs.measure(text)["silent_tails"] == [], text

    # every comma before a coordinating conjunction or a trailing reason is
    # listed, because only a reader can tell whether a second subject follows
    for text in ("This column shows the number, or how many records it has.",
                 "It can only append, and never takes anything back.",
                 "The PR says changes requested, because that is the last review.",
                 "The build failed, since the lockfile changed.",
                 "Put two concerns in one pass, and you will leave one unchecked.",
                 "It is short, but it is wrong.",
                 "It ran, so it passed.",
                 "Nobody asked, yet it shipped.",
                 "It did not stop, nor did it warn."):
        assert vs.measure(text)["comma_candidates"] == [text], text
    for text in ("It can only append and never takes anything back.",
                 "Once the evidence is on the page, an unsupported claim has nowhere to sit.",
                 "A record, a document and a line item."):
        assert vs.measure(text)["comma_candidates"] == [], text

    m = vs.measure("Alpha — beta — gamma.")
    assert m["em_dashes"] == 2, m
    # an unknown band name must be a clear refusal, not a traceback
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as fh:
        fh.write("A sentence about nothing.")
    fd2, listed = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd2, "w") as fh:
        fh.write("It shows the number, or how many records it has.")
    try:
        proc = subprocess.run([sys.executable, os.path.join(HERE, "voice_stats.py"), listed],
                              capture_output=True, text=True)
        assert "comma candidates (1)" in proc.stdout, proc
        assert "  It shows the number, or how many records it has." in proc.stdout, proc
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
        os.unlink(listed)

    print("test_voice_stats: all assertions passed")


if __name__ == "__main__":
    main()
