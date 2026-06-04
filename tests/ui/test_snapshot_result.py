from __future__ import annotations

from types import SimpleNamespace

from project.ui.components.snapshot_result import render_snapshot_result


class _FakeStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[tuple[str, bool]] = []

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))


def test_render_snapshot_result_renders_summary_card() -> None:
    fake_st = _FakeStreamlit()
    result = SimpleNamespace(
        dataset_snapshot_id="dataset_snapshot:test",
        universe_id="research_universe:test",
        assets=("AAPL", "MSFT", "GOOG", "TSLA"),
        data_start="2026-05-01",
        data_end="2026-05-31",
        quality_status="ok",
        provenance=SimpleNamespace(source_name="csv:fixture", bar_timeframe="1d"),
        dataset_snapshot=SimpleNamespace(captured_at="2026-05-31T00:00:00+00:00"),
    )

    render_snapshot_result(fake_st, result)

    assert fake_st.markdowns and fake_st.markdowns[0][1] is True
    html = fake_st.markdowns[0][0]
    assert "Snapshot created" in html
    assert "dataset_snapshot:test" in html
    assert "AAPL, MSFT (+2 more)" in html
    assert "Quality" in html
    assert "csv:fixture • 1d" in html
    assert "2026-05-31T00:00:00+00:00" in html


def test_render_snapshot_result_falls_back_without_markdown() -> None:
    class _PlainStreamlit:
        def __init__(self) -> None:
            self.captions: list[str] = []
            self.writes: list[str] = []

        def caption(self, text: str) -> None:
            self.captions.append(text)

        def write(self, text: object) -> None:
            self.writes.append(str(text))

    fake_st = _PlainStreamlit()
    result = SimpleNamespace(
        dataset_snapshot_id="dataset_snapshot:test",
        universe_id="research_universe:test",
        assets=("AAPL",),
        data_start="2026-05-01",
        data_end="2026-05-31",
        quality_status="warn",
        provenance=SimpleNamespace(source_name="csv:fixture", bar_timeframe="1d"),
    )

    render_snapshot_result(fake_st, result)

    assert fake_st.captions == []
    assert fake_st.writes == [
        "Snapshot created",
        "Snapshot: dataset_snapshot:test",
        "Universe: research_universe:test",
        "Assets: AAPL",
        "Window: 2026-05-01 -> 2026-05-31",
        "Quality: WARN",
        "Source: csv:fixture • 1d",
    ]
