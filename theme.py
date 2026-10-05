import streamlit as st

THEMES = {
    "light": {
        "background": "#ffffff",
        "sidebar": "#f8fafc",
        "surface": "#f9fafb",
        "text": "#111827",
        "muted": "#64748b",
        "border": "#e5e7eb",
        "input": "#ffffff",
        "accent": "#4f46e5",
        "insight": "#fff3cd",
        "grid": "#e5e7eb",
    },
    "dark": {
        "background": "#0f172a",
        "sidebar": "#111827",
        "surface": "#1f2937",
        "text": "#e5e7eb",
        "muted": "#9ca3af",
        "border": "#374151",
        "input": "#1f2937",
        "accent": "#818cf8",
        "insight": "#422006",
        "grid": "#374151",
    },
}


def apply_theme():
    theme = st.session_state.get("theme", "light")
    palette = THEMES.get(theme, THEMES["light"])
    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 1.5rem; }}
        .stApp {{ background-color: {palette['background']}; color: {palette['text']}; }}
        [data-testid="stSidebar"] {{ background-color: {palette['sidebar']}; }}
        [data-testid="stHeader"] {{ background-color: {palette['background']}; }}
        .stApp, .stApp label, .stApp p, .stApp h1, .stApp h2, .stApp h3,
        .stApp [data-testid="stMarkdown"], .stApp [data-testid="stCaptionContainer"] {{
            color: {palette['text']};
        }}
        .stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div {{
            background-color: {palette['input']}; color: {palette['text']};
            border-color: {palette['border']};
        }}
        .stApp [data-testid="stNumberInput"] button {{
            color: {palette['text']}; background-color: {palette['surface']};
        }}
        .stApp [data-testid="stTabs"] button {{ color: {palette['text']}; }}
        .stApp [data-testid="stTabs"] button[aria-selected="true"] {{
            color: {palette['accent']}; border-bottom-color: {palette['accent']};
        }}
        [data-testid="stMetric"] {{
            background: {palette['surface']}; border: 1px solid {palette['border']};
            border-radius: 10px; padding: 10px;
        }}
        .insight-box {{
            background: {palette['insight']}; color: {palette['text']};
            border-left: 4px solid {palette['accent']}; padding: 12px;
            border-radius: 5px; margin: 10px 0;
        }}
        .stDataFrame {{ color: {palette['text']}; }}
        [data-testid="stDataFrame"] {{ border-color: {palette['border']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_chart(chart):
    palette = THEMES.get(st.session_state.get("theme", "light"), THEMES["light"])
    return (
        chart.configure(background=palette["background"])
        .configure_axis(
            labelColor=palette["text"],
            titleColor=palette["text"],
            gridColor=palette["grid"],
            domainColor=palette["border"],
            tickColor=palette["border"],
        )
        .configure_legend(labelColor=palette["text"], titleColor=palette["text"])
        .configure_title(color=palette["text"])
    )
