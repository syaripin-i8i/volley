from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.schemas.calc import FitModule, Skill
from app.services import sde
from app.services.eve_constants import (
    ATTR_AOE_CLOUD_SIZE,
    ATTR_AOE_VELOCITY,
    ATTR_CHARGE_RATE,
    ATTR_DAMAGE_MULTIPLIER,
    ATTR_DRONE_BANDWIDTH_USED,
    ATTR_EM_DAMAGE,
    ATTR_EXPL_DAMAGE,
    ATTR_FALLOFF,
    ATTR_KIN_DAMAGE,
    ATTR_MAX_VELOCITY,
    ATTR_OPTIMAL_RANGE,
    ATTR_RATE_OF_FIRE,
    ATTR_THERM_DAMAGE,
    ATTR_TRACKING_SPEED,
    EFFECT_LAUNCHER_FITTED,
    EFFECT_TURRET_FITTED,
)

STACKING_PENALTY = [1.0, 0.869, 0.571, 0.283, 0.096, 0.023, 0.004]

ATTR_RATE_OF_FIRE_BONUS = 204
ATTR_DAMAGE_MULTIPLIER_BONUS = 292
ATTR_RATE_OF_FIRE_BONUS_SKILL = 293
ATTR_OPTIMAL_RANGE_BONUS = 351
ATTR_FALLOFF_BONUS = 349
ATTR_MISSILE_DAMAGE_BONUS = 213
ATTR_TRACKING_SPEED_BONUS = 767
ATTR_MISSILE_VELOCITY_BONUS = 547
ATTR_FLIGHT_TIME_BONUS = 557
ATTR_FLIGHT_TIME_BONUS_MODULE = 596
ATTR_EXPLOSION_VELOCITY_BONUS = 847
ATTR_EXPLOSION_RADIUS_BONUS = 848
ATTR_MAX_FLIGHT_TIME = 281
ATTR_MISSILE_EXPLOSION_RADIUS = 653
ATTR_MISSILE_EXPLOSION_VELOCITY = 654
ATTR_RATE_OF_FIRE_BONUS_GUNNERY = 441

DAMAGE_ATTRS = (
    ATTR_EM_DAMAGE,
    ATTR_THERM_DAMAGE,
    ATTR_KIN_DAMAGE,
    ATTR_EXPL_DAMAGE,
)
AMMO_MERGED_ATTRS = {
    *DAMAGE_ATTRS,
    ATTR_DAMAGE_MULTIPLIER,
    ATTR_RATE_OF_FIRE,
    ATTR_CHARGE_RATE,
    ATTR_OPTIMAL_RANGE,
    ATTR_FALLOFF,
    ATTR_TRACKING_SPEED,
    ATTR_AOE_CLOUD_SIZE,
    ATTR_AOE_VELOCITY,
    ATTR_MAX_VELOCITY,
    ATTR_MAX_FLIGHT_TIME,
    ATTR_MISSILE_EXPLOSION_RADIUS,
    ATTR_MISSILE_EXPLOSION_VELOCITY,
    ATTR_RATE_OF_FIRE_BONUS,
    ATTR_DAMAGE_MULTIPLIER_BONUS,
    ATTR_OPTIMAL_RANGE_BONUS,
    ATTR_FALLOFF_BONUS,
    ATTR_MISSILE_DAMAGE_BONUS,
    ATTR_TRACKING_SPEED_BONUS,
    ATTR_MISSILE_VELOCITY_BONUS,
    ATTR_FLIGHT_TIME_BONUS_MODULE,
    ATTR_EXPLOSION_VELOCITY_BONUS,
    ATTR_EXPLOSION_RADIUS_BONUS,
}


@dataclass
class FittedModule:
    type_id: int
    charge_type_id: int | None
    base_attrs: dict[int, float]
    modified_attrs: dict[int, float]
    hardpoint: str
    type_name: str = ""
    charge_name: str = ""

    def get_attr(self, attr_id: int) -> float:
        if attr_id in self.modified_attrs:
            return self.modified_attrs[attr_id]
        if attr_id in self.base_attrs:
            return self.base_attrs[attr_id]
        return 0.0


def apply_stacking(bonuses: list[float]) -> float:
    if not bonuses:
        return 1.0
    sorted_bonuses = sorted(bonuses, key=lambda value: abs(value - 1.0), reverse=True)
    result = 1.0
    for i, bonus in enumerate(sorted_bonuses):
        penalty = STACKING_PENALTY[i] if i < len(STACKING_PENALTY) else 0.0
        result *= max(0.0, 1.0 + (bonus - 1.0) * penalty)
    return result


class DogmaContext:
    def __init__(self, ship_type_id: int, modules: list[FitModule], skills: list[Skill]):
        self.ship_type_id = ship_type_id
        self.modules = modules
        self.skills = skills
        self.ship_attrs = sde.get_type_dogma_attributes(ship_type_id)
        self.ship_info = sde.get_type_info(ship_type_id)

    def calculate(self) -> list[FittedModule]:
        fitted_modules = self._build_fitted_modules()
        self._apply_skill_bonuses(fitted_modules)
        self._apply_module_bonuses(fitted_modules)
        return fitted_modules

    def _build_fitted_modules(self) -> list[FittedModule]:
        built: list[FittedModule] = []
        for module in self._expanded_modules(self.modules):
            type_info = sde.get_type_info(module.type_id)
            type_name = str(type_info.get("type_name", ""))
            base_attrs = sde.get_type_dogma_attributes(module.type_id)
            merged_attrs = dict(base_attrs)
            charge_name = ""
            if module.charge_type_id is not None:
                charge_attrs = sde.get_type_dogma_attributes(module.charge_type_id)
                charge_info = sde.get_type_info(module.charge_type_id)
                charge_name = str(charge_info.get("type_name", ""))
                for attr_id, value in charge_attrs.items():
                    if attr_id in AMMO_MERGED_ATTRS:
                        merged_attrs[attr_id] = value

            hardpoint = self._detect_hardpoint(module.type_id, type_info)
            built.append(
                FittedModule(
                    type_id=module.type_id,
                    charge_type_id=module.charge_type_id,
                    base_attrs=merged_attrs,
                    modified_attrs=dict(merged_attrs),
                    hardpoint=hardpoint,
                    type_name=type_name,
                    charge_name=charge_name,
                )
            )
        return built

    @staticmethod
    def _expanded_modules(modules: Iterable[FitModule]) -> list[FitModule]:
        expanded: list[FitModule] = []
        for module in modules:
            quantity = module.quantity if module.quantity > 0 else 1
            for _ in range(quantity):
                expanded.append(module)
        return expanded

    def _detect_hardpoint(self, type_id: int, type_info: dict) -> str:
        effects = set(sde.get_type_effects(type_id))
        if EFFECT_TURRET_FITTED in effects:
            return "turret"
        if EFFECT_LAUNCHER_FITTED in effects:
            return "missile"

        type_name = str(type_info.get("type_name", "")).lower()
        group_info = sde.get_group_info(int(type_info.get("group_id", 0))) if type_info.get("group_id") else {}
        group_name = str(group_info.get("group_name", "")).lower()
        text = f"{type_name} {group_name}"

        if any(token in text for token in ("turret", "cannon", "artillery", "blaster", "laser", "railgun")):
            return "turret"
        if any(token in text for token in ("launcher", "missile", "torpedo", "rocket", "heavy assault")):
            return "missile"
        if "drone" in text or ATTR_DRONE_BANDWIDTH_USED in sde.get_type_dogma_attributes(type_id):
            return "drone"
        return "none"

    def _apply_skill_bonuses(self, fitted_modules: list[FittedModule]) -> None:
        skill_cache: dict[int, tuple[dict[int, float], dict, dict]] = {}

        for skill in self.skills:
            level = max(0, min(skill.level, 5))
            if level == 0:
                continue
            if skill.type_id not in skill_cache:
                attrs = sde.get_type_dogma_attributes(skill.type_id)
                info = sde.get_type_info(skill.type_id)
                group_info = sde.get_group_info(int(info.get("group_id", 0))) if info.get("group_id") else {}
                skill_cache[skill.type_id] = (attrs, info, group_info)
            attrs, info, group_info = skill_cache[skill.type_id]

            for module in fitted_modules:
                if not self._skill_applies_to_module(info, group_info, module):
                    continue
                self._apply_single_skill(module, attrs, level)

    def _skill_applies_to_module(self, skill_info: dict, group_info: dict, module: FittedModule) -> bool:
        skill_name = str(skill_info.get("type_name", "")).lower()
        group_name = str(group_info.get("group_name", "")).lower()
        module_name = module.type_name.lower()
        charge_name = module.charge_name.lower()
        module_text = f"{module_name} {charge_name}"

        if module.hardpoint == "turret":
            if any(token in skill_name for token in ("missile", "rocket", "torpedo", "drone")):
                return False
            if "missile" in group_name:
                return False
            if "projectile" in skill_name:
                return any(token in module_text for token in ("cannon", "artillery"))
            if "hybrid" in skill_name:
                return any(token in module_text for token in ("railgun", "blaster"))
            if any(token in skill_name for token in ("laser", "energy turret")):
                return "laser" in module_text or "beam" in module_text
            return "gunnery" in group_name or group_name == "skill"

        if module.hardpoint == "missile":
            if any(token in skill_name for token in ("gunnery", "turret", "projectile", "hybrid", "laser", "drone")):
                return False
            if "missile" in group_name:
                return True
            return any(token in skill_name for token in ("missile", "rocket", "torpedo", "warhead"))

        if module.hardpoint == "drone":
            return "drone" in skill_name or "drone" in group_name

        return False

    def _apply_single_skill(self, module: FittedModule, skill_attrs: dict[int, float], level: int) -> None:
        if ATTR_DAMAGE_MULTIPLIER_BONUS in skill_attrs:
            damage_mult = 1.0 + (skill_attrs[ATTR_DAMAGE_MULTIPLIER_BONUS] / 100.0) * level
            self._apply_damage_multiplier(module, damage_mult)

        if ATTR_TRACKING_SPEED_BONUS in skill_attrs and module.hardpoint == "turret":
            tracking_mult = 1.0 + (skill_attrs[ATTR_TRACKING_SPEED_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_TRACKING_SPEED, tracking_mult)

        if ATTR_OPTIMAL_RANGE_BONUS in skill_attrs and module.hardpoint == "turret":
            optimal_mult = 1.0 + (skill_attrs[ATTR_OPTIMAL_RANGE_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_OPTIMAL_RANGE, optimal_mult)

        if ATTR_RATE_OF_FIRE_BONUS_SKILL in skill_attrs:
            rof_mult = 1.0 + (skill_attrs[ATTR_RATE_OF_FIRE_BONUS_SKILL] / 100.0) * level
            self._apply_rate_of_fire_multiplier(module, rof_mult)
        if ATTR_RATE_OF_FIRE_BONUS_GUNNERY in skill_attrs:
            rof_mult = 1.0 + (skill_attrs[ATTR_RATE_OF_FIRE_BONUS_GUNNERY] / 100.0) * level
            self._apply_rate_of_fire_multiplier(module, rof_mult)

        if ATTR_MISSILE_VELOCITY_BONUS in skill_attrs and module.hardpoint == "missile":
            velocity_mult = 1.0 + (skill_attrs[ATTR_MISSILE_VELOCITY_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_MAX_VELOCITY, velocity_mult)

        if ATTR_FLIGHT_TIME_BONUS in skill_attrs and module.hardpoint == "missile":
            flight_time_mult = 1.0 + (skill_attrs[ATTR_FLIGHT_TIME_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_MAX_FLIGHT_TIME, flight_time_mult)

        if ATTR_EXPLOSION_VELOCITY_BONUS in skill_attrs and module.hardpoint == "missile":
            exp_vel_mult = 1.0 + (skill_attrs[ATTR_EXPLOSION_VELOCITY_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_MISSILE_EXPLOSION_VELOCITY, exp_vel_mult)

        if ATTR_EXPLOSION_RADIUS_BONUS in skill_attrs and module.hardpoint == "missile":
            exp_rad_mult = 1.0 + (skill_attrs[ATTR_EXPLOSION_RADIUS_BONUS] / 100.0) * level
            self._mul_attr(module, ATTR_MISSILE_EXPLOSION_RADIUS, exp_rad_mult)

    def _apply_module_bonuses(self, fitted_modules: list[FittedModule]) -> None:
        support_modules = [module for module in fitted_modules if module.hardpoint == "none"]
        if not support_modules:
            return

        turret_damage_bonuses: list[float] = []
        turret_rof_bonuses: list[float] = []
        turret_tracking_bonuses: list[float] = []
        turret_optimal_bonuses: list[float] = []
        turret_falloff_bonuses: list[float] = []
        missile_damage_bonuses: list[float] = []
        missile_rof_bonuses: list[float] = []
        missile_velocity_bonuses: list[float] = []
        missile_flight_time_bonuses: list[float] = []
        missile_explosion_velocity_bonuses: list[float] = []
        missile_explosion_radius_bonuses: list[float] = []

        for module in support_modules:
            damage_mod = module.get_attr(ATTR_DAMAGE_MULTIPLIER)
            rof_mod = module.get_attr(ATTR_RATE_OF_FIRE_BONUS)
            tracking_bonus = module.get_attr(ATTR_TRACKING_SPEED_BONUS)
            optimal_bonus = module.get_attr(ATTR_OPTIMAL_RANGE_BONUS)
            falloff_bonus = module.get_attr(ATTR_FALLOFF_BONUS)
            missile_damage_bonus = module.get_attr(ATTR_MISSILE_DAMAGE_BONUS)
            missile_velocity_bonus = module.get_attr(ATTR_MISSILE_VELOCITY_BONUS)
            flight_time_bonus = module.get_attr(ATTR_FLIGHT_TIME_BONUS_MODULE)
            explosion_velocity_bonus = module.get_attr(ATTR_EXPLOSION_VELOCITY_BONUS)
            explosion_radius_bonus = module.get_attr(ATTR_EXPLOSION_RADIUS_BONUS)

            turret_like = any(value != 0 for value in (damage_mod, tracking_bonus, optimal_bonus, falloff_bonus))
            missile_like = any(
                value != 0
                for value in (
                    missile_damage_bonus,
                    missile_velocity_bonus,
                    flight_time_bonus,
                    explosion_velocity_bonus,
                    explosion_radius_bonus,
                )
            )

            if damage_mod not in (0.0, 1.0):
                turret_damage_bonuses.append(damage_mod)
            if missile_damage_bonus not in (0.0, 1.0):
                missile_damage_bonuses.append(missile_damage_bonus)

            if rof_mod not in (0.0, 1.0):
                if missile_like and not turret_like:
                    missile_rof_bonuses.append(rof_mod)
                elif turret_like and not missile_like:
                    turret_rof_bonuses.append(rof_mod)
                else:
                    turret_rof_bonuses.append(rof_mod)
                    missile_rof_bonuses.append(rof_mod)

            if tracking_bonus != 0:
                turret_tracking_bonuses.append(1.0 + tracking_bonus / 100.0)
            if optimal_bonus != 0:
                turret_optimal_bonuses.append(1.0 + optimal_bonus / 100.0)
            if falloff_bonus != 0:
                turret_falloff_bonuses.append(1.0 + falloff_bonus / 100.0)

            if missile_velocity_bonus != 0:
                missile_velocity_bonuses.append(1.0 + missile_velocity_bonus / 100.0)
            if flight_time_bonus != 0:
                missile_flight_time_bonuses.append(1.0 + flight_time_bonus / 100.0)
            if explosion_velocity_bonus != 0:
                missile_explosion_velocity_bonuses.append(1.0 + explosion_velocity_bonus / 100.0)
            if explosion_radius_bonus != 0:
                missile_explosion_radius_bonuses.append(1.0 + explosion_radius_bonus / 100.0)

        turret_damage_mult = apply_stacking(turret_damage_bonuses)
        turret_rof_mult = apply_stacking(turret_rof_bonuses)
        turret_tracking_mult = apply_stacking(turret_tracking_bonuses)
        turret_optimal_mult = apply_stacking(turret_optimal_bonuses)
        turret_falloff_mult = apply_stacking(turret_falloff_bonuses)

        missile_damage_mult = apply_stacking(missile_damage_bonuses)
        missile_rof_mult = apply_stacking(missile_rof_bonuses)
        missile_velocity_mult = apply_stacking(missile_velocity_bonuses)
        missile_flight_time_mult = apply_stacking(missile_flight_time_bonuses)
        missile_exp_velocity_mult = apply_stacking(missile_explosion_velocity_bonuses)
        missile_exp_radius_mult = apply_stacking(missile_explosion_radius_bonuses)

        for module in fitted_modules:
            if module.hardpoint == "turret":
                self._mul_attr(module, ATTR_DAMAGE_MULTIPLIER, turret_damage_mult)
                self._apply_rate_of_fire_multiplier(module, turret_rof_mult)
                self._mul_attr(module, ATTR_TRACKING_SPEED, turret_tracking_mult)
                self._mul_attr(module, ATTR_OPTIMAL_RANGE, turret_optimal_mult)
                self._mul_attr(module, ATTR_FALLOFF, turret_falloff_mult)
            elif module.hardpoint == "missile":
                for damage_attr in DAMAGE_ATTRS:
                    self._mul_attr(module, damage_attr, missile_damage_mult)
                self._apply_rate_of_fire_multiplier(module, missile_rof_mult)
                self._mul_attr(module, ATTR_MAX_VELOCITY, missile_velocity_mult)
                self._mul_attr(module, ATTR_MAX_FLIGHT_TIME, missile_flight_time_mult)
                self._mul_attr(module, ATTR_MISSILE_EXPLOSION_VELOCITY, missile_exp_velocity_mult)
                self._mul_attr(module, ATTR_MISSILE_EXPLOSION_RADIUS, missile_exp_radius_mult)
                self._mul_attr(module, ATTR_AOE_VELOCITY, missile_exp_velocity_mult)
                self._mul_attr(module, ATTR_AOE_CLOUD_SIZE, missile_exp_radius_mult)

    def _apply_damage_multiplier(self, module: FittedModule, multiplier: float) -> None:
        if module.hardpoint == "turret":
            self._mul_attr(module, ATTR_DAMAGE_MULTIPLIER, multiplier)
            return
        if module.hardpoint == "missile":
            for attr_id in DAMAGE_ATTRS:
                self._mul_attr(module, attr_id, multiplier)

    @staticmethod
    def _mul_attr(module: FittedModule, attr_id: int, multiplier: float) -> None:
        current = module.get_attr(attr_id)
        if current == 0.0:
            return
        module.modified_attrs[attr_id] = current * multiplier

    @staticmethod
    def _apply_rate_of_fire_multiplier(module: FittedModule, multiplier: float) -> None:
        if module.get_attr(ATTR_RATE_OF_FIRE) != 0:
            module.modified_attrs[ATTR_RATE_OF_FIRE] = module.get_attr(ATTR_RATE_OF_FIRE) * multiplier


def calculate_dogma(ship_type_id: int, modules: list[FitModule], skills: list[Skill]) -> list[FittedModule]:
    return DogmaContext(ship_type_id=ship_type_id, modules=modules, skills=skills).calculate()
