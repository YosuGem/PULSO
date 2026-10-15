#!/bin/bash
# Lanzador de Pulso para Linux y macOS.
#
# Equivalente a iniciar_noosfera.bat (que es solo para Windows).
# Levanta el servidor en 127.0.0.1:8080. CTRL+C para detenerlo.
#
# Uso:
#   chmod +x iniciar_noosfera.sh
#   ./iniciar_noosfera.sh
#
# La clave de API es de prueba local. Cámbiala antes de usarlo en serio:
#   export NOOSFERA_API_KEY="tu-clave"

set -e
cd "$(dirname "$0")"

export NOOSFERA_API_KEY="${NOOSFERA_API_KEY:-noosfera_local_prueba_2026}"
export NOOSFERA_PUERTO="${NOOSFERA_PUERTO:-8080}"
export NOOSFERA_HOST="${NOOSFERA_HOST:-127.0.0.1}"

echo "Iniciando Pulso en http://localhost:${NOOSFERA_PUERTO} (CTRL+C para detener)"
exec python noosfera.py --server "${NOOSFERA_PUERTO}"
