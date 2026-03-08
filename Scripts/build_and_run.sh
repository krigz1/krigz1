#!/usr/bin/env bash
set -euo pipefail

# LivingWorldMMO one-shot build + run helper.
# Usage examples:
#   bash Scripts/build_and_run.sh
#   bash Scripts/build_and_run.sh --target game
#   bash Scripts/build_and_run.sh --target server --run-args "-log -nosteam"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TARGET_KIND="editor"
CONFIG="Development"
RUN_ARGS=""
UE_ROOT="${UE_ROOT:-${UE5_ROOT:-}}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)   TARGET_KIND="${2:-}"; shift 2 ;;
    --config)   CONFIG="${2:-}"; shift 2 ;;
    --run-args) RUN_ARGS="${2:-}"; shift 2 ;;
    --ue-root)  UE_ROOT="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '1,60p' "$0"
<<<<<<< HEAD
=======
    --target)
      TARGET_KIND="${2:-}"
      shift 2
      ;;
    --config)
      CONFIG="${2:-}"
      shift 2
      ;;
    --run-args)
      RUN_ARGS="${2:-}"
      shift 2
      ;;
    --ue-root)
      UE_ROOT="${2:-}"
      shift 2
      ;;
    -h|--help)
      sed -n '1,24p' "$0"
>>>>>>> origin/main
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$UE_ROOT" ]]; then
  echo "ERROR: define UE_ROOT (or UE5_ROOT), e.g.:"
  echo "  export UE_ROOT=/opt/UnrealEngine-5.3"
  exit 1
fi

BUILD_SH="$UE_ROOT/Engine/Build/BatchFiles/Linux/Build.sh"
EDITOR_BIN="$UE_ROOT/Engine/Binaries/Linux/UnrealEditor"
UPROJECT="$ROOT_DIR/LivingWorldMMO.uproject"

if [[ ! -x "$BUILD_SH" ]]; then
  echo "ERROR: Build.sh not found: $BUILD_SH"
  exit 1
fi

if [[ ! -x "$EDITOR_BIN" ]]; then
  echo "ERROR: UnrealEditor not found: $EDITOR_BIN"
  exit 1
fi

case "$TARGET_KIND" in
  editor) TARGET_NAME="LivingWorldMMOEditor"; EXTRA_ARGS="" ;;
  game)   TARGET_NAME="LivingWorldMMO";       EXTRA_ARGS="-game" ;;
  server) TARGET_NAME="LivingWorldMMO";       EXTRA_ARGS="-server -log" ;;
<<<<<<< HEAD
=======
TARGET_NAME=""
RUN_CMD=()

case "$TARGET_KIND" in
  editor)
    TARGET_NAME="LivingWorldMMOEditor"
    RUN_CMD=("$EDITOR_BIN" "$UPROJECT" $RUN_ARGS)
    ;;
  game)
    TARGET_NAME="LivingWorldMMO"
    RUN_CMD=("$EDITOR_BIN" "$UPROJECT" -game $RUN_ARGS)
    ;;
  server)
    TARGET_NAME="LivingWorldMMO"
    RUN_CMD=("$EDITOR_BIN" "$UPROJECT" -server -log $RUN_ARGS)
    ;;
>>>>>>> origin/main
  *)
    echo "ERROR: unsupported --target '$TARGET_KIND' (editor|game|server)"
    exit 1
    ;;
esac

echo "[1/3] Generating project files..."
"$EDITOR_BIN" "$UPROJECT" -projectfiles -game -engine -progress >/dev/null

echo "[2/3] Building $TARGET_NAME ($CONFIG)..."
"$BUILD_SH" "$TARGET_NAME" Linux "$CONFIG" "$UPROJECT" -NoHotReloadFromIDE -Progress

echo "[3/3] Running..."
# shellcheck disable=SC2068
"$EDITOR_BIN" "$UPROJECT" $EXTRA_ARGS $RUN_ARGS
<<<<<<< HEAD
=======
echo "[3/3] Running: ${RUN_CMD[*]}"
# shellcheck disable=SC2068
${RUN_CMD[@]}
>>>>>>> origin/main
