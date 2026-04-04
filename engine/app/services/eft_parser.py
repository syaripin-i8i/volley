from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.calc import FitModule
from app.services import sde

SLOT_ORDER = ["high", "mid", "low", "rig", "drone"]
ALIASES = {
    "small electrochemical capacitor booster i": "'Saddle' Small Capacitor Booster I",
}


@dataclass
class ParsedModule:
    name: str
    charge_name: str | None
    slot: str


@dataclass
class FitParseResult:
    ship_name: str
    fit_name: str
    modules: list[ParsedModule] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_eft(text: str) -> FitParseResult:
    if not text or not text.strip():
        return FitParseResult(ship_name="", fit_name="", errors=["EFT text is empty."])

    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    first_non_empty = next((idx for idx, line in enumerate(lines) if line.strip()), None)
    if first_non_empty is None:
        return FitParseResult(ship_name="", fit_name="", errors=["EFT text has no content."])

    header = lines[first_non_empty].strip()
    if not (header.startswith("[") and header.endswith("]")):
        return FitParseResult(ship_name="", fit_name="", errors=["Missing EFT header line [Ship, Fit]."])

    header_text = header[1:-1]
    if "," in header_text:
        ship_name, fit_name = (part.strip() for part in header_text.split(",", 1))
    else:
        ship_name = header_text.strip()
        fit_name = ""

    result = FitParseResult(ship_name=ship_name, fit_name=fit_name)

    slot_index = 0
    seen_module = False
    saw_blank = False
    for raw_line in lines[first_non_empty + 1 :]:
        line = raw_line.strip()
        if not line:
            if not seen_module:
                continue
            if not saw_blank:
                slot_index += 1
            saw_blank = True
            continue
        saw_blank = False

        if line.lower().startswith("[empty ") and line.lower().endswith(" slot]"):
            continue
        if line.startswith("[") and line.endswith("]"):
            # Ignore unsupported section-like lines after the header.
            continue

        module_name, charge_name = _split_module_and_charge(line)
        slot = SLOT_ORDER[min(slot_index, len(SLOT_ORDER) - 1)]
        result.modules.append(
            ParsedModule(
                name=module_name,
                charge_name=charge_name,
                slot=slot,
            )
        )
        seen_module = True

    if not result.modules:
        result.errors.append("No modules were parsed from EFT text.")

    return result


def _split_module_and_charge(line: str) -> tuple[str, str | None]:
    if "," not in line:
        return line.strip(), None
    module_name, charge_name = line.split(",", 1)
    module = module_name.strip()
    charge = charge_name.strip()
    return module, (charge if charge else None)


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split())


def type_name_to_id(name: str) -> int | None:
    normalized = _normalize_name(name)
    if not normalized:
        return None
    alias = ALIASES.get(normalized.lower())
    if alias:
        normalized = alias
    return sde.type_name_to_id(normalized)


def resolve_fit(parsed: FitParseResult) -> tuple[int, list[FitModule]]:
    ship_type_id = type_name_to_id(parsed.ship_name)
    if ship_type_id is None:
        parsed.errors.append(f"Could not resolve ship type: {parsed.ship_name}")
        raise ValueError(parsed.errors[-1])

    modules: list[FitModule] = []
    for parsed_module in parsed.modules:
        module_type_id = type_name_to_id(parsed_module.name)
        if module_type_id is None:
            parsed.errors.append(f"Could not resolve module type: {parsed_module.name}")
            continue

        charge_type_id: int | None = None
        if parsed_module.charge_name:
            charge_type_id = type_name_to_id(parsed_module.charge_name)
            if charge_type_id is None:
                parsed.errors.append(f"Could not resolve charge type: {parsed_module.charge_name}")

        modules.append(
            FitModule(
                type_id=module_type_id,
                slot=parsed_module.slot,  # type: ignore[arg-type]
                charge_type_id=charge_type_id,
                quantity=1,
            )
        )

    return ship_type_id, modules
