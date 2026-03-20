# LivingWorldMMO

LivingWorldMMO is an Unreal Engine 5 TPS/MMO MVP focused on proving a small-scale living world loop in runtime.

## Overview

- Server-side Director orchestrates a limited set of economy, conflict, and wildlife events.
- Agent systems use LOD-aware AI updates for a 20-50 agent proof scenario.
- World state persists snapshots and event journal data across restart.
- ReplicationGraph optimizes network relevancy for the small playable test zone.
- Offline deterministic bridge (ELI/MLE) remains optional and is not required for the runtime proof.

## WorldProof_SmallScale

Current milestone: prove that one small playable zone can visibly react to:
- `Event.Economy.PriceUpdate`
- `Event.Conflict.BanditRaid`
- `Event.Wildlife.Disturbance`
- lightweight social events raised by nearby agents

Expected proof loop:
1. Launch the validation map.
2. Observe 20-50 spawned agents across merchants, bandits, and wildlife.
3. Watch the Director trigger periodic world events.
4. Verify visible reactions, readable logs, and snapshot persistence.

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

## Manual Runtime Check

1. Open `MVP_LivingValley`.
2. Run as dedicated server + one client.
3. Confirm overlay shows agent count, recent event count, director status, and persistence status.
4. Confirm logs show `LW.Agent`, `LW.Director`, `LW.EventBus`, and `LW.Persistence` style messages.
5. Restart and confirm previously saved state reloads.

## Out of Scope for This Milestone

- distributed MMO architecture
- region workers / Kafka / NATS
- large-scale population simulation
- complex narrative generation as a runtime dependency
