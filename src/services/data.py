from __future__ import annotations

import re

import pandas as pd

from src.config.mappings import DOUBLE_SCHOOL_COURSES
from src.config.settings import DATA_FILE


OPEN_ENDED_EXCLUSIONS = {
    "1-5",
    "1-7",
    "1-9",
    "1-12",
    "1-14",
    "1-16",
    "1-21",
    "1-23",
    "1-25",
    "1-27",
}


def read_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_processed() -> pd.DataFrame:
    df = read_data()
    df["RESPONDENT_AGE"] = pd.to_numeric(df.get("RESPONDENT_AGE"), errors="coerce")
    df["ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        df.get("ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"), errors="coerce"
    )
    df["NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        df.get("NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"), errors="coerce"
    )
    return df


def eligible_questions(df: pd.DataFrame) -> list[str]:
    question_columns = [col for col in df.columns if col.startswith("1-")]
    eligible = [
        col
        for col in question_columns
        if col.split()[0] not in OPEN_ENDED_EXCLUSIONS and col not in OPEN_ENDED_EXCLUSIONS
    ]
    return eligible


def eligible_mask(df: pd.DataFrame, minimum_ratio: float = 0.75) -> pd.Series:
    questions = eligible_questions(df)
    if not questions:
        return pd.Series(True, index=df.index)
    coverage = df[questions].replace(r"^\s*$", pd.NA, regex=True).notna().mean(axis=1)
    return coverage >= minimum_ratio


def split_codes(value: object) -> list[int]:
    if pd.isna(value):
        return []
    matches = re.findall(r"\d+", str(value))
    return [int(match) for match in matches]


def split_school_codes(value: object) -> list[str]:
    if pd.isna(value):
        return []
    parts = re.split(r"[;,]", str(value))
    return [part.strip() for part in parts if part.strip()]


def find_column(df: pd.DataFrame, prefix: str) -> str:
    if prefix in df.columns:
        return prefix
    matches = [col for col in df.columns if str(col).startswith(prefix)]
    if not matches:
        raise KeyError(f"Column starting with {prefix!r} was not found")
    return matches[0]


def schools_for_course(course: str, raw_value: object) -> list[str]:
    schools = split_school_codes(raw_value)
    if schools:
        return schools
    return DOUBLE_SCHOOL_COURSES.get(course, [])


def school_options(df: pd.DataFrame) -> list[str]:
    schools: set[str] = set()
    for _, row in df.iterrows():
        schools.update(schools_for_course(str(row.get("NOME_CURSO", "")), row.get("ESCOLAS_CURSO")))
    return sorted(schools)


def course_options(df: pd.DataFrame, selected_school: str | None) -> list[str]:
    filtered = df
    if selected_school:
        filtered = filtered[
            filtered.apply(
                lambda row: selected_school in schools_for_course(str(row["NOME_CURSO"]), row.get("ESCOLAS_CURSO")),
                axis=1,
            )
        ]
    return sorted(filtered["NOME_CURSO"].dropna().astype(str).unique().tolist())


def filter_data(df: pd.DataFrame, selected_school: str | None, selected_course: str | None) -> pd.DataFrame:
    filtered = df.copy()
    if selected_school:
        filtered = filtered[
            filtered.apply(
                lambda row: selected_school in schools_for_course(str(row["NOME_CURSO"]), row.get("ESCOLAS_CURSO")),
                axis=1,
            )
        ]
    if selected_course:
        filtered = filtered[filtered["NOME_CURSO"].astype(str) == selected_course]
    return filtered


def format_percentage(value: float) -> str:
    return f"{value:.1f}%"


def categorical_summary(series: pd.Series, drop_missing: bool = True) -> pd.DataFrame:
    clean = series.copy()
    if drop_missing:
        clean = clean.replace({"nan": pd.NA, "None": pd.NA, "": pd.NA}).dropna()
    counts = clean.astype(str).value_counts().reset_index()
    counts.columns = ["Categoria", "Respostas"]
    total = counts["Respostas"].sum()
    counts["Percentagem"] = (counts["Respostas"] / total * 100).round(1) if total else 0
    return counts


def code_counts(series: pd.Series, mapping: dict[int, str]) -> pd.DataFrame:
    codes = series.map(split_codes)
    exploded = codes.explode().dropna()
    if exploded.empty:
        return pd.DataFrame({"Opção": list(mapping.values()), "Respostas": [0] * len(mapping)})
    counts = exploded.astype(int).value_counts().reindex(mapping.keys(), fill_value=0).reset_index()
    counts.columns = ["Código", "Respostas"]
    counts["Opção"] = counts["Código"].map(mapping)
    counts = counts[["Opção", "Respostas"]]
    total = counts["Respostas"].sum()
    counts["Percentagem"] = (counts["Respostas"] / total * 100).round(1) if total else 0
    return counts


def mean_likert(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    for column in columns:
        numeric = pd.to_numeric(df[column], errors="coerce")
        numeric = numeric.mask(numeric == 66)
        mean_value = round(float(numeric.mean()), 2) if numeric.notna().any() else 0.0
        label = column.split(" ", 1)[0]
        rows.append({"Indicador": label, "Média": mean_value})
    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("Média", ascending=True).reset_index(drop=True)
    return result