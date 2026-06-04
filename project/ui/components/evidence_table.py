from __future__ import annotations

import html

from project.ui._streamlit import get_streamlit
from project.ui.components.table_rows import build_table_rows


def render_evidence_table(title: str, rows) -> None:
    st = get_streamlit()
    rows = tuple(rows)
    with st.container(border=True):
        st.subheader(title)
        if not rows:
            _surface_empty_state(st)
            return
        frame = build_table_rows(rows)
        _surface_summary(st, len(frame), _frame_columns(frame))
        st.dataframe(frame, use_container_width=True)


def _surface_summary(st, row_count: int, columns: tuple[str, ...]) -> None:
    summary = _summary_text(row_count, columns)
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_summary_html(row_count, columns), unsafe_allow_html=True)
        return
    st.caption(summary)


def _surface_empty_state(st) -> None:
    markdown_fn = getattr(st, "markdown", None)
    if callable(markdown_fn):
        markdown_fn(_empty_state_html(), unsafe_allow_html=True)
        return
    st.caption("No records captured yet.")


def _frame_columns(frame) -> tuple[str, ...]:
    if len(frame) == 0:
        return ()
    return tuple(str(column) for column in frame.rows[0].keys())


def _summary_text(row_count: int, columns: tuple[str, ...]) -> str:
    label = "record" if row_count == 1 else "records"
    if not columns:
        return f"{row_count} {label}"
    preview = ", ".join(columns[:4])
    if len(columns) > 4:
        preview = f"{preview}, ..."
    return f"{row_count} {label} • Columns: {preview}"


def _summary_html(row_count: int, columns: tuple[str, ...]) -> str:
    label = "record" if row_count == 1 else "records"
    preview = ", ".join(columns[:4]) or "n/a"
    if len(columns) > 4:
        preview = f"{preview}, ..."
    return "".join(
        [
            "<section style='margin:0.75rem 0 0.9rem;padding:0.9rem 1rem;"
            "border:1px solid #e2e8f0;border-radius:14px;"
            "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);"
            "box-shadow:0 6px 18px rgba(15,23,42,0.05);'>",
            "<div style='color:#64748b;font-size:0.68rem;font-weight:700;"
            "letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.25rem;'>"
            "Evidence table</div>",
            f"<div style='color:#0f172a;font-size:0.95rem;font-weight:700;"
            f"line-height:1.35;'>{row_count} {label} ready for review.</div>",
            f"<div style='color:#475569;font-size:0.82rem;line-height:1.5;"
            f"margin-top:0.3rem;'>Columns: {html.escape(preview)}</div>",
            "</section>",
        ]
    )


def _empty_state_html() -> str:
    return "".join(
        [
            "<section style='margin:0.75rem 0 0.9rem;padding:0.9rem 1rem;"
            "border:1px dashed #cbd5e1;border-radius:14px;"
            "background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);'>",
            "<div style='color:#0f172a;font-size:0.95rem;font-weight:700;"
            "line-height:1.35;'>No records captured yet.</div>",
            "<div style='color:#475569;font-size:0.82rem;line-height:1.5;"
            "margin-top:0.3rem;'>Rows will appear here after the workflow returns "
            "data.</div>",
            "</section>",
        ]
    )
