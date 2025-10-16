#!/usr/bin/env python3
import os, sys, time, urllib.parse, requests

# ---- Config ----
BASE = (sys.argv[1] if len(sys.argv) >= 2 else os.environ.get("BASE_URL", "http://192.168.10.18/fhir")).rstrip("/")
TIMEOUT = float(os.environ.get("TIMEOUT", "15"))
RETRIES = int(os.environ.get("RETRIES", "2"))
SLEEP_RETRY = float(os.environ.get("SLEEP_RETRY", "2"))
EXPECTED_TOTAL = int(os.environ.get("EXPECTED_TOTAL", "24"))

HEADERS = {"Accept": "application/fhir+json"}

def enc(s: str) -> str:
    return urllib.parse.quote(s, safe="")

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
    return None

def rtype(obj) -> str:
    return obj.get("resourceType", "") if isinstance(obj, dict) else ""

print("[INFO] Base:", BASE)

# 0) Ping rápido
meta = get_json(f"{BASE}/metadata")
if not meta or rtype(meta) != "CapabilityStatement":
    print("[FAIL] El servidor no responde /metadata correctamente"); sys.exit(1)
print("[OK] metadata")

# 1) Listar TODOS los ValueSet (paginación) y recolectar id/url
print("[INFO] Listando ValueSet…")
valuesets = []  # cada item: ("url", <canonical>) o ("id", <id>)
next_url = f"{BASE}/ValueSet?_count=200&_elements=id,url"
total_listados = 0

while True:
    page = get_json(next_url)
    if not page:
        print("[FAIL] Error listando ValueSet"); sys.exit(1)
    entries = (page.get("entry") or [])
    total_listados += len(entries)
    for e in entries:
        res = e.get("resource") or {}
        if res.get("resourceType") != "ValueSet":
            continue
        url = (res.get("url") or "").strip()
        vid = (res.get("id") or "").strip()
        if url:
            valuesets.append(("url", url))
        elif vid:
            valuesets.append(("id", vid))
    # paginación
    links = page.get("link") or []
    next_link = next((l.get("url") for l in links if l.get("relation") == "next" and l.get("url")), None)
    if not next_link:
        break
    next_url = next_link

print(f"[OK] ValueSet listados: {total_listados}")

# 2) Validar que el total sea EXACTAMENTE EXPECTED_TOTAL
if total_listados != EXPECTED_TOTAL:
    print(f"[FAIL] Se encontraron {total_listados} ValueSet(s); se requieren exactamente {EXPECTED_TOTAL}.")
    sys.exit(1)
print(f"[OK] Total de ValueSet = {EXPECTED_TOTAL}")

# 3) Expandir cada VS y exigir ≥ 1 concepto
print("[INFO] Expandiendo cada ValueSet (≥ 1 concepto)…")
vs_total = 0
vs_ok = 0
fails = []

for key, val in valuesets:
    if not val:
        continue
    vs_total += 1
    if key == "url":
        exp_u = f"{BASE}/ValueSet/%24expand?url={enc(val)}&_count=1&_elements=expansion.total,expansion.contains"
        label = val
    else:
        exp_u = f"{BASE}/ValueSet/{enc(val)}/%24expand?_count=1&_elements=expansion.total,expansion.contains"
        label = f"ValueSet/{val}"

    resp = get_json(exp_u)
    if not resp or rtype(resp) != "ValueSet":
        print(f"[FAIL] {label} -> respuesta inválida")
        fails.append(label)
        continue

    total = int((resp.get("expansion") or {}).get("total") or 0)
    contains = (resp.get("expansion") or {}).get("contains") or []
    if total > 0 or len(contains) > 0:
        print(f"[OK] {label}")
        vs_ok += 1
    else:
        print(f"[FAIL] {label} (sin conceptos)")
        fails.append(label)

print("--------------------------------------------")
print(f"[RESUMEN] ValueSet totales: {vs_total} | OK: {vs_ok} | FAIL: {len(fails)}")

if fails:
    print("[DETALLE] ValueSet que fallaron:")
    for f in fails:
        print(f)
    sys.exit(1)

print(f"[OK] Todos los ValueSet ({vs_total}) expanden con ≥ 1 concepto")
