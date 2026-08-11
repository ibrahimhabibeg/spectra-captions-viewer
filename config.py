import os
from huggingface_hub import download_bucket_files
import streamlit as st


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

CAPTIONS_JSONL_PATH = os.path.join(DATA_DIR, "captions.jsonl")
DESI_PARQUET_PATH = os.path.join(DATA_DIR, "crossmatch_desi.parquet")
SDSS_PARQUET_PATH = os.path.join(DATA_DIR, "crossmatch_sdss.parquet")


def ensure_data_files_exist():
    captions_exist = os.path.exists(CAPTIONS_JSONL_PATH)
    desi_exist = os.path.exists(DESI_PARQUET_PATH)
    sdss_exist = os.path.exists(SDSS_PARQUET_PATH)

    if not (captions_exist and desi_exist and sdss_exist):
        print(
            f"[config] Data files missing in '{DATA_DIR}'. Downloading from HuggingFace Storage Bucket '{HF_BUCKET}'...",
            flush=True,
        )
        os.makedirs(DATA_DIR, exist_ok=True)
        download_bucket_files(
            bucket_id=HF_BUCKET,
            files=[
                ("captions.jsonl", CAPTIONS_JSONL_PATH),
                ("crossmatch_desi.parquet", DESI_PARQUET_PATH),
                ("crossmatch_sdss.parquet", SDSS_PARQUET_PATH),
            ],
            token=HF_TOKEN,
        )
        print(
            "[config] Dataset download from HuggingFace Storage Bucket complete!",
            flush=True,
        )


ensure_data_files_exist()
