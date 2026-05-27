from __future__ import annotations

from types import ModuleType
import sys

import pytest

from project.ui._streamlit import get_option_menu, get_streamlit


def test_get_streamlit_raises_when_streamlit_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "streamlit", None)

    with pytest.raises(RuntimeError, match="Streamlit is not installed"):
        get_streamlit()


def test_get_streamlit_reloads_module_each_call(monkeypatch: pytest.MonkeyPatch) -> None:
    first = ModuleType("streamlit")
    second = ModuleType("streamlit")
    monkeypatch.setitem(sys.modules, "streamlit", first)
    assert get_streamlit() is first

    monkeypatch.setitem(sys.modules, "streamlit", second)
    assert get_streamlit() is second


def test_get_option_menu_returns_none_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "streamlit_option_menu", None)

    assert get_option_menu() is None


def test_get_option_menu_reloads_function_each_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_module = ModuleType("streamlit_option_menu")
    second_module = ModuleType("streamlit_option_menu")

    def first_option_menu(*args: object, **kwargs: object) -> str:
        return "first"

    def second_option_menu(*args: object, **kwargs: object) -> str:
        return "second"

    first_module.option_menu = first_option_menu  # type: ignore[attr-defined]
    second_module.option_menu = second_option_menu  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "streamlit_option_menu", first_module)
    assert get_option_menu() is first_option_menu

    monkeypatch.setitem(sys.modules, "streamlit_option_menu", second_module)
    assert get_option_menu() is second_option_menu
