import glob
import os

import streamlit as st


def get_config_value(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value:
        return value
    try:
        if st.secrets.get(key):
            return str(st.secrets[key])
    except Exception:
        pass
    return default


def first_existing(candidates: list[str]) -> str | None:
    return next((path for path in candidates if path and os.path.isfile(path)), None)


DATA_DIR = get_config_value("DATA_DIR", "data") or "data"
FEEDBACK_DATASET_REPO = get_config_value(
    "FEEDBACK_DATASET_REPO", "ibrahimhabibeg/spectra-captions-feedback-test"
)
HF_TOKEN = get_config_value("HF_TOKEN")

SPECTRA_CAPTIONS_JSONL_PATH = get_config_value(
    "SPECTRA_CAPTIONS_JSONL_PATH",
    first_existing(
        [
            os.path.join(DATA_DIR, "spectra_captions.jsonl"),
            os.path.join(DATA_DIR, "captions.jsonl"),
            "output/captions.jsonl",
        ]
    )
    or os.path.join(DATA_DIR, "spectra_captions.jsonl"),
)

_lightcurve_candidates = [
    os.path.join(DATA_DIR, "lightcurve_captions.jsonl"),
    *sorted(glob.glob(os.path.join(DATA_DIR, "yse_abc_*.jsonl")), reverse=True),
    *sorted(glob.glob(os.path.join(DATA_DIR, "*lightcurve*.jsonl")), reverse=True),
]
LIGHTCURVE_CAPTIONS_JSONL_PATH = get_config_value(
    "LIGHTCURVE_CAPTIONS_JSONL_PATH",
    first_existing(_lightcurve_candidates),
)

DESI_PARQUET_PATH = get_config_value(
    "DESI_PARQUET_PATH",
    first_existing(
        [
            os.path.join(DATA_DIR, "crossmatch_desi.parquet"),
            os.path.join(DATA_DIR, "crossmatch_desi_1.0arcsec.parquet"),
        ]
    )
    or os.path.join(DATA_DIR, "crossmatch_desi.parquet"),
)
SDSS_PARQUET_PATH = get_config_value(
    "SDSS_PARQUET_PATH",
    first_existing(
        [
            os.path.join(DATA_DIR, "crossmatch_sdss.parquet"),
            os.path.join(DATA_DIR, "crossmatch_sdss_1.0arcsec.parquet"),
        ]
    )
    or os.path.join(DATA_DIR, "crossmatch_sdss.parquet"),
)

# Backward-compatible alias used by older integrations.
CAPTIONS_JSONL_PATH = SPECTRA_CAPTIONS_JSONL_PATH
