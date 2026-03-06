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

```bash
export UE_ROOT=/opt/UnrealEngine-5.3
bash Scripts/validate_mvp.sh
bash Scripts/build_and_run.sh --target editor
```

Windows:

```powershell
$env:UE_ROOT="C:\UnrealEngine-5.3"
pwsh Scripts/build_and_run.ps1 -Target editor
```
