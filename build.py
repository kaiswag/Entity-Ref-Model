import json,collections,re
import os
HERE=os.path.dirname(os.path.abspath(__file__))
s=json.load(open(os.path.join(HERE,'entity-schema.json')))

# ---------- Pakete ----------
PKG_RULES=[  # (package, regex) – first match wins
 ("Grundlagen (System)", r"^(customer_group|customer_group_translation|unit|unit_translation|delivery_time|delivery_time_translation|document_type|document_type_translation)$"),
 ("Sichtbarkeit & Zuordnungen", r"^(product_visibility|landing_page_sales_channel|main_category|number_range_sales_channel|customer_group_registration_sales_channels|swag_dynamic_access_.*)$"),
 ("Suche (Advanced Search)", r"^advanced_search"),
 ("Kunden", r"^(product_review|product_review_summary|product_review_translation|product_review_summary_translation|swag_paypal_vault_token|swag_paypal_vault_token_mapping|swag_social_shopping_customer|custom_price)$"),
 ("Bestellungen & Dokumente", r"^(sales_channel_tracking_customer|sales_channel_tracking_order|swag_social_shopping_order|swag_paypal_transaction_report|swag_delay_action|b2b_order_employee)$"),
 ("CMS & Erlebniswelten", r"^(cms_|landing_page|swag_cms_extensions|app_cms_block|main_category$)"),
 ("Digital Sales Rooms", r"^dsr_"),
 ("Spatial / 3D", r"^(spatial_|ce_spatial)"),
 ("Custom Products", r"^swag_customized_products"),
 ("B2B Suite", r"^(b2b_|quote|customer_specific_features|ce_swag_sales_agent)"),
 ("Abos", r"^subscription"),
 ("Promotions & Bundles", r"^(promotion|bundle_)"),
 ("Bestellungen & Dokumente", r"^(order|document|state_machine_history)"),
 ("Kunden", r"^(customer|newsletter_recipient|sso_provider_customer)"),
 ("Medien", r"^media"),
 ("Regeln", r"^(rule|swag_dynamic_access)"),
 ("Mail & Flows", r"^(mail_|flow|swag_delay_action|webhook|swag_sequence)"),
 ("Zahlung & Versand", r"^(payment_method|shipping_method|app_payment_method|app_shipping_method|tax_provider)"),
 ("Sales Channel & Theme", r"^(sales_channel|theme|seo_url|snippet|product_export|swag_paypal_pos|swag_social|swag_language_pack)"),
 ("Katalog", r"^(product|category|property_group|unit|delivery_time|warehouse|measurement_display|custom_price)"),
 ("Grundlagen (System)", r".*"),
]
def pkg(e):
    for p,rx in PKG_RULES:
        if re.match(rx,e): return p
PKGS=["Grundlagen (System)","Medien","Regeln","Zahlung & Versand","Mail & Flows","Custom Products","CMS & Erlebniswelten","Katalog","Sales Channel & Theme","Sichtbarkeit & Zuordnungen","Suche (Advanced Search)","Kunden","Promotions & Bundles","Abos","B2B Suite","Bestellungen & Dokumente","Digital Sales Rooms","Spatial / 3D"]
assert set(PKGS)==set(p for p,_ in PKG_RULES), set(p for p,_ in PKG_RULES)^set(PKGS)

IGNORE_TARGET={'version','version_commit'}
AUDIT={'createdById','updatedById','createdByUserId','updatedByUserId'}

edges=[]  # (src, field, target, required, kind)
for e,d in s.items():
    props=d['properties']
    for f,p in props.items():
        if p.get('type')!='association': continue
        rel=p['relation']
        lf=p.get('localField')
        if rel not in('many_to_one','one_to_one'): continue
        if lf in (None,'id') : continue          # inverse side / extension pointing at us
        if lf.endswith('VersionId'): continue
        t=p['entity']
        if t in IGNORE_TARGET: continue
        if lf in AUDIT: continue
        req='required' in ((props.get(lf) or {}).get('flags') or {})
        if t==e: kind='self'
        else: kind='fk'
        edges.append(dict(src=e,field=lf,target=t,req=req,kind=kind))

# ---------- Weiche Abhängigkeiten (IDs in JSON, nicht im Schema) ----------
SOFT=[
 ("cms_slot","config (Element-Konfiguration)",["product","media","category","product_stream","product_manufacturer"],"Produkt-Slider/Box, Bild, Galerie, Kategorie-Navigation, Hersteller-Logo – IDs stehen im JSON der Slot-Konfiguration"),
 ("category","slotConfig",["media","product","product_stream"],"Überschreibungen der CMS-Slots je Kategorie"),
 ("product","slotConfig",["media","product"],"Überschreibungen der CMS-Slots je Produkt"),
 ("landing_page","slotConfig",["media","product","product_stream"],"Überschreibungen der CMS-Slots je Landingpage"),
 ("rule_condition","value",["product","category","customer_group","customer","sales_channel","payment_method","shipping_method","country","country_state","currency","language","tag","product_manufacturer","property_group_option","product_stream"],"Bedingungen speichern die gewählten IDs im JSON 'value'"),
 ("product_stream_filter","value",["product","category","product_manufacturer","property_group_option","tag","sales_channel"],"Filter dynamischer Produktgruppen"),
 ("flow_sequence","config",["mail_template","tag","customer_group","state_machine_state","document_type"],"Aktionen im Flow Builder (Mail senden, Tag setzen, Status ändern …)"),
 ("system_config","configurationValue",["cms_page","category","sales_channel","mail_template","media","state_machine_state"],"z. B. core.cms.default_product_cms_page, Plugin-Konfigurationen"),
 ("theme","configValues",["media"],"Logo, Favicon, Hintergrundbilder im Theme"),
 ("seo_url","foreignKey (polymorph)",["product","category","landing_page"],"SEO-URL zeigt je nach routeName auf Produkt, Kategorie oder Landingpage"),
 ("swag_customized_products_template_exclusion_condition","…",["swag_customized_products_template_option"],"Ausschlüsse verweisen auf Optionen"),
]
soft=[]
for src,field,targets,why in SOFT:
    if src not in s: continue
    for t in targets:
        if t in s: soft.append(dict(src=src,field=field,target=t,req=False,kind='soft',why=why))

ents={e:dict(pkg=pkg(e),translation=e.endswith('_translation'),
             mapping=(lambda pr: sum(1 for n,x in pr.items() if (x.get('flags') or {}).get('primary_key') and not n.lower().endswith('versionid'))>=2)(s[e]['properties']))
      for e in s}

# ---------- Paket-Matrix ----------
mat=collections.defaultdict(lambda: dict(req=0,opt=0,soft=0,items=[]))
for ed in edges+soft:
    a,b=ents[ed['src']]['pkg'],ents[ed['target']]['pkg']
    if a==b: continue
    c=mat[(a,b)]
    c['soft' if ed['kind']=='soft' else ('req' if ed['req'] else 'opt')]+=1
    c['items'].append([ed['src'],ed['field'],ed['target'],'soft' if ed['kind']=='soft' else ('req' if ed['req'] else 'opt')])

# ---------- Zyklen (Pflicht-FKs, Entity-Ebene) ----------
def scc(nodes,adj):
    idx={};low={};st=[];on=set();out=[];i=[0]
    import sys; sys.setrecursionlimit(10000)
    def sc(v):
        idx[v]=low[v]=i[0];i[0]+=1;st.append(v);on.add(v)
        for w in adj.get(v,()):
            if w not in idx: sc(w);low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            comp=[]
            while True:
                w=st.pop();on.discard(w);comp.append(w)
                if w==v:break
            out.append(comp)
    for v in nodes:
        if v not in idx: sc(v)
    return out
adj_req=collections.defaultdict(set); adj_all=collections.defaultdict(set)
for ed in edges:
    if ed['kind']=='self': continue
    adj_all[ed['src']].add(ed['target'])
    if ed['req']: adj_req[ed['src']].add(ed['target'])
cyc_req=[c for c in scc(list(s),adj_req) if len(c)>1]
cyc_all=[c for c in scc(list(s),adj_all) if len(c)>1]

# ---------- Entity-Reihenfolge (nur Pflicht-FKs) ----------
lvl={}
def level(e,stack=()):
    if e in lvl: return lvl[e]
    if e in stack: return 0
    l=0
    for t in adj_req.get(e,()): l=max(l,level(t,stack+(e,))+1)
    lvl[e]=l; return l
for e in s: level(e)

# Paket-Level: Pakete nach Pflicht-Abhängigkeiten zwischen Paketen
padj=collections.defaultdict(set)
for (a,b),c in mat.items():
    if c['req']: padj[a].add(b)
pcyc=[c for c in scc(PKGS,padj) if len(c)>1]
json.dump(dict(pkgs=PKGS,ents=ents,edges=edges,soft=soft,mat={f"{a}|{b}":v for (a,b),v in mat.items()},
               cyc_req=cyc_req,lvl=lvl),open(os.path.join(HERE,'model.json'),'w'))

# ---------- Prüfung: keine Pflicht-Referenz auf ein späteres Paket ----------
pos={p:i for i,p in enumerate(PKGS)}
back=[(a,b,it) for (a,b),c in mat.items() if pos[b]>pos[a] for it in c['items'] if it[3]=='req']
print(f"{len(s)} entities, {len(edges)} FK relations, {len(soft)} JSON references, {len(cyc_req)} mutual mandatory pairs")
if back:
    print("ERROR: mandatory references point to a later package:")
    for a,b,it in back: print(f"  {it[0]}.{it[1]} -> {it[2]}   ({a} -> {b})")
    raise SystemExit(1)
print("ok: load order valid, model.json written")

