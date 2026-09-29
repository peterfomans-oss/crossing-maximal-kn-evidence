"""Solver-free, standard-library-only check of the eight-vertex crossing table.

No encoder, archived checker, SAT variables, rotations, or catalogue is imported.
The two explicit K5 crossing patterns are stated as premises for the local check.
This script alone does not claim geometric realizability; see the separate
rotation/planarization certificate. Run with Python -B.
"""
from itertools import combinations, permutations
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def pair(e, f):
    return tuple(sorted((tuple(sorted(e)), tuple(sorted(f)))))


def options(q):
    a, b, c, d = q
    return (pair((a, b), (c, d)), pair((a, c), (b, d)), pair((a, d), (b, c)))


def pairs(n, word):
    qs = tuple(combinations(range(n), 4))
    assert len(word) == len(qs) and all(type(t) is int and 0 <= t <= 2 for t in word)
    return {options(q)[t] for q, t in zip(qs, word)}


def local_dictionary():
    # Lexicographic quadruples 0123,0124,0134,0234,1234.
    result = set()
    for seed in ((1, 1, 1, 1, 1), (1, 1, 1, 2, 2)):
        cross = pairs(5, seed)
        for perm in permutations(range(5)):
            result.add(frozenset(pair(tuple(perm[v] for v in e),
                                     tuple(perm[v] for v in f)) for e, f in cross))
    assert len(result) == 72
    return result


def check(n, word):
    vertices = set(range(n))
    cross = pairs(n, word)
    assert len(cross) == len(tuple(combinations(range(n), 4)))
    allowed = local_dictionary()
    for five in combinations(range(n), 5):
        relabel = {v: i for i, v in enumerate(five)}
        local = frozenset(pair(tuple(relabel[v] for v in e), tuple(relabel[v] for v in f))
                          for e, f in cross if set(e + f) <= set(five))
        assert local in allowed, ('forbidden K5', five)
    parity_checks = 0
    for six in combinations(range(n), 6):
        for first in combinations(six, 3):
            second = tuple(v for v in six if v not in first)
            if first >= second:
                continue
            total = sum(pair(e, f) in cross for e in combinations(first, 2)
                        for f in combinations(second, 2))
            assert total % 2 == 0, ('odd disjoint triangles', first, second)
            parity_checks += 1

    witnesses, uncrossed, edge_audit = [], [], []
    for edge in combinations(range(n), 2):
        partners = sorted(f for f in combinations(sorted(vertices - set(edge)), 2)
                          if pair(edge, f) in cross)
        if not partners:
            uncrossed.append(edge)
            centers = []  # Empty stars are deliberately excluded.
        else:
            centers = sorted(set.intersection(*(set(f) for f in partners)))
        edge_audit.append({'edge': edge, 'partners': partners, 'nonempty_centers': centers})
        # Intersection characterization independently enumerates every witness.
        for d in centers:
            a, b = edge
            rest = sorted(vertices - {a, b, d})
            valid_orders = [o for o in permutations(rest)
                            if all(pair((a, o[i]), (b, o[j])) in cross
                                   for i in range(len(o)) for j in range(i + 1, len(o)))]
            assert len(valid_orders) == 1
            order = valid_orders[0]
            star = tuple(int(pair(edge, (d, k)) in cross) for k in order)
            assert any(star)
            changes = sum(x != y for x, y in zip(star, star[1:]))
            witnesses.append({'d': d, 'edge': edge, 'order': order,
                              'star': ''.join(map(str, star)), 'changes': changes})

    # Separate exhaustive d,uv loop cross-checks the intersection method.
    direct = set()
    for d in range(n):
        for edge in combinations(sorted(vertices - {d}), 2):
            rest = sorted(vertices - {d} - set(edge))
            if not any(pair(edge, f) in cross for f in combinations(rest, 2)) and any(
                    pair(edge, (d, k)) in cross for k in rest):
                direct.add((d, edge))
    assert direct == {(w['d'], w['edge']) for w in witnesses}
    assert {w['d'] for w in witnesses} == vertices
    assert all(w['changes'] >= 2 for w in witnesses)
    return {'status': 'PASS', 'n': n, 'K4_checks': len(cross),
            'K5_checks': len(tuple(combinations(range(n), 5))), '2K3_checks': parity_checks,
            'uncrossed_edges': uncrossed, 'all_edges_crossed': not uncrossed,
            'nonempty_witness_count': len(witnesses), 'good_witness_count': 0,
            'witnesses': sorted(witnesses, key=lambda w: (w['d'], w['edge'])),
            'complete_edge_partner_audit': edge_audit,
            'scope': 'Crossing-table and witness check; drawability certified separately.'}


if __name__ == '__main__':
    certificate = json.loads((HERE / 'counterexample-k8.json').read_text(encoding='utf-8'))
    assert certificate['n'] == 8
    assert certificate['states'] == ['ab|cd', 'ac|bd', 'ad|bc']
    word = certificate['crossing_pattern']
    result = check(8, word)
    (HERE / 'counterexample-independent-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'complete_edge_partner_audit'}, indent=2))
