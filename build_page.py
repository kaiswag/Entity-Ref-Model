#!/usr/bin/env python3
"""model.json + entity-schema.json + version.json -> index.html (standalone page)"""
import json, collections, os

here = os.path.dirname(os.path.abspath(__file__))
p = lambda n: os.path.join(here, n)
m = json.load(open(p('model.json')))
schema = json.load(open(p('entity-schema.json')))
P = m['pkgs']; pi = {x: i for i, x in enumerate(P)}
E = sorted(m['ents']); ei = {e: i for i, e in enumerate(E)}

whys = {}; out = collections.defaultdict(list)
for ed in m['edges'] + m['soft']:
    k = 3 if ed['kind'] == 'self' else 2 if ed['kind'] == 'soft' else 0 if ed['req'] else 1
    w = ed.get('why'); row = [ei[ed['target']], ed['field'], k]
    if w: row.append(whys.setdefault(w, len(whys)))
    out[ed['src']].append(row)

FLAGS = ['primary_key', 'required', 'translatable', 'inherited', 'write_protected', 'computed', 'runtime',
         'cascade_delete', 'restrict_delete', 'set_null_on_delete', 'extension', 'deprecated', 'allow_html', 'search_ranking', 'immutable']
REL = {'many_to_one': 'n:1', 'one_to_many': '1:n', 'many_to_many': 'n:m', 'one_to_one': '1:1'}
descs = {}
short_type = lambda t: t.rsplit('\\', 1)[-1].replace('Field', '').lower() if '\\' in (t or '') else t
fields = []
for e in E:
    props = schema[e]['properties']
    fk = {pr['localField']: pr['entity'] for pr in props.values()
          if pr.get('type') == 'association' and pr['relation'] in ('many_to_one', 'one_to_one') and pr.get('localField') not in (None, 'id')}
    rows = []
    for f, pr in props.items():
        fl = pr.get('flags') or {}
        assoc = pr.get('type') == 'association'
        tgt = pr['entity'] if assoc else fk.get(f)
        d = pr.get('description')
        rows.append([f, 'association' if assoc else short_type(pr.get('type')),
                     sum(1 << i for i, k in enumerate(FLAGS) if k in fl),
                     ei.get(tgt, -1) if tgt else -1,
                     REL.get(pr.get('relation'), '') if assoc else ('fk' if f in fk else ''),
                     descs.setdefault(d, len(descs)) if d else -1])
    fields.append(rows)

ents = [[e, pi[m['ents'][e]['pkg']], m['lvl'][e], int(m['ents'][e]['translation']), int(m['ents'][e]['mapping']), out.get(e, [])] for e in E]
meta = json.load(open(p('version.json'))) if os.path.exists(p('version.json')) else {}
data = dict(pkgs=P, ents=ents, fields=fields, flagNames=FLAGS,
            descs=[d for d, _ in sorted(descs.items(), key=lambda x: x[1])],
            whys=[w for w, _ in sorted(whys.items(), key=lambda x: x[1])], cycles=m['cyc_req'],
            version=meta.get('version', '6.x'), shop=meta.get('shop', 'unbekannt'))
body = open(p('page.tpl.html')).read().replace('__DATA__', json.dumps(data, separators=(',', ':'), ensure_ascii=False))
html = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(p('index.html'), 'w').write(html)
print('ok: index.html')
