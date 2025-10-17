import os
import json
import tarfile
from pathlib import Path
import tempfile
import argparse

def build_index_and_package(source_dir: Path):
    """
    Crea estructuras de datos para .index.json y package.json
    leyendo los JSON FHIR en la carpeta.
    """
    files_info = []
    resources_info = []

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".json") and not file.startswith((".", "package", "index")):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(source_dir).as_posix()

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    resource_type = data.get("resourceType", "Unknown")
                    resource_id = data.get("id", "")
                    url = data.get("url", "")
                    kind = resource_type.lower()

                    files_info.append({
                        "filename": rel_path,
                        "resourceType": resource_type,
                        "id": resource_id,
                        "kind": kind,
                        "url": url
                    })

                    ref_path = rel_path.replace(".json", "")
                    resources_info.append({
                        "type": resource_type,
                        "reference": ref_path
                    })

                except Exception as e:
                    print(f"⚠️  Error leyendo {file_path}: {e}")

    index_file = {"index-version": 1, "files": files_info}
    package_manifest = {
        "name": "giis.fhir.package",
        "version": "1.0.0",
        "description": "GIIS FHIR Package",
        "fhirVersion": "4.0.1",
        "dependencies": {},
        "author": "CENS",
        "url": "http://cens.cl",
        "resources": resources_info
    }

    return index_file, package_manifest


def build_giis_package(source_dir: Path):
    """
    Crea el archivo giis-package.tgz con estructura:
    package/
      ├── package.json
      ├── .index.json
      ├── CodeSystem/...
      ├── ValueSet/...
      └── ConceptMap/...
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"❌ Carpeta no encontrada: {source_dir}")

    index_file, package_manifest = build_index_and_package(source_dir)

    output_tgz_path = source_dir / "giis-package.tgz"
    print(f"📦 Creando paquete: {output_tgz_path.name}")

    with tarfile.open(output_tgz_path, "w:gz") as tar:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            # ---- Crear package.json temporal
            manifest_path = temp_dir / "package.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(package_manifest, f, ensure_ascii=False, indent=2)
            tar.add(manifest_path, arcname="package/package.json")

            # ---- Crear .index.json temporal
            index_path = temp_dir / ".index.json"
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index_file, f, ensure_ascii=False, indent=2)
            tar.add(index_path, arcname="package/.index.json")

            # ---- Agregar cada recurso JSON
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.endswith(".json") and not file.startswith((".", "package", "index")):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(source_dir).as_posix()
                        tar.add(file_path, arcname=f"package/{rel_path}")
                        print(f"  ➕ {rel_path}")

    print(f"✅ Paquete creado: {output_tgz_path.resolve()}")
    print("📤 Cargar en Snowstorm con:")
    print(f"curl --form file=@{output_tgz_path.name} --form resourceUrls=\"*\" http://localhost/fhir-admin/load-package")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construye el paquete giis-package.tgz para Snowstorm.")
    parser.add_argument("-d", "--directory", required=True, help="Carpeta con los JSON FHIR (CodeSystem, ValueSet, ConceptMap, etc.)")
    args = parser.parse_args()

    build_giis_package(Path(args.directory))
