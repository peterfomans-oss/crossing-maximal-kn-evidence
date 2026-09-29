"""An explicit disk-and-strip K8 construction; Python standard library only.

Run with python -B.  Input SAT result and rotation are used only at the final
comparison, never to choose the constructed crossings or their edge orders.
"""
from __future__ import annotations
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent


def edge(a, b):
    return tuple(sorted((a, b)))


def cross(e, f):
    return tuple(sorted((e, f)))


def orient(a, b):
    return 1 if a < b else -1


def cyclic(row):
    i = row.index(min(row))
    return row[i:] + row[:i]


def signed(signs, e, f):
    return signs[cross(e, f)] * (1 if e < f else -1)


def add_sign(signs, e, f, value):
    signs[cross(e, f)] = value * (1 if e < f else -1)


def duplicate(rot, paths, signs, p, q, before, after, side):
    """side +1 means left of every directed p->j strip; -1 means right.

    (before,after) is a CCW sector at p. Left copies sweep clockwise in
    the disk; right copies counterclockwise. Longer sweep arcs run closer p.
    """
    oldrot = {v: list(r) for v, r in rot.items()}
    oldpaths = {e: list(xs) for e, xs in paths.items()}
    oldsigns = dict(signs)
    row = oldrot[p]
    assert row[(row.index(before) + 1) % len(row)] == after
    k = row.index(after)
    order = row[k:] + row[:k]
    rank = {v: i for i, v in enumerate(order)}
    rot[p].insert(rot[p].index(after), q)
    rot[q] = [p if v == q else v for v in rot[p]]
    for j in order:
        where = rot[j].index(p) + (side == -1)
        rot[j].insert(where, q)
        paths[edge(q, j)] = []
    paths[edge(p, q)] = []

    # Each old crossing involving the p-star gets one nearby strip crossing.
    insertions = {}
    for j in order:
        e, g = edge(p, j), edge(q, j)
        for c in oldpaths[e]:
            f = c[0] if c[1] == e else c[1]
            newc = cross(g, f)
            after_old = side * orient(p, j) * signed(oldsigns, e, f) > 0
            insertions[(f, c)] = (newc, after_old)
            add_sign(signs, g, f,
                     orient(q, j) * orient(p, j) * signed(oldsigns, e, f))

    for f, xs in oldpaths.items():
        result = []
        for c in xs:
            ins = insertions.get((f, c))
            if ins and not ins[1]:
                result.append(ins[0])
            result.append(c)
            if ins and ins[1]:
                result.append(ins[0])
        paths[f] = result

    # Local star crossings. Along p->i the longer arcs are encountered first.
    for i in order:
        js = [j for j in order if
              (rank[j] < rank[i] if side == 1 else rank[j] > rank[i])]
        js.sort(key=rank.get, reverse=(side == -1))
        local = [cross(edge(p, i), edge(q, j)) for j in js]
        if orient(p, i) == 1:
            paths[edge(p, i)] = local + paths[edge(p, i)]
        else:
            paths[edge(p, i)] += local[::-1]
        for j in js:
            add_sign(signs, edge(p, i), edge(q, j),
                     -side * orient(p, i) * orient(q, j))

    for j in order:
        is_ = [i for i in order if
               (rank[i] > rank[j] if side == 1 else rank[i] < rank[j])]
        is_.sort(key=rank.get, reverse=(side == 1))
        local = [cross(edge(p, i), edge(q, j)) for i in is_]
        inherited = []
        e, g = edge(p, j), edge(q, j)
        for c in oldpaths[e][::orient(p, j)]:
            f = c[0] if c[1] == e else c[1]
            inherited.append(cross(g, f))
        paths[g] = (local + inherited)[::orient(q, j)]

    for v in rot:
        rot[v] = cyclic(rot[v])
    return {"p": p, "q": q, "ccw_sector": [before, after],
            "copy_side_p_to_j": "left" if side == 1 else "right",
            "ccw_order_after_sector": order}


def check_planarization(rot, paths, signs):
    """Every dart has a rotation successor; count the closed face walks."""
    n, nc = len(rot), len(signs)
    assert set(paths) == set(combinations(sorted(rot), 2))
    assert set(c for xs in paths.values() for c in xs) == set(signs)
    assert sum(map(len, paths.values())) == 2 * nc
    for e, xs in paths.items():
        assert len(set(xs)) == len(xs)
        assert all(e in c and len(set(c[0] + c[1])) == 4 for c in xs)
    rotation = []
    for v, row in rot.items():
        darts = []
        for w in row:
            e = edge(v, w)
            darts.append((e, 0, 1) if v < w else (e, len(paths[e]), -1))
        rotation.append(darts)
    for c, sign in signs.items():
        e, f = c
        ie, jf = paths[e].index(c), paths[f].index(c)
        ep, em = (e, ie+1, 1), (e, ie, -1)
        fp, fm = (f, jf+1, 1), (f, jf, -1)
        rotation.append([ep, fp, em, fm] if sign == 1 else [ep, fm, em, fp])
    sigma = {}
    for row in rotation:
        for a, b in zip(row, row[1:] + row[:1]):
            assert a not in sigma
            sigma[a] = b
    ne = len(paths) + 2 * nc
    assert len(sigma) == 2 * ne
    face_next = {d: sigma[(d[0], d[1], -d[2])] for d in sigma}
    seen, faces = set(), []
    for d in sigma:
        if d in seen:
            continue
        walk, cur = [], d
        while cur not in seen:
            seen.add(cur)
            walk.append(cur)
            cur = face_next[cur]
        assert cur == d
        faces.append(walk)
    result = {"vertices": n + nc, "edges": ne, "faces": len(faces),
              "euler_characteristic": n + nc - ne + len(faces),
              "crossings": nc}
    assert result["euler_characteristic"] == 2, result
    assert nc == len(list(combinations(rot, 4)))
    for quad in combinations(rot, 4):
        assert sum(set(c[0] + c[1]) == set(quad) for c in signs) == 1
    return result


def main():
    # Straight square, vertices (0,0),(1,0),(1,1),(0,1), CCW labels 0,1,5,3.
    rot = {0: [1,5,3], 1: [0,5,3], 3: [0,1,5], 5: [0,1,3]}
    paths = {e: [] for e in combinations(sorted(rot), 2)}
    c = cross((0,5), (1,3))
    paths[(0,5)] = paths[(1,3)] = [c]
    signs = {c: 1}
    stages = [{"n": 4, "rotation": {v:list(r) for v,r in rot.items()},
               "planarization": check_planarization(rot, paths, signs)}]
    for p,q,b,a,s in [(0,2,5,3,1), (1,7,3,2,1),
                      (3,4,1,5,1), (5,6,0,7,-1)]:
        instruction = duplicate(rot, paths, signs, p,q,b,a,s)
        stages.append({"n": len(rot), "instruction": instruction,
                       "rotation": {v:list(r) for v,r in rot.items()},
                       "planarization": check_planarization(rot, paths, signs)})

    # Independent targets are read only after the whole construction is finished.
    target_rot = json.loads((HERE.parent / "search/n8-all/rotation.json0").read_text())
    target = json.loads((HERE.parent / "search/n8-all/result.json").read_text())
    assert all(rot[v] == cyclic(row) for v,row in enumerate(target_rot))
    target_cross = {cross(tuple(e), tuple(f)) for e,f in
                    target["verified_model"]["crossing_pairs"]}
    assert set(signs) == target_cross
    output = {"base_ccw_square": [0,1,5,3], "stages": stages,
              "edge_orders_canonical_direction": [
                  {"edge": e, "crossings": paths[e]} for e in sorted(paths)],
              "crossing_signs": [
                  {"crossing": c, "sign": signs[c]} for c in sorted(signs)],
              "matches_input_rotation": True, "matches_input_crossings": True,
              "uses_catalogue_or_sat_for_construction": False}
    (HERE / "twin_certificate.json").write_text(json.dumps(output, indent=2)+"\n")
    print(json.dumps({"stages": [s["planarization"] for s in stages],
                      "rotation_match": True, "crossing_match": True}))


if __name__ == "__main__":
    main()
