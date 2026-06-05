"""Polymarket prediction market data collector.

Fetches from 2 public REST APIs:
  - Gamma API:   Events + markets discovery
  - CLOB API:    Current prices (midpoint)

Stores to:
  - raw_polymarket_events   — event metadata
  - raw_polymarket_markets  — market details + current prices
  - raw_polymarket_prices   — daily price snapshots (build history over time)

No authentication required. Run daily to accumulate price history.
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any

from src.collectors.base import BaseCollector
from src.db.session import db_session
from src.models.polymarket import (
    RawPolymarketEvent,
    RawPolymarketMarket,
    RawPolymarketPrice,
)

GAMMA = "https://gamma-api.polymarket.com"
CLOB  = "https://clob.polymarket.com"
UA    = "hermes-quant/1.0"


class PolymarketCollector(BaseCollector):
    """Collect Polymarket prediction market data.

    Daily snapshots for price history — run via cron.
    """

    def __init__(self, name: str = "polymarket"):
        super().__init__(name)
        self._rate_delay = 0.3   # seconds between requests
        self._top_n_events = 20  # trending events to fetch
        self._max_markets_per_event = 10

    # ── REST helpers ──

    def _get(self, url: str) -> dict | list | None:
        time.sleep(self._rate_delay)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} on {url[:80]}")
            return None
        except Exception as e:
            print(f"  Error on {url[:80]}: {e}")
            return None

    def _parse_double_encoded(self, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return val
        return val

    # ── Fetch methods ──

    def _fetch_trending_events(self) -> list[dict]:
        url = f"{GAMMA}/events?limit={self._top_n_events}&active=true&closed=false&order=volume&ascending=false"
        data = self._get(url)
        if not isinstance(data, list):
            print("  No events returned")
            return []
        print(f"  Fetched {len(data)} trending events")
        return data

    # ── BaseCollector interface ──

    def fetch(self, **kwargs) -> dict[str, list[dict]]:
        """Fetch events + markets + current prices (from Gamma outcomePrices)."""
        events_raw = self._fetch_trending_events()
        markets_raw = []
        prices_raw = []

        snapshot_ts = datetime.now(timezone.utc)

        for event in events_raw:
            event_id = event.get("id", "")
            mkt_list = event.get("markets", [])[:self._max_markets_per_event]

            for m in mkt_list:
                m["event_id"] = event_id
                markets_raw.append(m)

                # Get current price from Gamma's outcomePrices (Yes = index 0)
                prices = self._parse_double_encoded(m.get("outcomePrices", "[]"))
                yes_price = None
                if isinstance(prices, list) and len(prices) > 0:
                    try:
                        yes_price = float(prices[0])
                    except (ValueError, TypeError):
                        pass

                if yes_price is not None:
                    prices_raw.append({
                        "condition_id": m.get("conditionId", ""),
                        "timestamp": snapshot_ts,
                        "price": yes_price,
                    })

        print(f"  Events: {len(events_raw)}  Markets: {len(markets_raw)}  Prices: {len(prices_raw)}")
        return {"events": events_raw, "markets": markets_raw, "prices": prices_raw}

    def validate(self, raw: dict[str, list[dict]]) -> dict[str, list[dict]]:
        """Validate and canonicalize."""
        validated_events = []
        for row in raw.get("events", []):
            validated_events.append({
                "event_id": str(row.get("id", "")),
                "title": row.get("title", "")[:500],
                "slug": row.get("slug", "")[:200],
                "description": row.get("description", ""),
                "category": row.get("category", ""),
                "tags": json.dumps(row.get("tags", []), ensure_ascii=False),
                "volume": row.get("volume"),
                "liquidity": row.get("liquidity"),
                "active": row.get("active"),
                "closed": row.get("closed"),
                "start_date": self._parse_dt(row.get("startDate")),
                "end_date": self._parse_dt(row.get("endDate")),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })

        validated_markets = []
        for row in raw.get("markets", []):
            outcome_prices = self._parse_double_encoded(row.get("outcomePrices", "[]"))
            outcomes = self._parse_double_encoded(row.get("outcomes", "[]"))
            clob_token_ids = self._parse_double_encoded(row.get("clobTokenIds", "[]"))

            validated_markets.append({
                "condition_id": str(row.get("conditionId", "")),
                "event_id": str(row.get("event_id", "")),
                "question": row.get("question", ""),
                "slug": row.get("slug", ""),
                "outcomes": json.dumps(outcomes, ensure_ascii=False),
                "outcome_prices": json.dumps(outcome_prices, ensure_ascii=False),
                "clob_token_ids": json.dumps(clob_token_ids, ensure_ascii=False),
                "volume": row.get("volume"),
                "liquidity": row.get("liquidity"),
                "active": row.get("active"),
                "closed": row.get("closed"),
                "end_date": self._parse_dt(row.get("endDate")),
                "category": row.get("category", ""),
                "raw_json": json.dumps(row, ensure_ascii=False, default=str),
            })

        validated_prices = []
        for row in raw.get("prices", []):
            if row.get("price") is None:
                continue
            validated_prices.append({
                "condition_id": str(row.get("condition_id", "")),
                "timestamp": row.get("timestamp"),
                "price": float(row["price"]),
            })

        return {
            "events": validated_events,
            "markets": validated_markets,
            "prices": validated_prices,
        }

    def store_raw(self, records: dict[str, list[dict]]) -> int:
        """Dedup and store. Prices are upserted (update price for same day)."""
        total = 0

        # Events (dedup by event_id)
        with db_session() as session:
            for rec in records.get("events", []):
                existing = session.query(RawPolymarketEvent).filter_by(
                    event_id=rec["event_id"]
                ).first()
                if existing:
                    # Update if event is still active
                    if rec.get("active") is not None:
                        existing.volume = rec.get("volume", existing.volume)
                        existing.active = rec.get("active", existing.active)
                        existing.closed = rec.get("closed", existing.closed)
                        total += 1
                    continue
                session.add(RawPolymarketEvent(**rec))
                total += 1

        # Markets (dedup by condition_id)
        with db_session() as session:
            for rec in records.get("markets", []):
                existing = session.query(RawPolymarketMarket).filter_by(
                    condition_id=rec["condition_id"]
                ).first()
                if existing:
                    # Update outcome prices
                    existing.outcome_prices = rec.get("outcome_prices", existing.outcome_prices)
                    existing.volume = rec.get("volume", existing.volume)
                    existing.active = rec.get("active", existing.active)
                    existing.closed = rec.get("closed", existing.closed)
                    total += 1
                    continue
                session.add(RawPolymarketMarket(**rec))
                total += 1

        # Prices — one row per market per day (upsert)
        with db_session() as session:
            for rec in records.get("prices", []):
                # Truncate timestamp to date boundary for daily snapshots
                ts_date = rec["timestamp"].replace(hour=0, minute=0, second=0, microsecond=0)
                existing = session.query(RawPolymarketPrice).filter_by(
                    condition_id=rec["condition_id"],
                    timestamp=ts_date,
                ).first()
                if existing:
                    existing.price = rec["price"]
                    total += 1
                    continue
                rec_copy = dict(rec)
                rec_copy["timestamp"] = ts_date
                session.add(RawPolymarketPrice(**rec_copy))
                total += 1

        return total

    def _parse_dt(self, val) -> datetime | None:
        if not val:
            return None
        try:
            s = str(val).replace("Z", "+00:00")
            return datetime.fromisoformat(s)
        except (ValueError, TypeError):
            return None
