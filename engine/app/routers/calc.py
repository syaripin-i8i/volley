from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.calc import DpsRequest, DpsResult, FitRequest, GraphRequest, GraphResult, Skill
from app.services import damage, eft_parser, sde

router = APIRouter(tags=["calc"])


@router.post("/calc/dps", response_model=DpsResult)
async def calc_dps(req: DpsRequest) -> DpsResult:
    try:
        fit = _resolve_fit_request(
            eft_text=req.eft_text,
            fit=req.fit,
            skills=req.skills,
        )
        return damage.calculate_dps(fit=fit, target=req.target)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc) or "DPS calculation is not implemented yet.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/calc/graph", response_model=GraphResult)
async def calc_graph(req: GraphRequest) -> GraphResult:
    try:
        fit = _resolve_fit_request(
            eft_text=req.eft_text,
            fit=req.fit,
            skills=req.skills,
        )
        resolved = req.model_copy(update={"fit": fit, "eft_text": None})
        return damage.calculate_graph(req=resolved)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc) or "Graph calculation is not implemented yet.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/sde/type/{type_id}")
async def get_sde_type(type_id: int) -> dict[str, Any]:
    try:
        type_info = sde.get_type_info(type_id)
        if not type_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"type_id={type_id} was not found in SDE.",
            )

        attrs = sde.get_type_dogma_attributes(type_id)
        effects = sde.get_type_effects(type_id)
        return {
            "type": type_info,
            "dogma_attributes": attrs,
            "effects": effects,
        }
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def _resolve_fit_request(
    eft_text: str | None,
    fit: FitRequest | None,
    skills: list[Skill],
) -> FitRequest:
    if eft_text:
        parsed = eft_parser.parse_eft(eft_text)
        ship_type_id, modules = eft_parser.resolve_fit(parsed)
        if not modules:
            error_text = "; ".join(parsed.errors) if parsed.errors else "No modules could be resolved from EFT text."
            raise ValueError(error_text)
        return FitRequest(
            ship_type_id=ship_type_id,
            modules=modules,
            skills=skills,
        )

    if fit is None:
        raise ValueError("Either eft_text or fit must be provided.")
    if skills:
        return FitRequest(ship_type_id=fit.ship_type_id, modules=fit.modules, skills=skills)
    return fit
