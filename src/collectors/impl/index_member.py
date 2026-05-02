"""申万行业成分构成 — IndexMemberCollector."""
import logging
import time

from src.collectors.base import BaseTushareCollector
from src.models.index_member import RawIndexMember

logger = logging.getLogger(__name__)


class IndexMemberCollector(BaseTushareCollector):
    """申万行业成分构成 (index_member_all API)."""

    model = RawIndexMember
    api_name = "index_member_all"
    checkpoint_key = "index_member"

    def __init__(self, token: str):
        super().__init__("index_member_all", token)

    def fetch(self, l3_code: str = "", **kwargs) -> list[dict]:
        return self.api_call(self.api_name, l3_code=l3_code, is_new="Y", limit=2000)

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
        """Not called; inline in run()."""
        return len(records)

    def run(self) -> dict:
        from sqlalchemy import text
        from src.db.session import db_session, get_session

        t0 = time.time()
        total, errors = 0, 0

        session = get_session()
        l3_codes = [r[0] for r in session.execute(
            text("SELECT DISTINCT index_code FROM ref_index_classify WHERE level='L3'")
        ).fetchall()]
        session.close()

        logger.info(f"Found {len(l3_codes)} L3 industry codes")

        for i, l3_code in enumerate(l3_codes):
            try:
                raw = self.fetch(l3_code=l3_code)
                if raw:
                    validated = self.validate(raw)
                    with db_session() as s:
                        for rec in validated:
                            existing = s.query(RawIndexMember).filter_by(
                                l3_code=rec["l3_code"],
                                ts_code=rec["ts_code"],
                            ).first()
                            if not existing:
                                s.add(RawIndexMember(**rec))
                                total += 1
                        s.commit()
            except Exception as e:
                logger.error(f"[{l3_code}] ERROR: {e}")
                errors += 1

            if (i + 1) % 50 == 0:
                logger.info(f"[{i+1}/{len(l3_codes)}] {total:,} rows")

            time.sleep(0.21)

        elapsed = time.time() - t0
        logger.info(
            f"index_member DONE: {len(l3_codes)} industries, "
            f"{total:,} rows, {errors} err, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "industries": len(l3_codes),
            "written": total,
            "errors": errors,
            "elapsed": elapsed,
        }
