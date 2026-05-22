from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from project.decision.models import Decision
from project.decision.system import decide_trade
from project.data.repository import DataRepository
from project.common.models import DecisionAction, DecisionReason
import project.ui.pages.trade_ideas as trade_ideas_page
from project.ui_services.trade_idea_views import (
    get_trade_ideas_page_view,
    submit_trade_decision,
)

from tests.ui.test_views_support import _seed_repository


def test_trade_ideas_detail_defaults_to_automatic_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _, trade_id, _ = _seed_repository(tmp_path)
    trade_idea = next(
        idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id
    )
    expected = decide_trade(trade_idea)
    repository.close()
    captured, fake_st, trade_id = _render_trade_detail_case(
        tmp_path,
        monkeypatch,
        auto_review=True,
        notes="auto notes",
        decision_action=expected.action,
        decision_reason=expected.structured_reason,
    )
    assert captured["args"] == (trade_id, None, None, "auto notes")
    assert fake_st.success_messages == [f"Recorded {expected.action} decision"]
    assert fake_st.rerun_calls == 1


def test_trade_ideas_detail_preserves_manual_review_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured, fake_st, trade_id = _render_trade_detail_case(
        tmp_path,
        monkeypatch,
        auto_review=False,
        action="watch",
        reason_label="Market conditions",
        notes="manual notes",
        decision_action="watch",
        decision_reason="market_conditions",
    )
    assert captured["args"] == (trade_id, "watch", "market_conditions", "manual notes")
    assert fake_st.success_messages == ["Recorded watch decision"]
    assert fake_st.rerun_calls == 1


def test_create_snapshot_and_trade_decision_mutations(tmp_path: Path) -> None:
    repository, _, trade_id, _ = _seed_repository(tmp_path)
    try:
        decision = submit_trade_decision(
            repository,
            trade_id,
            "watch",
            "market_conditions",
            "fixture",
        )
        updated_trade_ideas = get_trade_ideas_page_view(repository, trade_id)
        decisions = repository.get_decisions(trade_id)

        assert decision.action == "watch"
        assert len(decisions) == 1
        assert decisions[0][2] == "watch"
        assert updated_trade_ideas.queue == ()
        assert updated_trade_ideas.selected_detail is None
    finally:
        repository.close()


def test_trade_decision_defaults_to_shared_rules(tmp_path: Path) -> None:
    repository, _, trade_id, _ = _seed_repository(tmp_path)
    try:
        trade_idea = next(
            idea for idea in repository.get_trade_ideas() if idea.trade_id == trade_id
        )
        decision = submit_trade_decision(repository, trade_id, notes="auto")
        expected = decide_trade(trade_idea)

        assert decision.action == expected.action
        assert decision.structured_reason == expected.structured_reason
        assert decision.notes == "auto"
        assert repository.get_decisions(trade_id)[0][2] == expected.action
    finally:
        repository.close()


def _trade_detail(repository: DataRepository, trade_id: str):
    view = get_trade_ideas_page_view(repository, trade_id)
    assert view.selected_detail is not None
    return view.selected_detail


def _render_trade_detail_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    auto_review: bool,
    action: str = "watch",
    reason_label: str = "Market conditions",
    notes: str = "",
    decision_action: DecisionAction,
    decision_reason: DecisionReason,
) -> tuple[dict[str, object], _FakeTradeIdeasStreamlit, str]:
    repository, detail, fake_st, captured, trade_id = _prepare_trade_detail_case(
        tmp_path,
        auto_review=auto_review,
        action=action,
        reason_label=reason_label,
        notes=notes,
    )
    fake_submit_trade_decision = _fake_trade_detail_submitter(
        captured, decision_action, decision_reason
    )

    try:
        monkeypatch.setattr(
            trade_ideas_page, "submit_trade_decision", fake_submit_trade_decision
        )
        monkeypatch.setattr(
            trade_ideas_page, "render_evidence_table", lambda *_args, **_kwargs: None
        )
        trade_ideas_page._render_detail(fake_st, detail, repository)
    finally:
        repository.close()
    return captured, fake_st, trade_id


def _prepare_trade_detail_case(
    tmp_path: Path,
    *,
    auto_review: bool,
    action: str,
    reason_label: str,
    notes: str,
) -> tuple[DataRepository, object, _FakeTradeIdeasStreamlit, dict[str, object], str]:
    repository, _, trade_id, _ = _seed_repository(tmp_path)
    detail = _trade_detail(repository, trade_id)
    fake_st = _FakeTradeIdeasStreamlit(
        auto_review=auto_review,
        action=action,
        reason_label=reason_label,
        notes=notes,
    )
    captured: dict[str, object] = {}
    return repository, detail, fake_st, captured, trade_id


def _fake_trade_detail_submitter(
    captured: dict[str, object],
    decision_action: DecisionAction,
    decision_reason: DecisionReason,
):
    def fake_submit_trade_decision(
        _repository: DataRepository,
        submitted_trade_id: str,
        action: DecisionAction | None = None,
        reason: DecisionReason | None = None,
        notes: str = "",
    ) -> Decision:
        captured["args"] = (submitted_trade_id, action, reason, notes)
        return Decision.create(
            trade_id=submitted_trade_id,
            action=decision_action,
            structured_reason=decision_reason,
            notes=notes,
        )

    return fake_submit_trade_decision


class _FakeTradeIdeasStreamlit:
    def __init__(
        self,
        *,
        auto_review: bool,
        action: str = "watch",
        reason_label: str = "Market conditions",
        notes: str = "",
    ) -> None:
        self.auto_review = auto_review
        self.action = action
        self.reason_label = reason_label
        self.notes = notes
        self.success_messages: list[str] = []
        self.errors: list[str] = []
        self.rerun_calls = 0

    def __getattr__(self, name: str):
        if name in {"container", "form"}:
            return lambda *_args, **_kwargs: contextlib.nullcontext()
        if name == "checkbox":
            return lambda *_args, **_kwargs: self.auto_review
        if name == "radio":
            return self._radio
        if name == "selectbox":
            return self._selectbox
        if name == "text_area":
            return lambda *_args, **_kwargs: self.notes
        if name == "form_submit_button":
            return lambda *_args, **_kwargs: True
        if name in {"subheader", "write", "caption", "json"}:
            return lambda *_args, **_kwargs: None
        if name == "success":
            return self._success
        if name == "error":
            return self._error
        if name == "rerun":
            return self._rerun
        raise AttributeError(name)

    def _radio(self, *_args, **_kwargs) -> str:
        if self.auto_review:
            raise AssertionError("manual action control should not be shown")
        return self.action

    def _selectbox(self, *_args, **_kwargs) -> str:
        if self.auto_review:
            raise AssertionError("manual reason control should not be shown")
        return self.reason_label

    def _success(self, message: str) -> None:
        self.success_messages.append(message)

    def _error(self, message: str) -> None:
        self.errors.append(message)

    def _rerun(self) -> None:
        self.rerun_calls += 1
