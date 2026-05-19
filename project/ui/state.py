from __future__ import annotations

from collections.abc import MutableMapping


DEFAULT_STATE = {
    "ui_page": "Mission Control",
    "selected_hypothesis_id": "",
    "selected_trade_id": "",
    "selected_evaluation_id": "",
    "selected_research_project_id": "",
}


def ensure_state(state: MutableMapping[str, object]) -> None:
    for key, value in DEFAULT_STATE.items():
        state.setdefault(key, value)


def set_selected_page(state: MutableMapping[str, object], page: str) -> None:
    state["ui_page"] = page


def set_selected_hypothesis(state: MutableMapping[str, object], hypothesis_id: str) -> None:
    state["selected_hypothesis_id"] = hypothesis_id


def set_selected_trade(state: MutableMapping[str, object], trade_id: str) -> None:
    state["selected_trade_id"] = trade_id


def set_selected_evaluation(state: MutableMapping[str, object], evaluation_id: str) -> None:
    state["selected_evaluation_id"] = evaluation_id


def set_selected_research_project(
    state: MutableMapping[str, object], project_id: str
) -> None:
    state["selected_research_project_id"] = project_id
