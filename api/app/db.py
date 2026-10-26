import os
from functools import lru_cache

from google.auth.credentials import AnonymousCredentials
from google.cloud import firestore

from app.config import get_settings


@lru_cache
def get_db() -> firestore.Client:
    s = get_settings()
    if s.firestore_emulator_host:
        # The client reads FIRESTORE_EMULATOR_HOST from the environment; credentials aren't needed.
        os.environ.setdefault("FIRESTORE_EMULATOR_HOST", s.firestore_emulator_host)
        return firestore.Client(project=s.google_cloud_project, credentials=AnonymousCredentials())
    return firestore.Client(project=s.google_cloud_project)
