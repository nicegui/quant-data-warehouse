"""同花顺概念板块成分 — ThsMemberCollector

Tushare ths_member API — 同花顺概念板块成分列表。
遍历所有 THS 指数，每个拉取成分股列表。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.ths import RawThsMember
from src.collectors.base import BaseTushareCollector
from src.collectors.impl._utils import _f

logger = logging.getLogger(__name__)


class ThsMemberCollector(BaseTushareCollector):
    def __init__(self, token: str):
        super().__init__("ths_member", token)

    @property
    def checkpoint_key(self):
        return "ts_code"

    def fetch(self, ts_code: str = "", con_code: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if con_code:
            params["con_code"] = con_code
        return self.api_call("ths_member", **params)

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for x in raw:
            rec = {
                "raw_json": json.dumps(x, ensure_ascii=False, default=str),
                "ts_code": str(x.get("ts_code", "")),
                "con_code": str(x.get("con_code", "")),
                "con_name": str(x.get("con_name", "")),
                "weight": _f(x.get("weight")),
                "in_date": str(x.get("in_date", "")) if x.get("in_date") else None,
                "out_date": str(x.get("out_date", "")) if x.get("out_date") else None,
                "is_new": str(x.get("is_new", "")) if x.get("is_new") else None,
            }
            validated.append(rec)
        return validated

    def store_raw(self, records: list[dict]) -> int:
        if not records:
            return 0
        written = 0
        with db_session() as session:
            pairs = {(r["ts_code"], r["con_code"]) for r in records}
            # batch load existing keys — one query instead of N
            from sqlalchemy import or_
            existing_rows = session.query(
                RawThsMember.ts_code, RawThsMember.con_code
            ).filter(
                RawThsMember.ts_code.in_([p[0] for p in pairs])
            ).all()
            existing_set = {(row.ts_code, row.con_code) for row in existing_rows}
            for rec in records:
                key = (rec["ts_code"], rec["con_code"])
                if key in existing_set:
                    continue
                session.add(RawThsMember(**rec))
                written += 1
        return written

    def _get_index_codes(self) -> list[str]:
        try:
            from src.db.session import get_session
            from sqlalchemy import text
            session = get_session()
            rows = session.execute(
                text("SELECT ts_code FROM ref_ths_index ORDER BY ts_code")
            ).fetchall()
            session.close()
            return [r[0] for r in rows]
        except Exception:
            return []

    def run(self, **kwargs) -> dict:
        codes = self._get_index_codes()
        if not codes:
            logger.warning("No THS index codes found — run ths_index first")
            return {"status": "error", "fetched": 0, "written": 0}

        stats = {"fetched": 0, "written": 0, "errors": 0, "codes": len(codes)}
        t0 = time.time()

        for i, code in enumerate(codes):
            time.sleep(0.20)
            try:
                raw = self.fetch(ts_code=code)
            except Exception:
                stats["errors"] += 1
                continue

            if not raw:
                continue

            validated = self.validate(raw)
            written = self.store_raw(validated)
            stats["fetched"] += len(validated)
            stats["written"] += written

            if (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(codes) - i - 1) / rate if rate > 0 else 0
                logger.info("[%s] %d/%d codes, %s rows | %.1f c/s ETA %.0fs",
                            code, i + 1, len(codes),
                            f"{stats['written']:,}", rate, eta)

        elapsed = time.time() - t0
        logger.info("ths_member DONE: %d codes, %s rows, %d errors, %.0fs",
                    len(codes), f"{stats['written']:,}",
                    stats["errors"], elapsed)
        return {
            "status": "success" if stats["errors"] < len(codes) * 0.1 else "partial",
            "fetched": stats["fetched"],
            "written": stats["written"],
            "codes": len(codes),
            "errors": stats["errors"],
            "elapsed": elapsed,
        }
