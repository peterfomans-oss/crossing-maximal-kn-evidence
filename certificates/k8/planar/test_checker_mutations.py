"""Check meaningful invalid map/path certificates are rejected."""
from copy import deepcopy
import json
from pathlib import Path
from check_certificate import check, InvalidCertificate, HERE, DEFAULT_SOURCE

original=json.loads((HERE/'certificate.json').read_text())
rotation=json.loads((DEFAULT_SOURCE/'rotation.json0').read_text())
pairs=json.loads((DEFAULT_SOURCE/'result.json').read_text())['verified_model']['crossing_pairs']


def facecycles(cert):
    sigma={p:row[(i+1)%len(row)] for row in cert['vertex_port_rotations'] for i,p in enumerate(row)}
    alpha=cert['edge_port_pairing'];seen=set();result=[]
    for start in sigma:
        if start in seen:continue
        cur=start;walk=[]
        while cur not in seen:
            seen.add(cur);walk.append(cur);cur=sigma[alpha[cur]]
        result.append(walk)
    return result


def repeated_crossing(c):
    row=next(row for e,row in c['edge_crossing_orders'] if row)
    row.append(row[0])


def path_permutation(c):
    row=next(row for e,row in c['edge_crossing_orders'] if len(row)>1)
    row[0],row[1]=row[1],row[0]


def original_rotation(c):
    row=c['vertex_port_rotations'][0]
    row[0],row[1]=row[1],row[0]


def touching(c):
    row=c['vertex_port_rotations'][c['n']]
    row[1],row[2]=row[2],row[1]


def higher_genus(c):
    i=c['n']
    c['vertex_port_rotations'][i].reverse()
    c['crossing_endpoint_rotations'][0].reverse()
    c['face_port_cycles']=facecycles(c)


def missing_face(c):
    c['face_port_cycles'].pop()


result={'valid_original_passes':check(original,rotation,pairs)['valid'],'mutations':[]}
for name,mutate,expected in [
    ('repeated crossing on path',repeated_crossing,'repeated crossing'),
    ('path permutation inconsistent with pairing',path_permutation,'pairing does not follow'),
    ('original rotation changed',original_rotation,'original cyclic rotation'),
    ('touch instead of crossing',touching,'do not alternate'),
    ('alternating connected map on higher-genus surface',higher_genus,'not a sphere'),
    ('missing claimed face',missing_face,'claimed faces differ'),
]:
    altered=deepcopy(original);mutate(altered)
    try:
        check(altered,rotation,pairs)
    except InvalidCertificate as exc:
        message=str(exc)
        if expected not in message:raise RuntimeError((name,expected,message))
        result['mutations'].append({'mutation':name,'rejected':True,'reason':message})
    else:
        raise RuntimeError('Incorrectly accepted: '+name)
(HERE/'checker-mutation-tests.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
