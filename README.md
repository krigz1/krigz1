# LivingWorldMMO MVP

Unreal Engine 5 MVP d'un monde vivant (TPS/MMO) avec Director serveur, LOD IA multi-résolution, persistance Snapshot+Journal et ReplicationGraph.

## Quickstart Linux

```bash
export UE_ROOT=/opt/UnrealEngine-5.3
bash Scripts/validate_mvp.sh
bash Scripts/build_and_run.sh --target editor
```

## Quickstart Windows (PowerShell 7)

```powershell
$env:UE_ROOT = 'C:\UnrealEngine-5.3'
bash Scripts/validate_mvp.sh
pwsh ./Scripts/build_and_run.ps1 -Target editor
```

## Validation

```bash
bash Scripts/validate_mvp.sh
```

## Build targets

- `editor`
- `game`
- `server`


## ELI Bridge (Python)

```bash
python3 Scripts/eli_bridge/eli.py
```

Doc: `Docs/ELI_Bridge_Integration_FR.md`.
