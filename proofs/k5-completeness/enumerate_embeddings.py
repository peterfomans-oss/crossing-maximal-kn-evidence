"""Exhaustive K5 classification from rotations and plane embeddings, no catalogue.

Standard library only. Normalize row 0 to (1,2,3,4); enumerate 6^4 other
rotation rows and every crossing order on each edge. Positive outputs are
explicit sphere embeddings. Negative outputs exhaust every such edge order.
Run without -O (assertions are part of the verifier), preferably with -B.
"""
from itertools import combinations, permutations, product
from pathlib import Path
import json
import math
import time

HERE = Path(__file__).resolve().parent


def norm(e, f):
    return tuple(sorted((tuple(sorted(e)), tuple(sorted(f)))))


def options(q):
    a,b,c,d=q
    return (norm((a,b),(c,d)), norm((a,c),(b,d)), norm((a,d),(b,c)))


def faces(rotation):
    darts = {(v, w) for v, row in rotation.items() for w in row}
    assert all((w, v) in darts for v, w in darts)
    assert all(len(row) == len(set(row)) for row in rotation.values())
    successor = {(v, row[i]): row[(i+1)%len(row)]
                 for v, row in rotation.items() for i in range(len(row))}
    count = 0
    while darts:
        first = next(iter(darts)); current = first
        while current in darts:
            darts.remove(current)
            u,v=current
            current=(v, successor[v,u])
        assert current == first
        count += 1
    return count


def k4_crossing(rotation, q):
    """Determine crossing choice by explicit 5-vertex planarization, not signs."""
    result=[]
    for choice,(e,f) in enumerate(options(q)):
        a,b=e; c,d=f
        original={v:[-1 if tuple(sorted((v,w))) in (e,f) else w
                     for w in rotation[v] if w in q] for v in q}
        for row in ((a,c,b,d),(a,d,b,c)):
            r=dict(original); r[-1]=list(row)
            if faces(r) == 5:  # V=5,E=8 on a connected rotation map.
                result.append((choice, row))
    assert len(result) <= 1
    return result[0] if result else None


def map_from_orders(rotation, crossing, crossing_rows, orders):
    n=len(rotation); towards={}
    for e, ids in orders.items():
        path=[e[0]]+[n+i for i in ids]+[e[1]]
        assert len(path) == len(set(path))
        for i,v in enumerate(path):
            if i:
                towards[v,e,e[0]]=path[i-1]
            if i+1<len(path):
                towards[v,e,e[1]]=path[i+1]
    result={v:[towards[v,tuple(sorted((v,w))),w] for w in row]
            for v,row in enumerate(rotation)}
    for i,((e,f),row) in enumerate(zip(crossing,crossing_rows)):
        assert set(row)==set(e+f) and len(row)==4
        assert all((row[j] in e)!=(row[(j+1)%4] in e) for j in range(4))
        result[n+i]=[towards[n+i,e if v in e else f,v] for v in row]
    return result


def orbit(seed):
    qs=list(combinations(range(5),4))
    c=[options(q)[s] for q,s in zip(qs,seed)]
    output=set()
    for p in permutations(range(5)):
        mapped={norm(tuple(p[v] for v in e),tuple(p[v] for v in f)) for e,f in c}
        output.add(tuple(next(i for i,cross in enumerate(options(q)) if cross in mapped) for q in qs))
    return output


def main():
    started=time.perf_counter()
    n=5; edges=list(combinations(range(n),2)); qs=list(combinations(range(n),4))
    row_options=[]
    for v in range(1,n):
        rest=sorted(set(range(n))-{v})
        row_options.append([(rest[0],)+p for p in permutations(rest[1:])])
    examined=0; survivors=[]
    for tail in product(*row_options):
        examined+=1
        rotation=[(1,2,3,4)]+list(tail)
        k4=[k4_crossing(rotation,q) for q in qs]
        if any(r is None for r in k4):
            continue
        pattern=tuple(r[0] for r in k4)
        crossing=[options(q)[r[0]] for q,r in zip(qs,k4)]
        crossing_rows=[r[1] for r in k4]
        incident={e:tuple(i for i,c in enumerate(crossing) if e in c) for e in edges}
        order_choices=[list(permutations(incident[e])) for e in edges]
        cases=math.prod(math.factorial(len(incident[e])) for e in edges)
        checked=0; embeddings=0; maximum=-1; first=None
        for lists in product(*order_choices):
            checked+=1
            orders=dict(zip(edges,lists))
            F=faces(map_from_orders(rotation,crossing,crossing_rows,orders))
            maximum=max(maximum,F)
            if F==12:  # V=10,E=20, connected.
                embeddings+=1
                if first is None:
                    first={'edge_crossing_orders':[[e,orders[e]] for e in edges],
                           'crossing_endpoint_rotations':crossing_rows,'crossing_pairs':crossing,
                           'V':10,'E':20,'F':F}
        assert checked==cases
        survivors.append({'rotation':rotation,'pattern':pattern,'orders_checked':checked,
                          'plane_orders':embeddings,'maximum_faces':maximum,'first_embedding':first})
    assert examined==1296
    good=[r for r in survivors if r['plane_orders']]
    bad=[r for r in survivors if not r['plane_orders']]
    seeds=((1,1,1,1,1),(1,1,1,2,2))
    actual_orbit=set().union(*(orbit(r['pattern']) for r in good))
    claimed_orbit=orbit(seeds[0])|orbit(seeds[1])
    assert actual_orbit==claimed_orbit
    assert len(survivors)==36 and len(good)==24 and len(bad)==12 and len(actual_orbit)==72
    report={'method':'All normalized rotations and all crossing orders; no SAT or catalogue input.',
            'normalized_rotations_checked':examined,'K4_compatible_rotations':len(survivors),
            'plane_rotations':len(good),'nonrealizable_K4_compatible_rotations':len(bad),
            'edge_order_combinations_checked':sum(r['orders_checked'] for r in survivors),
            'two_explicit_seed_orbits_equal_all_realizable_tables':True,
            'labelled_crossing_tables':len(actual_orbit),'seeds':seeds,
            'classification':survivors,'seconds':time.perf_counter()-started}
    HERE.mkdir(exist_ok=True)
    (HERE/'classification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='classification'},indent=2))


if __name__=='__main__':
    main()
