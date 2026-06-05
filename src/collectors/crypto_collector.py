"""加密货币行情 — CryptoOhlcvCollector

Uses CCXT library to pull OHLCV from Binance/OKX/etc.
Supports multiple timeframes and multiple symbols.
"""

from __future__ import annotations

import json
from typing import Any

from src.db.session import db_session
from src.models.market import RawCryptoOhlcv, CuratedCryptoOhlcv
from src.collectors.base import BaseCollector


_SYMBOL_MAP = {
    "BTC/USDT": "BTCUSDT",
    "ETH/USDT": "ETHUSDT",
    "SOL/USDT": "SOLUSDT",
    "BNB/USDT": "BNBUSDT",
    "DOGE/USDT": "DOGEUSDT",
}

_TIMEFRAME_MAP = {
    "1d": "1d",
    "4h": "4h",
    "1h": "1h",
    "15m": "15m",
    "5m": "5m",
}


class CryptoOhlcvCollector(BaseCollector):
    """Crypto OHLCV collector via CCXT."""

    def __init__(self, exchange: str = "binance"):
        super().__init__("crypto_ohlcv")
        self.exchange = exchange
        self._api = None

    @property
    def api(self):
        """Lazy CCXT exchange instance."""
        if self._api is None:
            import ccxt
            self._api = getattr(ccxt, self.exchange)({
                "enableRateLimit": True,
            })
        return self._api

    def fetch(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1d",
        limit: int = 100,
        since: str = "",
        **kwargs,
    ) -> list[dict]:
        """Fetch OHLCV candles.

        Args:
            symbol: trading pair (e.g. 'BTC/USDT')
            timeframe: 1d | 4h | 1h | 15m | 5m
            limit: max candles to fetch
            since: ISO timestamp string
        """
        try:
            since_ts = None
            if since:
                import time
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                since_ts = int(dt.timestamp() * 1000)

            ohlcv = self.api.fetch_ohlcv(symbol, timeframe, since=since_ts, limit=limit)

            records = []
            for candle in ohlcv:
                records.append({
                    "exchange": self.exchange,
                    "symbol": _SYMBOL_MAP.get(symbol, symbol.replace("/", "")),
                    "timestamp_ms": candle[0],
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                    "timeframe": _TIMEFRAME_MAP.get(timeframe, timeframe),
                    "raw_json": json.dumps({
                        "ts": candle[0],
                        "o": candle[1],
                        "h": candle[2],
                        "l": candle[3],
                        "c": candle[4],
                        "v": candle[5],
                    }),
                })
            return records
        except Exception:
            return []

    def validate(self, raw: list[dict]) -> list[dict]:
        from datetime import datetime, timezone

        validated = []
        for row in raw:
            ts_ms = row.get("timestamp_ms", 0)
            timestamp = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            validated.append({
                "exchange": row["exchange"],
                "symbol": row["symbol"],
                "timestamp": timestamp,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
                "timeframe": row["timeframe"],
                "raw_json": row.get("raw_json"),
            })
        return validated

    def store_raw(self, records: list[dict]) -> int:
        return self._store_dedup(
            RawCryptoOhlcv, records,
            ["exchange", "symbol", "timestamp", "timeframe"]
        )

    def compute_curated(self, symbol: str = "BTCUSDT", timeframe: str = "1d") -> int:
        """Copy from raw to curated (simple pass-through for now)."""
        from src.db import nas_duckdb
        written = 0
        try:
            result = nas_duckdb.query(
                f"SELECT * FROM raw_crypto_ohlcv "
                f"WHERE symbol='{symbol}' AND timeframe='{timeframe}' "
                f"ORDER BY timestamp ASC"
            )
            cols = result["columns"]
            for row in result["rows"]:
                raw_row = dict(zip(cols, row))
                # Upsert to curated
                nas_duckdb.upsert("curated_crypto_ohlcv", [{
                    "asset_id": None,
                    "timestamp": raw_row["timestamp"],
                    "open": raw_row["open"],
                    "high": raw_row["high"],
                    "low": raw_row["low"],
                    "close": raw_row["close"],
                    "volume": raw_row["volume"],
                    "timeframe": raw_row["timeframe"],
                }], ["timestamp", "timeframe"])
                written += 1
        except Exception:
            # Fallback to local
            with db_session() as session:
                raw_rows = (
                    session.query(RawCryptoOhlcv)
                    .filter_by(symbol=symbol, timeframe=timeframe)
                    .order_by(RawCryptoOhlcv.timestamp.asc())
                    .all()
                )
                for raw_row in raw_rows:
                    existing = session.query(CuratedCryptoOhlcv).filter_by(
                        asset_id=None,
                        timestamp=raw_row.timestamp,
                        timeframe=raw_row.timeframe,
                    ).first()
                    if existing:
                        continue
                    curated = CuratedCryptoOhlcv(
                        asset_id=None,
                        timestamp=raw_row.timestamp,
                        open=raw_row.open,
                        high=raw_row.high,
                        low=raw_row.low,
                        close=raw_row.close,
                        volume=raw_row.volume,
                        timeframe=raw_row.timeframe,
                    )
                    session.add(curated)
                    written += 1
        return written
