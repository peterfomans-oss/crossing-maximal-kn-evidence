"""Independent standard-library checker for the rooted seven-vertex sharpness.

Reads only the explicit K8 crossing word. Imports neither a project checker nor
an encoder/catalogue, and performs no solving. Run with python -B.
"""
from itertools import combinations, permutations
from pathlib import Path
from hashlib import sha256
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'counterexample-k8.json'


def pair(e, f):
    return tuple(sorted((tuple(sorted(e)), tuple(sorted(f)))))


def matchings(q):
    a, b, c, d = q
    return (pair((a, b), (c, d)), pair((a, c), (b, d)),
            pair((a, d), (b, c)))


def parse_crossings(vertices, word):
    quads = tuple(combinations(vertices, 4))
    assert len(quads) == len(word)
    assert all(type(v) is int and 0 <= v <= 2 for v in word)
    result = {matchings(q)[v] for q, v in zip(quads, word)}
    for q in quads:
        assert sum(p in result for p in matchings(q)) == 1
    return result


def allowed_k5():
    result = set()
    for word in [(1, 1, 1, 1, 1), (1, 1, 1, 2, 2)]:
        seed = parse_crossings(range(5), word)
        for p in permutations(range(5)):
            result.add(frozenset(pair((p[a], p[b]), (p[c], p[d]))
                                 for (a, b), (c, d) in seed))
    assert len(result) == 72
    return result


def analyze(crossings, vertices, root=(0, 4)):
    vertices = tuple(sorted(vertices))
    rest = tuple(v for v in vertices if v not in root)
    partners = tuple(f for f in combinations(rest, 2)
                     if pair(root, f) in crossings)
    witnesses = []
    for d in rest:
        other = tuple(v for v in rest if v != d)
        # Direct definitions of deletion witness and nonempty star.
        if any(pair(root, f) in crossings for f in combinations(other, 2)):
            continue
        if not any(pair(root, (d, k)) in crossings for k in other):
            continue
        u, v = root
        orders = [p for p in permutations(other)
                  if all(pair((u, p[i]), (v, p[j])) in crossings
                         for i in range(len(p)) for j in range(i + 1, len(p)))]
        assert len(orders) == 1, (vertices, d, orders)
        order = orders[0]
        bits = tuple(int(pair(root, (d, k)) in crossings) for k in order)
        positive = tuple(i for i, b in enumerate(bits) if b)
        assert positive
        prefix = positive == tuple(range(len(positive)))
        suffix = positive == tuple(range(len(bits) - len(positive), len(bits)))
        changes = sum(a != b for a, b in zip(bits, bits[1:]))
        assert (prefix or suffix) == (changes <= 1)
        reverse_orders = [p for p in permutations(other)
                          if all(pair((v, p[i]), (u, p[j])) in crossings
                                 for i in range(len(p)) for j in range(i + 1, len(p)))]
        assert reverse_orders == [order[::-1]]
        witnesses.append({'center': d, 'order': order,
                          'star': ''.join(map(str, bits)), 'prefix': prefix,
                          'suffix': suffix, 'good': prefix or suffix})
    # Separate endpoint-intersection characterization cross-check.
    centers = sorted(set.intersection(*(set(f) for f in partners))) if partners else []
    assert centers == [w['center'] for w in witnesses]
    good_centers = [w['center'] for w in witnesses if w['good']]
    return {'vertices': vertices, 'root_edge': root, 'crossing_partners': partners,
            'crossed': bool(partners), 'nonempty_centers': centers,
            'witnesses': witnesses, 'good_centers': good_centers,
            'root_blocked': bool(partners) and not good_centers}


def proper_checks(crossings, vertices, root=(0, 4)):
    rest = tuple(v for v in vertices if v not in root)
    records = []
    for k in range(0, min(4, len(rest)) + 1):
        for chosen in combinations(rest, k):
            record = analyze(crossings, (*root, *chosen), root)
            assert not record['root_blocked'], record
            records.append(record)
    crossed = [r for r in records if r['crossed']]
    return {'total_subsets_with_2_through_6_vertices': len(records),
            'crossed_subsets': len(crossed),
            'crossed_subsets_with_good_center': len(crossed),
            'size_counts': {str(k): {'total': sum(len(r['vertices']) == k for r in records),
                                   'crossed': sum(len(r['vertices']) == k and r['crossed']
                                                  for r in records)}
                            for k in range(2, 7)},
            'records': records}


def main():
    raw = SOURCE.read_bytes()
    obj = json.loads(raw)
    assert obj['n'] == 8
    assert obj['states'] == ['ab|cd', 'ac|bd', 'ad|bc']
    crossings = parse_crossings(range(8), obj['crossing_pattern'])
    allowed = allowed_k5()
    for five in combinations(range(8), 5):
        inverse = {v: i for i, v in enumerate(five)}
        local = frozenset(pair((inverse[a], inverse[b]), (inverse[c], inverse[d]))
                          for (a, b), (c, d) in crossings if {a, b, c, d} <= set(five))
        assert local in allowed
    h = (0, 1, 2, 3, 4, 5, 7)
    full = analyze(crossings, h)
    assert full['root_blocked'] and full['nonempty_centers'] == [3]
    assert full['crossing_partners'] == ((1, 3), (3, 7))
    assert full['witnesses'][0]['order'] == (5, 7, 1, 2)
    assert full['witnesses'][0]['star'] == '0110'
    restricted_word = [next(t for t, p in enumerate(matchings(q)) if p in crossings)
                       for q in combinations(h, 4)]
    check_h = proper_checks(crossings, h)
    check_k8 = proper_checks(crossings, range(8))
    six_rows = []
    for deleted in h:
        if deleted in (0, 4):
            continue
        rec = analyze(crossings, tuple(v for v in h if v != deleted))
        six_rows.append({'deleted_vertex': deleted, **rec})
    result = {
        'status': 'PASS', 'source': '../counterexample-k8.json',
        'source_sha256': sha256(raw).hexdigest(),
        'checker_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope': 'Rooted seven-point bound sharpness; no global good-witness existence claim.',
        'independent_method': 'Direct witness definition and exhaustive permutation orders; no imported project code, SAT, or catalogue.',
        'K8_K4_checks': 70, 'K8_K5_checks': 56,
        'rooted_seven_vertex_example': full,
        'H_crossing_word_in_lexicographic_quad_order': restricted_word,
        'H_six_vertex_deletions': six_rows,
        'H_all_rooted_subsets_at_most_six': check_h,
        'K8_all_rooted_subsets_at_most_six': check_k8,
        'realizability_basis': 'Induced restriction of separately certified K8 planarization; not established by this checker alone.'
    }
    (HERE / 'sharpness.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'H_summary': {k: v for k, v in check_h.items() if k != 'records'},
                      'K8_summary': {k: v for k, v in check_k8.items() if k != 'records'},
                      'six_vertex_deletions': six_rows}, indent=2))


if __name__ == '__main__':
    main()
