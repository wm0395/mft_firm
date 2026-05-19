from __future__ import annotations

from collections.abc import Callable
from typing import Any

_streamlit: Any | None = None
_option_menu: Callable[..., str] | None = None

try:
    import streamlit as _streamlit_module  # type: ignore[import-not-found]
except ModuleNotFoundError:
    pass
else:
    _streamlit = _streamlit_module

try:
    from streamlit_option_menu import option_menu as _option_menu_func  # type: ignore[import-not-found]
except ModuleNotFoundError:
    pass
else:
    _option_menu = _option_menu_func


def get_streamlit() -> Any:
    if _streamlit is None:
        raise RuntimeError(
            "Streamlit is not installed. Install the project requirements to run the UI."
        )
    return _streamlit


def get_option_menu() -> Callable[..., str] | None:
    return _option_menu
