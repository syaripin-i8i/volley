from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import pymysql
import pymysql.cursors


def _get_connection() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.getenv("DB_HOST", "mariadb"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USERNAME", "seat"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_DATABASE", "seat"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_sde_available(auto_download: bool = True) -> bool:
    """Check that MariaDB is reachable. auto_download param kept for API compat."""
    try:
        conn = _get_connection()
        conn.close()
        return True
    except Exception:
        return False


@lru_cache(maxsize=4096)
def _cached_type_dogma_attributes(type_id: int) -> tuple[tuple[int, float], ...]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT attributeID, valueInt, valueFloat "
                "FROM dgmTypeAttributes WHERE typeID = %s",
                (type_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

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
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT effectID FROM dgmTypeEffects WHERE typeID = %s",
                (type_id,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return tuple(int(row["effectID"]) for row in rows)


def get_type_effects(type_id: int) -> list[int]:
    return list(_cached_type_effects(type_id))


@lru_cache(maxsize=4096)
def get_type_info(type_id: int) -> dict[str, Any]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT t.typeID AS type_id, t.typeName AS type_name, "
                "t.groupID AS group_id, g.categoryID AS category_id "
                "FROM invTypes AS t "
                "LEFT JOIN invGroups AS g ON g.groupID = t.groupID "
                "WHERE t.typeID = %s",
                (type_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return row or {}


@lru_cache(maxsize=4096)
def get_group_info(group_id: int) -> dict[str, Any]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT groupID AS group_id, groupName AS group_name, "
                "categoryID AS category_id "
                "FROM invGroups WHERE groupID = %s",
                (group_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return row or {}


@lru_cache(maxsize=4096)
def _cached_group_types(group_id: int, limit: int) -> tuple[tuple[int, str], ...]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT typeID AS type_id, typeName AS type_name "
                "FROM invTypes "
                "WHERE groupID = %s AND COALESCE(published, 1) = 1 "
                "AND LOWER(typeName) NOT LIKE '%%blueprint%%' "
                "ORDER BY typeName ASC LIMIT %s",
                (group_id, limit),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return tuple((int(row["type_id"]), str(row["type_name"])) for row in rows)


def get_group_types(group_id: int, limit: int = 200) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 1000))
    return [
        {"type_id": type_id, "type_name": type_name}
        for type_id, type_name in _cached_group_types(int(group_id), safe_limit)
    ]


@lru_cache(maxsize=8192)
def get_attribute_info(attribute_id: int) -> dict[str, Any]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT attributeID AS attribute_id, attributeName AS attribute_name, "
                "defaultValue AS default_value, stackable, highIsGood AS high_is_good "
                "FROM dgmAttributeTypes WHERE attributeID = %s",
                (attribute_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return row or {}


@lru_cache(maxsize=4096)
def get_effect_info(effect_id: int) -> dict[str, Any]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT effectID AS effect_id, effectName AS effect_name, "
                "effectCategory AS effect_category, preExpression AS pre_expression, "
                "postExpression AS post_expression, description AS description "
                "FROM dgmEffects WHERE effectID = %s",
                (effect_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    return row or {}


@lru_cache(maxsize=4096)
def get_effect_modifiers(effect_id: int) -> list[dict[str, Any]]:
    # dgmEffectsModifiers is not present in SeAT's MariaDB SDE
    return []


def search_types_by_name(name: str, limit: int = 30) -> list[dict[str, Any]]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT t.typeID AS type_id, t.typeName AS type_name, "
                "t.groupID AS group_id, g.categoryID AS category_id "
                "FROM invTypes AS t "
                "LEFT JOIN invGroups AS g ON g.groupID = t.groupID "
                "WHERE t.typeName LIKE %s "
                "ORDER BY t.typeName ASC LIMIT %s",
                (f"%{name}%", limit),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return list(rows)


WEAPON_GROUP_IDS: set[int] = set()


def preload_weapon_groups() -> set[int]:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT groupID FROM invGroups WHERE "
                "LOWER(groupName) LIKE '%turret%' OR "
                "LOWER(groupName) LIKE '%launcher%' OR "
                "LOWER(groupName) LIKE '%missile%' OR "
                "LOWER(groupName) LIKE '%drone%'"
            )
            rows = cur.fetchall()
    except Exception:
        return set()
    finally:
        conn.close()

    WEAPON_GROUP_IDS.clear()
    WEAPON_GROUP_IDS.update(int(row["groupID"]) for row in rows)
    return set(WEAPON_GROUP_IDS)


@lru_cache(maxsize=8192)
def type_name_to_id(name: str) -> int | None:
    """Resolve an EVE type name to its typeID using MariaDB. Returns None if not found."""
    from difflib import SequenceMatcher

    normalized = " ".join(name.strip().split())
    if not normalized:
        return None

    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            # 1. exact match
            cur.execute(
                "SELECT typeID FROM invTypes "
                "WHERE typeName = %s AND COALESCE(published, 1) = 1 "
                "AND LOWER(typeName) NOT LIKE '%%blueprint%%' "
                "ORDER BY typeID LIMIT 1",
                (normalized,),
            )
            row = cur.fetchone()
            if row:
                return int(row["typeID"])

            # 2. prefix match
            cur.execute(
                "SELECT typeID FROM invTypes "
                "WHERE typeName LIKE %s AND COALESCE(published, 1) = 1 "
                "AND LOWER(typeName) NOT LIKE '%%blueprint%%' "
                "ORDER BY LENGTH(typeName), typeID LIMIT 1",
                (f"{normalized}%",),
            )
            row = cur.fetchone()
            if row:
                return int(row["typeID"])

            # 3. partial match
            cur.execute(
                "SELECT typeID FROM invTypes "
                "WHERE typeName LIKE %s AND COALESCE(published, 1) = 1 "
                "AND LOWER(typeName) NOT LIKE '%%blueprint%%' "
                "ORDER BY LENGTH(typeName), typeID LIMIT 1",
                (f"%{normalized}%",),
            )
            row = cur.fetchone()
            if row:
                return int(row["typeID"])

            # 4. fuzzy match
            words = [t for t in normalized.lower().split() if len(t) >= 3]
            if not words:
                return None
            anchor = sorted(words, key=len, reverse=True)[0]
            cur.execute(
                "SELECT typeID, typeName FROM invTypes "
                "WHERE typeName LIKE %s AND COALESCE(published, 1) = 1 "
                "AND LOWER(typeName) NOT LIKE '%%blueprint%%' LIMIT 200",
                (f"%{anchor}%",),
            )
            candidates = cur.fetchall()
    finally:
        conn.close()

    if not candidates:
        return None

    def score(r: dict) -> float:
        candidate = str(r["typeName"]).lower()
        overlap = sum(1 for token in words if token in candidate)
        ratio = SequenceMatcher(None, normalized.lower(), candidate).ratio()
        size_bonus = sum(
            1 for size in ("small", "medium", "large", "x-large", "capital")
            if size in words and size in candidate
        )
        return overlap * 10 + ratio * 5 + size_bonus * 3

    best = max(candidates, key=score)
    return int(best["typeID"])


def clear_caches() -> None:
    _cached_type_dogma_attributes.cache_clear()
    _cached_type_effects.cache_clear()
    _cached_group_types.cache_clear()
    get_type_info.cache_clear()
    get_group_info.cache_clear()
    get_attribute_info.cache_clear()
    get_effect_info.cache_clear()
    type_name_to_id.cache_clear()
