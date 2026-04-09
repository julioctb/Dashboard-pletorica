#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_ENV="${PROJECT_ROOT}/.env"

usage() {
  cat <<'EOF'
Uso:
  ./scripts/switch_env.sh local [--dry-run]
  ./scripts/switch_env.sh cloud [--dry-run]

Opciones:
  local       Activa .env.local
  cloud       Activa .env.cloud
  --dry-run   Muestra acciones sin escribir archivos
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

MODE="$1"
DRY_RUN="false"

if [[ $# -eq 2 ]]; then
  if [[ "$2" == "--dry-run" ]]; then
    DRY_RUN="true"
  else
    echo "Opcion no valida: $2"
    usage
    exit 1
  fi
fi

case "$MODE" in
  local)
    SOURCE_ENV="${PROJECT_ROOT}/.env.local"
    ;;
  cloud|online)
    SOURCE_ENV="${PROJECT_ROOT}/.env.cloud"
    MODE="cloud"
    ;;
  *)
    echo "Modo no valido: $MODE"
    usage
    exit 1
    ;;
esac

if [[ ! -f "$SOURCE_ENV" ]]; then
  echo "No existe el archivo: $SOURCE_ENV"
  echo "Crea ese archivo antes de cambiar de entorno."
  exit 1
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_ENV="${PROJECT_ROOT}/.env.backup.${TIMESTAMP}"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] Modo destino: $MODE"
  echo "[dry-run] Origen: $SOURCE_ENV"
  if [[ -f "$TARGET_ENV" ]]; then
    echo "[dry-run] Se crearia backup: $BACKUP_ENV"
  fi
  echo "[dry-run] Se actualizaria: $TARGET_ENV"
  exit 0
fi

if [[ -f "$TARGET_ENV" ]]; then
  cp "$TARGET_ENV" "$BACKUP_ENV"
  echo "Backup actual guardado en: $BACKUP_ENV"
fi

cp "$SOURCE_ENV" "$TARGET_ENV"
echo "Entorno activo: $MODE"
echo "Archivo aplicado: $SOURCE_ENV -> $TARGET_ENV"

if [[ "$MODE" == "local" ]]; then
  cat <<'EOF'
Siguiente paso sugerido:
  npx supabase start
EOF
else
  cat <<'EOF'
Siguiente paso sugerido:
  npx supabase stop
EOF
fi
