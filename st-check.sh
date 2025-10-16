#!/bin/bash
# ========================================================
# Script: check-status.sh
# Descripción:
#   Ejecuta los scripts de verificación de artefactos FHIR
#   (CodeSystem, ValueSet, ConceptMap) y genera un reporte
#   por país.
# Uso:
#   ./check-status.sh <FHIR_SERVER> <CODESYSTEM_URL> <CODE> <COUNTRY>
# Ejemplo:
#   ./check-status.sh http://fhir.mspas.gob.gt:8180/fhir http://racsel.org/fhir/CodeSystem/local-codes AP-1 GT
# ========================================================

# --- Validar argumentos ---
if [ "$#" -ne 4 ]; then
  echo "❌ Uso incorrecto."
  echo "Uso: $0 <FHIR_SERVER> <CODESYSTEM_URL> <CODE> <COUNTRY>"
  exit 1
fi

FHIR_SERVER="$1"
CODESYSTEM_URL="$2"
CODE="$3"
COUNTRY="$4"

OUTPUT_FILE="st-status-${COUNTRY}.txt"

echo "=====================================================" > "$OUTPUT_FILE"
echo " Reporte de estado SNOWSTORM - FHIR - País: ${COUNTRY}" >> "$OUTPUT_FILE"
echo " Fecha: $(date)" >> "$OUTPUT_FILE"
echo "=====================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# --- Ejecución de los scripts ---
echo "▶ Ejecutando check-cs.py..."
python3 check-cs.py "$FHIR_SERVER" "$CODESYSTEM_URL" "$CODE" >> "$OUTPUT_FILE" 2>&1

echo "▶ Ejecutando check-vs.py..."
python3 check-vs.py "$FHIR_SERVER" >> "$OUTPUT_FILE" 2>&1

echo "▶ Ejecutando check-cm.py..."
python3 check-cm.py "$FHIR_SERVER" >> "$OUTPUT_FILE" 2>&1

# --- Finalización ---
echo "" >> "$OUTPUT_FILE"
echo "✅ Revisión completada para ${COUNTRY}" >> "$OUTPUT_FILE"
echo "Resultado guardado en: ${OUTPUT_FILE}"

exit 0
