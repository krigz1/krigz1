<<<<<<< HEAD
# LivingWorldMMO

Unreal Engine 5 experimental living-world simulation.

## Features

- Director AI controlling world events
- NPC memory system
- Spawn budget and anti-chaos controls
- ReplicationGraph optimized networking
- Offline deterministic simulation bridge (ELI)

## Project Structure

Source/LivingWorldMMO/      -> Unreal Engine C++ code  
Scripts/                    -> Python + build scripts  
Data/                       -> JSON world state and mythological data  
Docs/                       -> design and architecture documentation  

## Quick Start

Linux:
=======
# LivingWorldMMO MVP

Unreal Engine 5 MVP d'un monde vivant (TPS/MMO) avec Director serveur, LOD IA multi-résolution,
persistance Snapshot+Journal et ReplicationGraph.

## Quickstart Linux
Unreal Engine 5 MVP d'un monde vivant (TPS/MMO) avec Director serveur, LOD IA multi-résolution, persistance Snapshot+Journal et ReplicationGraph.

## Quickstart Linux
>>>>>>> origin/main

```bash
export UE_ROOT=/opt/UnrealEngine-5.3
bash Scripts/validate_mvp.sh
bash Scripts/build_and_run.sh --target editor
<<<<<<< HEAD
```

Windows:

```powershell
$env:UE_ROOT="C:\UnrealEngine-5.3"
pwsh Scripts/build_and_run.ps1 -Target editor
=======
Quickstart Windows (PowerShell 7)
$env:UE_ROOT = 'C:\UnrealEngine-5.3'
bash Scripts/validate_mvp.sh
pwsh ./Scripts/build_and_run.ps1 -Target editor
Validation
bash Scripts/validate_mvp.sh
Build targets

editor

game

server

ELI Bridge (Python)
python3 Scripts/eli_bridge/eli.py

Doc: Docs/ELI_Bridge_Integration_FR.md.

Living World + MLE (offline)

Le pipeline déterministe offline est fourni dans Scripts/eli_bridge/mle_living_world.py et s'appuie sur les données JSON sous Data/LivingMytho/ et Data/LivingWorld/ (schéma versionné + journaux append-only).

python3 Scripts/eli_bridge/mle_living_world.py

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

## Living World + MLE (offline)

Le pipeline déterministe offline est fourni dans `Scripts/eli_bridge/mle_living_world.py` et s'appuie sur les données JSON sous `Data/LivingMytho/` et `Data/LivingWorld/` (schéma versionné + journaux append-only).

```bash
python3 Scripts/eli_bridge/mle_living_world.py
```
>>>>>>> origin/main
```
