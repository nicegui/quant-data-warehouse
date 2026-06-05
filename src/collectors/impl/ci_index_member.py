"""中信行业成分 — CiIndexMemberCollector."""
import logging
import time

from src.collectors.base import BaseTushareCollector
from src.models.ci_index_member import RawCiIndexMember

logger = logging.getLogger(__name__)


class CiIndexMemberCollector(BaseTushareCollector):
    """中信行业成分 (ci_index_member API)."""

    model = RawCiIndexMember
    api_name = "ci_index_member"
    checkpoint_key = "ci_index_member"

    def __init__(self, token: str):
        super().__init__("ci_index_member", token)

    def fetch(self, ts_code: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, ts_code=ts_code, is_new="Y", limit=5000)

    def validate(self, raw: list[dict]) -> list[dict]:
        _s = lambda v: str(v) if v is not None else None
        validated = []
        for row in raw:
            validated.append({
                "l1_code": str(row.get("l1_code", "")),
                "l1_name": str(row.get("l1_name", "")),
                "l2_code": str(row.get("l2_code", "")),
                "l2_name": str(row.get("l2_name", "")),
                "l3_code": str(row.get("l3_code", "")),
                "l3_name": str(row.get("l3_name", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")),
                "in_date": _s(row.get("in_date")),
                "out_date": _s(row.get("out_date")),
                "is_new": _s(row.get("is_new")),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return len(records)

    def run(self) -> dict:
        from sqlalchemy import text
        from src.db.session import db_session, get_session

        t0 = time.time()
        total, errors = 0, 0

        session = get_session()
        stocks = [r[0] for r in session.execute(
            text("SELECT ts_code FROM ref_stock_basic WHERE list_status='L'")
        ).fetchall()]
        session.close()

        logger.info(f"Found {len(stocks)} listed stocks")

        for i, ts_code in enumerate(stocks):
            try:
                raw = self.fetch(ts_code=ts_code)
                if raw:
                    validated = self.validate(raw)
                    written = self._store_dedup(RawCiIndexMember, validated, ["ts_code", "l3_code"])
                    total += written
            except Exception as e:
                logger.error(f"[{ts_code}] ERROR: {e}")
                errors += 1

            if (i + 1) % 500 == 0:
                logger.info(f"[{i+1}/{len(stocks)}] {total:,} rows | {(i+1)/(time.time()-t0):.1f} stk/s")

            time.sleep(0.21)

        elapsed = time.time() - t0
        logger.info(
            f"ci_index_member DONE: {len(stocks)} stocks, "
            f"{total:,} rows, {errors} err, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "stocks": len(stocks),
            "written": total,
            "errors": errors,
            "elapsed": elapsed,
        }
