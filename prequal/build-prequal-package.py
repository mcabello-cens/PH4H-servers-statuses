#!/usr/bin/env python3
import json
import tarfile
import tempfile
import os
from pathlib import Path
from datetime import datetime

# === Configuración de recursos ===
CODE_SYSTEM_FILE = Path("PreQualCodeSystem.json")
VALUE_SET_FILE = Path("VacunasPreQualValueSet.json")
OUTPUT_TGZ = Path("prequal-package.tgz")

# === Validaciones ===
if not CODE_SYSTEM_FILE.exists() or not VALUE_SET_FILE.exists():
    raise FileNotFoundError("❌ No se encontró alguno de los archivos FHIR necesarios (.json).")

# === Cargar recursos FHIR ===
with open(CODE_SYSTEM_FILE, "r", encoding="utf-8") as f:
    cs_data = json.load(f)
with open(VALUE_SET_FILE, "r", encoding="utf-8") as f:
    vs_data = json.load(f)

# === Generar .index.json ===
index_data = {
    "index-version": 1,
    "files": [
        {
            "filename": f"CodeSystem/{CODE_SYSTEM_FILE.name}",
            "resourceType": "CodeSystem",
            "id": cs_data.get("id", "prequal-codesystem"),
            "kind": "codesystem",
            "url": cs_data.get("url"),
            "version": cs_data.get("version", "2024")
        },
        {
            "filename": f"ValueSet/{VALUE_SET_FILE.name}",
            "resourceType": "ValueSet",
            "id": vs_data.get("id", "prequal-valueset"),
            "kind": "valueset",
            "url": vs_data.get("url"),
            "version": vs_data.get("version", "2024")
        }
    ]
}

# === Generar package.json ===
package_data = {
    "name": "who.prequal.package",
    "version": datetime.now().strftime("%Y.%m.%d"),
    "description": "WHO Prequalified Vaccine Products (WHO/RACSEL Package)",
    "author": "WHO / RACSEL",
    "url": "http://who.org",
    "fhirVersion": "4.0.1",
    "dependencies": {},
    "resources": [
        {"type": "CodeSystem", "reference": f"CodeSystem/{CODE_SYSTEM_FILE.stem}"},
        {"type": "ValueSet", "reference": f"ValueSet/{VALUE_SET_FILE.stem}"}
    ]
}

# === Crear estructura temporal ===
temp_dir = tempfile.mkdtemp(prefix="prequal_pkg_")
package_dir = Path(temp_dir) / "package"
(package_dir / "CodeSystem").mkdir(parents=True, exist_ok=True)
(package_dir / "ValueSet").mkdir(parents=True, exist_ok=True)

# Guardar los archivos .index.json y package.json
with open(package_dir / ".index.json", "w", encoding="utf-8") as f:
    json.dump(index_data, f, ensure_ascii=False, indent=2)

with open(package_dir / "package.json", "w", encoding="utf-8") as f:
    json.dump(package_data, f, ensure_ascii=False, indent=2)

# Copiar los recursos FHIR
os.system(f'cp "{CODE_SYSTEM_FILE}" "{package_dir / "CodeSystem"}"')
os.system(f'cp "{VALUE_SET_FILE}" "{package_dir / "ValueSet"}"')

# === Crear el paquete TGZ ===
with tarfile.open(OUTPUT_TGZ, "w:gz") as tar:
    tar.add(package_dir, arcname="package")

print("✅ Paquete FHIR generado correctamente:")
print(f"   → Archivo: {OUTPUT_TGZ}")
print(f"   → Contenido:")
print(f"      - package/.index.json")
print(f"      - package/package.json")
print(f"      - package/CodeSystem/{CODE_SYSTEM_FILE.name}")
print(f"      - package/ValueSet/{VALUE_SET_FILE.name}")
