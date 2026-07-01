from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config.settings import PROCESSED_DATA_FILE, RAW_DATA_FILE
from src.services.data import split_codes, split_school_codes


def _source_file() -> Path:
    return RAW_DATA_FILE


def extract_raw() -> pd.DataFrame:
    source_file = _source_file()
    if not source_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {source_file}")
    df = pd.read_excel(source_file)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    transformed = df.copy()

    transformed["RESPONDENT_AGE"] = pd.to_numeric(transformed.get("RESPONDENT_AGE"), errors="coerce")
    transformed["ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        transformed.get("ANO_CONCLUSAO_DA_HABILITACAO_ANTERIOR"), errors="coerce"
    )
    transformed["NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"] = pd.to_numeric(
        transformed.get("NOTA_CONCLUSAO_HABILITACAO_ANTERIOR"), errors="coerce"
    )

    if "ESCOLAS_CURSO" in transformed.columns:
        transformed["ESCOLAS_CURSO_NORMALIZED"] = transformed["ESCOLAS_CURSO"].apply(split_school_codes)

    question_columns = [col for col in transformed.columns if col.startswith("1-")]
    for column in question_columns:
        if transformed[column].dtype == object:
            transformed[column] = transformed[column].astype("string")

    return transformed


def load_or_build_processed(force: bool = False) -> pd.DataFrame:
    if force or not PROCESSED_DATA_FILE.exists():
        processed = transform_data(extract_raw())
        PROCESSED_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        processed.to_csv(PROCESSED_DATA_FILE, index=False)
        return processed

    processed_mtime = PROCESSED_DATA_FILE.stat().st_mtime
    source_file = _source_file()
    if source_file.exists() and source_file.stat().st_mtime > processed_mtime:
        processed = transform_data(extract_raw())
        processed.to_csv(PROCESSED_DATA_FILE, index=False)
        return processed

    return pd.read_csv(PROCESSED_DATA_FILE)