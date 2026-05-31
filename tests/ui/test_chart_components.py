from __future__ import annotations

from datetime import datetime, UTC

from project.ui.components.trading_view_chart import trading_view_chart


def test_trading_view_chart_is_self_contained() -> None:
    html = trading_view_chart(
        [
            (datetime(2026, 5, 1, tzinfo=UTC), 100.0, 105.0, 99.0, 104.0, 1000.0),
        ]
    )

    assert "<svg" in html
    assert "https://unpkg.com" not in html
    assert "lightweight-charts" not in html
