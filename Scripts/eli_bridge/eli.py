#!/usr/bin/env python3
"""
ELI bridge core adapted for LivingWorldMMO.
- Robust JSON persistence
- Stable NPC keys (Name|id)
- World / relationships / threads state
- Generators bank + persistent NPC social model
- Unreal bridge IO files
"""

from __future__ import annotations

import json
import os
import random
import re
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

Path("logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler(
            "logs/eli_errors.log",
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("eli_bridge")


# =========================
# Core helpers
# =========================

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def clamp(n: int | float, low: int | float, high: int | float):
    return max(low, min(high, n))


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def slug_tag(value: str) -> str:
    out = re.sub(r"[^a-z0-9_]+", "_", (value or "").strip().lower(), flags=re.IGNORECASE)
    out = re.sub(r"_+", "_", out).strip("_")
    return out or "other"


def pick(seq, default=None):
    seq = list(seq or [])
    return random.choice(seq) if seq else default


def make_id(prefix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = "".join(random.choice("abcdef0123456789") for _ in range(4))
    return f"{prefix}_{stamp}_{rand}"


def load_json_file(path: Path, default_factory, repair_fn=None):
    try:
        if not path.exists():
            return default_factory()
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else default_factory()
        if repair_fn:
            data = repair_fn(data)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"JSON corrompu {path}: {e}")
        return default_factory()
    except OSError as e:
        logger.error(f"Erreur lecture {path}: {e}")
        return default_factory()


def save_json_file(path: Path, data: Any) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Échec écriture {path}: {e}")
        return False


# =========================
# Paths
# =========================

def resolve_base_path() -> Path:
    env = os.environ.get("ELI_BASE", "").strip()
    if env:
        p = Path(env)
        if p.exists():
            return p

    return Path(__file__).resolve().parents[2] / "Saved" / "EliBridge"


@dataclass(frozen=True)
class EliPaths:
    base: Path

    @property
    def content(self) -> Path:
        return self.base / "game_content"

    @property
    def log_file(self) -> Path:
        return self.base / "eli.log"

    @property
    def world_state(self) -> Path:
        return self.base / "world_state.json"

    @property
    def relationships(self) -> Path:
        return self.base / "relationships.json"

    @property
    def threads(self) -> Path:
        return self.content / "threads.json"

    @property
    def npc_db(self) -> Path:
        return self.content / "npcs_db.json"

    @property
    def event_in_json(self) -> Path:
        return self.content / "event_in.json"

    @property
    def event_out_json(self) -> Path:
        return self.content / "event_out.json"

    @property
    def quests_file(self) -> Path:
        return self.content / "quests.txt"

    @property
    def pnj_file(self) -> Path:
        return self.content / "pnj.txt"

    @property
    def dungeon_file(self) -> Path:
        return self.content / "dungeon.txt"

    @property
    def dialogue_file(self) -> Path:
        return self.content / "dialogues.txt"

    @property
    def items_file(self) -> Path:
        return self.content / "items.txt"

    @property
    def animals_file(self) -> Path:
        return self.content / "animals.txt"

    @property
    def animals_json_file(self) -> Path:
        return self.content / "animals.json"

    @property
    def next_scene_json(self) -> Path:
        return self.content / "next_scene.json"

    @property
    def next_scene_txt(self) -> Path:
        return self.content / "next_scene.txt"

    @property
    def universe_file(self) -> Path:
        return self.base / "universe.json"

    @property
    def rules_file(self) -> Path:
        return self.base / "rules.txt"

    @property
    def export_json_file(self) -> Path:
        return self.content / "export.json"


def ensure_folders(paths: EliPaths) -> None:
    paths.base.mkdir(parents=True, exist_ok=True)
    paths.content.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except Exception:
        return ""


def write_text(path: Path, text: str) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True
    except OSError as e:
        logger.error(f"write_text failed {path}: {e}")
        return False


def pick_many(seq, k):
    seq = list(seq or [])
    k = safe_int(k, 0)
    if not seq or k <= 0:
        return []
    if k >= len(seq):
        random.shuffle(seq)
        return seq
    return random.sample(seq, k)


# =========================
# TAGS
# =========================
CONSEQ_TAGS = {
    "réputation locale +": "rep_up",
    "réputation locale -": "rep_down",
    "un combat démarre": "combat_start",
    "un accès se débloque": "unlock_access",
    "un pnj devient méfiant": "npc_suspicious",
    "tu obtiens un indice utile": "get_clue",
    "tu perds du temps": "lose_time",
    "une faction te remarque": "faction_notice",
    "un prix augmente": "price_up",
    "un prix baisse": "price_down",
}

DELAY_TAGS = {
    "un pnj reviendra demander une faveur": "npc_favor_later",
    "une faction prépare une vengeance": "faction_revenge",
    "une rumeur sur toi se répand": "rumor_spreads",
    "une zone devient plus dangereuse": "zone_more_danger",
    "une zone devient plus sûre": "zone_safer",
    "un pnj te trahira peut-être": "npc_may_betray",
    "un pnj te protégera plus tard": "npc_may_protect",
}


def to_tags(immediate_list: List[str] | None, delayed_list: List[str] | None) -> Tuple[List[str], List[str]]:
    immediate, delayed = [], []
    for item in immediate_list or []:
        key = str(item).strip().lower()
        immediate.append(CONSEQ_TAGS.get(key, f"unknown__{slug_tag(key)}"))
    for item in delayed_list or []:
        key = str(item).strip().lower()
        delayed.append(DELAY_TAGS.get(key, f"unknown__{slug_tag(key)}"))
    return immediate, delayed


# =========================
# BANKS (generators)
# =========================
_NAME_A = ["Al", "Bel", "Cor", "Dar", "El", "Fen", "Gra", "Hel", "Ira", "Jen", "Ka", "Lor", "Mir", "Nor", "Or", "Sel", "Tor", "Val", "Zan"]
_NAME_B = ["a", "e", "i", "o", "u", "ae", "ia", "eo"]
_NAME_C = ["n", "r", "s", "th", "k", "m", "l", "v", "d", "g"]
_NAME_D = ["en", "is", "or", "a", "iel", "on", "ia", "eth", "ar", "yn"]

QUEST_PROBLEMS = [
    "un enfant a disparu", "un marchand s’est fait voler", "une bête rôde près des habitations",
    "un pont est devenu dangereux", "une personne importante a été menacée", "des réserves disparaissent",
    "un groupe rackette les voyageurs", "un ancien autel attire des choses bizarres",
]
QUEST_OBJECTIVES = [
    "enquêter et trouver la vérité", "retrouver la personne et la ramener",
    "escorter quelqu’un en sécurité", "récupérer un objet volé",
    "protéger une zone pendant un temps", "négocier une paix fragile",
    "infiltrer sans se faire voir", "apporter une preuve (lettre, sceau, relique)",
]
QUEST_COMPLICATIONS = [
    "mais le client ment sur un détail", "mais une faction s’en mêle",
    "mais tu dois choisir entre deux choses", "mais le temps est limité",
    "mais la récompense a un prix", "mais l’objectif change en cours de route",
]

PNJ_ROLES = ["marchand", "garde", "chasseur", "forgeron", "herboriste", "chef de clan", "messager", "prêtre", "exploratrice", "aubergiste"]
PNJ_TRAITS = [
    "gentil mais méfiant", "froid mais juste", "calme mais dangereux", "rancunier mais loyal",
    "doux mais manipulateur", "impulsif mais honnête", "orgueilleux mais protecteur", "fatigué mais courageux",
]
PNJ_EMOTIONS = ["joie", "tristesse", "colère", "peur", "doute", "fierté", "culpabilité", "curiosité", "espoir"]

DUNGEON_TYPES = ["catacombes", "mine abandonnée", "ruines anciennes", "fortin oublié", "temple enterré", "grotte humide"]
DUNGEON_TWISTS = [
    "un PNJ t’a envoyé ici pour te tester",
    "la récompense est piégée",
    "un ennemi parle et négocie",
    "tu dois choisir qui sauver",
    "le boss fuit si tu le bats trop vite",
]
DIALOGUE_SITUATIONS = [
    "a peur d’une attaque",
    "cache un secret",
    "cherche de l’aide",
    "veut te manipuler",
    "hésite à te faire confiance",
    "a besoin d’un service",
]
ITEM_BASE = ["Épée", "Dague", "Arc", "Bâton", "Casque", "Armure", "Bottes", "Anneau", "Amulette", "Gants"]
ITEM_MATERIAL = ["fer", "acier", "os", "bois noir", "argent", "cuivre", "obsidienne", "cristal", "cuir renforcé"]
ITEM_EFFECTS = ["+5% vitesse", "+8% dégâts", "+10% critique", "+12% défense", "+5% vol de vie", "+15% endurance", "+10% précision"]
RARITIES = ["Commun", "Inhabituel", "Rare", "Épique"]

SCENE_EVENT_TYPES = [
    "demande_aide", "rumeur", "conflit", "embuscade", "trahison", "danger_naturel", "animal", "mystere", "indice",
    "arrestation", "marche", "ceremonie", "penurie", "accident",
]
SCENE_LOCATIONS = [
    "clairiere", "pont", "ruines", "campement", "route_boueuse", "cabane", "entree_grotte", "bord_riviere",
    "falaise", "ancien_autel", "marche", "taverne", "tour_garde", "atelier", "place_centrale",
]
SCENE_OBJECTS_BY_THEME = {
    "medieval_fantasy": ["torche", "corde", "carte_froissee", "sceau_brise", "lettre_cachee", "cle_rouillee", "amulette_marquee", "bandage", "fleche_cassee", "potion_faible", "journal_trempe", "trace_sang", "contrat", "badge_garde"],
    "desert_ancien": ["gourde_entamee", "voile_poussiereux", "boussole_cassee", "carte_desert", "morceau_stele_gravee", "sable_noir", "amulette_solaire", "sceau_argile", "lampe_huile", "fragment_os_ancien"],
    "city": ["cle_cellule", "badge_patrouille", "contrat_plie", "bourse_trouee", "avis_recherche", "sceau_officiel", "registre", "plan_quartier", "bouteille_cassee", "capuche_trempee"],
    "anomaly": ["fragment_metal_inconnu", "lueur_neon_faible", "glyphes_technomagiques", "dalle_vibrante", "orbe_donnees_illisible", "porte_scellee_etrange"],
}
CHOICE_VERBS = ["aider", "refuser", "negocier", "menacer", "mentir", "espionner", "attaquer", "fuir", "proteger", "enqueter", "payer", "suivre", "denoncer", "cacher", "recuperer", "calmer"]
CONSEQUENCES_IMMEDIATE = ["reputation_locale_plus", "reputation_locale_moins", "combat_start", "unlock_access", "npc_suspicious", "get_clue", "lose_time", "faction_notice", "price_up", "price_down"]
CONSEQUENCES_DELAYED = ["npc_favor_later", "faction_revenge", "rumor_spreads", "zone_more_danger", "zone_safer", "npc_may_betray", "npc_may_protect"]

WEATHER_BY_THEME = {
    "desert_ancien": ["clair", "clair", "clair", "brouillard", "tempete"],
    "foret_futuriste": ["clair", "pluie", "pluie", "brouillard"],
    "medieval_fantasy": ["clair", "pluie", "brouillard", "tempete"],
    "city": ["clair", "pluie", "brouillard"],
    "anomaly": ["clair", "brouillard", "tempete"],
}

_RECENT = {
    "names": [],
    "quest_problems": [],
    "quest_objectives": [],
    "quest_complications": [],
}


def make_name() -> str:
    return pick(_NAME_A, "Al") + pick(_NAME_B, "a") + pick(_NAME_C, "n") + pick(_NAME_D, "en")


def _recent_push(key: str, value: str, cap: int = 25):
    if not value:
        return
    lst = _RECENT.setdefault(key, [])
    lst.append(value)
    if len(lst) > cap:
        del lst[0:len(lst) - cap]


def pick_unique_recent(seq, recent_key: str, avoid_last: int = 10, default=None):
    seq = list(seq or [])
    if not seq:
        return default
    recent = _RECENT.get(recent_key, [])[-max(0, int(avoid_last)):]
    candidates = [x for x in seq if x not in recent]
    choice = random.choice(candidates) if candidates else random.choice(seq)
    _recent_push(recent_key, choice)
    return choice


def make_name_unique(max_tries: int = 8):
    for _ in range(max_tries):
        name = make_name()
        if name not in _RECENT.get("names", [])[-20:]:
            _recent_push("names", name, cap=50)
            return name
    name = make_name()
    _recent_push("names", name, cap=50)
    return name


# =========================
# NPC helpers + model
# =========================
GOALS = ["protéger territoire", "gagner richesse", "servir faction", "rechercher artefact", "aider autres", "devenir puissant"]


def npc_key_from(npc_id: str, npc: dict) -> str:
    nid = (npc_id or npc.get("id") or npc.get("_id") or "").strip()
    name = (npc.get("name") or "").strip()
    if not nid and not name:
        return ""
    if not nid:
        nid = "unknown"
    if not name:
        name = "Unknown"
    return f"{name}|{nid}"


def _default_psyche() -> dict:
    return {"stress": random.randint(0, 35), "paranoia": random.randint(0, 35), "greed": random.randint(0, 100), "honor": random.randint(0, 100), "attachment": random.randint(0, 100)}


def _default_values() -> dict:
    return {"violence_tolerance": random.randint(0, 100), "lawfulness": random.randint(0, 100), "loyalty": random.randint(0, 100), "empathy_bias": random.randint(0, 100)}


def _default_social_strategies() -> dict:
    return {"manipulate": random.randint(0, 100), "avoid_conflict": random.randint(0, 100), "dominate": random.randint(0, 100), "bargain": random.randint(0, 100), "deceive": random.randint(0, 100)}


def repair_npc_psycho(npc: dict) -> dict:
    defaults = {
        "psyche": {"stress": 0, "paranoia": 0, "greed": 50, "honor": 50, "attachment": 50},
        "values": {"violence_tolerance": 50, "lawfulness": 50, "loyalty": 50, "empathy_bias": 50},
        "social_strategies": {"manipulate": 20, "avoid_conflict": 50, "dominate": 20, "bargain": 50, "deceive": 20},
    }
    out = dict(npc or {})
    for section, values in defaults.items():
        src = out.get(section, {}) if isinstance(out.get(section), dict) else {}
        for key, dval in values.items():
            src[key] = clamp(safe_int(src.get(key, dval), dval), 0, 100)
        out[section] = src
    return out


def generate_personality() -> dict:
    return {
        "courage": random.randint(0, 100),
        "agressivite": random.randint(0, 100),
        "empathie": random.randint(0, 100),
        "loyaute": random.randint(0, 100),
        "curiosite": random.randint(0, 100),
        "discipline": random.randint(0, 100),
    }


def generate_affinities() -> dict:
    zones = ["forêt", "ville", "montagne", "désert", "plaine"]
    objects = ["relique ancienne", "arme familiale", "outil sacré", "artefact trouvé", "bijou précieux"]
    factions = ["habitants", "gardes", "chasseurs", "bandits"]
    return {
        "zones": random.sample(zones, k=min(2, len(zones))),
        "objects": random.sample(objects, k=min(1, len(objects))),
        "factions": random.sample(factions, k=min(1, len(factions))),
    }


def generate_goals() -> list:
    if not GOALS:
        return []
    return random.sample(GOALS, k=2 if len(GOALS) >= 2 else 1)


def ensure_player_opinion(npc: dict, player_id: str):
    npc.setdefault("opinions", {})
    pid = (player_id or "p1").strip() or "p1"
    op = npc["opinions"].setdefault(pid, {"trust": 50, "fear": 0, "respect": 50, "last_seen": ""})
    op.setdefault("trust", 50)
    op.setdefault("fear", 0)
    op.setdefault("respect", 50)
    op.setdefault("last_seen", "")
    return op


def create_persistent_npc(default_location=None):
    npc = {
        "id": make_id("npc"),
        "name": make_name_unique(),
        "role": pick(PNJ_ROLES),
        "trait": pick(PNJ_TRAITS),
        "emotion": pick(PNJ_EMOTIONS),
        "personality": generate_personality(),
        "affinities": generate_affinities(),
        "goals": generate_goals(),
        "memory": [],
        "opinions": {},
        "relations": {},
        "location": default_location if default_location else pick(["forêt", "ville", "plaine"]),
        "state": "idle",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "rumor_knowledge": {},
        "psyche": _default_psyche(),
        "values": _default_values(),
        "social_strategies": _default_social_strategies(),
    }
    return repair_npc_psycho(npc)


def score_opinion_from_event(etype: str, severity: int, witnesses: int):
    etype = (etype or "").strip()
    s = clamp(safe_int(severity, 5), 1, 10)
    w = max(0, safe_int(witnesses, 0))
    dt = df = dr = 0
    if etype == "help":
        dt += 6 if s < 8 else 10
        dr += 4
    elif etype == "trade":
        dt += 2
        dr += 1
    elif etype == "quest_success":
        dt += 5
        dr += 6
    elif etype == "quest_fail":
        dt -= 2
        dr -= 2
    elif etype == "insult":
        dt -= 8
        df += 3
        dr -= 4
    elif etype == "trespass":
        dt -= 5
        df += 2
        dr -= 3
    elif etype == "crime":
        dt -= 12
        df += 8 if s >= 8 else 5
        dr -= 8
    elif etype == "kill":
        dt -= 18
        df += 15 if s >= 8 else 10
        dr -= 12
    if w >= 3:
        dt, df, dr = int(dt * 1.2), int(df * 1.2), int(dr * 1.2)
    return dt, df, dr


def npc_add_memory(npc: dict, player_id: str, etype: str, zone: str, severity: int, delta_trust=0, delta_fear=0, delta_respect=0, note=""):
    npc.setdefault("memory", [])
    op = ensure_player_opinion(npc, player_id)
    dt, df, dr = safe_int(delta_trust), safe_int(delta_fear), safe_int(delta_respect)
    sev = clamp(safe_int(severity, 5), 1, 10)
    op["trust"] = clamp(safe_int(op.get("trust", 50), 50) + dt, 0, 100)
    op["fear"] = clamp(safe_int(op.get("fear", 0), 0) + df, 0, 100)
    op["respect"] = clamp(safe_int(op.get("respect", 50), 50) + dr, 0, 100)
    op["last_seen"] = now_iso()
    npc["memory"].append({
        "time": now_iso(), "player_id": (player_id or "p1").strip() or "p1", "type": (etype or "event").strip(),
        "zone": (zone or "").strip(), "severity": sev, "effect": {"trust": dt, "fear": df, "respect": dr}, "note": (note or "")[:120],
    })
    if len(npc["memory"]) > 40:
        npc["memory"] = npc["memory"][-40:]
    npc["updated_at"] = now_iso()


# =========================
# World/relationships/threads
# =========================
def default_world_state() -> Dict[str, Any]:
    return {
        "meta": {"created_at": now_iso(), "updated_at": now_iso()},
        "scene": {"zone": "forêt", "zone_theme": "medieval_fantasy", "time": "jour", "weather": "clair", "danger": 4},
        "player_meta": {"global_reputation": 0, "flags": []},
        "world_flags": {"last_event": "", "factions": ["habitants", "gardes", "chasseurs", "bandits"], "economy_heat": 3, "rumors": {}},
    }


def repair_world_state(data: Dict[str, Any]) -> Dict[str, Any]:
    base = default_world_state()
    out = dict(data or {})
    out.setdefault("meta", base["meta"])
    out.setdefault("scene", base["scene"])
    out.setdefault("player_meta", base["player_meta"])
    out.setdefault("world_flags", base["world_flags"])
    out["scene"]["danger"] = clamp(safe_int(out["scene"].get("danger", 4), 4), 0, 10)
    out["world_flags"]["economy_heat"] = clamp(safe_int(out["world_flags"].get("economy_heat", 3), 3), 0, 10)
    out["meta"]["updated_at"] = now_iso()
    return out


def ensure_rumor_state(state: dict, player_id: str):
    state.setdefault("world_flags", {})
    state["world_flags"].setdefault("rumors", {})
    rumors = state["world_flags"]["rumors"]
    pid = (player_id or "p1").strip() or "p1"
    if pid == "SYSTEM":
        return {"rep": 0, "heat": 0}
    rumors.setdefault(pid, {"rep": 0, "heat": 0})
    rumors[pid].setdefault("rep", 0)
    rumors[pid].setdefault("heat", 0)
    return rumors[pid]


def update_rumor_from_event(state: dict, event: dict):
    pid = (event.get("player_id") or "").strip()
    if not pid or pid == "SYSTEM":
        return
    etype = (event.get("type") or "").strip()
    sev = clamp(safe_int(event.get("severity", 5), 5), 1, 10)
    witnesses = max(0, safe_int(event.get("witnesses", 0), 0))
    r = ensure_rumor_state(state, pid)
    heat_gain = (1 if witnesses >= 1 else 0) + (1 if witnesses >= 3 else 0) + (1 if witnesses >= 6 else 0)
    rep_delta = {"help": 2 if sev >= 8 else 1, "quest_success": 2, "insult": -1, "trespass": -1, "crime": -2, "kill": -3}.get(etype, 0)
    r["rep"] = clamp(safe_int(r.get("rep", 0), 0) + rep_delta, -50, 50)
    r["heat"] = clamp(safe_int(r.get("heat", 0), 0) + heat_gain, 0, 100)


def default_relationships() -> Dict[str, Any]:
    return {
        "meta": {"created_at": now_iso(), "updated_at": now_iso()},
        "npcs": {},
        "factions": {
            "habitants": {"gardes": "allié", "chasseurs": "neutre", "bandits": "rival"},
            "gardes": {"habitants": "allié", "chasseurs": "neutre", "bandits": "rival"},
            "chasseurs": {"habitants": "neutre", "gardes": "neutre", "bandits": "méfiant"},
            "bandits": {"habitants": "rival", "gardes": "rival", "chasseurs": "méfiant"},
        },
    }


def repair_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    base = default_relationships()
    out = dict(data or {})
    out.setdefault("meta", base["meta"])
    out.setdefault("npcs", {})
    out.setdefault("factions", base["factions"])
    out["meta"]["updated_at"] = now_iso()
    return out


def default_threads() -> Dict[str, Any]:
    return {"meta": {"created_at": now_iso(), "updated_at": now_iso()}, "threads": []}


def repair_threads(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data or {})
    out.setdefault("meta", {"created_at": now_iso(), "updated_at": now_iso()})
    out.setdefault("threads", [])
    if not isinstance(out["threads"], list):
        out["threads"] = []
    out["meta"]["updated_at"] = now_iso()
    clean = []
    for t in out["threads"]:
        if not isinstance(t, dict):
            continue
        t.setdefault("id", make_id("th"))
        t.setdefault("theme", "rumeur")
        t.setdefault("zone", "unknown")
        t.setdefault("factions", [])
        t.setdefault("npcs_involved", [])
        t["heat"] = clamp(safe_int(t.get("heat", 10), 10), 0, 100)
        t.setdefault("stage", "setup")
        t["stakes"] = clamp(safe_int(t.get("stakes", 3), 3), 1, 10)
        t.setdefault("hooks", [])
        t.setdefault("last_update", now_iso())
        t["cooldown"] = max(0, safe_int(t.get("cooldown", 0), 0))
        clean.append(t)
    out["threads"] = clean
    return out


def _repair_npc_db(data: dict) -> dict:
    out = dict(data or {})
    out.setdefault("meta", {"created_at": now_iso(), "updated_at": now_iso()})
    out.setdefault("npcs", {})
    if not isinstance(out["npcs"], dict):
        out["npcs"] = {}
    out["meta"]["updated_at"] = now_iso()
    repaired = {}
    for npc_id, npc in out["npcs"].items():
        if not isinstance(npc, dict):
            continue
        npc.setdefault("id", str(npc_id))
        repaired[str(npc_id)] = repair_npc_psycho(npc)
    out["npcs"] = repaired
    return out


# =========================
# Main bridge object
# =========================
class EliBridge:
    def __init__(self, base_path: Path | None = None):
        self.paths = EliPaths(base=base_path or resolve_base_path())
        ensure_folders(self.paths)

    def load_world_state(self) -> Dict[str, Any]:
        return load_json_file(self.paths.world_state, default_world_state, repair_world_state)

    def save_world_state(self, state: Dict[str, Any]) -> bool:
        return save_json_file(self.paths.world_state, repair_world_state(state))

    def load_relationships(self) -> Dict[str, Any]:
        return load_json_file(self.paths.relationships, default_relationships, repair_relationships)

    def save_relationships(self, rel: Dict[str, Any]) -> bool:
        return save_json_file(self.paths.relationships, repair_relationships(rel))

    def load_threads(self) -> Dict[str, Any]:
        return load_json_file(self.paths.threads, default_threads, repair_threads)

    def save_threads(self, threads: Dict[str, Any]) -> bool:
        return save_json_file(self.paths.threads, repair_threads(threads))

    def load_npc_db(self) -> Dict[str, Any]:
        return load_json_file(self.paths.npc_db, lambda: _repair_npc_db({"meta": {"created_at": now_iso(), "updated_at": now_iso()}, "npcs": {}}), _repair_npc_db)

    def save_npc_db(self, db: Dict[str, Any]) -> bool:
        return save_json_file(self.paths.npc_db, _repair_npc_db(db))

    def generate_100_persistent_npcs(self) -> int:
        db = self.load_npc_db()
        for _ in range(100):
            npc = create_persistent_npc()
            db["npcs"][npc["id"]] = npc
        self.save_npc_db(db)
        return len(db["npcs"])

    def process_event_in(self) -> Dict[str, Any]:
        event = load_json_file(self.paths.event_in_json, lambda: {}, lambda x: x)
        world = self.load_world_state()

        if event:
            world.setdefault("world_flags", {})
            world["world_flags"]["last_event"] = str(event.get("type") or "")
            world["world_flags"]["economy_heat"] = clamp(
                safe_int(world["world_flags"].get("economy_heat", 3), 3) + safe_int(event.get("severity", 0), 0) // 3,
                0,
                10,
            )
            update_rumor_from_event(world, event)
            self.save_world_state(world)

            if event.get("player_id") and event.get("target_npc_id"):
                db = self.load_npc_db()
                npc = db.get("npcs", {}).get(str(event.get("target_npc_id")))
                if npc:
                    dt, df, dr = score_opinion_from_event(str(event.get("type") or ""), safe_int(event.get("severity", 5), 5), safe_int(event.get("witnesses", 0), 0))
                    npc_add_memory(npc, str(event.get("player_id")), str(event.get("type") or "event"), str(event.get("zone") or ""), safe_int(event.get("severity", 5), 5), dt, df, dr, str(event.get("note") or ""))
                    db["npcs"][str(npc.get("id"))] = npc
                    self.save_npc_db(db)

        out = {"handled_at": now_iso(), "received": event, "world_flags": world.get("world_flags", {})}
        save_json_file(self.paths.event_out_json, out)
        return out



# =========================
# SCENE HELPERS / OMNI
# =========================
def _theme_bucket(zone_theme: str) -> str:
    low = (zone_theme or "").strip().lower()
    if "anomal" in low:
        return "anomaly"
    if "desert" in low:
        return "desert_ancien"
    if "foret" in low or "forêt" in low:
        return "foret_futuriste"
    if "ville" in low or "city" in low:
        return "city"
    return "medieval_fantasy"


def pick_weather_for_theme(zone_theme: str):
    bucket = _theme_bucket(zone_theme)
    bank = WEATHER_BY_THEME.get(bucket) or WEATHER_BY_THEME["medieval_fantasy"]
    return pick_unique_recent(bank, "scene_weather", avoid_last=6, default="clair")


def pick_scene_object(zone_theme: str):
    objects = SCENE_OBJECTS_BY_THEME.get((zone_theme or "medieval_fantasy").strip())
    if not objects:
        objects = SCENE_OBJECTS_BY_THEME.get("medieval_fantasy", [])
    return pick_unique_recent(objects, "scene_objects", avoid_last=10)


def pick_scene_event_type(thread=None):
    if not thread:
        return pick_unique_recent(SCENE_EVENT_TYPES, "scene_events", 10)
    stage = thread.get("stage")
    if stage == "crisis":
        pool = ["conflit", "embuscade", "trahison", "arrestation"]
    elif stage == "climax":
        pool = ["conflit", "trahison", "embuscade"]
    elif stage == "fallout":
        pool = ["rumeur", "ceremonie", "marche"]
    else:
        pool = SCENE_EVENT_TYPES
    return pick_unique_recent(pool, "scene_events", 10)


def pick_scene_objects_for_theme(zone_theme: str, k_min: int = 2, k_max: int = 4):
    bucket = _theme_bucket(zone_theme)
    bank = SCENE_OBJECTS_BY_THEME.get(bucket) or SCENE_OBJECTS_BY_THEME.get("medieval_fantasy", [])
    k_min = clamp(safe_int(k_min, 2), 1, 10)
    k_max = clamp(safe_int(k_max, 4), k_min, 10)
    k = random.randint(k_min, k_max)
    out = [pick_unique_recent(bank, "scene_objects", avoid_last=10) for _ in range(k)]
    seen, uniq = set(), []
    for x in out:
        if x and x not in seen:
            uniq.append(x)
            seen.add(x)
    return uniq


def normalize_scene_output(scene: dict):
    scene = scene or {}
    if not scene.get("scene_id"):
        scene["scene_id"] = make_id("scene")

    zone_theme = scene.get("zone_theme") or "medieval_fantasy"
    scene["zone_theme"] = zone_theme
    if not scene.get("weather"):
        scene["weather"] = pick_weather_for_theme(zone_theme)

    if "thread" in scene and isinstance(scene.get("thread"), dict):
        t = scene["thread"]
        scene["thread_id"] = t.get("id") or scene.get("thread_id")
        scene["thread_stage"] = t.get("stage") or scene.get("thread_stage")
        scene["thread_heat"] = t.get("heat") if t.get("heat") is not None else scene.get("thread_heat")

    npcs = scene.get("npcs", {})
    if not isinstance(npcs, dict):
        npcs = {}
    for slot in ["npc1", "npc2"]:
        npc = npcs.get(slot)
        if not isinstance(npc, dict):
            continue
        name = (npc.get("name") or npc.get("npc_name") or "").strip()
        npc_id = (npc.get("npc_id") or npc.get("id") or "").strip() or "unknown"
        npc_key = (npc.get("npc_key") or "").strip() or f"{name or 'Unknown'}|{npc_id}"
        npc["name"] = name or "Unknown"
        npc["npc_id"] = npc_id
        npc["npc_key"] = npc_key
        npcs[slot] = npc
    scene["npcs"] = npcs

    objs = scene.get("scene_objects", [])
    if not isinstance(objs, list):
        objs = []
    if len(objs) < 2:
        objs = (objs or []) + pick_scene_objects_for_theme(zone_theme, k_min=2, k_max=4)
    seen, cleaned = set(), []
    for o in objs:
        s = str(o).strip()
        if s and s not in seen:
            cleaned.append(s)
            seen.add(s)
    scene["scene_objects"] = cleaned[:4]

    choices = scene.get("choices", [])
    if not isinstance(choices, list):
        choices = []
    for c in choices:
        if not isinstance(c, dict):
            continue
        if not c.get("choice_id"):
            c["choice_id"] = make_id("choice")
        imm = c.get("immediate", []) if isinstance(c.get("immediate", []), list) else []
        dly = c.get("delayed", []) if isinstance(c.get("delayed", []), list) else []
        imm_tags, dly_tags = c.get("immediate_tags"), c.get("delayed_tags")
        if not isinstance(imm_tags, list) or not isinstance(dly_tags, list) or (not imm_tags and imm) or (not dly_tags and dly):
            imm_tags, dly_tags = to_tags(imm, dly)
            c["immediate_tags"] = imm_tags
            c["delayed_tags"] = dly_tags
    scene["choices"] = choices
    return scene


def build_scene_payload(zone: str, zone_theme: str, thread=None):
    return {
        "zone": zone,
        "zone_theme": zone_theme,
        "location": pick_unique_recent(SCENE_LOCATIONS, "scene_locations", 10),
        "event_type": pick_scene_event_type(thread),
        "object_focus": pick_scene_object(zone_theme),
        "thread_id": thread.get("id") if thread else None,
        "thread_stage": thread.get("stage") if thread else None,
        "thread_heat": thread.get("heat") if thread else None,
    }

# =========================
# Universe + validation
# =========================
def default_universe():
    return {
        "core": {"setting": "medieval_fantasy", "magic_level": 5},
        "rules": {"always_forbidden": [], "allowed_if_zone_is_anomaly": []},
        "zones": {"examples": [{"theme": "medieval_fantasy", "anomaly": False}, {"theme": "foret_futuriste", "anomaly": True}, {"theme": "desert_ancien", "anomaly": True}]},
    }


def _repair_universe(data: dict) -> dict:
    base = default_universe()
    out = dict(data or {})
    out.setdefault("core", base["core"])
    out.setdefault("rules", base["rules"])
    out.setdefault("zones", base["zones"])
    out["rules"].setdefault("always_forbidden", [])
    out["rules"].setdefault("allowed_if_zone_is_anomaly", [])
    out["zones"].setdefault("examples", base["zones"]["examples"])
    return out


def load_universe(base_path: Path | None = None):
    bridge = EliBridge(base_path)
    return load_json_file(bridge.paths.universe_file, default_universe, _repair_universe)


def is_zone_anomaly(u: dict, zone_theme: str) -> bool:
    for z in (u.get("zones", {}) or {}).get("examples", []):
        if z.get("theme") == zone_theme:
            return bool(z.get("anomaly", False))
    return False


def validate_scene_against_universe(u: dict, proposal: dict):
    forbidden = set((u.get("rules", {}) or {}).get("always_forbidden", []) or [])
    anomaly_allowed = set((u.get("rules", {}) or {}).get("allowed_if_zone_is_anomaly", []) or [])
    zone_theme = proposal.get("zone_theme", "medieval_fantasy")
    tokens = set(proposal.get("universe_tokens", []) or [])
    if tokens & forbidden:
        return False, f"Contient un token interdit: {list(tokens & forbidden)[0]}"
    if not is_zone_anomaly(u, zone_theme):
        bad = [t for t in tokens if t in anomaly_allowed]
        if bad:
            return False, f"Token techno/mix '{bad[0]}' interdit hors anomalie"
    return True, "OK"


# =========================
# Thread engine helpers (global)
# =========================
def load_threads(base_path: Path | None = None):
    return EliBridge(base_path).load_threads()


def save_threads(data: dict, base_path: Path | None = None):
    EliBridge(base_path).save_threads(data)


def pick_or_create_thread(threads_data: dict, zone: str, factions: list, npc_keys: list, theme_hint: str = "rumeur"):
    threads_data = repair_threads(threads_data)
    zone = (zone or "").strip() or "zone"
    factions = factions if isinstance(factions, list) else []
    npc_keys = [x for x in (npc_keys or []) if isinstance(x, str) and x.strip()]
    threads = threads_data.get("threads", []) or []

    active = [t for t in threads if isinstance(t, dict) and t.get("stage") != "dormant"]
    same_zone = [t for t in active if (t.get("zone") or "").strip().lower() == zone.lower()]
    candidates = same_zone if same_zone else active
    if candidates:
        t = random.choice(candidates)
        t.setdefault("factions", [])
        t.setdefault("npcs_involved", [])
        for f in factions:
            if f not in t["factions"]:
                t["factions"].append(f)
        for nk in npc_keys:
            if nk not in t["npcs_involved"]:
                t["npcs_involved"].append(nk)
        return t

    t = {
        "id": make_id("thread"),
        "theme": theme_hint or "rumeur",
        "zone": zone,
        "factions": list(dict.fromkeys(factions))[:4],
        "npcs_involved": list(dict.fromkeys(npc_keys))[:6],
        "heat": 10,
        "stage": "setup",
        "stakes": 3,
        "hooks": [],
        "last_update": now_iso(),
        "cooldown": 0,
    }
    threads_data["threads"].append(t)
    return t


def memory_driven_quests(zone: str, player_id: str = "p1", max_q: int = 2, budget: int = 200, threads_data: dict = None):
    zone = (zone or "").strip() or "zone"
    player_id = (player_id or "p1").strip() or "p1"
    max_q = clamp(safe_int(max_q, 2), 0, 10)
    budget = clamp(safe_int(budget, 200), 10, 5000)
    if player_id.upper() == "SYSTEM" or max_q == 0:
        return []

    db = _BRIDGE.load_npc_db()
    npcs_map = (db.get("npcs", {}) or {})
    npc_ids = list(npcs_map.keys())
    if len(npc_ids) > budget:
        npc_ids = random.sample(npc_ids, k=budget)

    low_trust, high_respect = [], []
    for nid in npc_ids:
        n = npcs_map.get(nid) or {}
        op = (n.get("opinions", {}) or {}).get(player_id)
        if not isinstance(op, dict):
            continue
        trust = clamp(safe_int(op.get("trust", 50), 50), 0, 100)
        respect = clamp(safe_int(op.get("respect", 50), 50), 0, 100)
        nkey = npc_key_from(str(nid), n)
        if trust < 25:
            low_trust.append((trust, n, nkey))
        if respect > 75:
            high_respect.append((respect, n, nkey))

    out, thread = [], None
    if threads_data is not None:
        factions = (_BRIDGE.load_world_state().get("world_flags", {}) or {}).get("factions", []) or []
        npc_keys = [x[2] for x in (low_trust[:1] + high_respect[:1])]
        thread = pick_or_create_thread(threads_data, zone, factions, npc_keys, theme_hint="dette" if low_trust else "rumeur")

    if low_trust and len(out) < max_q:
        npc = sorted(low_trust, key=lambda x: x[0])[0]
        style = pick_unique_recent(["prouver ta bonne foi : apporter une preuve", "réparer un tort : aider quelqu’un publiquement", "payer une caution : récupérer l’argent si tu réussis"], "memq_lowtrust_style", avoid_last=6, default="apporter une preuve")
        q = f"À {zone}, {npc[1].get('name','un PNJ')} ({npc[2]}) refuse de t’aider. Tu dois {style}."
        if thread:
            q += f" [thread_id={thread.get('id','')}]"
        out.append(q)

    if high_respect and len(out) < max_q:
        npc = sorted(high_respect, key=lambda x: -x[0])[0]
        mission = pick_unique_recent(["protéger un convoi", "calmer un conflit", "enquêter sur une rumeur", "escorter une personne importante"], "memq_highrespect_mission", avoid_last=6, default="enquêter sur une rumeur")
        q = f"À {zone}, {npc[1].get('name','un PNJ')} ({npc[2]}) te respecte beaucoup. Il te confie une mission risquée : {mission}."
        if thread:
            q += f" [thread_id={thread.get('id','')}]"
        out.append(q)

    return out[:max_q]

# =========================
# Runtime path aliases + compatibility wrappers
# =========================
_BRIDGE = EliBridge()
NEXT_SCENE_JSON = _BRIDGE.paths.next_scene_json
NEXT_SCENE_TXT = _BRIDGE.paths.next_scene_txt
SCENE_UNREAL_JSON = _BRIDGE.paths.content / "scene_unreal.json"
EVENT_IN_JSON = _BRIDGE.paths.event_in_json
EVENT_OUT_JSON = _BRIDGE.paths.event_out_json
EVENT_OUT_TXT = _BRIDGE.paths.content / "event_out.txt"
QUESTS_FILE = _BRIDGE.paths.quests_file
PNJ_FILE = _BRIDGE.paths.pnj_file
DUNGEON_FILE = _BRIDGE.paths.dungeon_file
DIALOGUE_FILE = _BRIDGE.paths.dialogue_file
ITEMS_FILE = _BRIDGE.paths.items_file
ANIMALS_FILE = _BRIDGE.paths.animals_file
ANIMALS_JSON_FILE = _BRIDGE.paths.animals_json_file
EXPORT_JSON_FILE = _BRIDGE.paths.export_json_file


def seed_random():
    random.seed()


IS_BRIDGE_MODE = str(os.environ.get("ELI_BRIDGE", "")).strip() == "1"

def ask(question: str) -> str:
    if IS_BRIDGE_MODE:
        return ""
    try:
        return input(f"{question}: ").strip()
    except EOFError:
        return ""


def ask_yes_no(question: str) -> bool:
    ans = ask(question + " (oui/non)")
    return ans.lower().startswith("oui")


def ask_player_id(default_id: str = "p1"):
    pid = ask(f"ID du joueur (ex: p1) [ENTER={default_id}]")
    return pid or default_id


def ensure_world_state_exists():
    st = _BRIDGE.load_world_state()
    _BRIDGE.save_world_state(st)
    return st


def ensure_relationships_exist():
    rel = _BRIDGE.load_relationships()
    _BRIDGE.save_relationships(rel)
    return rel


def load_npc_db():
    return _BRIDGE.load_npc_db()


def save_npc_db(db: dict):
    return _BRIDGE.save_npc_db(db)


def load_world_state():
    return _BRIDGE.load_world_state()


def save_world_state(state: dict):
    return _BRIDGE.save_world_state(state)


def load_relationships():
    return _BRIDGE.load_relationships()


def save_relationships(rel: dict):
    return _BRIDGE.save_relationships(rel)


def load_rules_text() -> str:
    return read_text(_BRIDGE.paths.rules_file).strip()


def find_persistent_npc_by_name(db: dict, name: str):
    q = (name or "").strip().lower()
    if not q:
        return None
    for npc in (db.get("npcs", {}) or {}).values():
        if (npc.get("name") or "").strip().lower() == q:
            return npc
    return None


def find_npc_by_name_partial(db: dict, query: str, max_results: int = 10):
    q = (query or "").strip().lower()
    if not q:
        return []
    out = []
    for npc in (db.get("npcs", {}) or {}).values():
        nm = (npc.get("name") or "").strip().lower()
        if q in nm:
            out.append(npc)
    out.sort(key=lambda n: len((n.get("name") or "")))
    return out[:max(0, safe_int(max_results, 10))]


def suggest_similar_npc_names(query: str, db: dict, max_results: int = 3):
    import difflib
    names = [(n.get("name") or "") for n in (db.get("npcs", {}) or {}).values() if (n.get("name") or "").strip()]
    return difflib.get_close_matches((query or "").strip(), names, n=max_results, cutoff=0.55)


def get_npc_memories_for_player(npc: dict, player_id: str):
    pid = (player_id or "p1").strip() or "p1"
    return [m for m in (npc.get("memory", []) or []) if str(m.get("player_id", "")).strip() == pid]


def trust_to_tone(trust: int, status: str):
    if status in ["allié", "protégé"] and trust >= 60:
        return "chaleureux"
    if status in ["rival", "menacé"] and trust <= 40:
        return "hostile"
    if status == "dette":
        return "gêné"
    if status == "méfiant":
        return "prudent"
    return "neutre"


def tone_line(tone: str, base: str):
    if tone == "chaleureux":
        return base.replace("«", "« (sourire) ")
    if tone == "hostile":
        return base.replace("«", "« (sec) ")
    if tone == "prudent":
        return base.replace("«", "« (bas) ")
    if tone == "gêné":
        return base.replace("«", "« (hésite) ")
    return base


def get_relation(rel: dict, a: str, b: str):
    return ((rel.get("npcs", {}) or {}).get((a or "").strip(), {}) or {}).get((b or "").strip())


def set_relation(rel: dict, a: str, b: str, status: str, trust: int, notes: str):
    rel.setdefault("npcs", {})
    rel["npcs"].setdefault(a, {})
    rel["npcs"][a][b] = {
        "status": status if status else "neutre",
        "trust": clamp(safe_int(trust, 50), 0, 100),
        "notes": (notes or "").strip(),
        "updated_at": now_iso(),
    }


def ensure_pair_relation(rel: dict, a: str, b: str, create_if_missing: bool = True):
    r = get_relation(rel, a, b)
    if r:
        return r
    if not create_if_missing:
        return {"status": "neutre", "trust": 50, "notes": "missing", "updated_at": now_iso()}
    set_relation(rel, a, b, "neutre", random.randint(20, 80), "auto")
    set_relation(rel, b, a, "neutre", random.randint(20, 80), "auto")
    return get_relation(rel, a, b)


def tweak_relation(rel: dict, a: str, b: str, delta_trust: int, new_status=None, extra_note: str = ""):
    r = get_relation(rel, a, b) or {"status": "neutre", "trust": 50, "notes": ""}
    trust = clamp(safe_int(r.get("trust", 50), 50) + safe_int(delta_trust, 0), 0, 100)
    status = new_status if new_status else r.get("status", "neutre")
    notes = (r.get("notes", "") + " | " + (extra_note or "")).strip(" |")
    set_relation(rel, a, b, status, trust, notes)
    return get_relation(rel, a, b)


def npc_attitude(npc: dict, player_id: str):
    op = ensure_player_opinion(npc, player_id)
    trust = clamp(safe_int(op.get("trust", 50), 50), 0, 100)
    fear = clamp(safe_int(op.get("fear", 0), 0), 0, 100)
    respect = clamp(safe_int(op.get("respect", 50), 50), 0, 100)
    if trust < 20:
        return "refuse"
    if fear > 70 and trust < 40:
        return "obeys_in_fear"
    if trust > 75 and respect > 60:
        return "friendly"
    return "neutral"


def can_interact(npc: dict, player_id: str, interaction_type: str, state: dict):
    op = ensure_player_opinion(npc, player_id)
    trust = clamp(safe_int(op.get("trust", 50), 50), 0, 100)
    if trust <= 15 and interaction_type in ["talk", "trade", "info", "quest_give", "quest_take"]:
        return False, "Le PNJ ne te fait pas confiance."
    return True, "OK"


def compute_lie_chance(npc: dict, player_id: str, topic: str = "info"):
    p = 0.08
    strat = npc.get("social_strategies", {}) or {}
    deceive = clamp(safe_int(strat.get("deceive", 50), 50), 0, 100)
    p += (deceive / 100) * 0.25
    op = ensure_player_opinion(npc, player_id)
    trust = clamp(safe_int(op.get("trust", 50), 50), 0, 100)
    if trust < 35:
        p += 0.18
    return max(0.0, min(0.85, p))


def npc_say_with_possible_lie(npc: dict, player_id: str, truth: str, lie: str, topic: str = "info"):
    lied = random.random() < compute_lie_chance(npc, player_id, topic=topic)
    return (lie if lied else truth), truth, lied


LIE_TELLS_SUBTLE = ["il hésite une fraction de seconde", "il évite ton regard", "il répond un peu trop vite"]
LIE_TELLS_STRONG = ["tu repères une contradiction", "un témoin proche raconte l’inverse"]


def build_lie_tells(lied: bool):
    if not lied:
        return (pick(LIE_TELLS_SUBTLE), "") if random.random() < 0.15 else ("", "")
    return pick(LIE_TELLS_SUBTLE), (pick(LIE_TELLS_STRONG) if random.random() < 0.35 else "")


def lie_detection_roll(npc: dict, player_id: str, severity: int, state: dict):
    p = 0.15 + (clamp(safe_int(severity, 1), 1, 10) / 10) * 0.10
    r = random.random()
    if r < p * 0.20:
        return 2
    if r < p:
        return 1
    return 0


def normalize_target(event: dict, npcs_db: dict = None):
    event = event or {}
    ttype = (event.get("action_target_type") or "").strip().lower()
    tid = (event.get("action_target_id") or "").strip()
    tname = (event.get("action_target_name") or "").strip()
    if ttype not in ("npc", "object", "zone", ""):
        ttype = ""
    if ttype in ("npc", "object", "zone") and not tid:
        tid = "unknown"
    tkey = ""
    if ttype == "npc":
        if tname and tid:
            tkey = f"{tname}|{tid}"
        elif tname:
            tkey = tname
    return {"action_target_type": ttype, "action_target_id": tid, "action_target_name": tname, "action_target_key": tkey}


# =========================
# UNREAL SCENE FORMAT — ELI OMNI READY
# =========================
def build_unreal_scene_payload(p: dict):
    p = p or {}
    zone = p.get("zone", "")
    location = p.get("location", "")
    scene_id = p.get("scene_id") or make_id("scene")
    thread_id = (p.get("thread_id") or "").strip()
    thread_stage = p.get("thread_stage")
    thread_heat = p.get("thread_heat")

    npcs = p.get("npcs") or {}
    npc1 = npcs.get("npc1") or {}
    npc2 = npcs.get("npc2") or {}

    def _runtime_npc_id(n: dict):
        if not isinstance(n, dict):
            return make_id("npc_spawn")
        pid = (n.get("persistent_id") or "").strip()
        nid = (n.get("npc_id") or "").strip()
        if pid and pid != "unknown":
            return pid
        if nid and nid != "unknown":
            return nid
        return make_id("npc_spawn")

    def fallback_npc(side: str):
        rid = make_id("npc_spawn")
        name = make_name_unique()
        return {
            "type": "npc", "npc_id": rid, "npc_key": f"{name}|unknown", "name": name,
            "role": pick(PNJ_ROLES), "faction": "habitants", "trait": pick(PNJ_TRAITS),
            "emotion": pick(PNJ_EMOTIONS), "persistent_id": "", "spawn_hint": f"{location} proche ({side})",
        }

    def npc_payload(n: dict, side_hint: str):
        if not isinstance(n, dict) or not n:
            return fallback_npc(side_hint)
        rid = _runtime_npc_id(n)
        name = (n.get("name") or "").strip() or make_name_unique()
        persistent_id = (n.get("persistent_id") or "").strip()
        npc_key = (n.get("npc_key") or "").strip()
        if not npc_key:
            base_id = (persistent_id or (n.get("npc_id") or "unknown"))
            npc_key = f"{name}|{base_id}"
        return {
            "type": "npc", "npc_id": rid, "npc_key": npc_key, "name": name,
            "role": n.get("role") or pick(PNJ_ROLES), "faction": n.get("faction") or "habitants",
            "trait": n.get("trait") or pick(PNJ_TRAITS), "emotion": n.get("emotion") or pick(PNJ_EMOTIONS),
            "persistent_id": persistent_id, "spawn_hint": f"{location} proche ({side_hint})",
        }

    npc1_payload = npc_payload(npc1, "gauche de la scène")
    npc2_payload = npc_payload(npc2, "droite de la scène")

    spawns = [npc1_payload, npc2_payload]
    for idx, obj in enumerate(p.get("scene_objects", []) or [], 1):
        spawns.append({"type": "object", "object_id": f"{scene_id}_obj_{idx}", "label": obj, "spawn_hint": f"{location} (près du sol, point {idx})"})

    triggers = [{"trigger_id": f"{scene_id}_dialogue", "type": "dialogue_start", "npc_ids": [npc1_payload.get("npc_id"), npc2_payload.get("npc_id")], "hint": "Le joueur approche et appuie sur Interagir"}]
    choice_triggers = []
    for c in (p.get("choices") or []):
        imm_tags = c.get("immediate_tags") if isinstance(c.get("immediate_tags"), list) else None
        dly_tags = c.get("delayed_tags") if isinstance(c.get("delayed_tags"), list) else None
        if imm_tags is None or dly_tags is None:
            imm_tags, dly_tags = to_tags(c.get("immediate", []) or [], c.get("delayed", []) or [])
        choice_triggers.append({
            "trigger_id": c.get("choice_id") or make_id("choice"), "type": "choice", "label": c.get("label") or "Choix",
            "immediate_tags": imm_tags, "delayed_tags": dly_tags, "relation_effect": c.get("relation_effect"),
        })

    return {
        "scene_id": scene_id, "zone": zone, "zone_theme": p.get("zone_theme"), "time": p.get("time"), "weather": p.get("weather"),
        "intensity": p.get("intensity"), "event_type": p.get("event_type"), "location": location,
        "thread_id": thread_id or None, "thread_stage": thread_stage or None, "thread_heat": thread_heat if thread_heat is not None else None,
        "spawns": spawns, "triggers": triggers, "choices": choice_triggers,
    }

# =========================
# Scene generation + scoring
# =========================
def npc_to_scene_npc(npc: dict, factions: list):
    npc = npc or {}
    nid = (npc.get("id") or "").strip()
    name = (npc.get("name") or "").strip() or make_name_unique()
    return {
        "npc_id": nid or "unknown",
        "npc_key": f"{name}|{nid or 'unknown'}",
        "name": name,
        "role": npc.get("role") or pick(PNJ_ROLES),
        "trait": npc.get("trait") or pick(PNJ_TRAITS),
        "emotion": npc.get("emotion") or pick(PNJ_EMOTIONS),
        "faction": npc.get("faction") or (pick(factions) if factions else "habitants"),
        "persistent_id": nid,
    }


def pick_persistent_npc_for_zone(zone_name: str, db: dict):
    z = (zone_name or "").strip().lower()
    cands = [n for n in (db.get("npcs", {}) or {}).values() if str(n.get("location", "")).strip().lower() == z]
    if cands:
        return pick(cands)
    alln = list((db.get("npcs", {}) or {}).values())
    return pick(alln) if alln else None


def build_npc_to_npc_dialogue(npc1: dict, npc2: dict, rel_data: dict, intensity: int, event_type: str):
    n1 = f"{npc1.get('name','')}|{npc1.get('persistent_id','') or npc1.get('npc_id','')}"
    n2 = f"{npc2.get('name','')}|{npc2.get('persistent_id','') or npc2.get('npc_id','')}"
    r = ensure_pair_relation(rel_data, n1, n2)
    status = r.get("status", "neutre")
    trust = int(r.get("trust", 50))
    tone = trust_to_tone(trust, status)
    raw = [
        f"{n1} : « On parle de {event_type}. Tu sais quelque chose ? »",
        f"{n2} : « Peut-être. Mais ça dépend de toi. »",
        f"{n1} : « Si ça tourne mal, on paie tous. »",
    ]
    return {"relation": {"status": status, "trust": trust, "tone": tone, "notes": r.get("notes", "")}, "lines": [tone_line(tone, x) for x in raw]}


def build_choices(npc1: dict, npc2: dict):
    count = random.randint(4, 7)
    out, used = [], set()
    while len(out) < count and len(used) < len(CHOICE_VERBS):
        v = pick(CHOICE_VERBS)
        if v in used:
            continue
        used.add(v)
        pref = {
            "attaquer": ["combat_start", "faction_notice"],
            "aider": ["reputation_locale_plus", "get_clue"],
            "mentir": ["npc_suspicious", "get_clue"],
            "enqueter": ["get_clue", "lose_time"],
        }.get(v.lower())
        imm = pick_many(pref if pref else CONSEQUENCES_IMMEDIATE, 2)
        dly = pick_many(CONSEQUENCES_DELAYED, 1)
        out.append({"id": len(out) + 1, "choice_id": make_id("choice"), "label": v.title(), "immediate": imm, "immediate_tags": imm, "delayed": dly, "delayed_tags": dly, "relation_effect": None})
    return out


def severity_label_from_intensity(intensity: int):
    if intensity >= 8:
        return "URGENT"
    if intensity >= 5:
        return "TENDU"
    return "CALME"


def force_event_for_intensity(event_type: str, intensity: int):
    intensity = clamp(safe_int(intensity, 4), 1, 10)
    if intensity >= 8:
        return pick(["embuscade", "arrestation", "danger_naturel", "conflit", "trahison"])
    event_type = (event_type or "").strip().lower()
    return event_type if event_type in SCENE_EVENT_TYPES else pick(SCENE_EVENT_TYPES)


def elisabeth_generate_scene(u: dict, state: dict, rel_data: dict, rules_text: str, proposals_n: int = 8):
    scene = state.get("scene", {}) or {}
    zone = scene.get("zone", "forêt")
    zone_theme = scene.get("zone_theme", "medieval_fantasy")
    time = scene.get("time", "jour")
    weather = scene.get("weather") or pick_weather_for_theme(zone_theme)
    danger = int(scene.get("danger", 4))
    factions = (state.get("world_flags", {}) or {}).get("factions", ["habitants", "gardes", "chasseurs", "bandits"])

    db = load_npc_db()
    if not db.get("npcs"):
        for _ in range(20):
            n = create_persistent_npc(default_location=zone)
            db["npcs"][n["id"]] = n
        save_npc_db(db)

    proposals = []
    for _ in range(max(1, safe_int(proposals_n, 8))):
        location = pick(SCENE_LOCATIONS)
        intensity = clamp(danger + random.randint(-2, 3), 1, 10)
        event_type = force_event_for_intensity(pick_scene_event_type(None), intensity)
        pn1 = pick_persistent_npc_for_zone(zone, db)
        pn2 = pick_persistent_npc_for_zone(zone, db)
        npc1 = npc_to_scene_npc(pn1, factions) if pn1 else npc_to_scene_npc({}, factions)
        npc2 = npc_to_scene_npc(pn2, factions) if pn2 else npc_to_scene_npc({}, factions)
        objs = pick_scene_objects_for_theme(zone_theme, 2, 4)
        desc = f"[{severity_label_from_intensity(intensity)}] Zone: {zone} ({zone_theme}) | {time}, {weather} | Lieu: {location} | Événement: {event_type}."
        proposal = {
            "scene_id": make_id("scene"), "zone": zone, "zone_theme": zone_theme, "time": time, "weather": weather, "danger": danger,
            "location": location, "event_type": event_type, "intensity": intensity, "npcs": {"npc1": npc1, "npc2": npc2},
            "npc_to_npc": build_npc_to_npc_dialogue(npc1, npc2, rel_data, intensity, event_type), "scene_objects": objs,
            "choices": build_choices(npc1, npc2), "description": desc, "universe_tokens": [], "wildlife_pack_size": 0,
        }
        proposal = normalize_scene_output(proposal)
        ok, reason = validate_scene_against_universe(u, proposal)
        proposal["universe_ok"], proposal["universe_reason"] = ok, reason
        proposals.append(proposal)
    return proposals


def eli_score_scene(u: dict, proposal: dict, state: dict, rules_text: str):
    score, reasons = 50, []
    if proposal.get("universe_ok"):
        score += 25
        reasons.append("univers respecté")
    else:
        score -= 40
        reasons.append("univers cassé")
        return clamp(score, 0, 100), reasons
    intensity = int(proposal.get("intensity", 4))
    danger = int(state.get("scene", {}).get("danger", 4))
    if abs(intensity - danger) <= 2:
        score += 10
        reasons.append("intensité cohérente")
    if proposal.get("npc_to_npc"):
        score += 8
        reasons.append("PNJ↔PNJ")
    if len(proposal.get("choices", [])) >= 5:
        score += 5
        reasons.append("choix joueurs")
    return clamp(score, 0, 100), reasons


def choose_best_scene(u: dict, proposals: list, state: dict, rules_text: str):
    best = None
    for p in proposals:
        s, r = eli_score_scene(u, p, state, rules_text)
        if best is None or s > best[0]:
            best = (s, r, p)
    return best


def update_thread_from_scene(threads_data: dict, scene: dict):
    threads_data = repair_threads(threads_data)
    zone = (scene.get("zone") or "zone").strip()
    intensity = clamp(safe_int(scene.get("intensity", 4), 4), 1, 10)
    event_type = (scene.get("event_type") or "").strip().lower()
    npcs = scene.get("npcs", {}) if isinstance(scene.get("npcs", {}), dict) else {}
    npc_keys = [npcs.get(s, {}).get("npc_key", "") for s in ["npc1", "npc2"] if isinstance(npcs.get(s), dict)]
    factions = [npcs.get(s, {}).get("faction", "") for s in ["npc1", "npc2"] if isinstance(npcs.get(s), dict)]
    thread = pick_or_create_thread(threads_data, zone, factions, npc_keys, theme_hint=event_type or "rumeur")
    heat = clamp(safe_int(thread.get("heat", 10), 10) + int((intensity - 4) * 3), 0, 100)
    thread["heat"] = heat
    thread["stage"] = "climax" if heat >= 65 else ("crisis" if heat >= 35 else "setup")
    thread["last_update"] = now_iso()
    return thread


def format_next_scene_txt(best_score: int, reasons: list, p: dict):
    lines = ["=== NEXT SCENE (PNJ vivants, joueurs réels) ===", f"Score: {best_score}/100", "Raisons:"]
    lines += [f"- {x}" for x in reasons]
    lines += ["\n--- CONTEXTE ---", f"SceneID: {p.get('scene_id')}", f"Zone: {p.get('zone','?')} | Thème: {p.get('zone_theme','?')}", f"Temps: {p.get('time','?')} | Météo: {p.get('weather','?')}", f"Lieu: {p.get('location','?')} | Type: {p.get('event_type','?')}", f"Intensité: {p.get('intensity','?')}/10", "\n--- DESCRIPTION ---", p.get("description", "")]
    return "\n".join(lines)


def action_next_scene():
    ensure_folders(_BRIDGE.paths)
    seed_random()
    u = load_universe()
    state = ensure_world_state_exists()
    rel_data = ensure_relationships_exist()
    rules_text = load_rules_text()
    threads_data = load_threads()

    proposals = elisabeth_generate_scene(u, state, rel_data, rules_text, proposals_n=10)
    result = choose_best_scene(u, proposals, state, rules_text)
    if result is None:
        logger.error("Aucune scène générée.")
        return None
    best_score, reasons, best = result
    best = normalize_scene_output(best)

    thread = update_thread_from_scene(threads_data, best)
    best["thread_id"], best["thread_stage"], best["thread_heat"] = thread.get("id"), thread.get("stage"), thread.get("heat")

    out = {"generated_at": now_iso(), "best_score": best_score, "reasons": reasons, "thread": {"id": thread.get("id"), "stage": thread.get("stage"), "heat": thread.get("heat"), "theme": thread.get("theme"), "zone": thread.get("zone")}, "scene": best}
    write_text(NEXT_SCENE_JSON, json.dumps(out, indent=2, ensure_ascii=False))
    write_text(NEXT_SCENE_TXT, format_next_scene_txt(best_score, reasons, best) + f"\n\n--- THREAD ---\nthread_id={thread.get('id')} | stage={thread.get('stage')} | heat={thread.get('heat')} | theme={thread.get('theme')}\n")
    write_text(SCENE_UNREAL_JSON, json.dumps(build_unreal_scene_payload(best), indent=2, ensure_ascii=False))
    save_threads(threads_data)
    save_world_state(state)
    save_relationships(rel_data)
    return out

# =========================
# UNREAL EVENT PIPELINE
# =========================
EVENT_TYPES = ["help", "crime", "kill", "trade", "insult", "quest_success", "quest_fail", "trespass"]
EVENT_CONTEXT_OPENERS = ["La tension monte.", "Une situation éclate sur place.", "Quelque chose tourne mal.", "Tout le monde remarque ce qui se passe."]
EVENT_DETAIL_BY_TYPE = {
    "help": ["Un PNJ appelle à l’aide, il manque de temps."],
    "trade": ["Un échange attire des regards jaloux."],
    "insult": ["Le ton monte, et ça peut dégénérer."],
    "crime": ["Un acte illégal met la zone en alerte."],
    "kill": ["Un mort, ça change tout : peur, colère, vengeance."],
    "quest_success": ["Ton succès fait parler de toi."],
    "quest_fail": ["Ton échec coûte du temps et de la confiance."],
    "trespass": ["Tu as franchi une limite."],
}
EVENT_IMMEDIATE_VARIANTS = {
    "help": [["réputation locale +", "tu obtiens un indice utile"]],
    "trade": [["un prix baisse", "un accès se débloque"]],
    "insult": [["réputation locale -", "un PNJ devient méfiant"]],
    "crime": [["réputation locale -", "une faction te remarque"]],
    "kill": [["un combat démarre", "une faction te remarque"]],
    "quest_success": [["réputation locale +", "un accès se débloque"]],
    "quest_fail": [["tu perds du temps", "réputation locale -"]],
    "trespass": [["un PNJ devient méfiant", "réputation locale -"]],
}
EVENT_DELAYED_VARIANTS = {
    "help": [["un PNJ reviendra demander une faveur"]],
    "trade": [["une rumeur sur toi se répand"]],
    "insult": [["une rumeur sur toi se répand"]],
    "crime": [["une faction prépare une vengeance"]],
    "kill": [["une zone devient plus dangereuse"]],
    "quest_success": [["un PNJ te protégera plus tard"]],
    "quest_fail": [["une rumeur sur toi se répand"]],
    "trespass": [["une faction prépare une vengeance"]],
}


def npc_key_from_parts(name: str, pid: str):
    name, pid = (name or "").strip(), (pid or "").strip()
    if not name and not pid:
        return ""
    if not pid:
        pid = "unknown"
    if not name:
        name = "Unknown"
    return f"{name}|{pid}"


def split_npc_key(npc_key: str):
    s = (npc_key or "").strip()
    if "|" in s:
        a, b = s.split("|", 1)
        return a.strip(), b.strip()
    return s, ""


def resolve_npc_actor(db: dict, npc_key_or_name: str):
    npcs = (db.get("npcs", {}) or {})
    q = (npc_key_or_name or "").strip()
    if not q:
        return None
    name_q, id_q = split_npc_key(q)
    if id_q and isinstance(npcs.get(id_q), dict):
        return npcs.get(id_q)
    exact = [n for n in npcs.values() if (n.get("name") or "").strip().lower() == name_q.lower()]
    if len(exact) == 1:
        return exact[0]
    pref = [n for n in npcs.values() if (n.get("name") or "").strip().lower().startswith(name_q.lower())]
    return pref[0] if len(pref) == 1 else None


def rel_key_for_npc(npc: dict, fallback_key_or_name: str):
    if isinstance(npc, dict):
        name = (npc.get("name") or "").strip()
        pid = (npc.get("id") or "").strip() or (npc.get("persistent_id") or "").strip()
        if name and pid:
            return npc_key_from_parts(name, pid)
    fb = (fallback_key_or_name or "").strip()
    if "|" in fb:
        n, pid = split_npc_key(fb)
        return npc_key_from_parts(n, pid)
    return npc_key_from_parts(fb, "unknown") if fb else ""


def build_event_context(event: dict, state: dict, rel: dict):
    scene = (state.get("scene", {}) or {}) if isinstance(state, dict) else {}
    zone = (event.get("zone") or scene.get("zone") or "forêt")
    zone_theme = (scene.get("zone_theme") or "medieval_fantasy")
    time = (scene.get("time") or "jour")
    weather = (scene.get("weather") or "clair")
    danger = clamp(safe_int(scene.get("danger", 4), 4), 0, 10)
    npc_a_in, npc_b_in = (event.get("npc_a") or "").strip(), (event.get("npc_b") or "").strip()

    db = load_npc_db()
    npc_a = rel_key_for_npc(resolve_npc_actor(db, npc_a_in), npc_a_in) if npc_a_in else ""
    npc_b = rel_key_for_npc(resolve_npc_actor(db, npc_b_in), npc_b_in) if npc_b_in else ""

    rel_summary = None
    if npc_a and npc_b:
        r = get_relation(rel, npc_a, npc_b)
        if isinstance(r, dict):
            rel_summary = {"pair": [npc_a, npc_b], "status": r.get("status", "neutre"), "trust": clamp(safe_int(r.get("trust", 50), 50), 0, 100), "notes": (r.get("notes", "") or "")}

    severity = clamp(safe_int(event.get("severity", 5), 5), 1, 10)
    sev_label = "URGENT" if severity >= 8 else ("TENDU" if severity >= 5 else "CALME")
    etype = (event.get("type") or "").strip().lower()
    base_line = (event.get("action_detail") or "").strip() or pick(EVENT_DETAIL_BY_TYPE.get(etype, ["Quelque chose se passe."]))
    target = normalize_target(event, npcs_db=db)

    context_text = f"[{sev_label}] Zone: {zone} ({zone_theme}) | {time}, {weather} | danger={danger}/10. {pick(EVENT_CONTEXT_OPENERS)} {base_line}"
    if npc_a:
        context_text += f" Acteur: {npc_a}."
    if npc_b:
        context_text += f" Cible: {npc_b}."

    return {
        "action_target": target,
        "zone": zone,
        "zone_theme": zone_theme,
        "time": time,
        "weather": weather,
        "danger": danger,
        "severity": severity,
        "severity_label": sev_label,
        "action_detail": (event.get("action_detail") or ""),
        "witnesses": max(0, safe_int(event.get("witnesses", 0), 0)),
        "faction_context": (event.get("faction_context") or ""),
        "context_text": context_text,
        "relationship": rel_summary,
        "npc_a_key": npc_a,
        "npc_b_key": npc_b,
    }


def npc_rumor_knowledge(npc: dict, player_id: str, state: dict):
    player_id = (player_id or "p1").strip()
    if not player_id or player_id.upper() == "SYSTEM":
        return 0, 0.0
    r = ensure_rumor_state(state, player_id)
    true_rep = clamp(safe_int(r.get("rep", 0), 0), -50, 50)
    heat = clamp(safe_int(r.get("heat", 0), 0), 0, 100)
    know_p = max(0.05, min(0.90, 0.10 + (heat / 100) * 0.55))
    if random.random() > know_p:
        return clamp(int(true_rep * random.uniform(-0.2, 0.2)), -50, 50), random.uniform(0.1, 0.35)
    noise = random.randint(-3, 3)
    return clamp(true_rep + noise, -50, 50), random.uniform(0.35, 0.95)


def apply_npc_memory_reaction(npc_actor: dict, player_id: str, interaction_type: str, state: dict):
    op = ensure_player_opinion(npc_actor, player_id)
    trust, fear, respect = clamp(safe_int(op.get("trust", 50), 50), 0, 100), clamp(safe_int(op.get("fear", 0), 0), 0, 100), clamp(safe_int(op.get("respect", 50), 50), 0, 100)
    perceived_rep, conf = npc_rumor_knowledge(npc_actor, player_id, state)
    rep_hint = "Il a l'air très sûr de ce qu'il croit savoir sur toi." if conf >= 0.75 else ("Il hésite comme s'il répétait des rumeurs." if conf >= 0.45 else "Il ne semble pas vraiment te connaître.")
    if npc_attitude(npc_actor, player_id) == "refuse":
        return False, "Le PNJ ne te fait pas confiance (trust < 20).", rep_hint
    effective_trust = clamp(trust + int(perceived_rep * conf * 0.6), 0, 100)
    if effective_trust <= 15 and interaction_type in ["help_request", "trade", "info", "quest_give", "quest_take", "talk"]:
        return False, "Le PNJ préfère éviter les ennuis avec toi.", rep_hint
    if fear >= 75 and trust < 40:
        return True, "OK", "Il te répond vite, mais on dirait qu'il a peur de toi."
    if trust >= 75 and respect >= 60:
        return True, "OK", "Son ton est plus chaleureux que la normale."
    return True, "OK", rep_hint


def merge_hints(*hints):
    cleaned, seen = [], set()
    for h in hints:
        if not h:
            continue
        core = str(h).strip().strip("() ")
        if not core or core.lower() in seen:
            continue
        seen.add(core.lower())
        cleaned.append(core)
    return (" ".join([f"({c})" for c in cleaned]))[:160] if cleaned else ""


def merge_npc_hints(ui_hint: str, mem_hint: str) -> str:
    ui_hint, mem_hint = (ui_hint or "").strip(), (mem_hint or "").strip()
    if ui_hint and mem_hint:
        return ui_hint if ui_hint.lower() == mem_hint.lower() else (f"{ui_hint}. {mem_hint}"[:120])
    return ui_hint or mem_hint


def update_dynamic_alliances(rel: dict, npc_actor_name: str, state: dict, event_type: str, severity: int):
    rel.setdefault("factions", default_relationships().get("factions", {}))
    fac = rel["factions"]
    for f in ["habitants", "gardes", "chasseurs", "bandits"]:
        fac.setdefault(f, {})
    def pair(a,b,status):
        fac.setdefault(a, {}); fac.setdefault(b, {})
        fac[a][b]=status; fac[b][a]=status
    danger = clamp(safe_int((state.get("scene", {}) or {}).get("danger", 4), 4), 0, 10)
    et = (event_type or "").strip().lower(); s = clamp(safe_int(severity,5),1,10)
    if et in ["crime","kill"] or danger >= 8 or s >= 8:
        pair("habitants", "gardes", "allié"); pair("gardes", "bandits", "rival"); pair("habitants", "bandits", "rival")


def apply_world_and_relation_updates(state: dict, rel: dict, zone: str, etype: str, rep_delta: int, economy_delta: int, danger_delta: int, npc_a: str, npc_b: str, severity: int):
    state.setdefault("meta", {"created_at": now_iso(), "updated_at": now_iso()}); state["meta"]["updated_at"] = now_iso()
    rel.setdefault("meta", {"created_at": now_iso(), "updated_at": now_iso()}); rel["meta"]["updated_at"] = now_iso()
    state.setdefault("player_meta", {}).setdefault("global_reputation", 0)
    state.setdefault("world_flags", {}).setdefault("economy_heat", 3)
    state.setdefault("world_flags", {}).setdefault("last_event", "")
    state.setdefault("scene", {}).setdefault("danger", 4)
    state["player_meta"]["global_reputation"] = clamp(safe_int(state["player_meta"].get("global_reputation", 0),0)+safe_int(rep_delta,0), -100, 100)
    state["world_flags"]["economy_heat"] = clamp(safe_int(state["world_flags"].get("economy_heat",3),3)+safe_int(economy_delta,0), 0, 10)
    state["scene"]["danger"] = clamp(safe_int(state["scene"].get("danger",4),4)+safe_int(danger_delta,0), 0, 10)
    state["world_flags"]["last_event"] = f"{etype} (zone={zone})"
    update_dynamic_alliances(rel, npc_a, state, etype, severity)
    rel_updates = []
    if npc_a and npc_b and npc_a != npc_b:
        ensure_pair_relation(rel, npc_a, npc_b)
        r = tweak_relation(rel, npc_a, npc_b, +5 if etype in ["help", "trade", "quest_success"] else -8, None if etype in ["help", "trade", "quest_success"] else "méfiant", f"event:{etype}")
        rel_updates.append({f"{npc_a}->{npc_b}": r})
    return rel_updates


def compute_event_response(event: dict, state: dict, rel: dict):
    etype = (event.get("type") or "").strip()
    zone = (event.get("zone") or (state.get("scene", {}) or {}).get("zone", "forêt")).strip()
    npc_a = (event.get("npc_a") or "").strip(); npc_b = (event.get("npc_b") or "").strip()
    player_id = (event.get("player_id") or "p1").strip(); is_system = player_id.upper() == "SYSTEM"

    state = repair_world_state(state if isinstance(state, dict) else {})
    state.setdefault("world_flags", {}).setdefault("factions", ["habitants", "gardes", "chasseurs", "bandits"])
    context = build_event_context(event, state, rel)
    sev = clamp(int(context.get("severity", 5)), 1, 10)
    update_rumor_from_event(state, {**event, "severity": sev, "witnesses": int(context.get("witnesses", 0))})

    interaction_type = (event.get("interaction_type") or "").strip().lower() or {
        "help": "help_request", "trade": "trade", "insult": "talk", "crime": "talk", "kill": "talk", "quest_success": "quest_take", "quest_fail": "quest_take", "trespass": "talk",
    }.get(etype, "talk")

    db = load_npc_db()
    npc_actor = resolve_npc_actor(db, npc_a)
    npc_target = resolve_npc_actor(db, npc_b)
    npc_a_key = rel_key_for_npc(npc_actor, npc_a); npc_b_key = rel_key_for_npc(npc_target, npc_b)

    ui_hint_in = (event.get("ui_hint") or "").strip(); hint_mem = ""; hint_lie = ""
    public_npc_line = ""; secret_truth_line = ""; lied = False

    if npc_actor and not is_system:
        public_npc_line, secret_truth_line, lied = npc_say_with_possible_lie(npc_actor, player_id, truth=f"{npc_actor.get('name','Le PNJ')} te donne une info utile, mais reste prudent.", lie=f"{npc_actor.get('name','Le PNJ')} te donne une info rassurante… peut-être trop.", topic="info")
        if lied:
            level = lie_detection_roll(npc_actor, player_id, sev, state)
            subtle, strong = build_lie_tells(True)
            hint_lie = strong if level == 2 and strong else (subtle if level == 1 and subtle else "")

    if npc_actor and not is_system:
        ok_mem, reason_mem, hint_mem_local = apply_npc_memory_reaction(npc_actor, player_id, interaction_type, state)
        hint_mem = hint_mem_local or ""
        if not ok_mem:
            npc_add_memory(npc_actor, player_id, etype, zone, sev, delta_trust=-2, delta_fear=+1, delta_respect=-1, note=f"Refus (mémoire): {reason_mem}")
            db["npcs"][npc_actor["id"]] = npc_actor; save_npc_db(db)
            imm_tags, dly_tags = to_tags(["tu perds du temps"], ["une rumeur sur toi se répand"])
            return {
                "time": now_iso(), "event_in": event, "context": context, "npc_dialogue": public_npc_line,
                "npc_hint": merge_hints(ui_hint_in, hint_mem, hint_lie), "immediate": ["tu perds du temps"], "immediate_tags": imm_tags,
                "delayed": ["une rumeur sur toi se répand"], "delayed_tags": dly_tags,
                "world_updates": {"global_reputation_delta": 0, "economy_heat_delta": 0, "danger_delta": 0}, "relationship_updates": [],
                "npc_refusal": {"npc": npc_actor.get("name"), "reason": reason_mem},
            }

        ok, reason = can_interact(npc_actor, player_id, interaction_type, state)
        if not ok:
            npc_add_memory(npc_actor, player_id, etype, zone, sev, delta_trust=-2, delta_fear=+1, delta_respect=-1, note=f"Refus interaction={interaction_type}: {reason}")
            db["npcs"][npc_actor["id"]] = npc_actor; save_npc_db(db)
            imm_tags, dly_tags = to_tags(["tu perds du temps"], ["une rumeur sur toi se répand"])
            return {
                "time": now_iso(), "event_in": event, "context": context, "npc_dialogue": public_npc_line,
                "npc_hint": merge_hints(ui_hint_in, hint_mem, hint_lie), "immediate": ["tu perds du temps"], "immediate_tags": imm_tags,
                "delayed": ["une rumeur sur toi se répand"], "delayed_tags": dly_tags,
                "world_updates": {"global_reputation_delta": 0, "economy_heat_delta": 0, "danger_delta": 0}, "relationship_updates": [],
                "npc_refusal": {"npc": npc_actor.get("name"), "reason": reason},
            }

        dt, df, dr = score_opinion_from_event(etype, sev, int(context.get("witnesses", 0)))
        npc_add_memory(npc_actor, player_id, etype, zone, sev, delta_trust=dt, delta_fear=df, delta_respect=dr, note=(secret_truth_line or context.get("context_text") or "")[:120])
        db["npcs"][npc_actor["id"]] = npc_actor; save_npc_db(db)

    immediate = list(pick(EVENT_IMMEDIATE_VARIANTS.get(etype, [["tu perds du temps", "une faction te remarque"]])))
    delayed = list(pick(EVENT_DELAYED_VARIANTS.get(etype, [["une rumeur sur toi se répand"]])))
    rep_delta = 0; economy_delta = 0; danger_delta = 0
    witnesses = int(context.get("witnesses", 0))

    if etype == "help": rep_delta += 1 if sev < 8 else 2
    elif etype == "trade": economy_delta += 1
    elif etype == "insult": rep_delta -= 1
    elif etype == "crime": rep_delta -= 2; danger_delta += 1 if sev < 8 else 2
    elif etype == "kill": rep_delta -= 3; danger_delta += 2 if sev < 8 else 3
    elif etype == "quest_success": rep_delta += 2
    elif etype == "quest_fail": rep_delta -= 1; danger_delta += 1 if random.random() < 0.50 else 0
    elif etype == "trespass": rep_delta -= 1; danger_delta += 1 if sev >= 8 else 0

    if witnesses >= 3:
        rep_delta = rep_delta + 1 if rep_delta > 0 else (rep_delta - 1 if rep_delta < 0 else rep_delta)
        if "une rumeur sur toi se répand" not in delayed and random.random() < 0.70:
            delayed.append("une rumeur sur toi se répand")

    immediate = list(dict.fromkeys(immediate))[:2]
    delayed = list(dict.fromkeys(delayed))[:2]

    system_mode = (event.get("system_mode") or "").strip().lower()
    if is_system:
        rep_delta = 0
        allow_world_impact = (system_mode == "npc_autonomous")
        if not allow_world_impact:
            rel_updates = []; economy_delta = 0; danger_delta = 0
        else:
            rel_updates = apply_world_and_relation_updates(state, rel, zone, etype, 0, economy_delta, danger_delta, npc_a_key, npc_b_key, sev)
    else:
        rel_updates = apply_world_and_relation_updates(state, rel, zone, etype, rep_delta, economy_delta, danger_delta, npc_a_key, npc_b_key, sev)

    imm_tags, dly_tags = to_tags(immediate, delayed)
    npc_hint_out = merge_hints(ui_hint_in, hint_mem, hint_lie)
    return {
        "time": now_iso(), "event_in": event, "context": context, "npc_dialogue": public_npc_line, "npc_hint": npc_hint_out,
        "immediate": immediate, "immediate_tags": imm_tags, "delayed": delayed, "delayed_tags": dly_tags,
        "world_updates": {"global_reputation_delta": rep_delta, "economy_heat_delta": economy_delta, "danger_delta": danger_delta},
        "relationship_updates": rel_updates,
    }


def write_event_outputs(out: dict):
    ensure_folders(_BRIDGE.paths)
    write_text(EVENT_OUT_JSON, json.dumps(out, indent=2, ensure_ascii=False))
    ctx = out.get("context", {}) or {}
    ev = out.get("event_in", {}) or {}
    zone = (ev.get("zone") or ctx.get("zone") or "").strip()
    txt = ["=== EVENT REACTION (Eli) ===", f"Type: {ev.get('type','')} | Zone: {zone} | Gravité: {ctx.get('severity','')}/10", "\n--- CONTEXTE ---", ctx.get("context_text", "")]
    if (out.get("npc_dialogue") or "").strip(): txt += ["\n--- PNJ ---", out["npc_dialogue"]]
    npc_hint = (out.get("npc_hint") or "").strip()
    if npc_hint: txt += ["\n--- INDICE (joueur) ---", npc_hint]
    if out.get("npc_refusal"):
        rr = out["npc_refusal"] or {}
        txt += ["\n--- REFUS PNJ ---", f"PNJ: {rr.get('npc','')} | Raison: {rr.get('reason','')}"]
    txt += ["\nImmédiat:"] + [f"- {x}" for x in out.get("immediate", [])] + ["Tags: " + ", ".join(out.get("immediate_tags", [])), "\nRetardé:"] + [f"- {x}" for x in out.get("delayed", [])] + ["Tags: " + ", ".join(out.get("delayed_tags", []))]
    wu = out.get("world_updates", {}) or {}
    txt += ["\nUpdates monde:", f"- réputation globale delta: {wu.get('global_reputation_delta', 0)}", f"- economy_heat delta: {wu.get('economy_heat_delta', 0)}", f"- danger delta: {wu.get('danger_delta', 0)}"]
    if out.get("relationship_updates"):
        txt += ["\nUpdates relations:", json.dumps(out["relationship_updates"], indent=2, ensure_ascii=False)]
    write_text(EVENT_OUT_TXT, "\n".join(txt))


def action_react_event_auto():
    ensure_folders(_BRIDGE.paths)
    state = ensure_world_state_exists()
    rel = ensure_relationships_exist()
    if not EVENT_IN_JSON.exists():
        return None
    raw = read_text(EVENT_IN_JSON).strip()
    if not raw:
        return None
    try:
        event = json.loads(raw)
        if not isinstance(event, dict):
            return None
    except Exception:
        return None
    event.setdefault("time", now_iso()); event.setdefault("type", "help"); event.setdefault("zone", state.get("scene", {}).get("zone", "forêt")); event.setdefault("npc_a", ""); event.setdefault("npc_b", ""); event.setdefault("severity", 5); event.setdefault("action_detail", ""); event.setdefault("witnesses", 0); event.setdefault("faction_context", ""); event.setdefault("action_target_type", ""); event.setdefault("action_target_id", ""); event.setdefault("action_target_name", ""); event.setdefault("player_id", "p1")
    event["severity"] = clamp(safe_int(event.get("severity", 5), 5), 1, 10)
    event["witnesses"] = max(0, safe_int(event.get("witnesses", 0), 0))
    out = compute_event_response(event, state, rel)
    save_world_state(state); save_relationships(rel); write_event_outputs(out)
    return out

# =========================
# Additional persistent NPC actions + menus
# =========================
def choose_persistent_npc_by_name_partial(db: dict, prompt: str = "Quel PNJ ?"):
    npcs = (db.get("npcs", {}) or {})
    if not npcs:
        return None
    q = ask(prompt + " (début/partie du nom)")
    if not q and IS_BRIDGE_MODE:
        # deterministic fallback in bridge mode
        first = sorted(npcs.values(), key=lambda n: (n.get("name", ""), n.get("id", "")))[0]
        return first
    matches = find_npc_by_name_partial(db, q, max_results=20)
    if not matches:
        return None
    return matches[0]


def generate_100_persistent_npcs():
    return _BRIDGE.generate_100_persistent_npcs()


def action_generate_100_persistent_npcs():
    ensure_folders(_BRIDGE.paths)
    seed_random()
    n = generate_100_persistent_npcs()
    print(f"✅ {n} PNJ persistants présents")


def npc_autonomous_events_tick(state: dict, rel: dict, steps: int = 1):
    db = load_npc_db()
    if not db.get("npcs"):
        return []

    state = state if isinstance(state, dict) else {}
    state.setdefault("world_flags", {})
    state["world_flags"].setdefault("rumors", {})
    zone = (state.get("scene", {}) or {}).get("zone", "forêt")

    events = []
    for _ in range(max(1, int(steps))):
        for npc in db["npcs"].values():
            if random.random() > 0.04:
                continue
            role = (npc.get("role") or "").lower()
            if "bandit" in role:
                etype, severity = pick(["crime", "trespass"]), random.randint(4, 9)
            elif "garde" in role:
                etype, severity = pick(["help", "quest_success"]), random.randint(2, 7)
            elif "marchand" in role:
                etype, severity = "trade", random.randint(1, 5)
            else:
                etype, severity = pick(["help", "trade", "trespass"]), random.randint(1, 7)
            npc_key = rel_key_for_npc(npc, npc.get("name", ""))
            events.append({
                "time": now_iso(), "type": etype, "zone": zone, "npc_a": npc_key, "npc_b": "", "severity": severity,
                "action_detail": "Événement autonome (sans joueur).", "witnesses": random.randint(0, 6),
                "faction_context": "", "action_target_type": "", "action_target_id": "", "action_target_name": "",
                "player_id": "SYSTEM", "system_mode": "npc_autonomous",
            })

    rumors = state["world_flags"]["rumors"]
    if isinstance(rumors, dict):
        for r in rumors.values():
            if isinstance(r, dict):
                r["heat"] = clamp(safe_int(r.get("heat", 0), 0) - 1, 0, 100)
    return events


def npc_alliance_tick(rel: dict, db: dict, state: dict, steps: int = 1):
    if not isinstance(rel, dict):
        return
    if not isinstance(db, dict) or not db.get("npcs"):
        return
    scene = state.get("scene", {}) if isinstance(state, dict) else {}
    zone = (scene.get("zone") or "forêt")
    npcs = list(db.get("npcs", {}).values())
    if len(npcs) < 2:
        return
    local = [n for n in npcs if (n.get("location", "") or "").lower() == str(zone).lower()]
    pool = local if len(local) >= 6 else npcs

    for _ in range(max(1, int(steps))):
        for __ in range(6):
            a, b = pick(pool), pick(pool)
            if not a or not b or a.get("id") == b.get("id"):
                continue
            a_key, b_key = rel_key_for_npc(a, a.get("name", "")), rel_key_for_npc(b, b.get("name", ""))
            if not a_key or not b_key:
                continue
            r = ensure_pair_relation(rel, a_key, b_key)
            ag, bg = " ".join(a.get("goals", [])), " ".join(b.get("goals", []))
            af = ((a.get("affinities", {}) or {}).get("factions", [""]) or [""])[0]
            bf = ((b.get("affinities", {}) or {}).get("factions", [""]) or [""])[0]
            ap = a.get("personality", {}) or {}

            delta, note = 0, ""
            if af and bf and af == bf and random.random() < 0.55:
                delta += random.randint(2, 6); note = "même faction"
            if ("protéger territoire" in ag and "protéger territoire" in bg) and random.random() < 0.35:
                delta += random.randint(2, 5); note = note or "objectif commun"
            if ("gagner richesse" in ag and "gagner richesse" in bg) and random.random() < 0.25:
                delta += random.randint(1, 4); note = note or "intérêts économiques"
            if ("bandit" in (a.get("role", "").lower())) or safe_int(ap.get("agressivite", 50), 50) > 75:
                if random.random() < 0.18:
                    delta -= random.randint(3, 10); note = "tension / trahison possible"

            if delta != 0:
                trust_after = clamp(safe_int(r.get("trust", 50), 50) + delta, 0, 100)
                new_status = "allié" if trust_after >= 80 else ("méfiant" if trust_after <= 25 else None)
                tweak_relation(rel, a_key, b_key, delta, new_status, f"alliance_tick: {note}")


def simulate_npc_life(steps: int = 1, state: dict = None):
    db = load_npc_db()
    if not db.get("npcs"):
        print("❌ Aucun PNJ persistant. Fais d'abord le menu 13.")
        return None

    if state is None or not isinstance(state, dict):
        state = load_world_state()

    locations = ["forêt", "ville", "plaine", "montagne", "désert"]
    rep_delta_total = econ_delta_total = danger_delta_total = 0

    for _ in range(max(1, int(steps))):
        for npc in db["npcs"].values():
            npc["updated_at"] = now_iso()
            if random.random() < 0.30:
                npc["location"] = pick(locations)
            if random.random() < 0.20:
                npc["emotion"] = pick(PNJ_EMOTIONS)
            if random.random() < 0.10:
                npc["goals"] = generate_goals()
            if random.random() < 0.15:
                npc["state"] = pick(["idle", "travelling", "working", "hiding", "searching", "resting"])

            g = " ".join(npc.get("goals", []))
            if "gagner richesse" in g and random.random() < 0.20:
                econ_delta_total += 1
            if "protéger territoire" in g and random.random() < 0.18:
                danger_delta_total -= 1
            if (npc.get("role") or "").lower() == "bandit":
                danger_delta_total += 1
            elif "devenir puissant" in g and random.random() < 0.15:
                danger_delta_total += 1
            if "aider autres" in g and random.random() < 0.18:
                rep_delta_total += 1

    state.setdefault("meta", {"created_at": now_iso(), "updated_at": now_iso()})
    state["meta"]["updated_at"] = now_iso()
    state.setdefault("player_meta", {})
    state.setdefault("world_flags", {})
    state.setdefault("scene", {})
    state["player_meta"].setdefault("global_reputation", 0)
    state["world_flags"].setdefault("economy_heat", 3)
    state["scene"].setdefault("danger", 4)

    state["player_meta"]["global_reputation"] = clamp(safe_int(state["player_meta"].get("global_reputation", 0), 0) + rep_delta_total, -100, 100)
    state["world_flags"]["economy_heat"] = clamp(safe_int(state["world_flags"].get("economy_heat", 3), 3) + econ_delta_total, 0, 10)
    state["scene"]["danger"] = clamp(safe_int(state["scene"].get("danger", 4), 4) + danger_delta_total, 0, 10)

    rel = load_relationships()
    auto_events = npc_autonomous_events_tick(state, rel, steps=1)
    for ev in auto_events[:10]:
        _ = compute_event_response(ev, state, rel)

    npc_alliance_tick(rel, db, state, steps=1)

    disk_db = load_npc_db(); disk_db.setdefault("npcs", {})
    for npc_id, npc_live in db.get("npcs", {}).items():
        if npc_id not in disk_db["npcs"]:
            disk_db["npcs"][npc_id] = npc_live
            continue
        dst = disk_db["npcs"][npc_id]
        for k in ["location", "emotion", "goals", "state", "updated_at"]:
            if k in npc_live:
                dst[k] = npc_live[k]

    save_npc_db(disk_db)
    save_world_state(state)
    save_relationships(rel)
    print(f"✅ Simulation PNJ faite (rep_delta={rep_delta_total}, economy_heat_delta={econ_delta_total}, danger_delta={danger_delta_total})")
    return state


def action_simulate_persistent_npcs():
    ensure_folders(_BRIDGE.paths)
    seed_random()
    simulate_npc_life(steps=1, state=load_world_state())


def action_view_npc_last_memories_for_player():
    ensure_folders(_BRIDGE.paths)
    db = load_npc_db()
    if not db.get("npcs"):
        print("❌ Aucun PNJ persistant dans la DB")
        return
    npc = choose_persistent_npc_by_name_partial(db, "Nom du PNJ")
    if not npc:
        return
    player_id = ask("player_id du joueur (ex: p1) [ENTER=p1]") or "p1"
    mems = get_npc_memories_for_player(npc, player_id)[-10:]
    print("\n=== 10 DERNIERS SOUVENIRS (PNJ -> CE JOUEUR) ===")
    print(f"PNJ: {npc.get('name')} | id={npc.get('id')}")
    print(f"Joueur: {player_id}")
    if not mems:
        print("(aucun souvenir enregistré pour ce joueur)")
        return
    for m in mems[::-1]:
        eff = m.get("effect", {}) if isinstance(m.get("effect", {}), dict) else {}
        print("\n---")
        print(f"Time: {m.get('time','')}")
        print(f"Type: {m.get('type','')} | Zone: {m.get('zone','')} | Gravité: {m.get('severity','')}/10")
        print(f"Effet: trust {eff.get('trust',0)} | fear {eff.get('fear',0)} | respect {eff.get('respect',0)}")
        print(f"Note: {m.get('note','')}")


def generate_quest_for_npc_with_social_context(state: dict, npc: dict, player_id: str, zone: str):
    state = state or {}
    npc = npc or {}
    profile_signal = 0
    op = ensure_player_opinion(npc, player_id)
    profile_signal = int((safe_int(op.get("trust", 50), 50) - 50) * 0.6 + (safe_int(op.get("respect", 50), 50) - 50) * 0.4)
    danger = clamp(safe_int((state.get("scene", {}) or {}).get("danger", 4), 4), 0, 10)

    problem = pick_unique_recent(QUEST_PROBLEMS, "quest_problems", avoid_last=8)
    objective = pick_unique_recent(QUEST_OBJECTIVES, "quest_objectives", avoid_last=8)
    complication = pick_unique_recent(QUEST_COMPLICATIONS, "quest_complications", avoid_last=8)

    if profile_signal <= -20:
        style = pick(["Le PNJ est méfiant. Il exige une preuve avant de te payer.", "On te surveille. Tu dois agir discrètement pour regagner la confiance."])
        extra = pick(["Apporte une preuve (sceau, témoin, objet).", "Accepte d’être escorté par un garde."])
        reward_hint = "Récompense: faible → moyenne (si preuve ok)."
    elif profile_signal >= 20:
        style = pick(["Le PNJ te fait confiance. Il te donne un accès spécial ou une info bonus.", "Le PNJ te paye mieux et te donne un raccourci."])
        extra = pick(["Indice bonus offert dès le début.", "Bonus de récompense si tu fais vite."])
        reward_hint = "Récompense: moyenne → haute."
    else:
        style = "Le PNJ ne te connaît pas vraiment. Mission standard."
        extra = "Conditions normales."
        reward_hint = "Récompense: normale."

    danger_line = " (Zone très dangereuse.)" if danger >= 8 else (" (Zone plutôt calme.)" if danger <= 2 else "")
    return (
        f"QUÊTE (PNJ: {npc.get('name','(sans nom)')}) — Zone: {zone}{danger_line}\n"
        f"- Contexte: {style}\n- Problème: {problem}\n- Objectif: {objective}\n"
        f"- Condition: {extra}\n- Complication: {complication}\n- {reward_hint}"
    )


def action_generate_quest_from_persistent_npc():
    ensure_folders(_BRIDGE.paths)
    state = load_world_state()
    db = load_npc_db()
    if not db.get("npcs"):
        print("❌ Aucun PNJ persistant. Fais d'abord le menu 13.")
        return
    npc = choose_persistent_npc_by_name_partial(db, "Nom du PNJ (début du nom)")
    if not npc:
        return
    player_id = (ask("ID du joueur (ex: p1) [ENTER=p1]") or "").strip() or "p1"
    if player_id.upper() == "SYSTEM":
        print("❌ SYSTEM n'est pas un joueur valide.")
        return
    default_zone = (state.get("scene", {}) or {}).get("zone", "forêt")
    zone = (ask(f"Zone [ENTER={default_zone}]") or "").strip() or default_zone
    quest = generate_quest_for_npc_with_social_context(state, npc, player_id, zone)
    timestamp = now_iso()
    block = "\n" + "=" * 60 + f"\n[{timestamp}] PNJ: {npc.get('name')} | Joueur: {player_id}\n\n" + quest + "\n" + "=" * 60 + "\n"
    existing = read_text(QUESTS_FILE)
    combined = existing + block
    sections = combined.split("=" * 60)
    if len(sections) > 40:
        sections = sections[-40:]
        combined = ("=" * 60).join(sections)
    write_text(QUESTS_FILE, combined)
    npc_id = npc.get("id")
    if npc_id:
        db.setdefault("npcs", {})
        db["npcs"][npc_id] = npc
        save_npc_db(db)
    save_world_state(state)
    print("✨ Quête influencée ajoutée dans quests.txt")


def action_view_npc_opinion():
    ensure_folders(_BRIDGE.paths)
    db = load_npc_db()
    if not db.get("npcs"):
        print("❌ Aucun PNJ persistant. Fais d'abord le menu 13.")
        return
    npc = choose_persistent_npc_by_name_partial(db, "Nom du PNJ (recherche début du nom)")
    if not npc:
        return
    player_id = (ask("player_id du joueur (ex: p1) [ENTER=p1]") or "").strip() or "p1"
    if player_id.upper() == "SYSTEM":
        print("❌ SYSTEM n'est pas un vrai joueur. Mets un id joueur (ex: p1).")
        return
    op = ensure_player_opinion(npc, player_id)
    mems = get_npc_memories_for_player(npc, player_id)
    mems = mems[-10:] if isinstance(mems, list) else []
    print("\n=== OPINION DU PNJ SUR CE JOUEUR ===")
    print(f"PNJ: {npc.get('name')} | id={npc.get('id')}")
    print(f"Joueur: {player_id}")
    print(f"Trust  : {op.get('trust', 50)}/100")
    print(f"Fear   : {op.get('fear', 0)}/100")
    print(f"Respect: {op.get('respect', 50)}/100")
    print(f"Dernière fois vu: {op.get('last_seen', '')}")
    print("\n=== 10 DERNIERS SOUVENIRS (PNJ -> ce joueur) ===")
    if not mems:
        print("(aucun souvenir enregistré pour ce joueur)")
    else:
        for m in mems[::-1]:
            eff = m.get("effect", {}) if isinstance(m.get("effect", {}), dict) else {}
            print("\n---")
            print(f"Time: {m.get('time','')}")
            print(f"Type: {m.get('type','')} | Zone: {m.get('zone','')} | Gravité: {m.get('severity','')}/10")
            print(f"Effet: trust {eff.get('trust',0)} | fear {eff.get('fear',0)} | respect {eff.get('respect',0)}")
            print(f"Note: {m.get('note','')}")
    out_file = _BRIDGE.paths.content / "npc_opinion_view.txt"
    lines = [
        "=== OPINION DU PNJ SUR CE JOUEUR ===",
        f"PNJ: {npc.get('name')} | id={npc.get('id')}",
        f"Joueur: {player_id}",
        f"Trust  : {op.get('trust', 50)}/100",
        f"Fear   : {op.get('fear', 0)}/100",
        f"Respect: {op.get('respect', 50)}/100",
        f"Dernière fois vu: {op.get('last_seen', '')}",
        "",
        "=== 10 DERNIERS SOUVENIRS (PNJ -> ce joueur) ===",
    ]
    if not mems:
        lines.append("(aucun souvenir enregistré pour ce joueur)")
    else:
        for m in mems[::-1]:
            eff = m.get("effect", {}) if isinstance(m.get("effect", {}), dict) else {}
            lines += ["---", f"Time: {m.get('time','')}", f"Type: {m.get('type','')} | Zone: {m.get('zone','')} | Gravité: {m.get('severity','')}/10", f"Effet: trust {eff.get('trust',0)} | fear {eff.get('fear',0)} | respect {eff.get('respect',0)}", f"Note: {m.get('note','')}", ""]
    write_text(out_file, "\n".join(lines))
    print(f"\n💾 Copie sauvegardée dans: {out_file}")


def action_react_event_manual():
    ensure_folders(_BRIDGE.paths)
    state = ensure_world_state_exists()
    rel = ensure_relationships_exist()
    etype = ask("Type d'événement (help/crime/kill/trade/insult/quest_success/quest_fail/trespass)")
    if etype not in EVENT_TYPES:
        print("❌ Type inconnu.")
        return
    zone = ask("Zone (ex: forêt / ville / désert)")
    npc_a = ask("Nom PNJ A (acteur PNJ) [optionnel ENTER]")
    npc_b = ask("Nom PNJ B (cible PNJ) [optionnel ENTER]")
    severity = ask("Gravité 1-10 (ENTER=5)")
    severity = int(severity) if severity.strip().isdigit() else 5
    severity = clamp(severity, 1, 10)
    action_detail = ask("Détail de l'action (ENTER = vide)")
    player_id = ask("ID du joueur (ex: p1) [ENTER=p1]") or "p1"
    event = {
        "time": now_iso(), "type": etype, "zone": zone, "npc_a": npc_a.strip(), "npc_b": npc_b.strip(), "severity": severity,
        "action_detail": action_detail.strip(), "witnesses": 0, "faction_context": "", "action_target_type": "", "action_target_id": "", "action_target_name": "", "player_id": player_id.strip(),
    }
    write_text(EVENT_IN_JSON, json.dumps(event, indent=2, ensure_ascii=False))
    out = compute_event_response(event, state, rel)
    save_world_state(state); save_relationships(rel); write_event_outputs(out)
    print("✅ event_out.json + event_out.txt générés (mode manuel).")


def export_json():
    ensure_folders(_BRIDGE.paths)
    data = {
        "meta": {"generated_at": now_iso(), "project": "LivingWorldMMO"},
        "universe": load_universe(),
        "rules_raw": load_rules_text(),
        "world_state": load_world_state(),
        "relationships": load_relationships(),
        "threads": load_threads(),
        "quests_raw": read_text(QUESTS_FILE),
        "pnj_raw": read_text(PNJ_FILE),
        "dungeon_raw": read_text(DUNGEON_FILE),
        "dialogues_raw": read_text(DIALOGUE_FILE),
        "items_raw": read_text(ITEMS_FILE),
        "animals_last_raw": read_text(ANIMALS_FILE),
        "npcs_db": load_npc_db(),
    }
    write_text(EXPORT_JSON_FILE, json.dumps(data, indent=2, ensure_ascii=False))
    print("✨ export.json créé (complet).")


def write_quests(zone: str, player_id: str = "p1"):
    quests = make_quests(zone, 5, player_id=player_id)
    write_text(QUESTS_FILE, "QUÊTES:\n" + "\n".join(f"- {q}" for q in quests))
    print("✨ Quêtes créées dans quests.txt")


def make_quests(theme: str, count: int = 5, player_id: str = "p1"):
    mods = memory_influenced_quest_modifiers(player_id=player_id, zone=theme)
    problems = list(QUEST_PROBLEMS) + list(mods.get("problem_bonus", []))
    objectives = list(QUEST_OBJECTIVES) + list(mods.get("objective_bonus", []))
    complications = list(QUEST_COMPLICATIONS) + list(mods.get("complication_bonus", []))
    quests, used = [], set()
    while len(quests) < clamp(safe_int(count, 5), 0, 50):
        p = pick_unique_recent(problems, "quests_problems", avoid_last=10)
        o = pick_unique_recent(objectives, "quests_objectives", avoid_last=10)
        c = pick_unique_recent(complications, "quests_complications", avoid_last=10)
        q = f"À {theme}, {p} : tu dois {o}, {c}."
        if q in used:
            continue
        used.add(q)
        quests.append(q)
    return quests


def memory_influenced_quest_modifiers(player_id: str, zone: str, budget_npcs: int = 200):
    if (player_id or "").strip().upper() == "SYSTEM":
        return {}
    db = load_npc_db(); npcs_map = (db.get("npcs", {}) or {})
    ids = list(npcs_map.keys())
    if len(ids) > budget_npcs:
        ids = random.sample(ids, k=budget_npcs)
    distrust = trusters = fearful = 0
    for nid in ids[: min(12, len(ids))]:
        op = (npcs_map.get(nid, {}).get("opinions", {}) or {}).get(player_id)
        if not isinstance(op, dict):
            continue
        t = clamp(safe_int(op.get("trust", 50), 50), 0, 100)
        f = clamp(safe_int(op.get("fear", 0), 0), 0, 100)
        if t < 25: distrust += 1
        if t > 70: trusters += 1
        if f > 65: fearful += 1
    mods = {}
    if distrust >= 4:
        mods["problem_bonus"] = ["on t’accuse à tort d’un crime", "un PNJ refuse de coopérer à cause de rumeurs"]
        mods["complication_bonus"] = ["mais la foule te soupçonne", "mais un témoin ment sur toi"]
    if trusters >= 4:
        mods["objective_bonus"] = ["protéger un PNJ important qui te fait confiance", "escorter quelqu’un parce que tu es le seul crédible"]
        mods["complication_bonus"] = mods.get("complication_bonus", []) + ["mais tu dois tenir ta parole"]
    if fearful >= 4:
        mods["problem_bonus"] = mods.get("problem_bonus", []) + ["la zone est paralysée par la peur"]
    return mods


def write_pnjs(zone: str, factions: list):
    pnjs = make_pnjs(zone, factions, 5)
    text = "PNJ:\n\n"
    for p in pnjs:
        text += f"Nom: {p['name']}\nCaractère: {p['character']}\nÉmotion: {p['emotion']}\nRôle: {p['role']} ({p['faction']}) de {zone}\nDialogue: {p['dialogue']}\n----------------------\n"
    write_text(PNJ_FILE, text)
    print("✨ PNJ créés dans pnj.txt")


def make_pnjs(zone: str, factions: list, count: int = 5):
    out, used = [], set()
    while len(out) < clamp(safe_int(count, 5), 0, 50):
        name = make_name_unique()
        if name in used:
            continue
        used.add(name)
        out.append({
            "name": name,
            "role": pick_unique_recent(PNJ_ROLES, "pnj_roles", avoid_last=8),
            "character": pick_unique_recent(PNJ_TRAITS, "pnj_traits", avoid_last=8),
            "emotion": pick(PNJ_EMOTIONS),
            "faction": pick(factions, "habitants") if factions else "habitants",
            "zone": zone,
            "dialogue": pick(["Je peux t’aider… mais pas gratuitement.", "La vérité est rarement jolie.", "Ne te mêle pas de ça… sauf si tu sais te battre."]),
        })
    return out


def write_dungeon(zone: str):
    write_text(DUNGEON_FILE, make_dungeon(zone))
    print("✨ Donjon créé dans dungeon.txt")


def make_dungeon(zone: str):
    return (
        f"DONJON : {pick(DUNGEON_TYPES).title()} de {zone}\n"
        f"- Entrée : un passage discret près de {zone}.\n"
        f"- Ambiance : sombre, humide, vieux symboles.\n"
        f"- Ennemis : faibles (1), moyens (2), élite (1).\n"
        f"- Mini-boss : {make_name()} (comportement adaptatif).\n"
        f"- Récompense : loot + info (histoire / réputation).\n"
        f"- Twist : {pick(DUNGEON_TWISTS)}."
    )


def make_dialogue(pnj_name: str, zone: str, player_id: str = "p1"):
    situation = pick(DIALOGUE_SITUATIONS)
    emotion = pick(PNJ_EMOTIONS)
    text = f"PNJ: {pnj_name}\n\nSituation: Dans {zone}, le PNJ {situation}.\n\n"
    base_choices = [("Je vais t'aider.", "Le PNJ te donne un indice et te teste ensuite."), ("Je veux une récompense.", "Le PNJ accepte mais te surveille."), ("Je négocie.", "Vous trouvez un compromis fragile."), ("Je refuse.", "Le PNJ se souvient et ta réputation peut baisser."), ("Je menace.", "Le PNJ se ferme et prépare un contre-coup.")]
    for i, (c, cons) in enumerate(pick_many(base_choices, random.randint(3, 5)), 1):
        text += f"Choix {i}: \"{c}\"\n→ Conséquence: {cons}\n\n"
    text += f"Emotion du PNJ: {emotion}"
    return text.strip()


def write_dialogue():
    pnj = ask("Nom du PNJ pour le dialogue")
    zone = ask("Zone (forêt, ville, désert...)")
    player_id = ask("ID du joueur [ENTER=p1]") or "p1"
    write_text(DIALOGUE_FILE, make_dialogue(pnj, zone, player_id))
    print("✨ Dialogue créé dans dialogues.txt")


def make_items(zone: str, count: int = 10):
    out, used = [], set()
    while len(out) < clamp(safe_int(count, 10), 0, 200):
        key = (f"{pick(ITEM_BASE)} en {pick(ITEM_MATERIAL)}", pick(RARITIES), pick(ITEM_EFFECTS), pick([f"Monstres près de {zone}", f"Donjon de {zone}", f"Quête PNJ dans {zone}"]))
        if key in used:
            continue
        used.add(key)
        out.append({"name": key[0], "rarity": key[1], "effect": key[2], "source": key[3]})
    return out


def write_items(zone: str):
    items = make_items(zone, 10)
    text = "OBJETS & LOOT:\n\n"
    for i, it in enumerate(items, 1):
        text += f"{i}) {it['name']}\n   - Rareté: {it['rarity']}\n   - Effet: {it['effect']}\n   - Où ça tombe: {it['source']}\n----------------------\n"
    write_text(ITEMS_FILE, text)
    print("✨ Items créés dans items.txt")


ANIMAL_SPECIES = [("Loup", "predateur"), ("Cerf", "proie"), ("Sanglier", "omnivore"), ("Aigle", "predateur"), ("Renard", "omnivore"), ("Ours", "predateur")]
ANIMAL_HABITATS = ["forêts", "collines", "rivières", "falaises", "plaines", "marécages", "ruines", "grottes"]
ANIMAL_TEMPER = ["craintif", "territorial", "prudent", "agressif si menacé", "curieux", "calme"]
ANIMAL_BEHAV = ["chasser", "fuir", "observer", "protéger le groupe", "attaquer si provocation", "se cacher"]


def make_animals(zone: str, count: int = 5):
    out, used = [], set()
    while len(out) < clamp(safe_int(count, 5), 0, 80):
        species, typ = pick(ANIMAL_SPECIES)
        habitat = f"{pick(ANIMAL_HABITATS)} autour de {zone}"
        temper = pick(ANIMAL_TEMPER)
        behaviors = pick_many(ANIMAL_BEHAV, 3)
        aggression, fear = random.randint(0, 10), random.randint(0, 10)
        emotions = (["peur"] if fear >= 7 else []) + (["colère"] if aggression >= 7 else []) + ["faim"]
        if random.random() < 0.4:
            emotions.append("curiosité")
        emotions = list(dict.fromkeys(emotions))
        key = (species, habitat, temper, aggression, fear)
        if key in used:
            continue
        used.add(key)
        out.append({"species": species, "type": typ, "habitat": habitat, "temperament": temper, "emotions": emotions, "behaviors": behaviors, "aggression": aggression, "fear": fear})
    return out


def animals_to_text(animals: list) -> str:
    text = "ANIMAUX:\n\n"
    for a in (animals or []):
        if not isinstance(a, dict):
            continue
        text += f"Espèce: {a.get('species','')}\nType: {a.get('type','')}\nHabitat: {a.get('habitat','')}\nTempérament: {a.get('temperament','')}\nÉmotions: {', '.join(a.get('emotions', []) or [])}\nComportements: {', '.join(a.get('behaviors', []) or [])}\nAgressivité (0-10): {a.get('aggression','')}\nPeur (0-10): {a.get('fear','')}\n----------------------\n"
    return text


def load_animals_json():
    data = load_json_file(ANIMALS_JSON_FILE, lambda: [], repair_fn=None)
    return data if isinstance(data, list) else []


def save_animals_json(data: list):
    save_json_file(ANIMALS_JSON_FILE, data if isinstance(data, list) else [])


def write_animals(zone: str):
    animals = make_animals(zone, 5)
    write_text(ANIMALS_FILE, animals_to_text(animals))
    current = load_animals_json()
    current.append({"created_at": now_iso(), "zone": zone, "animals": animals})
    save_animals_json(current)
    print("✨ Animaux créés dans animals.txt et ajoutés dans animals.json")


def main():
    ensure_folders(_BRIDGE.paths)
    seed_random()
    _ = load_universe()
    ensure_world_state_exists()
    ensure_relationships_exist()

    print("✅ Eli est en ligne (PNJ vivants, joueurs RÉELS dans Unreal)")
    print("📌 universe.json:", "OK")
    print("📌 rules.txt:", "OK" if _BRIDGE.paths.rules_file.exists() else "optionnel (absent)")
    print("📌 world_state.json:", "OK")
    print("📌 relationships.json:", "OK")
    print("📌 npcs_db.json:", "OK" if _BRIDGE.paths.npc_db.exists() else "absent (tu peux générer via menu 13)")

    while True:
        print("\n=== MENU ===")
        print("1) Pack complet (Quêtes + PNJ + Donjon)")
        print("2) Quêtes (différent à chaque fois)")
        print("3) PNJ (différent à chaque fois)")
        print("4) Donjon (différent à chaque fois)")
        print("5) Dialogue interactif (différent à chaque fois)")
        print("6) Objets & Loot (différent à chaque fois)")
        print("7) Animaux (différent à chaque fois)")
        print("8) Export JSON (export.json)")
        print("9) Générer une scène vivante (next_scene + scene_unreal.json)")
        print("10) Réagir à un événement joueur (manuel)")
        print("11) Réagir à un événement joueur (AUTO Unreal: lit event_in.json)")
        print("12) Réglages du monde (zone/theme/temps/météo/danger)")
        print("13) Générer 100 PNJ persistants (npcs_db.json)")
        print("14) Simuler la vie des PNJ persistants (hors écran)")
        print("15) Voir opinion d’un PNJ sur un joueur (recherche partielle + 10 souvenirs)")
        print("16) Voir les 10 derniers souvenirs (PNJ -> ce joueur uniquement)")
        print("17) Générer une quête (PNJ persistant + rumeurs + souvenirs)")
        print("0) Quitter")

        choice = ask("Choisis un numéro").strip()
        state = load_world_state()
        zone = (state.get("scene", {}) or {}).get("zone", "forêt")
        factions = (state.get("world_flags", {}) or {}).get("factions", ["habitants", "gardes", "chasseurs", "bandits"])

        if choice == "1":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            player_id = ask_player_id("p1")
            if ask_yes_no("Je crée le pack complet. Tu veux ?"):
                write_quests(z, player_id=player_id); write_pnjs(z, factions); write_dungeon(z)
        elif choice == "2":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            player_id = ask_player_id("p1")
            if ask_yes_no("Je crée 5 quêtes. Tu veux ?"):
                write_quests(z, player_id=player_id)
        elif choice == "3":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            if ask_yes_no("Je crée 5 PNJ. Tu veux ?"):
                write_pnjs(z, factions)
        elif choice == "4":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            if ask_yes_no("Je crée 1 donjon. Tu veux ?"):
                write_dungeon(z)
        elif choice == "5":
            if ask_yes_no("Je crée 1 dialogue. Tu veux ?"):
                write_dialogue()
        elif choice == "6":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            if ask_yes_no("Je crée 10 items. Tu veux ?"):
                write_items(z)
        elif choice == "7":
            z = ask(f"Zone [ENTER={zone}]").strip() or zone
            if ask_yes_no("Je crée 5 animaux. Tu veux ?"):
                write_animals(z)
        elif choice == "8":
            if ask_yes_no("Je génère export.json. Tu veux ?"):
                export_json()
        elif choice == "9":
            action_next_scene()
        elif choice == "10":
            action_react_event_manual()
        elif choice == "11":
            action_react_event_auto()
        elif choice == "12":
            # minimal world settings behavior to keep compatibility
            st = load_world_state(); sc = st.setdefault("scene", {})
            z = ask(f"Nouvelle zone [ENTER={sc.get('zone','forêt')}]")
            if z.strip():
                sc["zone"] = z.strip()
            zt = ask(f"Nouveau zone_theme [ENTER={sc.get('zone_theme','medieval_fantasy')}]")
            if zt.strip():
                sc["zone_theme"] = zt.strip(); sc["weather"] = pick_weather_for_theme(sc.get("zone_theme", "medieval_fantasy"))
            t = ask(f"Temps (jour/nuit) [ENTER={sc.get('time','jour')}]")
            if t.strip() in ["jour", "nuit"]:
                sc["time"] = t.strip()
            d = ask(f"Danger 0-10 [ENTER={sc.get('danger',4)}]")
            if d.strip().isdigit():
                sc["danger"] = clamp(int(d.strip()), 0, 10)
            save_world_state(st)
            print("💾 world_state.json sauvegardé.")
        elif choice == "13":
            if ask_yes_no("Je génère 100 PNJ persistants. Tu veux ?"):
                action_generate_100_persistent_npcs()
        elif choice == "14":
            if ask_yes_no("Je simule la vie des PNJ persistants. Tu veux ?"):
                s = ask("Combien de ticks ? (ENTER=1)")
                steps = int(s) if s.strip().isdigit() else 1
                simulate_npc_life(steps=clamp(steps, 1, 50), state=load_world_state())
        elif choice == "15":
            action_view_npc_opinion()
        elif choice == "16":
            action_view_npc_last_memories_for_player()
        elif choice == "17":
            if ask_yes_no("Je génère une quête influencée par PNJ + rumeurs. Tu veux ?"):
                action_generate_quest_from_persistent_npc()
        elif choice == "0":
            print("👋 Bye !")
            break
        else:
            print("❌ Choix invalide.")


if __name__ == "__main__":
    # Bridge mode keeps non-interactive behavior.
    if IS_BRIDGE_MODE:
        bridge = EliBridge()
        result = bridge.process_event_in()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        main()
