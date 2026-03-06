#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import logging
import math
import random
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_SECONDS = 300
TTL_ZONE_H = 72
TTL_POI_H = 168
TTL_GLOBAL_H = 24


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def unix_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _h64(*parts: Any) -> int:
    h = hashlib.blake2b(digest_size=8)
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"|")
    return int.from_bytes(h.digest(), "big", signed=False)


def MakeSeedContext(req: dict, director_state: dict) -> dict:
    world_seed = str(director_state.get("world_seed", "0x0"))
    now = unix_ts()
    slot = now // SLOT_SECONDS
    request_hash = hex(_h64(json.dumps(req, sort_keys=True, ensure_ascii=False)))[2:]
    seed64 = _h64(world_seed, request_hash, slot, req.get("zone_id", ""), req.get("poi_id", ""))
    return {
        "world_seed": world_seed,
        "request_hash": request_hash,
        "seed_epoch_slot": slot,
        "seed": seed64,
    }


def _rng(seed_context: dict) -> random.Random:
    return random.Random(seed_context["seed"])


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict) -> bool:
    try:
        data["updated_ts"] = utc_now_iso()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except OSError as e:
        logging.getLogger("mle").error(f"_save_json failed {path}: {e}")
        return False
def _save_json(path: Path, data: dict) -> None:
    data["updated_ts"] = utc_now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@dataclass
class LWContext:
    constraints: dict
    budgets: dict
    zone_states: dict
    economy_state: dict
    guild_state: dict
    territory_state: dict
    dungeon_state: dict
    rumor_feed: dict
    director_state: dict


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _lw() -> Path:
    return _root() / "Data" / "LivingWorld"


def _lm() -> Path:
    return _root() / "Data" / "LivingMytho"


def _archives() -> Path:
    return _root() / "Data" / "Archives"


def LoadContext(zone_id: str) -> LWContext:
    lw = _lw()
    return LWContext(
        constraints=_load_json(lw / "world_constraints.json"),
        budgets=_load_json(lw / "spawn_budget.json"),
        zone_states=_load_json(lw / "zone_states_latest.json"),
        economy_state=_load_json(lw / "economy_state.json"),
        guild_state=_load_json(lw / "guild_state.json"),
        territory_state=_load_json(lw / "territory_state.json"),
        dungeon_state=_load_json(lw / "dungeon_state.json"),
        rumor_feed=_load_json(lw / "rumor_feed.json"),
        director_state=_load_json(lw / "director_state.json"),
    )


def ValidateSchemas() -> dict:
    required = [
        _lm() / "taxonomy_tags.json",
        _lm() / "mytho_atoms.json",
        _lm() / "inworld_mythologies.json",
        _lm() / "creature_blueprints.json",
        _lm() / "loot_tables.json",
        _lm() / "runtime_guards.json",
        _lm() / "ingestion_sources.json",
        _lw() / "world_constraints.json",
        _lw() / "spawn_budget.json",
        _lw() / "director_state.json",
        _lw() / "zone_states_latest.json",
        _lw() / "economy_state.json",
        _lw() / "guild_state.json",
        _lw() / "territory_state.json",
        _lw() / "dungeon_state.json",
        _lw() / "rumor_feed.json",
        _archives() / "grayscale_asset_manifest.json",
        _archives() / "archives_index.json",
    ]
    checks = {}
    passed = True
    for f in required:
        ok = f.exists()
        if ok:
            data = _load_json(f)
            ok = isinstance(data.get("schema_version"), int) and bool(data.get("world_id")) and bool(data.get("updated_ts"))
        checks[str(f.relative_to(_root()))] = ok
        passed = passed and ok
    return {"passed": passed, "checks": checks}


def BuildWorldSignals(zone_id: str, poi_id: str | None, telemetry: dict) -> dict:
    t = telemetry or {}
    return {
        "hunts_level": float(t.get("hunts_level", 0.0)),
        "deaths_level": float(t.get("deaths_level", 0.0)),
        "noise_level": float(t.get("noise_level", 0.0)),
        "scarcity_level": float(t.get("scarcity_level", 0.0)),
        "conflict_level": float(t.get("conflict_level", 0.0)),
        "crime_level": float(t.get("crime_level", 0.0)),
        "players_recent_count": int(t.get("players_recent_count", 0)),
        "guilds_recent_count": int(t.get("guilds_recent_count", 0)),
        "dungeon_contest_state": str(t.get("dungeon_contest_state", "idle")),
        "weather": str(t.get("weather", "clair")),
        "time": str(t.get("time", "jour")),
        "zone_level": int(t.get("zone_level", 1)),
        "town_distance_m": float(t.get("town_distance_m", 9999)),
        "poi_tags": list(t.get("poi_tags", [])),
    }


def _bucket_consume(bucket: dict, amount: float, refill_per_min: float, cap: float, now_ts: int) -> bool:
    last = int(bucket.get("_last_refill", now_ts))
    mins = max(0.0, (now_ts - last) / 60.0)
    tokens = min(cap, float(bucket.get("tokens", cap)) + mins * refill_per_min)
    ok = tokens >= amount
    if ok:
        tokens -= amount
    bucket["tokens"] = tokens
    bucket["_last_refill"] = now_ts
    return ok


def TokenBucketConsume(ctx: LWContext, req: dict, now_ts: int) -> tuple[bool, dict]:
    anti = ctx.director_state.setdefault("director", {}).setdefault("global_anti_spam", {})
    g = anti.setdefault("token_bucket", {"capacity": 30, "refill_per_min": 6, "tokens": 30})
    l = anti.setdefault("legendary_bucket", {"capacity": 3, "refill_per_hour": 0.5, "tokens": 3})
    rarity = req.get("rarity_hint", "common")
    g_ok = _bucket_consume(g, 1, float(g.get("refill_per_min", 6)), float(g.get("capacity", 30)), now_ts)
    l_ok = True
    if rarity in ("legendary", "worldboss"):
        l_ok = _bucket_consume(l, 1, float(l.get("refill_per_hour", 0.5)) / 60.0, float(l.get("capacity", 3)), now_ts)
    return g_ok and l_ok, {"global": g_ok, "legendary": l_ok}


def CheckProgression(ctx: LWContext, req: dict) -> tuple[bool, dict]:
    signals = req.get("world_signals", {})
    zone_level = int(signals.get("zone_level", 1))
    rarity = req.get("rarity_hint", "common")
    ranges = ctx.constraints.get("progression_rules", {}).get("zone_level_ranges", [])
    for r in ranges:
        if r.get("min", 1) <= zone_level <= r.get("max", 1):
            return rarity in r.get("rarity_caps", []), {"zone_level": zone_level, "allowed": r.get("rarity_caps", [])}
    return True, {"zone_level": zone_level, "allowed": "any"}


def ZoneBudgetAllows(ctx: LWContext, req: dict) -> tuple[bool, dict]:
    zone_id = req.get("zone_id", "default_zone")
    rarity = req.get("rarity_hint", "common")
    z = ctx.budgets.get("zones", {}).get(zone_id, {})
    budget = z.get("budget", {})
    current = z.get("current", {})
    cap = int(budget.get(rarity, 0))
    used = int(current.get(rarity, 0))
    return used < cap, {"used": used, "cap": cap, "rarity": rarity}


def SanitizeTextOrRewrite(text: str, runtime_guards: dict, rng: random.Random, zone_id: str = "zone", poi_id: str = "poi") -> str:
    out = str(text or "")
    for term in runtime_guards.get("banned_terms", []):
        if term.lower() in out.lower():
            tpl = rng.choice(runtime_guards.get("safe_templates", {}).get("rumor_templates", ["Un murmure trouble traverse {zone}."]))
            return tpl.format(zone=zone_id, poi=poi_id, theme="mystère")
    for pat in runtime_guards.get("fingerprints", []):
        if re.search(pat, out, flags=re.IGNORECASE):
            tpl = rng.choice(runtime_guards.get("safe_templates", {}).get("entity_name_templates", ["Écho de {zone}"]))
            return tpl.format(zone=zone_id, poi=poi_id, theme="mystère")
    return out


def _rarity_weights(signals: dict) -> dict:
    pressure = float(signals.get("conflict_level", 0.0) + signals.get("scarcity_level", 0.0))
    return {
        "common": 1.0,
        "elite": 0.6 + pressure * 0.2,
        "rare": 0.2 + pressure * 0.2,
        "legendary": max(0.01, pressure * 0.06),
    }


def _pick_weighted(rng: random.Random, weights: dict) -> str:
    items = [(k, max(0.0, float(v))) for k, v in weights.items()]
    total = sum(v for _, v in items)
    if total <= 0:
        return items[0][0]
    x = rng.random() * total
    acc = 0.0
    for k, v in items:
        acc += v
        if x <= acc:
            return k
    return items[-1][0]


def _uniq_hash(entity: dict, zone_id: str, seed_slot: int) -> str:
    h = _h64(entity.get("form_id", ""), sorted(entity.get("power_ids", [])), sorted(entity.get("motif_ids", [])), entity.get("theme_id", ""), zone_id, entity.get("rarity", "common"), seed_slot)
    return f"0x{h:016x}"


def _memory_recent_contains(ctx: LWContext, uniq: str, scope: str, now_ts: int) -> bool:
    mem = ctx.director_state.setdefault("selection_memory", {}).setdefault("recent_uniqueness_hashes", [])
    ttl = TTL_GLOBAL_H if scope == "global" else (TTL_POI_H if scope == "poi" else TTL_ZONE_H)
    fresh = []
    found = False
    for e in mem:
        if now_ts - int(e.get("ts", 0)) <= ttl * 3600:
            fresh.append(e)
            if e.get("hash") == uniq and e.get("scope") == scope:
                found = True
    ctx.director_state["selection_memory"]["recent_uniqueness_hashes"] = fresh
    return found


def RegisterUniqueness(ctx: LWContext, uniq: str, scope: str, now_ts: int) -> None:
    mem = ctx.director_state.setdefault("selection_memory", {}).setdefault("recent_uniqueness_hashes", [])
    mem.append({"hash": uniq, "scope": scope, "ts": now_ts})


def MLE_Generate(ctx: LWContext, req: dict, rng: random.Random) -> dict:
    atoms = _load_json(_lm() / "mytho_atoms.json")
    mythologies = _load_json(_lm() / "inworld_mythologies.json").get("mythologies", [])
    blueprints = _load_json(_lm() / "creature_blueprints.json").get("blueprints", [])
    zone_id = req.get("zone_id", "default_zone")
    signals = req.get("world_signals", {})

    pressure = ctx.zone_states.get("zone_states", {}).get(zone_id, {}).get("myth_pressure", {})
    myth_weights = {m["id"]: float(pressure.get(m["id"], 0.1)) for m in mythologies}
    chosen_myth_id = _pick_weighted(rng, myth_weights or {"none": 1.0})
    chosen_myth = next((m for m in mythologies if m.get("id") == chosen_myth_id), mythologies[0] if mythologies else {"id": "none"})

    requested = req.get("rarity_hint")
    rarity = requested or _pick_weighted(rng, _rarity_weights(signals))
    bp = next((b for b in blueprints if b.get("rarity") == rarity), blueprints[0] if blueprints else {})

    rerolls = 0
    entity = {}
    seed_slot = int(req["seed_context"]["seed_epoch_slot"])
    for attempt in range(8):
        rerolls = attempt
        form = rng.choice(atoms.get("forms", [])) if atoms.get("forms") else {}
        powers = atoms.get("powers", [])
        motifs = atoms.get("motifs", [])
        themes = atoms.get("themes", [])
        weaknesses = atoms.get("weaknesses", [])
        entity = {
            "entity_id": f"ent_{_h64(zone_id, req.get('request_id', ''), attempt):016x}",
            "rarity": rarity,
            "form_id": form.get("id", "unknown"),
            "power_ids": [p.get("id") for p in powers[: int(bp.get("pick_counts", {}).get("powers", 1))]],
            "motif_ids": [m.get("id") for m in motifs[: int(bp.get("pick_counts", {}).get("motifs", 1))]],
            "theme_id": (themes[0].get("id") if themes else "none"),
            "weakness_ids": [w.get("id") for w in weaknesses[:1]],
            "mythology_id": chosen_myth.get("id", "none"),
            "behavior_profile": bp.get("behavior_profile", {}),
            "spawn_profile": bp.get("spawn_profile", {}),
            "balance_multipliers": bp.get("balance_multipliers", {}),
        }
        uniq = _uniq_hash(entity, zone_id, seed_slot)
        scope = "poi" if req.get("poi_id") else "zone"
        if not _memory_recent_contains(ctx, uniq, scope, unix_ts()):
            entity["uniqueness_hash"] = uniq
            RegisterUniqueness(ctx, uniq, scope, unix_ts())
            break
    return {
        "spawn_payload": entity,
        "chosen": {"mythology_id": chosen_myth.get("id", "none"), "blueprint_id": bp.get("id", "none")},
        "rerolls_count": rerolls,
        "constraints_failed": [],
    }


def MLE_GenerateDungeonBoss(ctx: LWContext, req: dict, dungeon_state: dict, rng: random.Random) -> dict:
    out = MLE_Generate(ctx, req, rng)
    sc = req.get("boss_theme_constraints", {})
    forbidden = set(sc.get("forbidden_power_tags_any", []))
    if forbidden:
        out["constraints_failed"].append("forbidden_power_tags_not_implemented_in_mvp")
    out["spawn_payload"]["boss"] = True
    return out


def Ecosystem_TickSlow(zone_state: dict, now_ts: int) -> dict:
    pops = zone_state.setdefault("ecology_populations", {})
    deltas = {}
    for species, payload in pops.items():
        count = int(payload.get("count", 0))
        cap = max(1, int(count * 1.25 + 20))
        growth = int(0.08 * count * (1.0 - count / cap))
        new_count = max(0, count + growth)
        payload["count"] = new_count
        payload["trend"] = "up" if growth > 0 else ("down" if growth < 0 else "stable")
        deltas[species] = growth
    return {"population_deltas": deltas}


def Ecosystem_Adjust(ctx: LWContext, req: dict, rng: random.Random) -> dict:
    signals = req.get("world_signals", {})
    hooks = []
    if float(signals.get("hunts_level", 0)) > 0.7 and float(signals.get("scarcity_level", 0)) > 0.6:
        hooks.append({"type": "migration_event", "zone_id": req.get("zone_id")})
    return {"memory_hooks": hooks, "economy_modifiers": {"price_mul_delta": 0.02 * len(hooks)}, "spawn_request": None}


def Politics_Trigger(ctx: LWContext, req: dict, rng: random.Random) -> dict:
    s = req.get("world_signals", {})
    if float(s.get("conflict_level", 0.0)) + float(s.get("crime_level", 0.0)) > 1.2:
        return {"event": "embargo", "severity": 0.6}
    return {"event": "none", "severity": 0.0}


def Karma_Update(event: dict) -> dict:
    kind = event.get("type", "")
    delta = -2 if kind in ("crime", "kill") else (1 if kind in ("help", "quest_success") else 0)
    return {"karma_local_delta": delta, "karma_global_delta": math.copysign(max(0, abs(delta) // 2), delta), "myth_pressure_delta": 0.05 * max(0, -delta)}


def Dungeon_ContestOrBoss(ctx: LWContext, req: dict, rng: random.Random) -> dict:
    dstate = ctx.dungeon_state.setdefault("dungeons", {})
    dungeon_id = req.get("dungeon_id", "ruins_01")
    d = dstate.setdefault(dungeon_id, {"owner": "neutral", "taxes": {"entry_fee": 0}, "contest_window": {"start_ts": "", "end_ts": ""}, "myth_influence": {}})
    if req.get("request_type") == "dungeon_boss":
        return MLE_GenerateDungeonBoss(ctx, req, d, rng)
    d["contest_window"] = {"start_ts": utc_now_iso(), "end_ts": utc_now_iso()}
    return {"contest_started": True, "dungeon_id": dungeon_id}


def Memory_RecordEvent(event: dict) -> dict:
    zone_id = event.get("zone_id", "default_zone")
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    base = _lw() / "journals" / zone_id
    base.mkdir(parents=True, exist_ok=True)
    events = base / f"{month}.events.jsonl"
    audit = base / f"{month}.audit.jsonl"
    with open(events, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    with open(audit, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": utc_now_iso(),
                    "kind": "record",
                    "event_id": event.get("request_id"),
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    return {"events_file": str(events.relative_to(_root())), "audit_file": str(audit.relative_to(_root()))}
    events.write_text((events.read_text(encoding="utf-8") if events.exists() else "") + json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8")
    audit.write_text((audit.read_text(encoding="utf-8") if audit.exists() else "") + json.dumps({"ts": utc_now_iso(), "kind": "record", "event_id": event.get("request_id")}, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"events_file": str(events.relative_to(_root())), "audit_file": str(audit.relative_to(_root()))}


def Rumor_Publish(hook: dict) -> dict:
    feed = _load_json(_lw() / "rumor_feed.json")
    feed.setdefault("rumors", [])
    runtime_guards = _load_json(_lm() / "runtime_guards.json")
    seed = _h64(hook.get("text", ""), hook.get("zone_id", ""), hook.get("poi_id", ""))
    rng = random.Random(seed)
    text = SanitizeTextOrRewrite(hook.get("text", ""), runtime_guards, rng, hook.get("zone_id", "zone"), hook.get("poi_id", "poi"))
    text_hash = hex(_h64(text))[2:]
    if any(r.get("_hash") == text_hash for r in feed["rumors"]):
        return {"published": False, "reason": "dedupe"}
    rid = f"rumor_{_h64(text, unix_ts()):016x}"
    rumor = {
        "id": rid,
        "zone_id": hook.get("zone_id", "default_zone"),
        "poi_id": hook.get("poi_id", ""),
        "text": text,
        "hint_level": int(hook.get("hint_level", 1)),
        "expires_ts": hook.get("expires_ts", utc_now_iso()),
        "source_type": hook.get("source_type", "system"),
        "_hash": text_hash,
    }
    feed["rumors"].append(rumor)
    _save_json(_lw() / "rumor_feed.json", feed)
    rumor.pop("_hash", None)
    return {"published": True, "rumor": rumor}


def Archives_CreateEntry(event: dict, grayscale_manifest: dict) -> dict:
    idx = _load_json(_archives() / "archives_index.json")
    idx.setdefault("entries", [])
    atlases = grayscale_manifest.get("atlases", [])
    atlas = atlases[0]["atlas_id"] if atlases else "atlas_gray_01"
    entry = {
        "id": f"arc_{_h64(event.get('request_id',''), unix_ts()):016x}",
        "event_id": event.get("request_id", ""),
        "atlas_id": atlas,
        "overlay": {"zone_id": event.get("zone_id", "default_zone"), "stamp": utc_now_iso()},
    }
    idx["entries"].append(entry)
    _save_json(_archives() / "archives_index.json", idx)
    return entry


def _choose_system(req: dict, rng: random.Random) -> tuple[str, dict]:
    s = req.get("world_signals", {})
    weights = {
        "MLE": 0.7 + float(s.get("conflict_level", 0)),
        "Ecosystem": 0.4 + float(s.get("hunts_level", 0)),
        "Politics": 0.3 + float(s.get("crime_level", 0)),
        "Dungeon": 0.2 + (0.6 if req.get("request_type") == "dungeon_boss" else 0.0),
        "NoOp": 0.1,
    }
    return _pick_weighted(rng, weights), weights


def _apply_deltas(ctx: LWContext, req: dict, deltas: dict) -> None:
    zone_id = req.get("zone_id", "default_zone")
    rarity = req.get("rarity_hint", "common")
    z = ctx.budgets.setdefault("zones", {}).setdefault(zone_id, {"budget": {}, "current": {}})
    z.setdefault("current", {}).setdefault(rarity, 0)
    z["current"][rarity] += int(deltas.get("budget_deltas", {}).get("spawn", 0))


def _persist_ctx(ctx: LWContext):
    _save_json(_lw() / "director_state.json", ctx.director_state)
    _save_json(_lw() / "spawn_budget.json", ctx.budgets)
    _save_json(_lw() / "zone_states_latest.json", ctx.zone_states)
    _save_json(_lw() / "dungeon_state.json", ctx.dungeon_state)


def Director_HandleRequest(req_json: dict) -> dict:
    req = dict(req_json or {})
    zone_id = req.get("zone_id", "default_zone")
    ctx = LoadContext(zone_id)

    seed_context = MakeSeedContext(req, ctx.director_state)
    req["seed_context"] = seed_context
    rng = _rng(seed_context)

    if "world_signals" not in req:
        req["world_signals"] = BuildWorldSignals(zone_id, req.get("poi_id"), req.get("telemetry", {}))

    prog_ok, prog_data = CheckProgression(ctx, req)
    bucket_ok, bucket_data = TokenBucketConsume(ctx, req, unix_ts())
    budget_ok, budget_data = ZoneBudgetAllows(ctx, req)

    checks = {"progression": prog_ok, "token_buckets": bucket_ok, "zone_budget": budget_ok}
    constraints_failed = [k for k, v in checks.items() if not v]

    chosen_system, weights = _choose_system(req, rng)
    memory_hooks: list[dict] = []
    rumor_hooks: list[dict] = []
    spawn_payload = None
    deltas = {"budget_deltas": {}, "pressure_deltas": {}, "economy_deltas": {}, "territory_deltas": {}, "dungeon_deltas": {}}
    chosen_meta = {"system": chosen_system, "mythology_id": None, "blueprint_id": None}
    rerolls_count = 0

    if constraints_failed:
        chosen_system = "NoOp"
    elif chosen_system == "MLE":
        gen = MLE_Generate(ctx, req, rng)
        spawn_payload = gen["spawn_payload"]
        chosen_meta.update(gen["chosen"])
        rerolls_count = gen["rerolls_count"]
        deltas["budget_deltas"] = {"spawn": 1}
        rumor_hooks.append({"zone_id": zone_id, "poi_id": req.get("poi_id", ""), "text": f"Une créature {spawn_payload.get('rarity')} rôde.", "hint_level": 1, "source_type": "director"})
    elif chosen_system == "Ecosystem":
        st = ctx.zone_states.setdefault("zone_states", {}).setdefault(zone_id, {})
        eco = Ecosystem_TickSlow(st, unix_ts())
        memory_hooks.append({"type": "ecosystem_tick", **eco})
    elif chosen_system == "Politics":
        ev = Politics_Trigger(ctx, req, rng)
        memory_hooks.append({"type": "politics", **ev})
    elif chosen_system == "Dungeon":
        d = Dungeon_ContestOrBoss(ctx, req, rng)
        memory_hooks.append({"type": "dungeon", **d})

    uniqueness_hash = spawn_payload.get("uniqueness_hash") if isinstance(spawn_payload, dict) else f"0x{_h64(seed_context['seed']):016x}"
    response = {
        "response_type": "director_response",
        "request_id": req.get("request_id", f"req_{seed_context['request_hash'][:12]}"),
        "seed_context": seed_context,
        "picked_system": chosen_system,
        "validation": {
            "passed": len(constraints_failed) == 0,
            "checks": {**checks, "progression_detail": prog_data, "bucket_detail": bucket_data, "budget_detail": budget_data},
            "uniqueness_hash": uniqueness_hash,
        },
        "why_log": {
            "weights": weights,
            "chosen": chosen_meta,
            "budgets_before_after": {"zone_budget": budget_data},
            "constraints_failed": constraints_failed,
            "rerolls_count": rerolls_count,
        },
        "memory_hooks": memory_hooks,
        "rumor_hooks": rumor_hooks,
        "spawn_payload": spawn_payload,
        "deltas": deltas,
    }

    for hook in rumor_hooks:
        Rumor_Publish(hook)
    _apply_deltas(ctx, req, deltas)
    Memory_RecordEvent({**response, "zone_id": zone_id})
    _persist_ctx(ctx)
    return response


def Director_TickSlow(now_ts: int) -> dict:
    now_ts = int(now_ts)
    ctx = LoadContext("default_zone")
    zones = ctx.director_state.setdefault("zone_metrics", {})
    for z, m in zones.items():
        for key in ["activity_score_ema", "death_rate_ema", "noise_score_ema", "economy_scarcity_ema", "conflict_score_ema", "crime_score_ema"]:
            m[key] = max(0.0, min(1.0, float(m.get(key, 0.0)) * 0.98))
        zstate = ctx.zone_states.setdefault("zone_states", {}).setdefault(z, {})
        pressure = zstate.setdefault("myth_pressure", {})
        for myth_id, value in list(pressure.items()):
            pressure[myth_id] = max(0.0, float(value) - 0.01)
    anti = ctx.director_state.setdefault("director", {}).setdefault("global_anti_spam", {})
    g = anti.setdefault(
        "token_bucket",
        {"capacity": 30, "tokens": 30, "refill_per_min": 6},
    )
    last = int(g.get("_last_refill", now_ts))
    mins = max(0.0, (now_ts - last) / 60.0)
    g["tokens"] = min(
        float(g.get("capacity", 30)),
        float(g.get("tokens", 0)) + mins * float(g.get("refill_per_min", 6)),
    )
    g["_last_refill"] = now_ts


    # refill buckets and expire rumors
    _ = TokenBucketConsume(ctx, {"rarity_hint": "common"}, now_ts)  # refill only side effect with amount=1 is not ideal
    # compensate consumption for maintenance tick
    anti = ctx.director_state.setdefault("director", {}).setdefault("global_anti_spam", {})
    anti.setdefault("token_bucket", {}).setdefault("tokens", 0)
    anti["token_bucket"]["tokens"] = min(float(anti["token_bucket"].get("capacity", 30)), float(anti["token_bucket"].get("tokens", 0)) + 1)

    feed = ctx.rumor_feed
    fresh = []
    for r in feed.get("rumors", []):
        exp = r.get("expires_ts") or utc_now_iso()
        try:
            exp_ts = int(datetime.fromisoformat(exp.replace("Z", "+00:00")).timestamp())
        except Exception:
            exp_ts = now_ts + 3600
        if exp_ts >= now_ts:
            fresh.append(r)
    feed["rumors"] = fresh
    _save_json(_lw() / "rumor_feed.json", feed)

    ctx.director_state.setdefault("director", {})["last_tick_ts"] = utc_now_iso()
    _persist_ctx(ctx)
    return {"tick_ts": now_ts, "zones_updated": len(zones), "rumors_active": len(fresh)}


if __name__ == "__main__":
    print(json.dumps(ValidateSchemas(), indent=2, ensure_ascii=False))
