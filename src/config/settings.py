from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = BASE_DIR / "Cópia_bd_selo.XLS"
RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "Cópia_bd_selo.XLS"
PROCESSED_DATA_FILE = BASE_DIR / "data" / "processed" / "dashboard_data.csv"
UNIVERSE_SIZE = 387
RESPONSE_RATE_NUMERATOR = 281
BRAND_RGB = (13, 40, 194)
BRAND_BLUE = f"rgb{BRAND_RGB}"


def brand_mix(white_ratio: float) -> str:
    red, green, blue = BRAND_RGB
    return f"rgb({round(red * (1 - white_ratio) + 255 * white_ratio)}, {round(green * (1 - white_ratio) + 255 * white_ratio)}, {round(blue * (1 - white_ratio) + 255 * white_ratio)})"


BRAND_CONTINUOUS_SCALE = [
    brand_mix(0.92),
    brand_mix(0.72),
    brand_mix(0.46),
    BRAND_BLUE,
]
BRAND_DISCRETE_SEQUENCE = [
    BRAND_BLUE,
    brand_mix(0.22),
    brand_mix(0.42),
    brand_mix(0.62),
]