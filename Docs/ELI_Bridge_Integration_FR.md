# ELI Bridge — Intégration initiale (MVP)

Ce document adapte la base `ELI.PY` fournie vers une version propre et maintenable pour ce repo UE5.

## Fichier ajouté

- `Scripts/eli_bridge/eli.py`

## Objectif de cette base

- Avoir un noyau **factuel, lisible, efficace** avant d'ajouter les prochains blocs.
- Éviter les défauts du snippet initial (doublons de fonctions, recursion bug sur `safe_int`, répétitions de `save_world_state`, etc.).
- Garder un pont simple avec UE via fichiers JSON (`event_in.json` / `event_out.json`).

## Chemins de travail

Par défaut, les fichiers persistent dans `Saved/EliBridge/` du repo.

Tu peux surcharger avec :

```bash
export ELI_BASE=/chemin/perso
```

## Exécution

```bash
python3 Scripts/eli_bridge/eli.py
```

## Ce qui est déjà pris en charge

- JSON robuste (load/save)
- état monde (`world_state.json`) avec réparation
- relations (`relationships.json`) avec réparation
- threads (`threads.json`) avec réparation
- conversion tags immédiats/différés en tags Unreal-friendly
- helpers de clé PNJ stable `Name|id`
- traitement minimal `event_in.json` -> `event_out.json`

## Prochaine étape

Quand tu m'envoies le prochain bloc, je l'intègre dans cette base (sans casser l'existant), avec tests et évolution incrémentale.


## Ajouts générateurs + PNJ persistants

La base intègre maintenant :
- banques de génération (noms, quêtes, rôles/traits/émotions PNJ),
- anti-répétition (`pick_unique_recent`, `make_name_unique`),
- base PNJ persistante (`npcs_db.json`) avec modèle psycho/valeurs/stratégies,
- mémoires sociales par joueur (`npc_add_memory`) et mise à jour réputation/rumeur via événements.

Le bridge `process_event_in()` prend en charge :
- MAJ `world_state` (event + economy + rumeurs),
- MAJ ciblée d'un PNJ (`target_npc_id`) si présent (opinions + mémoire).


## Ajouts Scene Banks (ELI Omni ready)

Ajouts intégrés dans `eli.py` :
- banques de scène (`SCENE_EVENT_TYPES`, `SCENE_LOCATIONS`, `SCENE_OBJECTS_BY_THEME`),
- météo cohérente par thème (`WEATHER_BY_THEME`, `_theme_bucket`, `pick_weather_for_theme`),
- normalisation de scène (`normalize_scene_output`) avec tags immédiats/différés et clés PNJ stables,
- helpers de threads global (`pick_or_create_thread`) et quêtes dérivées mémoire (`memory_driven_quests`).

Ces briques sont posées pour recevoir les prochains blocs (génération de scènes complètes, export étendu, etc.) sans réécriture structurelle.


## Ajouts Unreal Scene Format + Event Pipeline

Intégration supplémentaire :
- `build_unreal_scene_payload(...)` pour produire un payload UE5 prêt (spawns/triggers/choices + thread metadata).
- `action_next_scene()` pour générer `next_scene.json`, `next_scene.txt` et `scene_unreal.json`.
- pipeline événement (`compute_event_response`, `build_event_context`, `write_event_outputs`, `action_react_event_auto`) avec:
  - normalisation de cibles,
  - indices PNJ non-spoiler,
  - tags immédiats/retardés,
  - updates monde/relations.

Les fonctions ont été ajoutées en mode défensif (safe defaults, no-crash sur JSON incomplet) pour rester compatibles avec les prochains blocs.


## Ajouts Persistent NPC Actions (menus 13-17)

La couche ELI inclut désormais:
- génération batch PNJ persistants,
- simulation autonome hors-écran (événements SYSTEM + alliances),
- visualisation opinion/souvenirs PNJ par joueur,
- génération de quête sociale basée mémoire+rumeurs,
- menu CLI complet (1..17) avec mode bridge non-interactif (`ELI_BRIDGE=1`).
