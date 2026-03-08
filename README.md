# LivingWorldMMO

LivingWorldMMO is an Unreal Engine 5 TPS/MMO MVP focused on a server-driven living world simulation.

## Overview

- Server-side Director orchestrates economy/conflict world events
- Agent systems use LOD-aware AI updates
- World state persists snapshots and event journal data
- ReplicationGraph optimizes network relevancy at scale
- Offline deterministic bridge (ELI/MLE) supports content simulation pipelines

## Repository Structure

- `Source/LivingWorldMMO/` — UE5 C++ module and runtime subsystems
- `Config/` — engine/game defaults and gameplay tags
- `Data/` — world/myth state JSONs and journals
- `Scripts/` — build/run helpers, validation, ELI/MLE bridge
- `Docs/` — architecture and integration documentation

## Build and Run

### Linux

```bash
export UE_ROOT=/opt/UnrealEngine-5.3
bash Scripts/validate_mvp.sh
bash Scripts/build_and_run.sh --target editor
```

### Windows (PowerShell)

```powershell
$env:UE_ROOT = "C:\UnrealEngine-5.3"
pwsh Scripts/build_and_run.ps1 -Target editor
```

## Minimal Usage Examples

### Run repository diagnostics

```bash
bash Scripts/ci/validate_repo.sh
```

### Run offline deterministic director check

```bash
python3 Scripts/eli_bridge/mle_living_world.py
```
