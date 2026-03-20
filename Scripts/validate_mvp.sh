#!/usr/bin/env bash
set -euo pipefail

if ! command -v rg &>/dev/null; then
  echo "⚠️  ripgrep non trouvé, fallback sur grep."
  rg() { grep -rn "$@"; }
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "LivingWorldMMO.uproject"
  "Source/LivingWorldMMO/Public/Agents/LWAgentBrainComponent.h"
  "Source/LivingWorldMMO/Private/Director/LWDirectorSubsystem.cpp"
  "Source/LivingWorldMMO/Private/Net/LWReplicationGraph.cpp"
  "Config/DefaultEngine.ini"
  "Config/DefaultGame.ini"
  "Config/Tags/GameplayTags.ini"
  "Docs/MVP_Implementation_Guide_FR.md"
  "Data/LivingMytho/runtime_guards.json"
  "Data/LivingWorld/director_state.json"
  "Scripts/eli_bridge/mle_living_world.py"
)

for f in "${required_files[@]}"; do
  [[ -f "$f" ]] || { echo "MISSING: $f"; exit 1; }
  echo "OK: $f"
done

rg -n "Event\.Conflict\.BanditRaid" Config/Tags/GameplayTags.ini >/dev/null
rg -n "Event\.Wildlife\.Disturbance" Config/Tags/GameplayTags.ini >/dev/null
rg -n "ReplicationGraphClassName" Config/DefaultEngine.ini >/dev/null
rg -n "ValidateAgainstCodeElisabeth" Source/LivingWorldMMO/Private/Director/LWDirectorSubsystem.cpp >/dev/null
rg -n "MaxAutonomousSeverity" Config/DefaultGame.ini >/dev/null
rg -n "def Director_HandleRequest" Scripts/eli_bridge/mle_living_world.py >/dev/null
rg -n "schema_version" Data/LivingWorld/director_state.json >/dev/null
rg -n "RunEconomyPass" Source/LivingWorldMMO/Private/Director/LWDirectorSubsystem.cpp >/dev/null
rg -n "GetDirectorStatus" Source/LivingWorldMMO/Public/Director/LWDirectorSubsystem.h >/dev/null

echo "Validation MVP: PASS"
