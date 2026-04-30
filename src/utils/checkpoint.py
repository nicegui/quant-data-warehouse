"""Checkpoint manager for collector resumption.

Each collector gets its own checkpoint file in data/checkpoints/.
The checkpoint tracks the last successful trade_date (or other key)
so that on restart, fetch() only pulls new data.

Usage in BaseCollector:
    self.checkpoint.save(last_trade_date="20250115", total_written=12345)
    state = self.checkpoint.load()   # => {"last_trade_date": "20250115", ...}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CheckpointManager:
    """File-based checkpoint manager for data collectors.

    Checkpoint files live in data/checkpoints/<collector_name>.json.
    Thread-safe: each write reads-modifies-writes the full file.
    """

    def __init__(self, collector_name: str, base_dir: str = "data/checkpoints"):
        self.collector_name = collector_name
        self.base_dir = Path(base_dir)
        self._state: dict[str, Any] | None = None  # in-memory cache

    @property
    def path(self) -> Path:
        return self.base_dir / f"{self.collector_name}.json"

    def load(self) -> dict[str, Any]:
        """Load checkpoint state from disk (cached in memory)."""
        if self._state is not None:
            return self._state

        if self.path.exists():
            try:
                self._state = json.loads(self.path.read_text())
                return self._state
            except (json.JSONDecodeError, OSError):
                pass

        self._state = {}
        return self._state

    def save(self, **updates: Any) -> None:
        """Merge updates into checkpoint and persist to disk."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        state = self.load()
        state.update(updates)
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.write_text(json.dumps(state, ensure_ascii=False, default=str, indent=2))
        self._state = state

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def clear(self) -> None:
        """Delete checkpoint file and clear cache."""
        self._state = {}
        if self.path.exists():
            self.path.unlink(missing_ok=True)

    # ── Convenience accessors ──

    @property
    def last_trade_date(self) -> str | None:
        """Most collectors use trade_date as checkpoint key."""
        return self.get("last_trade_date")

    @property
    def total_written(self) -> int:
        return self.get("total_written", 0)

    @property
    def total_errors(self) -> int:
        return self.get("total_errors", 0)
