import os

# Data Paths (Can be local paths or URLs)
DESI_PARQUET_PATH = os.getenv(
    "DESI_PARQUET_PATH", "data/crossmatch_desi_1.0arcsec.parquet"
)
SDSS_PARQUET_PATH = os.getenv(
    "SDSS_PARQUET_PATH", "data/crossmatch_sdss_1.0arcsec.parquet"
)
CAPTIONS_JSONL_PATH = os.getenv(
    "CAPTIONS_JSONL_PATH", "output/captions.jsonl"
)

# HuggingFace Feedback Dataset Repository ID
FEEDBACK_DATASET_REPO = os.getenv(
    "FEEDBACK_DATASET_REPO", "ibrahimhabibeg/spectra-captions-feedback-test"
)

# Optional HuggingFace Token for writing feedback (read from HF Space secret or local env)
HF_TOKEN = os.getenv("HF_TOKEN", None)
