from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from app.schemas.calc import (
    ChargeOption,
    FitModule,
    FitModuleState,
    FitRequest,
    FitState,
)
from app.services import eft_parser, sde

SlotName = Literal["high", "mid", "low", "rig", "drone"]
SLOT_ORDER: tuple[SlotName, ...] = ("high", "mid", "low", "rig", "drone")
CHARGE_CATEGORY_ID = 8

_UA = "seat-volley/0.1"


@dataclass
class _ChargeCandidate:
    type_id: int
    remaining: int
    slot: SlotName | None


def resolve_eft_to_fit_state(eft_text: str) -> FitState:
    parsed = eft_parser.parse_eft(eft_text)
    ship_type_id, modules = eft_parser.resolve_fit(parsed)
    if not modules:
        error_text = "; ".join(parsed.errors) if parsed.errors else "No modules could be resolved from EFT text."
        raise ValueError(error_text)

    fit = FitRequest(ship_type_id=ship_type_id, modules=modules, skills=[])
    source_label = parsed.fit_name.strip() if parsed.fit_name else parsed.ship_name.strip()
    return build_fit_state(
        fit=fit,
        source="eft",
        source_label=source_label or "EFT",
        eft_text=eft_text.strip(),
        warnings=parsed.errors,
    )


def import_zkill_to_fit_state(url: str) -> FitState:
    kill_id = _extract_kill_id(url)
    zkill_payload = _fetch_json(f"https://zkillboard.com/api/killID/{kill_id}/", timeout=15)
    if not isinstance(zkill_payload, list) or not zkill_payload:
        raise ValueError("Could not find killmail metadata on zKillboard.")

    zkill_entry = zkill_payload[0] if isinstance(zkill_payload[0], dict) else {}
    hash_value = str((zkill_entry.get("zkb") or {}).get("hash") or "").strip()
    if not hash_value:
        raise ValueError("zKillboard response did not include killmail hash.")

    killmail_payload = _fetch_json(
        f"https://esi.evetech.net/latest/killmails/{kill_id}/{hash_value}/?datasource=tranquility",
        timeout=20,
    )
    fit, warnings = _fit_from_killmail_payload(killmail_payload)
    source_label = f"zKill #{kill_id}"
    eft_text = _fit_to_eft_text(fit=fit, fit_name=source_label)
    return build_fit_state(
        fit=fit,
        source="zkill",
        source_label=source_label,
        eft_text=eft_text,
        warnings=warnings,
    )


def build_fit_state(
    fit: FitRequest,
    source: Literal["eft", "zkill", "fit"],
    source_label: str | None = None,
    eft_text: str | None = None,
    warnings: list[str] | None = None,
) -> FitState:
    module_name_cache: dict[int, str] = {}
    charge_name_cache: dict[int, str] = {}
    charge_option_cache: dict[tuple[int, int | None], list[ChargeOption]] = {}

    module_states: list[FitModuleState] = []
    for module in fit.modules:
        module_name = _resolve_type_name(module.type_id, module_name_cache)
        charge_name: str | None = None
        if module.charge_type_id is not None:
            charge_name = _resolve_type_name(module.charge_type_id, charge_name_cache)
        option_key = (module.type_id, module.charge_type_id)
        if option_key not in charge_option_cache:
            charge_option_cache[option_key] = _build_charge_options(
                module_type_id=module.type_id,
                current_charge_type_id=module.charge_type_id,
            )
        module_states.append(
            FitModuleState(
                type_id=module.type_id,
                slot=module.slot,
                quantity=max(1, int(module.quantity)),
                type_name=module_name,
                charge_type_id=module.charge_type_id,
                charge_name=charge_name,
                charge_options=charge_option_cache[option_key],
            )
        )

    return FitState(
        source=source,
        source_label=(source_label or "").strip() or None,
        eft_text=eft_text,
        fit=fit,
        modules=module_states,
        warnings=list(dict.fromkeys((warnings or []))),
    )


def _build_charge_options(module_type_id: int, current_charge_type_id: int | None) -> list[ChargeOption]:
    group_ids = _module_charge_groups(module_type_id)
    if current_charge_type_id:
        current_info = sde.get_type_info(current_charge_type_id)
        current_group_id = int(current_info.get("group_id", 0) or 0)
        if current_group_id > 0 and current_group_id not in group_ids:
            group_ids.append(current_group_id)

    options: dict[int, str] = {}
    for group_id in group_ids:
        for candidate in sde.get_group_types(group_id, limit=300):
            type_id = int(candidate.get("type_id", 0))
            type_name = str(candidate.get("type_name", "")).strip()
            if type_id <= 0 or type_name == "":
                continue
            options[type_id] = type_name

    if current_charge_type_id and current_charge_type_id not in options:
        current_name = _resolve_type_name(current_charge_type_id, {})
        options[current_charge_type_id] = current_name

    sorted_options = sorted(options.items(), key=lambda item: item[1].lower())
    return [ChargeOption(type_id=type_id, type_name=type_name) for type_id, type_name in sorted_options]


def _module_charge_groups(module_type_id: int) -> list[int]:
    attrs = sde.get_type_dogma_attributes(module_type_id)
    groups: set[int] = set()
    for attr_id, raw_value in attrs.items():
        attr_info = sde.get_attribute_info(attr_id)
        attr_name = str(attr_info.get("attribute_name", "")).strip()
        if not attr_name.startswith("chargeGroup"):
            continue
        group_id = int(raw_value or 0)
        if group_id > 0:
            groups.add(group_id)
    return sorted(groups)


def _resolve_type_name(type_id: int, cache: dict[int, str]) -> str:
    if type_id in cache:
        return cache[type_id]
    info = sde.get_type_info(type_id)
    name = str(info.get("type_name", "")).strip() or f"type_id:{type_id}"
    cache[type_id] = name
    return name


def _extract_kill_id(url: str) -> int:
    cleaned = (url or "").strip()
    if cleaned == "":
        raise ValueError("zKill URL is empty.")

    parsed = urllib_parse.urlparse(cleaned)
    host = parsed.netloc.lower()
    if parsed.scheme not in ("http", "https") or host not in ("zkillboard.com", "www.zkillboard.com"):
        raise ValueError("Invalid zKill URL. Use https://zkillboard.com/kill/<kill_id>/")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) != 2 or path_parts[0].lower() != "kill" or not re.fullmatch(r"\d+", path_parts[1]):
        raise ValueError("Invalid zKill URL. Use https://zkillboard.com/kill/<kill_id>/")

    return int(path_parts[1])


def _fetch_json(url: str, timeout: int) -> dict | list:
    request = urllib_request.Request(url=url, headers={"Accept": "application/json", "User-Agent": _UA})
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore").strip()
        message = f"Failed to fetch remote resource (HTTP {exc.code})."
        if body:
            message = f"{message} {body[:300]}"
        raise RuntimeError(message) from exc
    except urllib_error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        raise RuntimeError(f"Failed to fetch remote resource: {reason}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Remote service returned invalid JSON.") from exc
    if not isinstance(payload, (dict, list)):
        raise RuntimeError("Remote service returned unexpected response format.")
    return payload


def _fit_from_killmail_payload(killmail: dict | list) -> tuple[FitRequest, list[str]]:
    if not isinstance(killmail, dict):
        raise ValueError("Invalid killmail payload.")

    victim = killmail.get("victim") if isinstance(killmail.get("victim"), dict) else {}
    ship_type_id = int(victim.get("ship_type_id", 0) or 0)
    if ship_type_id <= 0:
        raise ValueError("Killmail does not include a valid victim ship type.")

    raw_items = victim.get("items")
    if not isinstance(raw_items, list):
        raw_items = []
    items = _flatten_items(raw_items)

    module_candidates: list[FitModule] = []
    slot_charges: dict[SlotName, list[_ChargeCandidate]] = {slot: [] for slot in SLOT_ORDER}
    cargo_charges: list[_ChargeCandidate] = []

    for item in items:
        type_id = int(item.get("item_type_id", 0) or 0)
        flag = int(item.get("flag", -1) or -1)
        if type_id <= 0 or flag < 0:
            continue

        item_info = sde.get_type_info(type_id)
        if not item_info:
            continue
        quantity = _item_quantity(item)
        slot = _slot_from_flag(flag)
        if _is_charge_like_item(item_info):
            candidate = _ChargeCandidate(type_id=type_id, remaining=quantity, slot=slot)
            if slot is None:
                cargo_charges.append(candidate)
            else:
                slot_charges[slot].append(candidate)
            continue

        if slot is None:
            continue

        module_candidates.append(
            FitModule(
                type_id=type_id,
                slot=slot,
                charge_type_id=None,
                quantity=max(1, quantity),
            )
        )

    if not module_candidates:
        raise ValueError("Killmail could not be converted into a fit (no fitted modules found).")

    warnings: list[str] = []
    for module in module_candidates:
        assigned_charge = _assign_charge_type(module, slot_charges, cargo_charges)
        module.charge_type_id = assigned_charge
        if assigned_charge is None and _module_charge_groups(module.type_id):
            module_name = _resolve_type_name(module.type_id, {})
            warnings.append(f"No charge/script could be inferred for {module_name}.")

    return FitRequest(ship_type_id=ship_type_id, modules=module_candidates, skills=[]), warnings


def _flatten_items(items: list[dict]) -> list[dict]:
    flat: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        flat.append(item)
        nested = item.get("items")
        if isinstance(nested, list) and nested:
            flat.extend(_flatten_items(nested))
    return flat


def _item_quantity(item: dict) -> int:
    qty_destroyed = int(item.get("quantity_destroyed", 0) or 0)
    qty_dropped = int(item.get("quantity_dropped", 0) or 0)
    qty = qty_destroyed + qty_dropped
    return qty if qty > 0 else 1


def _slot_from_flag(flag: int) -> SlotName | None:
    if 11 <= flag <= 18:
        return "low"
    if 19 <= flag <= 26:
        return "mid"
    if 27 <= flag <= 34:
        return "high"
    if 92 <= flag <= 99:
        return "rig"
    if flag == 87:
        return "drone"
    if 125 <= flag <= 132:
        return "low"
    if 158 <= flag <= 163:
        return "high"
    return None


def _is_charge_like_item(type_info: dict) -> bool:
    category_id = int(type_info.get("category_id", 0) or 0)
    if category_id == CHARGE_CATEGORY_ID:
        return True

    type_name = str(type_info.get("type_name", "")).lower()
    return type_name.endswith(" script") or type_name.endswith(" charge")


def _assign_charge_type(
    module: FitModule,
    slot_charges: dict[SlotName, list[_ChargeCandidate]],
    cargo_charges: list[_ChargeCandidate],
) -> int | None:
    module_groups = set(_module_charge_groups(module.type_id))
    if not module_groups:
        return None

    ordered_candidates = slot_charges.get(module.slot, []) + cargo_charges
    needed = max(1, int(module.quantity))
    for charge in ordered_candidates:
        if charge.remaining <= 0:
            continue
        charge_info = sde.get_type_info(charge.type_id)
        charge_group_id = int(charge_info.get("group_id", 0) or 0)
        if charge_group_id not in module_groups:
            continue
        charge.remaining = max(0, charge.remaining - needed)
        return charge.type_id

    return None


def _fit_to_eft_text(fit: FitRequest, fit_name: str | None = None) -> str:
    ship_name = _resolve_type_name(fit.ship_type_id, {})
    title = fit_name.strip() if fit_name else "Imported"
    lines: list[str] = [f"[{ship_name}, {title}]"]

    for slot in SLOT_ORDER:
        slot_modules = [module for module in fit.modules if module.slot == slot]
        if not slot_modules:
            continue
        lines.append("")
        for module in slot_modules:
            module_name = _resolve_type_name(module.type_id, {})
            charge_part = ""
            if module.charge_type_id is not None:
                charge_name = _resolve_type_name(module.charge_type_id, {})
                charge_part = f", {charge_name}"
            count = max(1, int(module.quantity))
            for _ in range(count):
                lines.append(f"{module_name}{charge_part}")

    return "\n".join(lines).strip()
