"""Independent small verifier: rebuild the subdivided graph without port data.

Only four certificate fields are used: n, crossing_pairs, edge_crossing_orders,
crossing_endpoint_rotations. The original rotations and target crossing table
are read separately. No SAT, finite catalogue, or producer module is imported.
"""
from itertools import combinations
from pathlib import Path
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent


def norm(e, f):
    return tuple(sorted((tuple(sorted(e)), tuple(sorted(f)))))


def verify(cert, source_rotation, target_pattern):
    n = cert['n']
    assert type(n) is int and n >= 4 and len(source_rotation) == n
    crossing_count = math.comb(n, 4)
    crossing = [norm(*p) for p in cert['crossing_pairs']]
    assert len(crossing) == len(set(crossing)) == crossing_count
    for e, f in crossing:
        assert len(e) == len(f) == 2 and len(set(e + f)) == 4
        assert all(type(v) is int and 0 <= v < n for v in e + f)
    target = []
    for q in combinations(range(n), 4):
        a, b, c, d = q
        choices = (norm((a,b),(c,d)), norm((a,c),(b,d)), norm((a,d),(b,c)))
        hits = [i for i, p in enumerate(choices) if p in crossing]
        assert len(hits) == 1
        target.append(hits[0])
    assert target == target_pattern

    edges = set(combinations(range(n), 2))
    paths, neighbor_toward, graph = {}, {}, {v: set() for v in range(n + len(crossing))}
    for edge, ids in cert['edge_crossing_orders']:
        edge = tuple(edge)
        assert edge in edges and edge not in paths
        assert len(ids) == len(set(ids))
        assert set(ids) == {i for i, p in enumerate(crossing) if edge in p}
        path = [edge[0]] + [n+i for i in ids] + [edge[1]]
        assert len(path) == len(set(path))
        paths[edge] = path
        for i, v in enumerate(path):
            if i > 0:
                neighbor_toward[v, edge, edge[0]] = path[i-1]
            if i+1 < len(path):
                neighbor_toward[v, edge, edge[1]] = path[i+1]
        for a, b in zip(path, path[1:]):
            assert b not in graph[a], ('reused subdivided segment', a, b)
            graph[a].add(b)
            graph[b].add(a)
    assert set(paths) == edges

    rotation = {}
    for v, row in enumerate(source_rotation):
        assert len(row) == n-1 and set(row) == set(range(n)) - {v}
        rotation[v] = [neighbor_toward[v, tuple(sorted((v,w))), w] for w in row]
    cr = cert['crossing_endpoint_rotations']
    assert len(cr) == len(crossing)
    for i, ((e, f), row) in enumerate(zip(crossing, cr)):
        assert len(row) == 4 and set(row) == set(e + f)
        assert all((row[j] in e) != (row[(j+1)%4] in e) for j in range(4))
        v = n+i
        rotation[v] = [neighbor_toward[v, e if w in e else f, w] for w in row]
    for v, row in rotation.items():
        assert len(row) == len(set(row)) and set(row) == graph[v]

    reached, todo = set(), [0]
    while todo:
        v = todo.pop()
        if v not in reached:
            reached.add(v)
            todo.extend(graph[v] - reached)
    assert reached == set(graph)

    # The successor at the head determines the next dart of a face walk.
    successor = {(v, row[i]): row[(i+1)%len(row)]
                 for v, row in rotation.items() for i in range(len(row))}
    darts = {(u, v) for u in graph for v in graph[u]}
    unvisited, faces = set(darts), []
    while unvisited:
        start = min(unvisited)
        face, dart = [], start
        while dart in unvisited:
            unvisited.remove(dart)
            face.append(dart)
            u, v = dart
            dart = (v, successor[v, u])
        assert dart == start
        faces.append(face)
    V, E, F = len(graph), len(darts)//2, len(faces)
    assert V == n+crossing_count and E == math.comb(n, 2)+2*crossing_count and V-E+F == 2
    return {'status': 'PASS', 'vertices': V, 'edges': E, 'faces': F, 'euler': V-E+F,
            'connected': True, 'original_edges_checked': len(paths),
            'proper_crossings_checked': len(crossing), 'original_rotations_match': True,
            'target_crossing_table_matches': True,
            'ignored_producer_fields': ['ports', 'vertex_port_rotations', 'edge_port_pairing', 'face_port_cycles'],
            'conclusion': 'Connected orientable genus-zero embedding with alternating crossing vertices: a simple drawing certificate.'}


if __name__ == '__main__':
    path = HERE / 'planar/certificate.json'
    cert = json.loads(path.read_text(encoding='utf-8'))
    source = HERE / 'allcrossed/n9-maxuncrossed4'
    rotation = json.loads((source / 'rotation.json').read_text(encoding='utf-8'))['rotation_system']
    pattern = json.loads((source / 'result.json').read_text(encoding='utf-8'))['verified_model']['crossing_pattern']
    result = verify(cert, rotation, pattern)
    result['certificate_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE / 'embedding-independent-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
