#!/usr/bin/env python3
"""Derive a document's grouping and order from an idea graph.

Sections come from the example-of and same edges; order comes from a topological
sort of the needs edges, run once across groups and again inside each group whose
members constrain one another. Reads only.

  graph_order.py --ideas ideas.tsv --graph graph.tsv
"""
import argparse, collections, sys

RELATIONS = ("needs", "same", "example-of")


def read_ideas(path):
    slugs, seen, duplicates = [], set(), []
    for raw in open(path, encoding="utf-8"):
        parts = raw.rstrip("\n").split("\t")
        if len(parts) < 2 or parts[0] in ("idea", ""):
            continue
        slug = parts[0]
        if slug in seen:
            duplicates.append(slug)
            continue
        seen.add(slug)
        slugs.append(slug)
    return slugs, duplicates


def read_graph(path, known):
    edges, refused = [], []
    for raw in open(path, encoding="utf-8"):
        if raw.startswith("#") or not raw.strip():
            continue
        parts = [p.strip() for p in raw.rstrip("\n").split("\t")]
        if len(parts) < 3:
            refused.append(tuple(parts) + ("<missing>",) * (3 - len(parts)))
            continue
        src, relation, dst = parts[0], parts[1], parts[2]
        if (relation not in RELATIONS or src not in known or dst not in known
                or src == dst):
            refused.append((src, relation, dst))
        else:
            edges.append((src, relation, dst))
    return edges, refused


def group(slugs, edges):
    """example-of and same are undirected here, and the hub names the group."""
    parent = {s: s for s in slugs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_a] = root_b

    hubs = {dst for _src, relation, dst in edges if relation == "example-of"}
    for src, relation, dst in edges:
        if relation in ("example-of", "same"):
            union(src, dst)
    members = collections.defaultdict(list)
    for slug in slugs:
        members[find(slug)].append(slug)
    named = {}
    for group_members in members.values():
        hub = next((m for m in group_members if m in hubs), None)
        named[hub or group_members[0]] = sorted(group_members)
    return named


def levelise(nodes, prerequisites):
    """Kahn's algorithm, keeping each level so a free choice stays visible."""
    levels, placed = [], set()
    while len(placed) < len(nodes):
        ready = sorted(n for n in nodes
                       if n not in placed and prerequisites[n] <= placed)
        if not ready:
            return levels, sorted(set(nodes) - placed)
        levels.append(ready)
        placed |= set(ready)
    return levels, []


def order(named, edges):
    group_of = {m: g for g, ms in named.items() for m in ms}
    prerequisites = {g: set() for g in named}
    for src, relation, dst in edges:
        if relation != "needs":
            continue
        source_group, target_group = group_of.get(src), group_of.get(dst)
        if source_group and target_group and source_group != target_group:
            prerequisites[source_group].add(target_group)
    return levelise(list(named), prerequisites)


def order_within(named, edges):
    """A needs edge between two members of one group orders that group's items.

    The group is named for its claim, and a section that opens on an example
    before stating the claim is the ordering defect this whole file exists to
    catch, so every other member waits on it.
    """
    sequences, stuck = {}, {}
    for name, group_members in named.items():
        member_set = set(group_members)
        prerequisites = {m: {name} for m in group_members if m != name}
        prerequisites[name] = set()
        constrained = False
        for src, relation, dst in edges:
            if relation == "needs" and src in member_set and dst in member_set:
                prerequisites[src].add(dst)
                constrained = True
        if not constrained:
            continue
        levels, cycle = levelise(group_members, prerequisites)
        if cycle:
            stuck[name] = cycle
        else:
            sequences[name] = [m for level in levels for m in level]
    return sequences, stuck


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ideas", required=True)
    ap.add_argument("--graph", required=True)
    args = ap.parse_args()

    slugs, duplicates = read_ideas(args.ideas)
    if not slugs:
        print("no idea rows parsed from %s" % args.ideas)
        print("expected tab-separated rows whose first column is a word slug")
        return 1
    if duplicates:
        print("DUPLICATE %d slug(s) — an idea counted twice corrupts every count "
              "downstream:" % len(duplicates))
        for slug in sorted(set(duplicates)):
            print("   %s" % slug)
        return 1

    edges, refused = read_graph(args.graph, set(slugs))
    named = group(slugs, edges)
    levels, cycle = order(named, edges)
    sequences, stuck = order_within(named, edges)

    print("%d ideas, %d edges, %d groups derived\n"
          % (len(slugs), len(edges), len(named)))
    if refused:
        print("REFUSED %d edge(s) — unknown node, unknown relation, self-edge, or "
              "fewer than three columns:" % len(refused))
        for edge in refused:
            print("   %s" % "\t".join(edge))
        print()

    orphans = [s for s in slugs if all(s not in (src, dst) for src, _r, dst in edges)]
    if orphans:
        print("ORPHAN %d idea(s) with no edge, each landing in its own single-idea "
              "group:" % len(orphans))
        for orphan in orphans:
            print("   %s" % orphan)
        print()

    print("derived order (each level is a free choice among its members):")
    for depth, level in enumerate(levels, 1):
        for name in level:
            print("  level %d  %-20s %2d ideas" % (depth, name, len(named[name])))
            if name in sequences:
                print("             within: %s" % ", ".join(sequences[name]))
    free = [l for l in levels if len(l) > 1]
    print("\n%d level(s) leave a genuine choice; a person picks within those." % len(free))
    if cycle:
        print("\nCYCLE among groups: %s" % ", ".join(cycle))
    for name, members in sorted(stuck.items()):
        print("CYCLE inside %s among: %s" % (name, ", ".join(members)))
    return 1 if (cycle or stuck or refused or orphans) else 0


if __name__ == "__main__":
    sys.exit(main())
