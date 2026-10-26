from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes.v1 import router as v1_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        sched = None
        if settings.scheduler_enabled:
            from app.deps import get_container
            from app.scheduler import start

            sched = start(get_container(), settings.scheduler_minutes)
        yield
        if sched:
            sched.shutdown(wait=False)

    app = FastAPI(
        title=f"{settings.carrier_name} API",
        version="0.2.0",
        description="Arizona demo. All non-LIVE data is labelled SYNTHETIC / SIMULATED / AI.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3100", "http://127.0.0.1:3100"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    health = APIRouter()

    @health.get("/healthz", tags=["system"])
    def healthz() -> dict:
        return {
            "status": "ok",
            "carrier": settings.carrier_name,
            "demo_mode": settings.demo_mode,
            "firestore_emulator": bool(settings.firestore_emulator_host),
            "scheduler": settings.scheduler_enabled,
        }

    app.include_router(health)
    app.include_router(health, prefix=API_PREFIX)
    app.include_router(v1_router, prefix=API_PREFIX)
    return app


app = create_app()
