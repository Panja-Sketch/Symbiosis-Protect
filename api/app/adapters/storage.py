"""Blob storage adapter for proof photos/documents. Local disk in dev; Cloud Storage in cloud (Phase 9)."""

import hashlib
from pathlib import Path
from typing import Protocol


class BlobStorage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> str: ...
    def read(self, key: str) -> bytes: ...


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if self.root.resolve() not in p.parents:
            raise ValueError("invalid storage key")
        return p

    def save(self, key: str, data: bytes, content_type: str) -> str:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return key

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
