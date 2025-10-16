#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.parse
import requests

# ---- Config y defaults (compatibles con el Bash original) ----
def env(name, default):
    return os.environ.get(name, default)

TIMEOUT   = float(env("TIMEOUT", "15"))
RETRIES   = int(env("RETRIES", "1"))
SLEEP_RETRY = float(env("SLEEP_RETRY", "1"))

# Args
if len(sys.argv) < 2:
    print("[FAIL] Uso: check_codesystems.py BASE_URL [CS_LOCAL_URL] [LOCAL_CODE]")
    sys.exit(1)

BASE = sys.argv[1].rstrip("/")
CS_LOCAL_ARG = sys.argv[2] if len(sys.argv) >= 3 else None
CODE_LOCAL_ARG = sys.argv[3] if len(sys.argv) >= 4 else None

# CodeSystem URLs
CS_SNOMED  = env("CS_SNOMED",  "http://snomed.info/sct")
CS_CIE10   = env("CS_CIE10",   "http://hl7.org/fhir/sid/icd-10")
CS_CIE11   = env("CS_CIE11",   "http://id.who.int/icd/release/11/mms")
CS_LOCAL   = CS_LOCAL_ARG or env("CS_LOCAL", "http://racsel.org/connectathon")
CS_RACSEL  = env("CS_RACSEL",  "http://racsel.org/connectathon")
CS_PREQUAL = env("CS_PREQUAL", "http://smart.who.int/pcmt-vaxprequal/CodeSystem/PreQualProductIDs")

# Códigos para $lookup
CODE_SNOMED  = env("CODE_SNOMED",  "96309000")
CODE_CIE10   = env("CODE_CIE10",   "E79.0")
CODE_CIE11   = env("CODE_CIE11",   "XM0N24")
CODE_LOCAL   = CODE_LOCAL_ARG or env("LOCAL_CODE", "LOCAL123")
CODE_RACSEL  = env("CODE_RACSEL",  "A10")
CODE_PREQUAL = env("CODE_PREQUAL", "PolioVaccineInactivatedIProduct8b13b5fcf5e9268b345775be7c3f077c")

headers = {
    "Accept": "application/fhir+json"
}

def enc(s: str) -> str:
    return urllib.parse.quote(s, safe="")

def get_json(url: str):
    """GET con reintentos; devuelve dict o None."""
    last_exc = None
    for attempt in range(RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            if attempt >= RETRIES:
                break
            time.sleep(SLEEP_RETRY)
    return None

def resource_type(obj) -> str:
    if not isinstance(obj, dict):
        return ""
    return obj.get("resourceType", "") or ""

def count_total(obj) -> int:
    """Total de un search con _summary=count (usualmente en root)."""
    if not isinstance(obj, dict):
        return 0
    # FHIR Bundle suele tener 'total' en la raíz
    t = obj.get("total")
    if isinstance(t, int):
        return t
    try:
        # fallback muy defensivo
        entry0 = (obj.get("entry") or [])[0]
        res = (entry0 or {}).get("resource") or {}
        t2 = res.get("total")
        return int(t2) if t2 is not None else 0
    except Exception:
        return 0

def must_ok(cond: bool, ok_msg: str, fail_msg: str):
    if cond:
        print(f"[OK] {ok_msg}")
    else:
        print(f"[FAIL] {fail_msg}")
        sys.exit(1)

print(f"[INFO] Base: {BASE}")

# 0) /metadata
# meta = get_json(f"{BASE}/metadata")
# must_ok(resource_type(meta) == "CapabilityStatement", "metadata", "no responde /metadata")

def check_cs_exists(label: str, url: str):
    q = f"{BASE}/CodeSystem?url={enc(url)}&_summary=count"
    js = get_json(q)
    n = count_total(js)
    if n >= 1:
        print(f"[OK] CodeSystem {label} presente ({url})")
    else:
        print(f"[FAIL] CodeSystem {label} NO encontrado ({url})")
        sys.exit(1)

def do_lookup(label: str, system: str, code: str):
    # %24lookup para ser robustos (aunque en Python no es necesario como en Bash)
    u = f"{BASE}/CodeSystem/%24lookup?system={enc(system)}&code={enc(code)}"
    r = get_json(u)
    if not r or resource_type(r) != "Parameters":
        print(f"[FAIL] $lookup {label} ({system}|{code})")
        sys.exit(1)
    # Éxito adicional: que traiga algún parámetro útil (display/name/code)
    params = [p for p in (r.get("parameter") or []) if p.get("name") in ("display", "name", "code")]
    if len(params) >= 1:
        print(f"[OK] $lookup {label} ({code})")
    else:
        print(f"[WARN] $lookup {label} sin display/name (aceptado)")

# 1) Existencia de CodeSystems
check_cs_exists("SNOMED", CS_SNOMED)
check_cs_exists("CIE10",  CS_CIE10)
check_cs_exists("CIE11",  CS_CIE11)
check_cs_exists("LOCAL",  CS_LOCAL)
check_cs_exists("RACSEL", CS_RACSEL)
check_cs_exists("PREQUAL", CS_PREQUAL)

# 2) Lookups
do_lookup("SNOMED", CS_SNOMED, CODE_SNOMED)
do_lookup("CIE10",  CS_CIE10,  CODE_CIE10)
do_lookup("CIE11",  CS_CIE11,  CODE_CIE11)
do_lookup("LOCAL",  CS_LOCAL,  CODE_LOCAL)
do_lookup("RACSEL", CS_RACSEL, CODE_RACSEL)
do_lookup("PREQUAL", CS_PREQUAL, CODE_PREQUAL)

print("[OK] Validación de CodeSystems y $lookup completada.")
