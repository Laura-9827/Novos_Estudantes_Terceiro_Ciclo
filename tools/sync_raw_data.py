from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config.settings import RAW_DATA_FILE  # noqa: E402
from src.etl.pipeline import load_or_build_processed  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a new raw spreadsheet into data/raw and optionally rebuild the processed dashboard dataset.",
    )
    parser.add_argument(
        "source",
        help="Path to the new raw spreadsheet (.XLS or .XLSX).",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild data/processed/dashboard_data.csv after copying the raw file.",
    )
    return parser.parse_args()


def sync_raw_file(source_path: Path) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    RAW_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, RAW_DATA_FILE)
    return RAW_DATA_FILE


def main() -> None:
    args = parse_args()
    source_path = Path(args.source).expanduser().resolve()

    copied_to = sync_raw_file(source_path)
    print(f"Raw file copied to {copied_to}")

    if args.rebuild:
        processed = load_or_build_processed(force=True)
        print(f"Processed dataset rebuilt with shape {processed.shape}")


if __name__ == "__main__":
    main()