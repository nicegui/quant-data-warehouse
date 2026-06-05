"""KPL Concept (开盘啦题材) collector — concept list + constituents."""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from src.collectors.base import BaseTushareCollector
from src.models.kpl_concept import RawKplConcept, RawKplConceptCons

logger = logging.getLogger(__name__)


class KplConceptCollector(BaseTushareCollector):
    """Collect KPL concept list and constituent stocks."""

    model = RawKplConceptCons
    api_name = "kpl_concept_cons"
    checkpoint_key = "kpl_concept"

    def __init__(self, token: str):
        super().__init__("kpl_concept", token)

    def fetch(self, **kwargs) -> list[dict]:
        """Unused — custom run() delegates to fetch_concepts / fetch_cons."""
        return []

    def fetch_concepts(self) -> list[dict]:
        """Fetch all KPL concept codes."""
        return self.api_call("kpl_concept", limit=5000)

    def fetch_cons(self, ts_code: str, trade_date: Optional[str] = None) -> Optional[list]:
        """Fetch concept constituents."""
        params = {"ts_code": ts_code, "limit": 3000}
        if trade_date:
            params["trade_date"] = trade_date
        return self.api_call(self.api_name, **params)

    def validate_concept(self, raw: list[dict]) -> list[dict]:
        validated = []
        for row in raw:
            validated.append({
                "trade_date": str(row.get("trade_date", "")),
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")),
                "z_t_num": int(row["z_t_num"]) if row.get("z_t_num") else None,
                "up_num": str(row.get("up_num")) if row.get("up_num") else None,
            })
        return validated

    def validate(self, raw_data: list) -> list:
        validated = []
        for row in raw_data:
            validated.append({
                "ts_code": str(row.get("ts_code", "")),
                "name": str(row.get("name", "")),
                "con_name": str(row.get("con_name", "")),
                "con_code": str(row.get("con_code", "")),
                "trade_date": str(row.get("trade_date", "")),
                "desc": str(row.get("desc")) if row.get("desc") else None,
                "hot_num": int(row["hot_num"]) if row.get("hot_num") else None,
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        """Not called; inline in run()."""
        return len(records)

    def run(self) -> dict:
        """Full historical backfill: concept list → all constituents."""
        from src.db.session import db_session

        total_concepts = 0
        total_cons = 0
        errors = 0
        t0 = time.time()

        # Step 1: Get concept list
        logger.info("Fetching KPL concept list...")
        concepts_raw = self.fetch_concepts()
        if not concepts_raw:
            return {"status": "empty", "fetched": 0, "written": 0}

        concepts = self.validate_concept(concepts_raw)
        logger.info(f"Got {len(concepts)} concepts")

        # Step 1b: Store concept list
        total_concepts += self._store_dedup(RawKplConcept, concepts, ["ts_code", "trade_date"])

        # Step 2: Get checkpoint — which concept index to resume from
        last_idx = self.get_checkpoint_date()
        start_idx = int(last_idx) if last_idx else 0
        if start_idx > 0:
            logger.info(f"Resuming from concept index {start_idx}")

        # Step 3: Iterate concepts
        concept_codes = list(dict.fromkeys(c["ts_code"] for c in concepts))  # unique, order preserved

        for i, ts_code in enumerate(concept_codes):
            if i < start_idx:
                continue

            try:
                raw_cons = self.fetch_cons(ts_code)
                if raw_cons:
                    validated = self.validate(raw_cons)
                    total_cons += self._store_dedup(
                        RawKplConceptCons, validated, ["ts_code", "con_code", "trade_date"]
                    )
                    logger.info(f"[{i+1}/{len(concept_codes)}] {ts_code} => {len(raw_cons)} rows")
                else:
                    logger.info(f"[{i+1}/{len(concept_codes)}] {ts_code} => EMPTY")

                time.sleep(0.22)

            except Exception as e:
                logger.error(f"[{ts_code}] ERROR: {e}")
                errors += 1

            # Checkpoint every 20 concepts
            if (i + 1) % 20 == 0:
                self._update_checkpoint(str(i + 1), total_cons)

        # Final checkpoint
        self._update_checkpoint(str(len(concept_codes)), total_cons)
        elapsed = time.time() - t0
        logger.info(
            f"kpl_concept DONE: {len(concept_codes)} concepts, "
            f"{total_concepts} concept-meta + {total_cons} constituents, "
            f"{errors} errors, {int(elapsed)}s"
        )
        return {
            "status": "success",
            "concepts": len(concept_codes),
            "concept_meta": total_concepts,
            "constituents": total_cons,
            "errors": errors,
            "elapsed": elapsed,
        }
