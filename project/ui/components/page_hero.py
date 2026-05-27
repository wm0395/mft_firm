from __future__ import annotations

import html
from collections.abc import Sequence

from project.ui._streamlit import get_streamlit


def render_page_hero(
    summary: str,
    note: str | None = None,
    context: Sequence[tuple[str, object]] | None = None,
) -> None:
    st = get_streamlit()
    markdown = getattr(st, "markdown", None)
    if not callable(markdown):
        return
    parts = ['<section class="ui-hero">']
    parts.append('<div class="ui-hero__eyebrow">Operator snapshot</div>')
    parts.append(f'<div class="ui-hero__summary">{html.escape(summary)}</div>')
    if context:
        parts.append(_context_html(context))
    if note:
        parts.append(f'<div class="ui-hero__note">{html.escape(note)}</div>')
    parts.append("</section>")
    markdown(
        "\n".join(parts),
        unsafe_allow_html=True,
    )


def _context_html(context: Sequence[tuple[str, object]]) -> str:
    chips = []
    for label, value in context:
        chips.append(
            "".join(
                [
                    '<span class="ui-hero__chip">',
                    f'<span class="ui-hero__chip-label">{html.escape(str(label))}</span>',
                    f'<span class="ui-hero__chip-value">{html.escape(str(value))}</span>',
                    "</span>",
                ]
            )
        )
    return f'<div class="ui-hero__chips">{"".join(chips)}</div>'
