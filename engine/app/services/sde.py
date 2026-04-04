from __future__ import annotations

import bz2
import os
import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests

SDE_BZ2_URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2"
DEFAULT_SDE_PATH = "/data/sde.db"

WEAPON_GROUP_IDS: set[int] = set()


def _resolve_sde_path() -> Path:
    return Path(os.getenv("SDE_PATH", DEFAULT_SDE_PATH))


def _resolve_version_path() -> Path:
    override = os.getenv("SDE_VERSION_PATH")
    if override:
        return Path(override)
    return _resolve_sde_path().with_name("sde_version.txt")


def download_sde(
    target_path: Path | None = None,
    version_path: Path | None = None,
    timeout_seconds: int = 1800,
) -> Path:
    destination = target_path or _resolve_sde_path()
    version_file = version_path or _resolve_version_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    version_file.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = destination.with_suffix(destination.suffix + ".tmp")

    with requests.get(SDE_BZ2_URL, stream=True, timeout=timeout_seconds) as response:
        response.raise_for_status()
        decompressor = bz2.BZ2Decompressor()
        with tmp_path.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                file_handle.write(decompressor.decompress(chunk))
        last_modified = response.headers.get("Last-Modified")

    tmp_path.replace(destination)

    version_value = last_modified or datetime.now(tz=timezone.utc).isoformat()
    version_file.write_text(version_value + "\n", encoding="utf-8")

    return destination


def ensure_sde_available(auto_download: bool = True) -> bool:
    sde_path = _resolve_sde_path()
    if sde_path.exists():
        return True
    if not auto_download:
        return False
    try:
        download_sde(target_path=sde_path)
        clear_caches()
        return True
    except Exception:
        return False


def get_connection() -> sqlite3.Connection:
    sde_path = _resolve_sde_path()
    if not sde_path.exists():
        raise FileNotFoundError(f"SDE database not found: {sde_path}")

    uri = f"file:{sde_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@lru_cache(maxsize=4096)
def _cached_type_dogma_attributes(type_id: int) -> tuple[tuple[int, float], ...]:
    query = """
        SELECT attributeID, valueInt, valueFloat
        FROM dgmTypeAttributes
        WHERE typeID = ?
    """
    with get_connection() as conn:
        rows = conn.execute(query, (type_id,)).fetchall()

    values: list[tuple[int, float]] = []
    for row in rows:
        value = row["valueFloat"]
        if value is None:
            value = row["valueInt"]
        if value is None:
            continue
        values.append((int(row["attributeID"]), float(value)))
    return tuple(values)


def get_type_dogma_attributes(type_id: int) -> dict[int, float]:
    return dict(_cached_type_dogma_attributes(type_id))


@lru_cache(maxsize=4096)
def _cached_type_effects(type_id: int) -> tuple[int, ...]:
    query = """
        SELECT effectID
        FROM dgmTypeEffects
        WHERE typeID = ?
    """
    with get_connection() as conn:
        rows = conn.execute(query, (type_id,)).fetchall()
    return tuple(int(row["effectID"]) for row in rows)


def get_type_effects(type_id: int) -> list[int]:
    return list(_cached_type_effects(type_id))


@lru_cache(maxsize=4096)
def get_type_info(type_id: int) -> dict[str, Any]:
    query = """
        SELECT
            t.typeID AS type_id,
            t.typeName AS type_name,
            t.groupID AS group_id,
            g.categoryID AS category_id
        FROM invTypes AS t
        LEFT JOIN invGroups AS g ON g.groupID = t.groupID
        WHERE t.typeID = ?
    """
    with get_connection() as conn:
        row = conn.execute(query, (type_id,)).fetchone()
    if row is None:
        return {}
    return dict(row)


@lru_cache(maxsize=4096)
def get_group_info(group_id: int) -> dict[str, Any]:
    query = """
        SELECT
            groupID AS group_id,
            groupName AS group_name,
            categoryID AS category_id
        FROM invGroups
        WHERE groupID = ?
    """
    with get_connection() as conn:
        row = conn.execute(query, (group_id,)).fetchone()
    if row is None:
        return {}
    return dict(row)


@lru_cache(maxsize=8192)
def get_attribute_info(attribute_id: int) -> dict[str, Any]:
    query = """
        SELECT
            attributeID AS attribute_id,
            attributeName AS attribute_name,
            defaultValue AS default_value,
            stackable,
            highIsGood AS high_is_good
        FROM dgmAttributeTypes
        WHERE attributeID = ?
    """
    with get_connection() as conn:
        row = conn.execute(query, (attribute_id,)).fetchone()
    if row is None:
        return {}
    return dict(row)


@lru_cache(maxsize=4096)
def get_effect_info(effect_id: int) -> dict[str, Any]:
    query = """
        SELECT
            effectID AS effect_id,
            effectName AS effect_name,
            effectCategory AS effect_category,
            preExpression AS pre_expression,
            postExpression AS post_expression,
            description AS description
        FROM dgmEffects
        WHERE effectID = ?
    """
    with get_connection() as conn:
        row = conn.execute(query, (effect_id,)).fetchone()
    if row is None:
        return {}
    return dict(row)


@lru_cache(maxsize=4096)
def get_effect_modifiers(effect_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='dgmEffectsModifiers'"
        ).fetchone()
        if table_exists is None:
            return []
        rows = conn.execute(
            "SELECT * FROM dgmEffectsModifiers WHERE effectID = ?",
            (effect_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def search_types_by_name(name: str, limit: int = 30) -> list[dict[str, Any]]:
    query = """
        SELECT
            t.typeID AS type_id,
            t.typeName AS type_name,
            t.groupID AS group_id,
            g.categoryID AS category_id
        FROM invTypes AS t
        LEFT JOIN invGroups AS g ON g.groupID = t.groupID
        WHERE t.typeName LIKE ? COLLATE NOCASE
        ORDER BY t.typeName ASC
        LIMIT ?
    """
    like_value = f"%{name}%"
    with get_connection() as conn:
        rows = conn.execute(query, (like_value, limit)).fetchall()
    return [dict(row) for row in rows]


def preload_weapon_groups() -> set[int]:
    query = """
        SELECT groupID
        FROM invGroups
        WHERE
            LOWER(groupName) LIKE '%turret%'
            OR LOWER(groupName) LIKE '%launcher%'
            OR LOWER(groupName) LIKE '%missile%'
            OR LOWER(groupName) LIKE '%drone%'
    """
    try:
        with get_connection() as conn:
            rows = conn.execute(query).fetchall()
    except FileNotFoundError:
        return set()

    WEAPON_GROUP_IDS.clear()
    WEAPON_GROUP_IDS.update(int(row["groupID"]) for row in rows)
    return set(WEAPON_GROUP_IDS)


def clear_caches() -> None:
    _cached_type_dogma_attributes.cache_clear()
    _cached_type_effects.cache_clear()
    get_type_info.cache_clear()
    get_group_info.cache_clear()
    get_attribute_info.cache_clear()
    get_effect_info.cache_clear()
    get_effect_modifiers.cache_clear()
