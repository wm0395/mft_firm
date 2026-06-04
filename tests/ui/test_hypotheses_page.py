from __future__ import annotations

import contextlib
from types import SimpleNamespace

import project.ui.pages.hypotheses as hypotheses_page


class _FakeBlock:
    def __init__(self, parent: "_FakeStreamlit") -> None:
        self._parent = parent

    def __enter__(self) -> "_FakeStreamlit":
        return self._parent

    def __exit__(self, *_args) -> bool:
        return False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {
            "selected_hypothesis_id": "hypothesis:rsi_mean_reversion"
        }
        self.titles: list[str] = []
        self.captions: list[str] = []
        self.subheaders: list[str] = []
        self.writes: list[str] = []
        self.infos: list[str] = []
        self.markdowns: list[tuple[str, bool]] = []
        self.columns_calls: list[int] = []

    def title(self, text: str) -> None:
        self.titles.append(text)

    def caption(self, text: str) -> None:
        self.captions.append(text)

    def subheader(self, text: str) -> None:
        self.subheaders.append(text)

    def write(self, text: object) -> None:
        self.writes.append(str(text))

    def info(self, text: str) -> None:
        self.infos.append(text)

    def markdown(self, text: str, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append((text, unsafe_allow_html))

    def container(self, **_kwargs):
        return contextlib.nullcontext()

    def columns(self, count: int):
        self.columns_calls.append(count)
        return tuple(_FakeBlock(self) for _ in range(count))


def test_hypotheses_page_renders_selected_hypothesis_summary(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}
    view = SimpleNamespace(
        columns=(
            SimpleNamespace(
                status="active",
                cards=(
                    SimpleNamespace(
                        hypothesis_id="hypothesis:rsi_mean_reversion",
                        name="RSI Mean Reversion",
                        status="active",
                        version=1,
                        explainability_level="high",
                        required_signals=("rsi_14", "close"),
                        readiness="ready",
                        blockers=(),
                        latest_backtest="hypothesis:rsi_mean_reversion 12.35%",
                        validation_failures=0,
                    ),
                ),
            ),
        ),
        selected_detail=SimpleNamespace(
            hypothesis_id="hypothesis:rsi_mean_reversion",
            name="RSI Mean Reversion",
            status="active",
            version=1,
            explainability_level="high",
            thesis="Mean reversion after RSI extremes",
            horizon="3d",
            direction_policy="long-only",
            required_signals=("rsi_14", "close"),
            readiness="ready",
            blockers=(),
            latest_backtest="hypothesis:rsi_mean_reversion 12.35%",
            validation_failures=0,
            strategy_spec={"thesis": "Mean reversion after RSI extremes"},
            dossier={"hypothesis_id": "hypothesis:rsi_mean_reversion"},
        ),
        debug_payload={"definitions": [], "registry": {}},
    )

    monkeypatch.setattr(hypotheses_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        hypotheses_page,
        "get_hypotheses_page_view",
        lambda _repository, _current: view,
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_hypothesis_card",
        lambda card, on_select=None: captured.setdefault("board", []).append(card),
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", []).append(cards),
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )

    hypotheses_page.render(object())

    assert fake_st.titles == ["Hypotheses"]
    summary_html = next(
        html for html, unsafe in fake_st.markdowns if "Selected hypothesis" in html
    )
    assert "RSI Mean Reversion" in summary_html
    board_header_html = next(
        html for html, unsafe in fake_st.markdowns if "Lifecycle column" in html
    )
    assert "1 hypothesis" in board_header_html
    assert fake_st.writes[:7] == [
        "Thesis: Mean reversion after RSI extremes",
        "Horizon: 3d",
        "Direction policy: long-only",
        "Readiness: ready",
        "Required signals: rsi_14, close",
        "Latest backtest: hypothesis:rsi_mean_reversion 12.35%",
        "Validation failures: 0",
    ]
    assert fake_st.captions == []
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)


def test_hypotheses_page_renders_empty_selected_detail_state(monkeypatch) -> None:
    fake_st = _FakeStreamlit()
    captured: dict[str, object] = {}
    view = SimpleNamespace(
        columns=(
            SimpleNamespace(
                status="active",
                cards=(
                    SimpleNamespace(
                        hypothesis_id="hypothesis:rsi_mean_reversion",
                        name="RSI Mean Reversion",
                        status="active",
                        version=1,
                        explainability_level="high",
                        required_signals=("rsi_14", "close"),
                        readiness="ready",
                        blockers=(),
                        latest_backtest="hypothesis:rsi_mean_reversion 12.35%",
                        validation_failures=0,
                    ),
                ),
            ),
        ),
        selected_detail=None,
        debug_payload={"definitions": [], "registry": {}},
    )

    monkeypatch.setattr(hypotheses_page, "get_streamlit", lambda: fake_st)
    monkeypatch.setattr(
        hypotheses_page,
        "get_hypotheses_page_view",
        lambda _repository, _current: view,
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_hypothesis_card",
        lambda card, on_select=None: captured.setdefault("board", []).append(card),
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_status_cards",
        lambda cards: captured.setdefault("cards", []).append(cards),
    )
    monkeypatch.setattr(
        hypotheses_page,
        "render_json_debug",
        lambda title, payload: captured.setdefault("debug", (title, payload)),
    )

    hypotheses_page.render(object())

    empty_state_html = next(
        html for html, unsafe in fake_st.markdowns if "No hypothesis selected." in html
    )
    assert "Open a card" in empty_state_html
    assert "Board" in empty_state_html
    board_header_html = next(
        html for html, unsafe in fake_st.markdowns if "Lifecycle column" in html
    )
    assert "1 hypothesis" in board_header_html
    assert fake_st.infos == []
    assert captured["debug"] == ("Raw JSON / Debug", view.debug_payload)
