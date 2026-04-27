"""Tests for Tushare collectors."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.collectors.tushare_collector import ConsultationCollector


def test_consultation_validate():
    """Test consultation data validation."""
    collector = ConsultationCollector(token="test_token")

    raw = [
        {
            "id": "123",
            "title": "Test News",
            "content": "Content here",
            "source": "sina",
            "datetime": "2025-01-01 10:00:00",
        }
    ]

    validated = collector.validate(raw)
    assert len(validated) == 1
    assert validated[0]["news_id"] == "123"
    assert validated[0]["title"] == "Test News"
