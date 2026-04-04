from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Skill(BaseModel):
    type_id: int
    level: int = Field(ge=0, le=5)


class FitModule(BaseModel):
    type_id: int
    slot: Literal["high", "mid", "low", "rig", "drone"]
    charge_type_id: int | None = None
    quantity: int = Field(default=1, ge=1)


class FitRequest(BaseModel):
    ship_type_id: int
    modules: list[FitModule] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)


class TargetProfile(BaseModel):
    sig_radius: float
    velocity: float
    distance: float | None = None
    angle: float = 90.0
    armor_resist: dict[str, float] = Field(default_factory=dict)
    shield_resist: dict[str, float] = Field(default_factory=dict)


class DpsResult(BaseModel):
    raw_dps: float
    applied_dps: float
    application_pct: float
    volley: float
    weapon_type: Literal["turret", "missile", "drone", "mixed"]


class DpsRequest(BaseModel):
    eft_text: str | None = None
    fit: FitRequest | None = None
    target: TargetProfile
    skills: list[Skill] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_fit_source(self) -> "DpsRequest":
        if not self.eft_text and self.fit is None:
            raise ValueError("Either eft_text or fit must be provided.")
        return self


class GraphRequest(BaseModel):
    eft_text: str | None = None
    fit: FitRequest | None = None
    target: TargetProfile
    skills: list[Skill] = Field(default_factory=list)
    distance_range: list[float] = Field(default_factory=lambda: [0.0, 100_000.0])
    steps: int = Field(default=100, ge=1)

    @model_validator(mode="after")
    def validate_fit_source(self) -> "GraphRequest":
        if not self.eft_text and self.fit is None:
            raise ValueError("Either eft_text or fit must be provided.")
        return self


class GraphResult(BaseModel):
    distances: list[float] = Field(default_factory=list)
    applied_dps: list[float] = Field(default_factory=list)
    raw_dps: float
    optimal_km: float | None
    falloff_km: float | None
