from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.carrier_name} API",
        version="0.1.0",
        description="Arizona demo. All non-LIVE data is labelled SYNTHETIC / SIMULATED / AI.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3100", "http://127.0.0.1:3100"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter()

    @router.get("/healthz", tags=["system"])
    def healthz() -> dict:
        return {
            "status": "ok",
            "carrier": settings.carrier_name,
            "demo_mode": settings.demo_mode,
            "firestore_emulator": bool(settings.firestore_emulator_host),
        }

    app.include_router(router)
    app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
