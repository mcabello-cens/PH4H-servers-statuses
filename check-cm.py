#!/usr/bin/env python3
import os, sys, time, urllib.parse, requests

# ----------------- Config -----------------
BASE = (sys.argv[1] if len(sys.argv) >= 2 else os.environ.get("BASE_URL", "http://localhost:8180/fhir")).rstrip("/")
TIMEOUT = float(os.environ.get("TIMEOUT", "15"))
RETRIES = int(os.environ.get("RETRIES", "1"))
SLEEP_RETRY = float(os.environ.get("SLEEP_RETRY", "1"))
DEBUG = int(os.environ.get("DEBUG", "0"))

HEADERS = {"Accept": "application/fhir+json"}

def enc(s: str) -> str: return urllib.parse.quote(s, safe="")
def dec(s: str) -> str: return urllib.parse.unquote(s)

def get_json(url: str):
    last = None
    for _ in range(RETRIES + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(SLEEP_RETRY)
    if DEBUG: print(f"[DEBUG] GET failed: {url} -> {last}")
    return None

def rtype(obj) -> str: return obj.get("resourceType", "") if isinstance(obj, dict) else ""
def lstrip_spaces(s: str) -> str: return s[len(s) - len(s.lstrip()):]

# ----------------- 0) Ping -----------------
meta = get_json(f"{BASE}/metadata")
if not meta or rtype(meta) != "CapabilityStatement":
    print(f"[FAIL] /metadata no responde en {BASE}"); sys.exit(1)
print(f"[OK] metadata en {BASE}")

# ----------------- 1) Listar ConceptMaps (SIN filtros) -----------------
print("[INFO] Listando ConceptMap (SIN filtros)…")
entries = []  # (id, name from search or empty)
next_url = f"{BASE}/ConceptMap"
while True:
    page = get_json(next_url)
    if not page: print("[FAIL] Error listando ConceptMap"); sys.exit(1)
    for e in (page.get("entry") or []):
        res = e.get("resource") or {}
        if res.get("resourceType") == "ConceptMap":
            cid = (res.get("id") or "").strip()
            name = (res.get("name") or "").strip()
            if cid: entries.append((cid, name))
    link_next = next((l.get("url") for l in (page.get("link") or []) if l.get("relation")=="next" and l.get("url")), None)
    if not link_next: break
    next_url = link_next
print(f"[OK] ConceptMaps listados: {len(entries)}")

# ----------------- 2) Selección VS (sin marcar FAIL los demás) -----------------
candidates = []  # (id, name)
for cid, name in entries:
    if name:
        if lstrip_spaces(name).startswith("VS"): candidates.append((cid, name))
        elif DEBUG: print(f"[DEBUG] skip {cid} name='{name}' (no comienza por 'VS')")
    else:
        cm = get_json(f"{BASE}/ConceptMap/{enc(cid)}")
        if cm and rtype(cm)=="ConceptMap" and lstrip_spaces(cm.get("name","")).startswith("VS"):
            candidates.append((cid, cm.get("name","")))
        elif DEBUG:
            n = cm.get("name","") if cm else ""
            print(f"[DEBUG] skip {cid} name='{n}' (no VS o sin acceso)")

print(f"[INFO] ConceptMaps con name iniciando en 'VS': {len(candidates)}")

# ----------------- 3) Traducir candidatos VS -----------------
oks = fails = warns = 0
for cid, _name in candidates:
    cm = get_json(f"{BASE}/ConceptMap/{enc(cid)}")
    if not cm or rtype(cm)!="ConceptMap":
        # solo fallos de candidatos VS cuentan como FAIL
        print(f"[FAIL] GET {BASE}/ConceptMap/{cid}"); fails += 1; continue

    url_cm = (cm.get("url") or "").strip()
    src_uri = (cm.get("sourceUri") or cm.get("sourceCanonical") or "").strip()
    tgt_uri = (cm.get("targetUri") or cm.get("targetCanonical") or "").strip()
    if not url_cm or not src_uri or not tgt_uri:
        print(f"[FAIL] GET {BASE}/ConceptMap/{cid}  (sin url/source/target)"); fails += 1; continue

    exp = get_json(f"{BASE}/ValueSet/%24expand?url={enc(src_uri)}&_count=1")
    if not exp or rtype(exp)!="ValueSet":
        print(f"[FAIL] GET {BASE}/ValueSet/$expand?url={src_uri}&_count=1"); fails += 1; continue

    contains = ((exp.get("expansion") or {}).get("contains") or [])
    if not contains:
        print(f"[FAIL] GET {BASE}/ValueSet/$expand?url={src_uri}&_count=1  (sin conceptos)"); fails += 1; continue

    first = contains[0] or {}
    code = (first.get("code") or "").strip()
    system = (first.get("system") or "").strip()
    if not code or not system:
        print(f"[FAIL] GET {BASE}/ValueSet/$expand?url={src_uri}&_count=1  (primer concepto sin code/system)"); fails += 1; continue

    tr_url = (f"{BASE}/ConceptMap/%24translate"
              f"?url={enc(url_cm)}&code={enc(code)}&system={enc(system)}"
              f"&source={enc(src_uri)}&target={enc(tgt_uri)}")
    tres = get_json(tr_url)

    # Prefijo según resultado
    if not tres or rtype(tres)!="Parameters":
        print(f"[FAIL] GET {dec(tr_url)}"); fails += 1; continue

    matches = [p for p in (tres.get("parameter") or []) if p.get("name")=="match"]
    if matches:
        print(f"[OK] GET {dec(tr_url)}"); oks += 1
    else:
        print(f"[WARN] GET {dec(tr_url)}"); warns += 1

print("--------------------------------------------")
print(f"[RESUMEN] VS traducidos: OK={oks} | WARN={warns} | FAIL={fails}")
# Solo candidatos VS afectan OK/WARN/FAIL. Los no-VS no se cuentan.
sys.exit(1 if fails > 0 else 0)
