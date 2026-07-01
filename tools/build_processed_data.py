from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.pipeline import load_or_build_processed


if __name__ == "__main__":
    df = load_or_build_processed(force=True)
    print(f"Processed dataset written with shape {df.shape}")