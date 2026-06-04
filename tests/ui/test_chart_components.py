from __future__ import annotations

from datetime import datetime, UTC

from project.ui.components.trading_view_chart import trading_view_chart


def test_trading_view_chart_is_self_contained() -> None:
    html = trading_view_chart(
        [
            (datetime(2026, 5, 1, tzinfo=UTC), 100.0, 105.0, 99.0, 104.0, 1000.0),
            (datetime(2026, 5, 2, tzinfo=UTC), 104.0, 106.0, 101.0, 105.0, 1500.0),
        ]
    )

    assert "<svg" in html
    assert "https://unpkg.com" not in html
    assert "lightweight-charts" not in html
    assert "Chart snapshot" in html
    assert "Last close" in html
    assert "Green up / red down" in html


def test_trading_view_chart_uses_empty_state_card() -> None:
    html = trading_view_chart([])

    assert "No OHLCV data available." in html
    assert "Load market data or widen the selected range" in html
