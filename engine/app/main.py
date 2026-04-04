import logging

from fastapi import FastAPI

from app.routers.calc import router as calc_router
from app.services import sde

logger = logging.getLogger(__name__)

app = FastAPI(title="Volley Engine", version="0.1.0")
app.include_router(calc_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def startup() -> None:
    sde_ready = sde.ensure_sde_available(auto_download=True)
    if not sde_ready:
        logger.warning("SDE was not found and auto-download failed. SDE endpoints may not work.")
        return
    sde.preload_weapon_groups()
