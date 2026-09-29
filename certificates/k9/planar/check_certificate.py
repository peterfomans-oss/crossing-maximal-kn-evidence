"""Independent, Python-standard-library-only sphere-map certificate checker.

Does not import the recovery script, SAT encoders, catalogues, graph libraries,
or any archived executable code. Run without -O (checks are explicit regardless).
"""
import argparse
from collections import Counter, deque
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / 'allcrossed/n9-maxuncrossed4'


class InvalidCertificate(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidCertificate(message)


def freeze(value):
    return tuple(map(freeze, value)) if isinstance(value, list) else value


def cyclic_equal(a, b):
    return len(a) == len(b) and (not a or any(a == b[i:]+b[:i] for i in range(len(b))))


def check(cert, source_rotation, source_pairs):
    require(cert.get('schema') == 'simple-drawing-planarization-v1', 'unsupported schema')
    n=cert['n']
    require(n == len(source_rotation), 'source order mismatch')
    vertices=set(range(n))
    edges=set(combinations(range(n),2))
    rs=cert['original_rotation_system']
    require(rs == source_rotation, 'claimed source rotations differ')
    for v,row in enumerate(rs):
        require(len(row)==n-1 and set(row)==vertices-{v}, 'invalid original rotation')
    pairs=[freeze(p) for p in cert['crossing_pairs']]
    require(pairs == [freeze(p) for p in source_pairs], 'crossing data differ from source')
    require(len(set(pairs))==len(pairs), 'duplicate crossing pair')
    for e,f in pairs:
        require(e in edges and f in edges and e<f, 'nonnormalized crossing edges')
        require(set(e).isdisjoint(f), 'adjacent edges cross')
    four_counts=Counter(tuple(sorted(e+f)) for e,f in pairs)
    require(four_counts == Counter({q:1 for q in combinations(range(n),4)}), 'not exactly one crossing per K4')
    nc=len(pairs)
    incidence={e:{i for i,p in enumerate(pairs) if e in p} for e in edges}

    orders={}
    for e,order in cert['edge_crossing_orders']:
        e=tuple(e)
        require(e in edges and e not in orders, 'invalid or repeated original edge')
        require(len(order)==len(set(order)), 'repeated crossing on original path')
        require(set(order)==incidence[e], 'path has missing or extra crossings')
        orders[e]=order
    require(set(orders)==edges, 'missing original edge')

    # A port is a half-edge attached to a node. For crossing i on edge (a,b),
    # side 0 points toward a and side 1 toward b along that simple edge path.
    ports={}
    for number,description in cert['ports']:
        require(type(number) is int and number not in ports, 'repeated or invalid port number')
        ports[number]=freeze(description)
    require(set(ports)==set(range(len(ports))), 'port numbers are not consecutive')
    require(len(set(ports.values()))==len(ports), 'duplicate port description')
    expected_ports={('v',v,e) for e in edges for v in e}
    expected_ports.update(('x',i,e,side) for i,p in enumerate(pairs) for e in p for side in (0,1))
    require(set(ports.values())==expected_ports, 'incorrect port set')
    port_number={p:i for i,p in ports.items()}

    node_of={}
    rows=cert['vertex_port_rotations']
    require(len(rows)==n+nc, 'wrong planarized vertex count')
    all_row_ports=[p for row in rows for p in row]
    require(len(all_row_ports)==len(ports) and set(all_row_ports)==set(ports), 'rotations do not partition the ports')
    rotations={}
    for index,row in enumerate(rows):
        node=('v',index) if index<n else ('x',index-n)
        expected={k for k,p in ports.items() if p[:2]==node}
        require(set(row)==expected and len(row)==len(expected), 'ports at wrong planarized vertex')
        require(len(row)==(n-1 if index<n else 4), 'wrong node degree')
        rotations[node]=row
        node_of.update({p:node for p in row})
        if index<n:
            neighbor_rotation=[next(v for v in ports[p][2] if v!=index) for p in row]
            require(cyclic_equal(neighbor_rotation,rs[index]), 'original cyclic rotation mismatch')
        else:
            i=index-n
            edge_colors=[ports[p][2] for p in row]
            require(edge_colors[0]==edge_colors[2] and edge_colors[1]==edge_colors[3] and edge_colors[0]!=edge_colors[1], 'crossing branches do not alternate')
            require(set(edge_colors)==set(pairs[i]), 'crossing has wrong edge colors')
            ends=[ports[p][2][ports[p][3]] for p in row]
            require(cyclic_equal(ends,cert['crossing_endpoint_rotations'][i]), 'redundant endpoint rotation mismatch')

    alpha=cert['edge_port_pairing']
    require(len(alpha)==len(ports), 'wrong alpha length')
    for p,q in enumerate(alpha):
        require(type(q) is int and q in ports and q!=p and alpha[q]==p, 'alpha is not a fixed-point-free involution')

    reconstructed={}
    node_segments=set()
    edge_paths=[]
    for e in sorted(edges):
        a,b=e
        order=orders[e]
        path=[('v',a)]+[('x',i) for i in order]+[('v',b)]
        require(len(set(path))==len(path), 'original path is not simple')
        edge_paths.append([list(e), [list(v) for v in path]])
        outgoing=port_number['v',a,e]
        links=[]
        for i in order:
            incoming=port_number['x',i,e,0]
            links.append((outgoing,incoming))
            outgoing=port_number['x',i,e,1]
        links.append((outgoing,port_number['v',b,e]))
        require(len(links)==len(path)-1, 'path segment count mismatch')
        for p,q in links:
            require(p not in reconstructed and q not in reconstructed, 'port reused in paths')
            reconstructed[p]=q;reconstructed[q]=p
            segment=frozenset((node_of[p],node_of[q]))
            require(len(segment)==2 and segment not in node_segments, 'loop or duplicate planarized segment')
            node_segments.add(segment)
    require([reconstructed[p] for p in range(len(ports))]==alpha, 'pairing does not follow the original paths')

    adjacency={v:set() for v in rotations}
    for p,q in enumerate(alpha):
        adjacency[node_of[p]].add(node_of[q])
    visited={('v',0)};todo=deque(visited)
    while todo:
        for v in adjacency[todo.popleft()]-visited:
            visited.add(v);todo.append(v)
    require(visited==set(rotations), 'planarization disconnected')

    # Face successor is sigma(alpha(dart)), with the SAME cyclic direction at
    # every vertex. This is the orientable combinatorial-map convention.
    sigma={p:row[(i+1)%len(row)] for row in rows for i,p in enumerate(row)}
    require(set(sigma.values())==set(ports), 'sigma is not a permutation')
    successor={p:sigma[alpha[p]] for p in ports}
    require(set(successor.values())==set(ports), 'face successor is not a permutation')
    seen=set();face_cycles=[]
    for start in ports:
        if start in seen:continue
        walk=[];p=start
        while p not in seen:
            seen.add(p);walk.append(p);p=successor[p]
        require(p==start, 'face traversal failed to close at its start')
        face_cycles.append(walk)
    require(seen==set(ports), 'not all darts traversed')
    claimed=cert['face_port_cycles']
    normalize=lambda f:tuple(f[f.index(min(f)):]+f[:f.index(min(f))])
    require(all(f for f in claimed), 'empty claimed face')
    require(Counter(map(normalize,claimed))==Counter(map(normalize,face_cycles)), 'claimed faces differ from independently traversed faces')
    V=len(rotations);E=len(ports)//2;F=len(face_cycles)
    require(V==n+nc and E==len(edges)+2*nc, 'wrong V/E subdivision arithmetic')
    require(V-E+F==2, 'orientable surface is not a sphere')
    uncrossed=[e for e in sorted(edges) if not incidence[e]]
    return {'valid':True,'n':n,'original_edges':len(edges),'crossing_vertices':nc,
            'planarized_vertices':V,'planarized_edges':E,'faces':F,'euler_characteristic':V-E+F,
            'connected':True,'all_original_edge_paths_simple':True,
            'crossing_branches_alternate':True,'all_original_rotations_match':True,
            'all_darts_partitioned_by_faces':True,'exactly_one_crossing_per_K4':True,
            'uncrossed_edges':uncrossed,
            'conclusion':'The supplied crossings and original rotations admit an actual simple drawing on the sphere, hence in the plane.'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('certificate',nargs='?',type=Path,default=HERE/'certificate.json')
    parser.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    parser.add_argument('--output',type=Path,default=HERE/'certificate-check.json')
    args=parser.parse_args()
    rs_path=args.source/'rotation.json0';pair_path=args.source/'result.json'
    report=check(json.loads(args.certificate.read_text()),json.loads(rs_path.read_text()),json.loads(pair_path.read_text())['verified_model']['crossing_pairs'])
    report['sha256']={str(p.resolve()):sha256(p.read_bytes()).hexdigest() for p in (args.certificate,rs_path,pair_path,Path(__file__))}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
