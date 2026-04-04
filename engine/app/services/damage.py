from __future__ import annotations

import math
from dataclasses import dataclass

from app.schemas.calc import DpsResult, GraphRequest, GraphResult, FitRequest, TargetProfile
from app.services import dogma
from app.services.eve_constants import (
    ATTR_AOE_CLOUD_SIZE,
    ATTR_AOE_DAMAGE_REDUCTION_FACTOR,
    ATTR_AOE_VELOCITY,
    ATTR_DAMAGE_MULTIPLIER,
    ATTR_EM_DAMAGE,
    ATTR_EXPL_DAMAGE,
    ATTR_FALLOFF,
    ATTR_KIN_DAMAGE,
    ATTR_OPTIMAL_RANGE,
    ATTR_OPTIMAL_SIG_RADIUS,
    ATTR_RATE_OF_FIRE,
    ATTR_THERM_DAMAGE,
    ATTR_TRACKING_SPEED,
)

ATTR_TURRET_SIGNATURE_RESOLUTION = 620
ATTR_MISSILE_EXPLOSION_RADIUS = 653
ATTR_MISSILE_EXPLOSION_VELOCITY = 654
ATTR_MISSILE_DAMAGE_REDUCTION_FACTOR = 1353

DAMAGE_ATTRS = (ATTR_EM_DAMAGE, ATTR_THERM_DAMAGE, ATTR_KIN_DAMAGE, ATTR_EXPL_DAMAGE)


def _normalize_scaled(value: float) -> float:
    if value > 1000:
        return value / 1000.0
    return value


def _safe_cycle_seconds(cycle_ms: float) -> float:
    if cycle_ms <= 0:
        return 1.0
    return cycle_ms / 1000.0


def _damage_sum(mod: dogma.FittedModule) -> float:
    return sum(mod.get_attr(attr) for attr in DAMAGE_ATTRS)


def calc_turret_mult(
    atk_tracking: float,
    atk_optimal_sig: float,
    atk_optimal: float,
    atk_falloff: float,
    tgt_sig_radius: float,
    tgt_speed: float,
    tgt_angle: float = 90.0,
    atk_speed: float = 0.0,
    atk_angle: float = 0.0,
    distance: float | None = None,
) -> float:
    angular = _calc_angular_speed(atk_speed, atk_angle, distance, tgt_speed, tgt_angle)
    range_factor = _calc_range_factor(atk_optimal, atk_falloff, distance)
    tracking_factor = _calc_tracking_factor(atk_tracking, atk_optimal_sig, angular, tgt_sig_radius)
    cth = range_factor * tracking_factor
    return _cth_to_mult(cth)


def _calc_angular_speed(atk_speed, atk_angle, distance, tgt_speed, tgt_angle):
    if distance is None or distance == 0:
        return 0.0
    atk_rad = math.radians(atk_angle)
    tgt_rad = math.radians(tgt_angle)
    transversal = abs(atk_speed * math.sin(atk_rad) - tgt_speed * math.sin(tgt_rad))
    return transversal / distance


def _calc_range_factor(optimal, falloff, distance):
    if distance is None:
        return 1.0
    if falloff == 0:
        return 1.0 if distance <= optimal else 0.0
    return 0.5 ** ((max(0.0, distance - optimal) / falloff) ** 2)


def _calc_tracking_factor(tracking, optimal_sig, angular, tgt_sig):
    if tracking <= 0 or tgt_sig <= 0:
        return 1.0
    return 0.5 ** ((angular * optimal_sig / (tracking * tgt_sig)) ** 2)


def _cth_to_mult(cth: float) -> float:
    cth = max(0.0, min(1.0, cth))
    wrecking_chance = min(cth, 0.01)
    wrecking_part = wrecking_chance * 3
    normal_chance = cth - wrecking_chance
    if normal_chance > 0:
        avg = (0.01 + cth) / 2 + 0.49
        normal_part = normal_chance * avg
    else:
        normal_part = 0.0
    return normal_part + wrecking_part


def calc_missile_mult(
    explosion_radius: float,
    explosion_velocity: float,
    damage_reduction_factor: float,
    tgt_sig_radius: float,
    tgt_speed: float,
) -> float:
    factors = [1.0]
    if explosion_radius > 0:
        factors.append(tgt_sig_radius / explosion_radius)
    if tgt_speed > 0 and explosion_radius > 0:
        speed_term = (explosion_velocity * tgt_sig_radius) / (explosion_radius * tgt_speed)
        if speed_term > 0:
            factors.append(speed_term**damage_reduction_factor)
    return max(0.0, min(1.0, min(factors)))


@dataclass
class WeaponDps:
    raw_dps: float
    applied_dps: float
    application_pct: float
    volley: float
    weapon_type: str


def calc_fit_dps(
    fitted_modules: list[dogma.FittedModule],
    tgt_sig_radius: float,
    tgt_speed: float,
    tgt_angle: float = 90.0,
    distance: float | None = None,
    atk_speed: float = 0.0,
) -> list[WeaponDps]:
    results: list[WeaponDps] = []

    for mod in fitted_modules:
        cycle_seconds = _safe_cycle_seconds(mod.get_attr(ATTR_RATE_OF_FIRE))
        damage = _damage_sum(mod)
        if damage <= 0:
            continue

        if mod.hardpoint == "turret":
            damage_multiplier = mod.get_attr(ATTR_DAMAGE_MULTIPLIER) or 1.0
            volley = damage * damage_multiplier
            raw_dps = volley / cycle_seconds

            tracking = _normalize_scaled(mod.get_attr(ATTR_TRACKING_SPEED))
            optimal = mod.get_attr(ATTR_OPTIMAL_RANGE)
            falloff = mod.get_attr(ATTR_FALLOFF)
            optimal_sig = _normalize_scaled(
                mod.get_attr(ATTR_OPTIMAL_SIG_RADIUS) or mod.get_attr(ATTR_TURRET_SIGNATURE_RESOLUTION) or 40000.0
            )
            turret_mult = calc_turret_mult(
                atk_tracking=tracking,
                atk_optimal_sig=optimal_sig,
                atk_optimal=optimal,
                atk_falloff=falloff,
                tgt_sig_radius=tgt_sig_radius,
                tgt_speed=tgt_speed,
                tgt_angle=tgt_angle,
                atk_speed=atk_speed,
                distance=distance,
            )
            applied_dps = raw_dps * turret_mult
            app_pct = (applied_dps / raw_dps * 100.0) if raw_dps > 0 else 0.0
            results.append(
                WeaponDps(
                    raw_dps=raw_dps,
                    applied_dps=applied_dps,
                    application_pct=app_pct,
                    volley=volley,
                    weapon_type="turret",
                )
            )
        elif mod.hardpoint == "missile":
            volley = damage
            raw_dps = volley / cycle_seconds
            explosion_radius = mod.get_attr(ATTR_MISSILE_EXPLOSION_RADIUS) or mod.get_attr(ATTR_AOE_CLOUD_SIZE)
            explosion_velocity = mod.get_attr(ATTR_MISSILE_EXPLOSION_VELOCITY) or mod.get_attr(ATTR_AOE_VELOCITY)
            drf = mod.get_attr(ATTR_MISSILE_DAMAGE_REDUCTION_FACTOR) or mod.get_attr(ATTR_AOE_DAMAGE_REDUCTION_FACTOR)
            if drf <= 0:
                drf = 1.0

            missile_mult = calc_missile_mult(
                explosion_radius=explosion_radius,
                explosion_velocity=explosion_velocity,
                damage_reduction_factor=drf,
                tgt_sig_radius=tgt_sig_radius,
                tgt_speed=tgt_speed,
            )
            applied_dps = raw_dps * missile_mult
            app_pct = (applied_dps / raw_dps * 100.0) if raw_dps > 0 else 0.0
            results.append(
                WeaponDps(
                    raw_dps=raw_dps,
                    applied_dps=applied_dps,
                    application_pct=app_pct,
                    volley=volley,
                    weapon_type="missile",
                )
            )
        elif mod.hardpoint == "drone":
            volley = damage
            raw_dps = volley / cycle_seconds
            results.append(
                WeaponDps(
                    raw_dps=raw_dps,
                    applied_dps=raw_dps,
                    application_pct=100.0,
                    volley=volley,
                    weapon_type="drone",
                )
            )

    return results


def calc_dps_vs_distance(
    fitted_modules: list[dogma.FittedModule],
    tgt_sig_radius: float,
    tgt_speed: float,
    tgt_angle: float = 90.0,
    distance_range: tuple[float, float] = (0, 100_000),
    steps: int = 100,
) -> dict:
    min_distance, max_distance = distance_range
    if steps <= 0:
        steps = 1
    distances = [
        min_distance + (max_distance - min_distance) * i / steps
        for i in range(steps + 1)
    ]

    dps_series: list[float] = []
    raw_reference = 0.0
    for distance in distances:
        weapon_values = calc_fit_dps(
            fitted_modules=fitted_modules,
            tgt_sig_radius=tgt_sig_radius,
            tgt_speed=tgt_speed,
            tgt_angle=tgt_angle,
            distance=distance,
        )
        raw_reference = sum(item.raw_dps for item in weapon_values)
        dps_series.append(sum(item.applied_dps for item in weapon_values))

    turret_mods = [mod for mod in fitted_modules if mod.hardpoint == "turret"]
    if turret_mods:
        optimal_km = max((mod.get_attr(ATTR_OPTIMAL_RANGE) for mod in turret_mods), default=0.0) / 1000.0
        falloff_km = max((mod.get_attr(ATTR_FALLOFF) for mod in turret_mods), default=0.0) / 1000.0
    else:
        optimal_km = None
        falloff_km = None

    return {
        "distances_km": [value / 1000.0 for value in distances],
        "applied_dps": dps_series,
        "raw_dps": raw_reference,
        "optimal_km": optimal_km,
        "falloff_km": falloff_km,
    }


def _resolve_weapon_type(weapon_results: list[WeaponDps]) -> str:
    kinds = {result.weapon_type for result in weapon_results}
    if not kinds:
        return "mixed"
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


def calculate_dps(fit: FitRequest, target: TargetProfile) -> DpsResult:
    fitted_modules = dogma.calculate_dogma(
        ship_type_id=fit.ship_type_id,
        modules=fit.modules,
        skills=fit.skills,
    )
    weapon_values = calc_fit_dps(
        fitted_modules=fitted_modules,
        tgt_sig_radius=target.sig_radius,
        tgt_speed=target.velocity,
        tgt_angle=target.angle,
        distance=target.distance,
    )
    raw_dps = sum(item.raw_dps for item in weapon_values)
    applied_dps = sum(item.applied_dps for item in weapon_values)
    volley = sum(item.volley for item in weapon_values)
    app_pct = (applied_dps / raw_dps * 100.0) if raw_dps > 0 else 0.0

    return DpsResult(
        raw_dps=raw_dps,
        applied_dps=applied_dps,
        application_pct=app_pct,
        volley=volley,
        weapon_type=_resolve_weapon_type(weapon_values),
    )


def calculate_graph(req: GraphRequest) -> GraphResult:
    if req.fit is None:
        raise ValueError("GraphRequest.fit is required after request resolution.")
    fitted_modules = dogma.calculate_dogma(
        ship_type_id=req.fit.ship_type_id,
        modules=req.fit.modules,
        skills=req.fit.skills,
    )
    range_values = tuple(req.distance_range[:2]) if len(req.distance_range) >= 2 else (0.0, 100_000.0)
    graph = calc_dps_vs_distance(
        fitted_modules=fitted_modules,
        tgt_sig_radius=req.target.sig_radius,
        tgt_speed=req.target.velocity,
        tgt_angle=req.target.angle,
        distance_range=(float(range_values[0]), float(range_values[1])),
        steps=req.steps,
    )
    return GraphResult(
        distances=graph["distances_km"],
        applied_dps=graph["applied_dps"],
        raw_dps=graph["raw_dps"],
        optimal_km=graph["optimal_km"],
        falloff_km=graph["falloff_km"],
    )
