# Living World MMO TPS - MVP (UE5) 

## 1) Portée MVP jouable
- Boucle TPS: déplacement, tir, ennemis hostiles (Bandits), PNJ neutres (Marchands), faune (Wildlife).
- 1 ville (`City_Hub`) + 1 biome (`Valley_Wilds`) dans une map World Partition.
- 3 types d'agents: `Merchant`, `Bandit`, `Wildlife`.
- 2 événements dynamiques: `BanditRaid`, `PriceUpdate`.
- Persistance minimale: snapshot des agents + journal d'événements (`SaveGame`).

## 2) Actions UE5 (clic par clic)
1. Ouvrir `LivingWorldMMO.uproject` dans UE5.3+.
2. Vérifier plugins actifs: GameplayAbilities, GameplayTags, ReplicationGraph, MassEntity.
3. Créer dossier contenu:
   - `/Game/LivingWorld/Maps`
   - `/Game/LivingWorld/Blueprints/Agents`
   - `/Game/LivingWorld/Data`
4. Créer map `MVP_LivingValley` (Open World template), activer World Partition.
5. Placer 1 zone urbaine (meshes city kit) et 1 zone forêt/plaine (biome).
6. Créer Blueprint `BP_AgentBase` dérivé de `ALWAgentCharacter`.
7. Dupliquer:
   - `BP_MerchantAgent`: AgentBrain.ArchetypeId=`Merchant_T1`, Faction=`MerchantGuild`.
   - `BP_BanditAgent`: AgentBrain.ArchetypeId=`Bandit_T1`, Faction=`Bandits`.
   - `BP_WildlifeAgent`: AgentBrain.ArchetypeId=`Wildlife_Deer`, Faction=`Wildlife`.
8. Créer `BP_LWGameMode` dérivé de `ALWGameMode`:
   - MerchantClass = `BP_MerchantAgent`
   - BanditClass = `BP_BanditAgent`
   - WildlifeClass = `BP_WildlifeAgent`
   - SpawnPerType = 8
9. Dans `World Settings` de `MVP_LivingValley`, définir GameMode Override = `BP_LWGameMode`.
10. Créer DataTable `DT_LWGameplayTags` (row struct `GameplayTagTableRow`) avec tags du fichier config.
11. Play-In-Editor en mode Dedicated Server + 1 client.
12. Vérifier sortie logs:
    - Pulse économie toutes 5s.
    - Raid bandit toutes 15s.

## 3) Pipeline serveur (tick intelligent)
- **ULWAgentSubsystem**: rebalance LOD toutes 0.5s via distance joueur.
- **ULWAgentBrainComponent**: tick event-driven par intervalle selon LOD:
  - Micro: 100 ms
  - Meso: 500 ms
  - Macro: 2 s
- **ULWDirectorSubsystem**:
  - Pass économie: 5 s
  - Pass conflits: 15 s
  - Pass anti-entropie: à chaque tick (clamp/stabilité).
- **ULWWorldStateSubsystem**:
  - upsert états agents
  - snapshots SaveGame
  - journal événements.

## 4) Exemples concrets
- **Raid bandit**: Director émet `Event.Conflict.BanditRaid` (sévérité 0.8) proche porte sud.
- **Migration créature**: Wildlife passe de Macro->Meso->Micro à l'approche joueur; état continu conservé.
- **Marchand ajustant prix**: Director émet `Event.Economy.PriceUpdate` avec `FoodPriceDelta`.

## 5) Script de validation
Exécuter:
```bash
bash Scripts/validate_mvp.sh
```
Le script vérifie structure, configs, classes critiques et tags.

## 6) Extension MMO scalable (phase 2)
- Déporter simulation macro vers workers dédiés (process séparé par région logique).
- Partitionner shard en régions de simulation; bus d'événements append-only (Kafka/NATS/Redis Streams).
- Snapshot incrémental + event sourcing compacté.
- Cognition streaming:
  - Charger seulement graphes sociaux/rumeurs pertinents pour régions actives.
- Compression d'état:
  - Delta state par agent (position quantifiée, besoins sur 8 bits, tags en bitset).
- Déterminisme partiel:
  - RNG seedée par `(ShardId, RegionId, FrameWindow)`.
- Anti-entropie Director:
  - contrôleurs PID sur inflation, violence, migration, densité spawn.


## 7) Build + run automatisé
Exécuter:
```bash
export UE_ROOT=/opt/UnrealEngine-5.3
bash Scripts/build_and_run.sh --target editor
```
Variantes:
- `--target game` : lance en mode jeu.
- `--target server --run-args "-nosteam"` : lance serveur dédié.
- `--config Shipping` : compile en Shipping.
