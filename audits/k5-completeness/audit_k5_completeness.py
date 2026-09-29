"""Independent local K4 uniqueness audit and isolated rerun of K5 enumeration."""
from pathlib import Path
from itertools import product,permutations,combinations
from collections import Counter
import importlib.util
import json

HERE=Path(__file__).resolve().parent
RELEASE=HERE.parents[1]
PROOF=RELEASE/'proofs/k5-completeness'
spec=importlib.util.spec_from_file_location('review_k5',PROOF/'enumerate_embeddings.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.HERE=HERE/'k5-rerun'
mod.main()

def independent_faces(rows):
    # Follow alpha(sigma(d)), opposite composition to producer, same orbit count.
    next_at={}
    for v,row in rows.items():
        assert len(set(row))==len(row)
        for i,w in enumerate(row):next_at[v,w]=row[(i+1)%len(row)]
    unseen=set(next_at);count=0
    while unseen:
        d=min(unseen);first=d
        while d in unseen:
            unseen.remove(d)
            v,w=d;d=(next_at[v,w],v)
        assert d==first
        count+=1
    return count

choices=(((0,1),(2,3)),((0,2),(1,3)),((0,3),(1,2)))
hist=Counter();records=[]
row_options=[]
for v in range(4):
    rest=[w for w in range(4) if w!=v]
    row_options.append([(rest[0],)+p for p in permutations(rest[1:])])
for rs in product(*row_options):
    hits=[]
    for idx,(e,f) in enumerate(choices):
        a,b=e;c,d=f
        for xr in [(a,c,b,d),(a,d,b,c)]:
            rows={v:[4 if tuple(sorted((v,w))) in (e,f) else w for w in row] for v,row in enumerate(rs)}
            rows[4]=list(xr)
            if independent_faces(rows)==5:hits.append((idx,xr))
    assert len(hits)<=1
    expected=mod.k4_crossing(rs,(0,1,2,3))
    assert expected==(hits[0] if hits else None)
    hist[str(len(hits))]+=1;records.append({'rotations':rs,'planar_choices':hits})

new=json.loads((mod.HERE/'classification.json').read_text())
old=json.loads((PROOF/'classification.json').read_text())
assert {k:v for k,v in new.items() if k!='seconds'}=={k:v for k,v in old.items() if k!='seconds'}

def canonical(row):
    j=row.index(min(row));return tuple(row[j:]+row[:j])

lookup={tuple(tuple(row) for row in rec['rotations']):rec['planar_choices'] for rec in records}
qs=list(combinations(range(5),4));edges=list(combinations(range(5),2))
allrows=[]
for v in range(1,5):
    rest=[w for w in range(5) if w!=v]
    allrows.append([(rest[0],)+p for p in permutations(rest[1:])])
independent=[]
for tail in product(*allrows):
    rs=[(1,2,3,4)]+list(tail);cross=[];crossrows=[];pattern=[]
    for q in qs:
        relabel={v:i for i,v in enumerate(q)}
        key=tuple(canonical([relabel[w] for w in rs[v] if w in relabel]) for v in q)
        hit=lookup[key]
        if not hit:break
        idx,xr=hit[0]
        pair=choices[idx]
        cross.append(tuple(tuple(q[w] for w in e) for e in pair))
        crossrows.append(tuple(q[w] for w in xr));pattern.append(idx)
    else:
        orderlists=[list(permutations(i for i,p in enumerate(cross) if e in p)) for e in edges]
        tested=0;count=0;maximum=0
        for candidate in product(*orderlists):
            toward={};tested+=1
            for e,ids in zip(edges,candidate):
                path=[e[0]]+[5+i for i in ids]+[e[1]]
                for j,v in enumerate(path):
                    if j:toward[v,e,e[0]]=path[j-1]
                    if j+1<len(path):toward[v,e,e[1]]=path[j+1]
            rows={v:[toward[v,tuple(sorted((v,w))),w] for w in row] for v,row in enumerate(rs)}
            for i,(pair,xr) in enumerate(zip(cross,crossrows)):
                rows[5+i]=[toward[5+i,next(e for e in pair if w in e),w] for w in xr]
            F=independent_faces(rows);maximum=max(maximum,F);count+=F==12
        independent.append({'rotation':[list(r) for r in rs],'pattern':pattern,'orders_checked':tested,
                            'plane_orders':count,'maximum_faces':maximum})
project=lambda records:[{k:r[k] for k in ('rotation','pattern','orders_checked','plane_orders','maximum_faces')} for r in records]
assert independent==project(new['classification'])
positive=0
for entry in new['classification']:
    cert=entry['first_embedding']
    if cert is None:continue
    rs=entry['rotation'];cross=cert['crossing_pairs'];orders={tuple(e):ids for e,ids in cert['edge_crossing_orders']}
    paths={e:[e[0]]+[5+i for i in ids]+[e[1]] for e,ids in orders.items()}
    toward={}
    for e,path in paths.items():
        for i,v in enumerate(path):
            if i:toward[v,e,e[0]]=path[i-1]
            if i+1<len(path):toward[v,e,e[1]]=path[i+1]
    rows={v:[toward[v,tuple(sorted((v,w))),w] for w in row] for v,row in enumerate(rs)}
    for i,(pair,row) in enumerate(zip(cross,cert['crossing_endpoint_rotations'])):
        rows[5+i]=[toward[5+i,tuple(next(e for e in pair if w in e)),w] for w in row]
    assert independent_faces(rows)==12
    positive+=1
result={'K4_all_cyclic_rotation_systems':16,'K4_counts_by_number_of_planar_crossing_choices':dict(hist),
        'K4_unique_choice_and_orientation_verified':True,'K4_full_records':records,
        'K5_rerun_matches_except_runtime':True,'K5_positive_certificates_independently_traversed':positive,
        'K5_full_classification_rederived_from_independent_K4_lookup_and_map_traversal':True,
        'K5_edge_order_cases':new['edge_order_combinations_checked']}
(HERE/'k5-completeness-audit-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='K4_full_records'},indent=2))
