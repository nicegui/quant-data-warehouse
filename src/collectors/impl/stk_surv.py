"""机构调研 — StkSurvCollector

Tushare stk_surv API — 上市公司机构调研记录。
Per-stock API（单次最大100条），自动分页防截断。
串行遍历全市场，checkpoint 断点续传。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from src.db.session import db_session
from src.models.news import RawStkSurv
from src.collectors.base import BaseTushareCollector

logger = logging.getLogger(__name__)

# Years to paginate for stocks with >100 records
_PAGE_YEARS = list(range(2010, 2027))


class StkSurvCollector(BaseTushareCollector):
    """机构调研 collector — 全市场遍历，自动分页."""

    def __init__(self, token: str):
        super().__init__("stk_surv", token)

    @property
    def checkpoint_key(self) -> str:
        return "ts_code"

    # ── Fetch ───────────────────────────────────────────

    def fetch(self, ts_code: str = "", trade_date: str = "",
              start_date: str = "", end_date: str = "", **kwargs) -> list[dict]:
        params: dict[str, Any] = {}
        if ts_code:
            params["ts_code"] = ts_code
        if trade_date:
            params["trade_date"] = trade_date
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        params.update({k: v for k, v in kwargs.items() if v})
        return self.api_call("stk_surv", **params)

    def fetch_all_stock(self, ts_code: str) -> list[dict]:
        """Fetch all surveys for one stock, paginating if >100 rows.

        Most stocks have <100 surveys total (one call suffices).
        Hot stocks (e.g. 300750.SZ) need year-by-year pagination.
        """
        raw = self.fetch(ts_code=ts_code, start_date="20100101", end_date="20300101")
        if len(raw) < 100:
            return raw

        # Paginate by year to stay under 100-row limit
        logger.info("%s: %d rows, paginating by year", ts_code, len(raw))
        result = []
        for yr in _PAGE_YEARS:
            time.sleep(0.35)  # 200次/分钟限制
            chunk = self.fetch(
                ts_code=ts_code,
                start_date=f"{yr}0101",
                end_date=f"{yr}1231",
            )
            result.extend(chunk)
            if len(chunk) >= 100:
                # Rare: even a single year has >100 — split by half-year
                logger.warning("%s: yr %d has %d rows, half-year split", ts_code, yr, len(chunk))
                extra = []
                for half, (h_start, h_end) in enumerate([
                    (f"{yr}0101", f"{yr}0630"),
                    (f"{yr}0701", f"{yr}1231"),
                ]):
                    time.sleep(0.35)
                    h_chunk = self.fetch(ts_code=ts_code, start_date=h_start, end_date=h_end)
                    extra.extend(h_chunk)
                result.extend(extra)
        return result

    # ── Validate ────────────────────────────────────────

    def validate(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "ts_code": row.get("ts_code", ""),
                "name": row.get("name", ""),
                "surv_date": row.get("surv_date", ""),
                "fund_visitors": str(row.get("fund_visitors", "")) if row.get("fund_visitors") else None,
                "rece_place": row.get("rece_place"),
                "rece_mode": row.get("rece_mode"),
                "rece_org": row.get("rece_org"),
                "org_type": row.get("org_type"),
                "comp_rece": row.get("comp_rece"),
                "content": row.get("content"),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })
        return validated

    # ── Store ───────────────────────────────────────────

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(RawStkSurv, records, ["ts_code", "surv_date", "rece_org"])

    # ── Run ─────────────────────────────────────────────

    def run(self, **kwargs) -> dict:
        """全市场遍历，checkpoint 断点续传。"""
        try:
            df = self.pro.stock_basic(exchange="", list_status="L", fields="ts_code")
            all_stocks = sorted(df["ts_code"].tolist())
        except Exception as e:
            logger.error("Failed to get stock list: %s", e)
            return {"status": "failed", "error": str(e), "fetched": 0, "written": 0}

        existing_stocks: set[str] = set()
        try:
            from src.db import nas_duckdb
            result = nas_duckdb.query("SELECT DISTINCT ts_code FROM raw_stk_surv")
            existing_stocks = {row[0] for row in result["rows"] if row[0]}
        except Exception:
            pass

        last_processed = self.get_checkpoint_date() or ""
        start_idx = 0
        if last_processed:
            for i, code in enumerate(all_stocks):
                if code >= last_processed:
                    start_idx = i
                    break

        pending = [s for s in all_stocks[start_idx:] if s not in existing_stocks]
        if not pending:
            logger.info("stk_surv: all %d stocks up to date", len(all_stocks))
            return {"status": "success", "fetched": 0, "written": 0}

        logger.info("stk_surv: %d/%d pending", len(pending), len(all_stocks))

        total_fetched, total_written, total_errors = 0, 0, 0
        t0 = time.time()

        for i, sc in enumerate(pending):
            try:
                raw = self.fetch_all_stock(sc)
            except Exception as e:
                if "频率超限" in str(e):
                    time.sleep(3)
                    raw = self.fetch_all_stock(sc)
                else:
                    logger.error("[%d/%d] %s ERROR: %s", i + 1, len(pending), sc, e)
                    total_errors += 1
                    self._update_checkpoint(sc, total_written)
                    continue

            if raw:
                validated = self.validate(raw)
                written = self.store_raw(validated)
                total_fetched += len(raw)
                total_written += written

            self._update_checkpoint(sc, total_written)

            if (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(pending) - i - 1) / rate if rate > 0 else 0
                logger.info("[%d/%d] %s +%d rows | %.1f s/s ETA %.0fs",
                            i + 1, len(pending), sc, total_written, rate, eta)

            time.sleep(0.20)

        return {
            "status": "success" if total_errors == 0 else "partial",
            "fetched": total_fetched,
            "written": total_written,
            "errors": total_errors,
        }
