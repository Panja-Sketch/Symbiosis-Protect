"""TTL caches: in-memory (tests / no emulator) and Firestore (`cache` collection, expires_at)."""

import hashlib
import json
import time
from datetime import UTC, datetime, timedelta


class MemoryCache:
    def __init__(self, clock=time.time):
        self._d: dict[str, tuple[float, str]] = {}
        self._clock = clock

    def get(self, key):
        hit = self._d.get(key)
        if not hit or hit[0] < self._clock():
            return None
        return json.loads(hit[1])

    def set(self, key, value, ttl_seconds):
        self._d[key] = (self._clock() + ttl_seconds, json.dumps(value, default=str))


class FirestoreCache:
    def __init__(self, db, collection="cache"):
        self._col = db.collection(collection)

    @staticmethod
    def _id(key: str) -> str:
        return hashlib.sha1(key.encode()).hexdigest()

    def get(self, key):
        snap = self._col.document(self._id(key)).get()
        if not snap.exists:
            return None
        d = snap.to_dict()
        if d["expires_at"] < datetime.now(UTC):
            return None
        return json.loads(d["payload"])

    def set(self, key, value, ttl_seconds):
        self._col.document(self._id(key)).set({
            "key": key, "payload": json.dumps(value, default=str),
            "expires_at": datetime.now(UTC) + timedelta(seconds=ttl_seconds),  # Firestore TTL field
        })
