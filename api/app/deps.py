"""Wiring: builds the adapters + engine once. Firestore when an emulator/cloud project is configured, else memory."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.adapters.cache import FirestoreCache, MemoryCache
from app.adapters.history import DerivedHistoryProvider
from app.adapters.notifier import ConsoleEmailNotifier, InAppNotifier, NotifierChain
from app.adapters.scenario import ScenarioProvider
from app.adapters.storage import BlobStorage, LocalStorage
from app.adapters.weather import CompositeWeatherProvider, NWSProvider, OpenMeteoProvider
from app.ai.service import Assistant, load_cfg
from app.config import Settings, get_settings
from app.engine.engine import Engine
from app.engine.playbooks import Config, load_config, load_rules
from app.seed import load_derived, seed_store
from app.sense.service import SenseService
from app.store import FirestoreStore, MemoryStore, Store


@dataclass
class Container:
    settings: Settings
    store: Store
    engine: Engine
    weather: ScenarioProvider
    history: DerivedHistoryProvider
    config: Config
    email: ConsoleEmailNotifier
    storage: BlobStorage
    assistant: Assistant
    sense: SenseService


def build_container(settings: Settings | None = None, store: Store | None = None, cache=None, weather=None, storage=None, gemini=None) -> Container:
    s = settings or get_settings()
    if store is None:
        if s.firestore_emulator_host:
            from app.db import get_db

            db = get_db()
            store, cache = FirestoreStore(db), cache or FirestoreCache(db)
        else:
            store = MemoryStore()
    cache = cache or MemoryCache()
    if not store.list("accounts"):
        seed_store(store)
    history = DerivedHistoryProvider(load_derived())
    live = weather or CompositeWeatherProvider(NWSProvider(s.nws_user_agent, cache), OpenMeteoProvider(cache))
    scenario = ScenarioProvider(live, store, history)
    email = ConsoleEmailNotifier(store)
    config = load_config()
    engine = Engine(store, scenario, history, NotifierChain(InAppNotifier(store), email), load_rules(), config)
    root = Path(__file__).resolve().parents[2] / s.local_storage_dir
    if gemini is None and s.ai_enabled:
        from app.ai.gemini import GeminiExplainer

        gemini = GeminiExplainer(s.google_cloud_project, s.google_cloud_location, s.gemini_model)
    assistant = Assistant(store, cache, load_cfg(), gemini, s.ai_asks_per_hour, s.gemini_model)
    return Container(s, store, engine, scenario, history, config, email, storage or LocalStorage(root), assistant, SenseService(store, engine))


@lru_cache
def get_container() -> Container:
    return build_container()
