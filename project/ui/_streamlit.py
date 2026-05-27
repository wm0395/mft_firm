from __future__ import annotations

from collections.abc import Callable
from typing import Any

def get_streamlit() -> Any:
    try:
        import streamlit as streamlit_module  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Streamlit is not installed. Install the project requirements to run the UI."
        ) from exc
    return streamlit_module


def get_option_menu() -> Callable[..., str] | None:
    try:
        from streamlit_option_menu import option_menu  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        return None
    return option_menu
