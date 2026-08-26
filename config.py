import os
import streamlit as st
from huggingface_hub import HfApi

def get_config_value(key: str, default: str | None = None) -> str | None:
    val = os.getenv(key)
    if val is not None and val != "":
        return val
    try:
        if key in st.secrets:
            sec_val = st.secrets[key]
            if sec_val is not None and str(sec_val) != "":
                return str(sec_val)
    except Exception:
        pass
    return default


DATA_DIR = get_config_value("DATA_DIR", "data")
HF_BUCKET = get_config_value("HF_BUCKET", "ibrahimhabibeg/spectra_captions")
FEEDBACK_DATASET_REPO = get_config_value(
    "FEEDBACK_DATASET_REPO", "ibrahimhabibeg/spectra-captions-feedback-test"
)
HF_TOKEN = get_config_value("HF_TOKEN", None)

SPECTRA_CAPTIONS_JSONL_PATH = os.path.join(DATA_DIR, "captions.jsonl")
CAPTIONS_JSONL_PATH = SPECTRA_CAPTIONS_JSONL_PATH
DESI_PARQUET_PATH = os.path.join(DATA_DIR, "crossmatch_desi.parquet")
SDSS_PARQUET_PATH = os.path.join(DATA_DIR, "crossmatch_sdss.parquet")
LIGHTCURVE_CAPTIONS_JSONL_PATH = os.path.join(DATA_DIR, "lightcurve_captions.jsonl")


def ensure_data_files_exist():
    captions_exist = os.path.exists(SPECTRA_CAPTIONS_JSONL_PATH)
    desi_exist = os.path.exists(DESI_PARQUET_PATH)
    sdss_exist = os.path.exists(SDSS_PARQUET_PATH)
    lightcurve_captions_exist = os.path.exists(LIGHTCURVE_CAPTIONS_JSONL_PATH)

    if not (captions_exist and desi_exist and sdss_exist and lightcurve_captions_exist):
        print(
            f"[config] Data files missing in '{DATA_DIR}'. Downloading from HuggingFace Storage Bucket '{HF_BUCKET}'...",
            flush=True,
        )
        os.makedirs(DATA_DIR, exist_ok=True)
        api = HfApi()
        api.download_bucket_files(
            bucket_id=HF_BUCKET,
            files=[
                ("captions.jsonl", SPECTRA_CAPTIONS_JSONL_PATH),
                ("crossmatch_desi.parquet", DESI_PARQUET_PATH),
                ("crossmatch_sdss.parquet", SDSS_PARQUET_PATH),
                ("lightcurve_captions.jsonl", LIGHTCURVE_CAPTIONS_JSONL_PATH),
            ],
            token=HF_TOKEN,
        )
        print(
            "[config] Dataset download from HuggingFace Storage Bucket complete!",
            flush=True,
        )


ensure_data_files_exist()
