from __future__ import annotations

import html
from collections.abc import Callable

from project.ui._streamlit import get_streamlit


def render_action_panel(
    title: str,
    explanation: str,
    button_label: str,
    *,
    key: str,
    on_click: Callable[[], None] | None = None,
    target_page: str | None = None,
    disabled: bool = False,
    disabled_reason: str | None = None,
) -> None:
    st = get_streamlit()
    with st.container(border=True):
        markdown_fn = getattr(st, "markdown", None)
        if callable(markdown_fn):
            markdown_fn(
                _action_panel_html(
                    title,
                    explanation,
                    button_label,
                    target_page,
                    disabled_reason,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.subheader(title)
            _surface_text(st, "Recommended next step")
            _surface_text(st, explanation)
            if target_page:
                _surface_text(st, f"Destination: {target_page}")
            if disabled_reason:
                _surface_text(st, f"Disabled: {disabled_reason}")
        st.button(
            button_label,
            key=key,
            on_click=None if disabled else on_click,
            type="primary",
            disabled=disabled,
        )


def _action_panel_html(
    title: str,
    explanation: str,
    button_label: str,
    target_page: str | None,
    disabled_reason: str | None,
) -> str:
    return "".join(
        [
            "<section style='margin:0.15rem 0 0.9rem;padding:0.95rem 1rem;border:1px "
            "solid #e2e8f0;border-radius:14px;background:linear-gradient(180deg,#ffffff "
            "0%,#f8fafc 100%);box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Recommended next step</div>",
            f"<div style='color:#0f172a;font-size:1rem;font-weight:700;line-height:1.3;'>"
            f"{html.escape(title)}</div>",
            f"<div style='color:#475569;font-size:0.88rem;line-height:1.55;margin-top:0.35rem;'>"
            f"{html.escape(explanation)}</div>",
            "<div style='display:flex;flex-wrap:wrap;gap:0.45rem;margin-top:0.8rem;'>",
            _action_panel_chip("Button", button_label, "action"),
            *_action_panel_chips(target_page, disabled_reason),
            "</div>",
            "</section>",
        ]
    )


def _action_panel_chips(
    target_page: str | None,
    disabled_reason: str | None,
) -> tuple[str, ...]:
    chips: list[str] = []
    if target_page:
        chips.append(_action_panel_chip("Destination", target_page, "ok"))
    if disabled_reason:
        chips.append(_action_panel_chip("Status", disabled_reason, "warning"))
    return tuple(chips)


def _action_panel_chip(label: str, value: str, tone: str) -> str:
    return "".join(
        [
            "<div style='display:flex;flex-direction:column;gap:0.1rem;padding:0.5rem "
            "0.7rem;border-radius:12px;background:#ffffff;border:1px solid #e2e8f0;"
            "min-width:120px;'>",
            f"<div style='color:#64748b;font-size:0.62rem;font-weight:700;"
            f"letter-spacing:0.12em;text-transform:uppercase;'>{html.escape(label)}</div>",
            f"<div style='color:{_action_panel_tone_color(tone)};font-size:0.84rem;"
            f"font-weight:700;line-height:1.35;word-break:break-word;'>"
            f"{html.escape(value)}</div>",
            "</div>",
        ]
    )


def _action_panel_tone_color(tone: str) -> str:
    if tone == "ok":
        return "#15803d"
    if tone == "warning":
        return "#b45309"
    return "#4f46e5"


def _surface_text(st, text: str) -> None:
    write_fn = getattr(st, "write", None)
    if callable(write_fn):
        write_fn(text)
        return
    caption_fn = getattr(st, "caption", None)
    if callable(caption_fn):
        caption_fn(text)
