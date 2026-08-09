import os

# Configurable data directory path (defaults to 'data')
DATA_DIR = os.getenv("DATA_DIR", "data")


def resolve_data_file(filename: str, fallback_local_path: str) -> str:
    """Resolve a file path inside DATA_DIR with a fallback path if default differs."""
    primary_path = os.path.join(DATA_DIR, filename)
    if os.path.exists(primary_path):
        return primary_path
    if os.path.exists(fallback_local_path):
        return fallback_local_path
    return primary_path


# Paths for the three required data files
CAPTIONS_JSONL_PATH = resolve_data_file("captions.jsonl", "output/captions.jsonl")
DESI_PARQUET_PATH = resolve_data_file(
    "crossmatch_desi.parquet", "data/crossmatch_desi_1.0arcsec.parquet"
)
SDSS_PARQUET_PATH = resolve_data_file(
    "crossmatch_sdss.parquet", "data/crossmatch_sdss_1.0arcsec.parquet"
)

# HuggingFace Feedback Dataset Repository ID
FEEDBACK_DATASET_REPO = os.getenv(
    "FEEDBACK_DATASET_REPO", "ibrahimhabibeg/spectra-captions-feedback-test"
)

# Optional HuggingFace Token for writing feedback
HF_TOKEN = os.getenv("HF_TOKEN", None)
