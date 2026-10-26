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


class GcsStorage:
    """Cloud Storage BlobStorage. The bucket has a 30-day lifecycle delete rule (see infra/deploy.sh)."""

    def __init__(self, bucket: str, client=None):
        if client is None:
            from google.cloud import storage

            client = storage.Client()
        self.bucket = client.bucket(bucket)

    def save(self, key: str, data: bytes, content_type: str) -> str:
        self.bucket.blob(key).upload_from_string(data, content_type=content_type)
        return key

    def read(self, key: str) -> bytes:
        return self.bucket.blob(key).download_as_bytes()
