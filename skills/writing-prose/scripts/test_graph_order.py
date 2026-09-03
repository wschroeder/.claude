#!/usr/bin/env python3
"""Tests for graph_order.py. Run: python3 test_graph_order.py"""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "graph_order.py")

IDEAS_HEADER = "idea\tsource\tlocator\tthe one sentence it supports\n"


def run(ideas, edges):
    """Run the derivation over a throwaway ideas file and graph."""
    tmp = tempfile.mkdtemp()
    ideas_path = os.path.join(tmp, "ideas.tsv")
    graph_path = os.path.join(tmp, "graph.tsv")
    open(ideas_path, "w").write(
        IDEAS_HEADER + "".join("%s\t-\t-\tsentence\n" % i for i in ideas))
    open(graph_path, "w").write("".join("%s\t%s\t%s\n" % e for e in edges))
    try:
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--ideas", ideas_path, "--graph", graph_path],
            capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_example_of_groups_children_under_their_hub():
    code, out = run(["claim", "case-a", "case-b"],
                    [("case-a", "example-of", "claim"),
                     ("case-b", "example-of", "claim")])
    assert code == 0, out
    assert "1 groups derived" in out, out
    assert "claim" in out and "3 ideas" in out, out


def test_needs_puts_the_prerequisite_group_at_a_lower_level():
    code, out = run(["root", "root-case", "later", "later-case"],
                    [("root-case", "example-of", "root"),
                     ("later-case", "example-of", "later"),
                     ("later", "needs", "root")])
    assert code == 0, out
    root_line = next(l for l in out.split("\n") if " root " in l)
    later_line = next(l for l in out.split("\n") if " later " in l)
    assert root_line.split()[1] == "1", root_line
    assert later_line.split()[1] == "2", later_line


def test_an_idea_with_no_edge_is_named_as_an_orphan():
    code, out = run(["claim", "case-a", "stranded"],
                    [("case-a", "example-of", "claim")])
    assert "ORPHAN 1 idea" in out, out
    assert "stranded" in out, out


def test_an_edge_naming_an_unknown_node_is_refused_and_listed():
    code, out = run(["claim", "case-a"],
                    [("case-a", "example-of", "claim"),
                     ("ghost", "example-of", "claim")])
    assert "REFUSED 1 edge" in out, out
    assert "ghost" in out, out


def test_an_unknown_relation_is_refused_rather_than_ignored():
    code, out = run(["claim", "case-a"],
                    [("case-a", "example-of", "claim"),
                     ("case-a", "relates-to", "claim")])
    assert "REFUSED 1 edge" in out, out
    assert "relates-to" in out, out


def test_same_merges_two_ideas_into_one_group():
    code, out = run(["claim", "case-a", "restated"],
                    [("case-a", "example-of", "claim"),
                     ("restated", "same", "claim")])
    assert code == 0, out
    assert "1 groups derived" in out, out
    assert "3 ideas" in out, out


def test_a_cycle_exits_non_zero_and_names_its_members():
    code, out = run(["a", "a-case", "b", "b-case"],
                    [("a-case", "example-of", "a"),
                     ("b-case", "example-of", "b"),
                     ("a", "needs", "b"),
                     ("b", "needs", "a")])
    assert code == 1, out
    assert "CYCLE" in out, out
    assert "a" in out and "b" in out, out


def test_an_orphan_stops_the_step_rather_than_passing():
    code, out = run(["claim", "case-a", "stranded"],
                    [("case-a", "example-of", "claim")])
    assert code == 1, out


def test_a_refused_edge_stops_the_step_rather_than_passing():
    code, out = run(["claim", "case-a"],
                    [("case-a", "example-of", "claim"),
                     ("ghost", "example-of", "claim")])
    assert code == 1, out


def test_levels_holding_more_than_one_group_are_counted_as_free_choices():
    code, out = run(["root", "root-case", "x", "x-case", "y", "y-case"],
                    [("root-case", "example-of", "root"),
                     ("x-case", "example-of", "x"),
                     ("y-case", "example-of", "y"),
                     ("x", "needs", "root"),
                     ("y", "needs", "root")])
    assert code == 0, out
    assert "1 level(s) leave a genuine choice" in out, out


def test_zero_ideas_is_refused_rather_than_reported_clean():
    code, out = run([], [])
    assert code == 1, out
    assert "no idea rows parsed" in out, out


def test_a_duplicate_slug_is_refused():
    code, out = run(["claim", "item", "item"],
                    [("item", "example-of", "claim")])
    assert code == 1, out
    assert "DUPLICATE" in out, out
    assert "item" in out, out


def test_a_truncated_edge_line_is_refused_not_skipped():
    tmp = tempfile.mkdtemp()
    ideas_path = os.path.join(tmp, "ideas.tsv")
    graph_path = os.path.join(tmp, "graph.tsv")
    open(ideas_path, "w").write(
        IDEAS_HEADER + "claim\t-\t-\ts\nitem\t-\t-\ts\n")
    open(graph_path, "w").write("item\texample-of\tclaim\nitem\tneeds\n")
    try:
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--ideas", ideas_path, "--graph", graph_path],
            capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = proc.stdout + proc.stderr
    assert proc.returncode == 1, out
    assert "REFUSED 1 edge" in out, out


def test_a_self_edge_is_refused():
    code, out = run(["claim", "item"],
                    [("item", "example-of", "claim"),
                     ("item", "needs", "item")])
    assert code == 1, out
    assert "REFUSED 1 edge" in out, out


def test_needs_inside_one_group_orders_its_members():
    code, out = run(["claim", "item-a", "item-b"],
                    [("item-a", "example-of", "claim"),
                     ("item-b", "example-of", "claim"),
                     ("item-b", "needs", "item-a")])
    assert code == 0, out
    assert "within: claim, item-a, item-b" in out, out
    assert out.index("item-a") < out.index("item-b"), out


def test_the_groups_claim_leads_its_own_within_sequence():
    code, out = run(["claim", "aaa-case", "zzz-case"],
                    [("aaa-case", "example-of", "claim"),
                     ("zzz-case", "example-of", "claim"),
                     ("zzz-case", "needs", "aaa-case")])
    assert code == 0, out
    assert "within: claim, aaa-case, zzz-case" in out, out


def test_a_cycle_inside_one_group_is_reported_not_truncated():
    code, out = run(["claim", "item-a", "item-b"],
                    [("item-a", "example-of", "claim"),
                     ("item-b", "example-of", "claim"),
                     ("item-b", "needs", "item-a"),
                     ("item-a", "needs", "item-b")])
    assert code == 1, out
    assert "CYCLE inside claim" in out, out


def test_an_orphan_becomes_its_own_single_group():
    code, out = run(["claim", "case-a", "stranded"],
                    [("case-a", "example-of", "claim")])
    assert "own single-idea group" in out, out
    assert "stranded" in out, out


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print("ok   %s" % name)
        except AssertionError as exc:
            failures += 1
            print("FAIL %s\n%s" % (name, exc))
    print("\n%d passed, %d failed" % (
        sum(1 for n in globals() if n.startswith("test_")) - failures, failures))
    sys.exit(1 if failures else 0)
