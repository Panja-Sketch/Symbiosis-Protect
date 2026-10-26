"""Document store behind the engine: in-memory (tests) or Firestore (emulator/cloud)."""

import copy
from typing import Protocol


class Store(Protocol):
    def get(self, col: str, id: str) -> dict | None: ...
    def put(self, col: str, id: str, doc: dict) -> None: ...
    def delete(self, col: str, id: str) -> None: ...
    def list(self, col: str, **where) -> list[dict]: ...


class MemoryStore:
    def __init__(self):
        self._c: dict[str, dict[str, dict]] = {}

    def get(self, col, id):
        d = self._c.get(col, {}).get(id)
        return copy.deepcopy(d) if d is not None else None

    def put(self, col, id, doc):
        self._c.setdefault(col, {})[id] = copy.deepcopy(doc)

    def delete(self, col, id):
        self._c.get(col, {}).pop(id, None)

    def list(self, col, **where):
        rows = [copy.deepcopy(d) for d in self._c.get(col, {}).values()]
        return [r for r in rows if all(r.get(k) == v for k, v in where.items())]


class FirestoreStore:
    def __init__(self, db):
        self._db = db

    def get(self, col, id):
        s = self._db.collection(col).document(id).get()
        return s.to_dict() if s.exists else None

    def put(self, col, id, doc):
        self._db.collection(col).document(id).set(doc)

    def delete(self, col, id):
        self._db.collection(col).document(id).delete()

    def list(self, col, **where):
        q = self._db.collection(col)
        for k, v in where.items():
            q = q.where(k, "==", v)
        return [s.to_dict() for s in q.stream()]
