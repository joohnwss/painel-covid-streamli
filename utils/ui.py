import streamlit as st


def kpi_card(label: str, value: str, note: str = "") -> str:
    note_html = f"<div class='kpi-note'>{note}</div>" if note else ""
    return f"""
    <div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        {note_html}
    </div>"""


def insight_box(text: str):
    st.markdown(
        f"<div class='callout callout-insight'>"
        f"<strong>Insight:</strong> {text}</div>",
        unsafe_allow_html=True,
    )


def action_box(text: str):
    st.markdown(
        f"<div class='callout callout-action'>"
        f"<strong>Ação para o hospital:</strong> {text}</div>",
        unsafe_allow_html=True,
    )


def context_box(text: str):
    st.markdown(
        f"<div class='callout callout-context'>"
        f"<strong>Leitura de contexto:</strong> {text}</div>",
        unsafe_allow_html=True,
    )


def warning_box(text: str):
    st.markdown(
        f"<div class='callout callout-warning'>"
        f"<strong>Critério de interpretação:</strong> {text}</div>",
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    st.markdown(f"<h2 class='sec-title'>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='sec-sub'>{subtitle}</div>", unsafe_allow_html=True)
