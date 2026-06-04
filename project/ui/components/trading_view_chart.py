from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape


@dataclass(frozen=True)
class _ChartBar:
    label: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def trading_view_chart(
    ohlcv_data: list[tuple[datetime, float, float, float, float, float]],
) -> str:
    bars = tuple(_normalize_bar(row) for row in ohlcv_data)
    if not bars:
        return _empty_chart_html()
    return _chart_html(bars)


def _normalize_bar(
    row: tuple[datetime, float, float, float, float, float],
) -> _ChartBar:
    timestamp, open_, high, low, close_, volume = row
    if hasattr(timestamp, "strftime"):
        label = timestamp.strftime("%Y-%m-%d")
    else:
        label = str(timestamp)
    return _ChartBar(
        label=label,
        open=float(open_),
        high=float(high),
        low=float(low),
        close=float(close_),
        volume=float(volume),
    )


def _chart_html(bars: tuple[_ChartBar, ...]) -> str:
    return "".join(
        [
            "<div style='width:100%;overflow-x:auto;padding:0.5rem 0;'>",
            "<div style='min-width:1120px;'>",
            _chart_summary_html(bars),
            "<div style='margin-bottom:0.5rem;color:#64748b;font-size:0.78rem;'>",
            "Local OHLCV chart rendered without remote scripts.</div>",
            _chart_svg(bars),
            "</div></div>",
        ]
    )


def _chart_summary_html(bars: tuple[_ChartBar, ...]) -> str:
    first = bars[0]
    last = bars[-1]
    change = last.close - first.close
    change_pct = (change / first.close * 100) if first.close else 0.0
    avg_volume = sum(bar.volume for bar in bars) / len(bars)
    period = first.label if len(bars) == 1 else f"{first.label} → {last.label}"
    tone = "ok" if change >= 0 else "warning"
    return "".join(
        [
            "<section style='margin:0.15rem 0 0.75rem;padding:0.95rem 1rem;"
            "border:1px solid #e2e8f0;border-radius:14px;background:linear-gradient("
            "180deg,#ffffff 0%,#f8fafc 100%);box-shadow:0 6px 18px "
            "rgba(15,23,42,0.05);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Chart snapshot</div>",
            f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
            f"{escape(period)}</div>",
            "<div style='display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.75rem;'>",
            _chart_chip("Last close", f"{last.close:.2f}", tone),
            _chart_chip("Change", f"{change:+.2f} ({change_pct:+.2f}%)", tone),
            _chart_chip("Avg volume", f"{avg_volume:,.0f}", "action"),
            _chart_chip("Legend", "Green up / red down", "primary"),
            "</div></section>",
        ]
    )


def _chart_svg(bars: tuple[_ChartBar, ...]) -> str:
    width = 1120
    height = 560
    left = 64
    right = 92
    price_top = 40
    price_bottom = 360
    volume_top = 428
    volume_bottom = 500
    price_min = min(bar.low for bar in bars)
    price_max = max(bar.high for bar in bars)
    volume_max = max((bar.volume for bar in bars), default=0.0) or 1.0
    slot = (width - left - right) / len(bars)
    candle_width = max(4.0, min(18.0, slot * 0.55))
    parts = [
        f"<svg viewBox='0 0 {width} {height}' width='100%' height='{height}' "
        "role='img' aria-label='OHLCV chart' xmlns='http://www.w3.org/2000/svg'>",
        "<rect x='0' y='0' width='1120' height='560' rx='16' fill='#ffffff' "
        "stroke='#e2e8f0'/>",
        "<text x='24' y='24' fill='#0f172a' font-size='14' font-weight='700'>"
        "Price and volume</text>",
        *_price_grid(width, left, right, price_top, price_bottom, price_min, price_max),
        *_volume_grid(width, left, right, volume_top, volume_bottom),
    ]
    for index, bar in enumerate(bars):
        center_x = left + slot * (index + 0.5)
        parts.append(
            _candle_svg(
                bar,
                center_x,
                candle_width,
                price_min,
                price_max,
                price_top,
                price_bottom,
            )
        )
        parts.append(
            _volume_svg(
                bar,
                center_x,
                candle_width,
                volume_max,
                volume_top,
                volume_bottom,
            )
        )
    parts.extend(_time_labels(bars, left, slot, height))
    parts.append("</svg>")
    return "".join(parts)


def _price_grid(
    width: int,
    left: int,
    right: int,
    top: int,
    bottom: int,
    price_min: float,
    price_max: float,
) -> tuple[str, ...]:
    ticks = []
    for index in range(5):
        price = price_min + ((price_max - price_min) * index / 4)
        y = _scale(price, price_min, price_max, top, bottom)
        ticks.append(
            "".join(
                [
                    f"<line x1='{left}' y1='{y:.2f}' ",
                    f"x2='{width - right}' y2='{y:.2f}' ",
                    "stroke='#e2e8f0' stroke-width='1'/>",
                    f"<text x='{width - 8}' y='{y + 4:.2f}' ",
                    "text-anchor='end' fill='#94a3b8' font-size='11'>",
                    f"{price:.2f}</text>",
                ]
            )
        )
    return tuple(ticks)


def _volume_grid(
    width: int,
    left: int,
    right: int,
    top: int,
    bottom: int,
) -> tuple[str, ...]:
    return (
        f"<line x1='{left}' y1='{top}' x2='{width - right}' y2='{top}' "
        "stroke='#e2e8f0' stroke-width='1'/>",
        f"<line x1='{left}' y1='{bottom}' x2='{width - right}' y2='{bottom}' "
        "stroke='#e2e8f0' stroke-width='1'/>",
        f"<text x='{width - 8}' y='{top - 6}' text-anchor='end' "
        "fill='#94a3b8' font-size='11'>Volume</text>",
    )


def _candle_svg(
    bar: _ChartBar,
    x: float,
    candle_width: float,
    price_min: float,
    price_max: float,
    price_top: int,
    price_bottom: int,
) -> str:
    color = "#16a34a" if bar.close >= bar.open else "#dc2626"
    high_y = _scale(bar.high, price_min, price_max, price_top, price_bottom)
    low_y = _scale(bar.low, price_min, price_max, price_top, price_bottom)
    open_y = _scale(bar.open, price_min, price_max, price_top, price_bottom)
    close_y = _scale(bar.close, price_min, price_max, price_top, price_bottom)
    body_y = min(open_y, close_y)
    body_height = max(2.0, abs(close_y - open_y))
    left = x - (candle_width / 2)
    title = (
        f"{bar.label} O:{bar.open:.2f} H:{bar.high:.2f} "
        f"L:{bar.low:.2f} C:{bar.close:.2f}"
    )
    return "".join(
        [
            "<g>",
            f"<title>{escape(title)}</title>",
            f"<line x1='{x:.2f}' y1='{high_y:.2f}' x2='{x:.2f}' y2='{low_y:.2f}' ",
            f"stroke='{color}' stroke-width='2' stroke-linecap='round'/>",
            f"<rect x='{left:.2f}' y='{body_y:.2f}' width='{candle_width:.2f}' "
            f"height='{body_height:.2f}' rx='2' fill='{color}' opacity='0.85'/>",
            "</g>",
        ]
    )


def _volume_svg(
    bar: _ChartBar,
    x: float,
    candle_width: float,
    volume_max: float,
    volume_top: int,
    volume_bottom: int,
) -> str:
    color = "#16a34a" if bar.close >= bar.open else "#dc2626"
    volume_height = max(1.0, (bar.volume / volume_max) * (volume_bottom - volume_top))
    y = volume_bottom - volume_height
    left = x - (candle_width / 2)
    title = f"{bar.label} Volume:{bar.volume:.0f}"
    return "".join(
        [
            "<g>",
            f"<title>{escape(title)}</title>",
            f"<rect x='{left:.2f}' y='{y:.2f}' width='{candle_width:.2f}' "
            f"height='{volume_height:.2f}' rx='2' fill='{color}' opacity='0.25'/>",
            "</g>",
        ]
    )


def _time_labels(
    bars: tuple[_ChartBar, ...],
    left: int,
    slot: float,
    height: int,
) -> tuple[str, ...]:
    labels = []
    for index in sorted({0, len(bars) // 2, len(bars) - 1}):
        bar = bars[index]
        x = left + slot * (index + 0.5)
        labels.append(
            f"<text x='{x:.2f}' y='{height - 18}' text-anchor='middle' "
            f"fill='#64748b' font-size='11'>{escape(bar.label)}</text>"
        )
    return tuple(labels)


def _scale(
    value: float,
    minimum: float,
    maximum: float,
    top: int,
    bottom: int,
) -> float:
    if maximum <= minimum:
        return float((top + bottom) / 2)
    return bottom - ((value - minimum) / (maximum - minimum)) * (bottom - top)


def _empty_chart_html() -> str:
    return (
        "<div style='padding:1rem 1.1rem;border:1px dashed #cbd5e1;"
        "border-radius:12px;background:#f8fafc;color:#475569;'>"
        "<div style='font-weight:700;color:#0f172a;margin-bottom:0.25rem;'>"
        "No OHLCV data available.</div>"
        "<div style='font-size:0.88rem;line-height:1.5;'>"
        "Load market data or widen the selected range to render the chart.</div>"
        "</div>"
    )


def _chart_chip(label: str, value: str, tone: str) -> str:
    return "".join(
        [
            "<div style='display:flex;flex-direction:column;gap:0.1rem;padding:0.55rem "
            "0.7rem;border-radius:12px;background:#ffffff;border:1px solid #e2e8f0;"
            "min-width:120px;'>",
            f"<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;'>{escape(label)}</div>",
            f"<div style='color:{_chart_tone_color(tone)};font-size:0.84rem;"
            f"font-weight:700;line-height:1.35;word-break:break-word;'>"
            f"{escape(value)}</div>",
            "</div>",
        ]
    )


def _chart_tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"
