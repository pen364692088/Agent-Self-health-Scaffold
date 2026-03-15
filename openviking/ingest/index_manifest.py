#!/usr/bin/env python3
"""Persistent idempotency manifest for OpenViking embedding operations."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, Any


DEFAULT_MANIFEST_PATH = Path("/home/moonlight/.openclaw/workspace/artifacts/openviking/index_manifest.json")


@dataclass
class ManifestRecord:
    doc_id: str
    doc_content_hash: str
    chunker_version: str
    embedding_version: str
    embedding_complete: bool
    embedding_coverage_pct: float
    indexed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


class IndexManifest:
    def __init__(self, path: str | Path = DEFAULT_MANIFEST_PATH):
        self.path = Path(path)
        self._data: Dict[str, Any] = {"version": "index_manifest.v1", "docs": {}}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._data = {"version": "index_manifest.v1", "docs": {}}
            return
        try:
            self._data = json.loads(self.path.read_text())
            if "docs" not in self._data or not isinstance(self._data["docs"], dict):
                self._data["docs"] = {}
        except Exception:
            self._data = {"version": "index_manifest.v1", "docs": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2) + "\n")

    def get(self, doc_id: str) -> dict | None:
        return self._data.get("docs", {}).get(doc_id)

    def upsert(self, record: ManifestRecord) -> None:
        self._data.setdefault("docs", {})[record.doc_id] = record.to_dict()

    def should_skip(
        self,
        *,
        doc_id: str,
        doc_content_hash: str,
        chunker_version: str,
        embedding_version: str,
        min_coverage: float = 0.98,
    ) -> bool:
        rec = self.get(doc_id)
        if not rec:
            return False
        return (
            rec.get("embedding_complete") is True
            and rec.get("doc_content_hash") == doc_content_hash
            and rec.get("chunker_version") == chunker_version
            and rec.get("embedding_version") == embedding_version
            and float(rec.get("embedding_coverage_pct", 0.0)) >= min_coverage
        )


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
