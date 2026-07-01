from __future__ import annotations

import streamlit as st

from src.config.settings import BRAND_BLUE


def apply_blue_theme() -> None:
    theme_css = """
        <style>
        :root {
            --brand: __BRAND_BLUE__;
            --brand-soft: rgba(13, 40, 194, 0.10);
            --brand-softer: rgba(13, 40, 194, 0.06);
            --ink: #0f172a;
            --muted: #475569;
            --card: #ffffff;
            --border: rgba(15, 23, 42, 0.08);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(13, 40, 194, 0.08), transparent 30%),
                linear-gradient(180deg, #f8fbff 0%, #ffffff 45%, #f6f9ff 100%);
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .hero {
            padding: 1.4rem 1.5rem;
            border: 1px solid var(--border);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(13, 40, 194, 0.97), rgba(13, 40, 194, 0.78));
            color: white;
            box-shadow: 0 18px 40px rgba(13, 40, 194, 0.16);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
        }
        .hero p {
            margin: 0.4rem 0 0;
            opacity: 0.92;
            max-width: 900px;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.5rem;
        }
        div[data-baseweb="select"] > div {
            border-radius: 14px;
        }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.75rem;
            line-height: 1.1;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.05rem;
            line-height: 1.05;
        }
        div[data-testid="stMetricValue"] svg {
            display: none;
        }
        </style>
        """.replace("__BRAND_BLUE__", BRAND_BLUE)
    st.markdown(theme_css, unsafe_allow_html=True)