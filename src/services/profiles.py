from __future__ import annotations

import pandas as pd

from src.config.mappings import Q_18
from src.services.data import categorical_summary, code_counts, find_column


def typical_profile(df: pd.DataFrame) -> dict[str, str]:
    age_bins = [18, 24, 29, 34, 39, 44, 49, 59, 100]
    age_labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-59", "60+"]
    age_bucket = pd.cut(df["RESPONDENT_AGE"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)
    age_mode = age_bucket.value_counts().index[0] if not age_bucket.dropna().empty else "-"

    def modal_value(column: str) -> str:
        series = df[column].replace({"nan": pd.NA, "None": pd.NA}).dropna()
        if series.empty:
            return "-"
        return str(series.astype(str).value_counts().index[0])

    return {
        "género": modal_value("RESPONDENT_GENDER"),
        "faixa_etária": str(age_mode),
        "nacionalidade": modal_value("NACIONALIDADE_1"),
        "situação profissional": modal_value("CONDICAO_PROFISSIONAL_ALUNO"),
        "setor profissional": modal_value("SCHOLARSHIP_GRANT_OWNER"),
    }


def profile_subsections(df: pd.DataFrame) -> dict[str, list[tuple[str, str]]]:
    def first_category(column: str) -> str:
        counts = categorical_summary(df[column], drop_missing=True)
        if counts.empty:
            return "-"
        first = counts.iloc[0]
        return f"{first['Categoria']} ({first['Percentagem']}%)"

    def coded_category(column: str, mapping: dict[int, str]) -> str:
        counts = code_counts(df[column], mapping)
        if counts.empty:
            return "-"
        first = counts.iloc[0]
        total = counts["Respostas"].sum()
        percentage = round(first["Respostas"] / total * 100, 1) if total else 0
        return f"{first['Opção']} ({percentage}%)"

    age_bins = [18, 24, 29, 34, 39, 44, 49, 59, 100]
    age_labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-59", "60+"]
    age_bucket = pd.cut(df["RESPONDENT_AGE"], bins=age_bins, labels=age_labels, right=True, include_lowest=True)
    age_counts = age_bucket.value_counts().reset_index()
    age_counts.columns = ["Categoria", "Respostas"]
    age_counts["Percentagem"] = (age_counts["Respostas"] / age_counts["Respostas"].sum() * 100).round(1)
    age_mode = age_counts.iloc[0] if not age_counts.empty else None

    sociodemografico = [
        ("Género", first_category("RESPONDENT_GENDER")),
        ("Idade", f"{age_mode['Categoria']} ({age_mode['Percentagem']}%)" if age_mode is not None else "-"),
        ("Nacionalidade", first_category("NACIONALIDADE_1")),
    ]

    profissional = [
        ("Situação profissional", first_category("CONDICAO_PROFISSIONAL_ALUNO")),
        ("Setor de trabalho", coded_category(find_column(df, "1-8"), Q_18)),
    ]

    return {
        "sociodemográfico": sociodemografico,
        "profissional": profissional,
    }