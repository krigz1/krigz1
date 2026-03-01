#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  "LivingWorldMMO.uproject"
  "Source/LivingWorldMMO/Public/Agents/LWAgentBrainComponent.h"
  "Source/LivingWorldMMO/Private/Director/LWDirectorSubsystem.cpp"
  "Source/LivingWorldMMO/Private/Net/LWReplicationGraph.cpp"
  "Config/DefaultEngine.ini"
  "Config/Tags/GameplayTags.ini"
  "Docs/MVP_Implementation_Guide_FR.md"
)

for f in "${required_files[@]}"; do
  [[ -f "$f" ]] || { echo "MISSING: $f"; exit 1; }
  echo "OK: $f"
done

rg -n "Event\.Conflict\.BanditRaid" Config/Tags/GameplayTags.ini >/dev/null
rg -n "ReplicationGraphClassName" Config/DefaultEngine.ini >/dev/null
rg -n "RunEconomyPass" Source/LivingWorldMMO/Private/Director/LWDirectorSubsystem.cpp >/dev/null

echo "Validation MVP: PASS"
