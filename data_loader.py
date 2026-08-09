import json
import os
import tempfile
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import requests

NEEDED_COLS = [
    "wiki_entity_id",
    "object_id",
    "spectrum",
    "Z",
    "ZERR",
    "Z_ERR",
    "evidence_quotes",
    "arxiv_id",
    "ra_spectra",
    "dec_spectra",
    "ra_mentions",
    "dec_mentions",
]


def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def load_captions(path: str) -> list[dict]:
    """Load JSONL captions from a local file path or URL."""
    print(f"[data_loader] Loading captions from: {path}", flush=True)
    captions = []
    if is_url(path):
        resp = requests.get(path, stream=True)
        resp.raise_for_status()
        lines = resp.text.strip().split("\n")
        for line in lines:
            if line.strip():
                captions.append(json.loads(line))
    else:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    captions.append(json.loads(line))
    print(f"[data_loader] Successfully loaded {len(captions)} captions.", flush=True)
    return captions


def download_file(url: str) -> str:
    """Download a remote URL to a local temporary file with progress logging."""
    filename = url.split("/")[-1].split("?")[0]
    temp_dir = tempfile.gettempdir()
    local_path = os.path.join(temp_dir, filename)

    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        print(f"[data_loader] Using cached file: {local_path}", flush=True)
        return local_path

    print(f"[data_loader] Downloading {url} -> {local_path} ...", flush=True)
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    total_size = int(resp.headers.get("content-length", 0))

    downloaded = 0
    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(
                        f"[data_loader] Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)",
                        flush=True,
                    )
                else:
                    print(
                        f"[data_loader] Downloaded {downloaded / (1024*1024):.1f} MB",
                        flush=True,
                    )
    print(f"[data_loader] Finished downloading {local_path}", flush=True)
    return local_path


def load_parquet(path: str) -> pd.DataFrame:
    """
    Load a Parquet file from a local path or URL cleanly.
    Uses column filtering via PyArrow to drastically reduce memory & bandwidth footprint.
    """
    print(f"[data_loader] Processing parquet path: {path}", flush=True)
    target_path = path
    if is_url(path):
        target_path = download_file(path)

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"Parquet file not found at path: {target_path}")

    # Read table with column filter
    table = pq.read_table(target_path)
    available_cols = [c for c in NEEDED_COLS if c in table.schema.names]
    df = table.select(available_cols).to_pandas()

    ram_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(
        f"[data_loader] Loaded Parquet ({target_path}): {len(df)} rows, {len(available_cols)} columns, RAM: {ram_mb:.2f} MB",
        flush=True,
    )
    return df


def get_object_data(
    captions: list[dict], desi_df: pd.DataFrame, sdss_df: pd.DataFrame, index: int
) -> dict:
    """
    Given the captions list, DESI and SDSS dataframes, and a target caption index,
    returns a dictionary containing caption details, quotes, and observation spectra.
    """
    if index < 0 or index >= len(captions):
        raise IndexError(f"Caption index {index} out of bounds (0 to {len(captions)-1}).")

    caption_record = captions[index]
    object_key = caption_record["object_key"]
    dataset_source = caption_record["dataset_source"].lower()

    # Select appropriate parquet dataframe
    df = desi_df if dataset_source == "desi" else sdss_df

    # Filter by wiki_entity_id
    matches = df[df["wiki_entity_id"] == object_key]

    # Extract all evidence quotes (deduplicated by quote_id)
    seen_quote_ids = set()
    evidence_quotes = []

    for _, row in matches.iterrows():
        arxiv_id = str(row.get("arxiv_id", "Unknown"))
        eq = row.get("evidence_quotes", {})
        if isinstance(eq, dict):
            quote_ids = eq.get("quote_id", [])
            quotes = eq.get("quote", [])
            # Convert numpy arrays to lists if necessary
            if hasattr(quote_ids, "tolist"):
                quote_ids = quote_ids.tolist()
            if hasattr(quotes, "tolist"):
                quotes = quotes.tolist()

            for qid, q in zip(quote_ids, quotes):
                qid_str = str(qid)
                if qid_str not in seen_quote_ids:
                    seen_quote_ids.add(qid_str)
                    evidence_quotes.append({
                        "quote_id": qid_str,
                        "arxiv_id": arxiv_id,
                        "quote": str(q)
                    })

    # Group by object_id for distinct spectral observations
    observations = []
    if not matches.empty:
        # Group preserving order of appearance
        grouped = matches.groupby("object_id", sort=False)
        for obj_id, group in grouped:
            first_row = group.iloc[0]
            spectrum = first_row.get("spectrum", {})

            # Extract redshift and error
            z_val = first_row.get("Z", None)
            if z_val is not None and pd.notna(z_val):
                z_val = float(z_val)
            else:
                z_val = None

            # DESI uses ZERR, SDSS uses Z_ERR
            z_err_col = "ZERR" if dataset_source == "desi" else "Z_ERR"
            z_err_val = first_row.get(z_err_col, None)
            if z_err_val is not None and pd.notna(z_err_val):
                z_err_val = float(z_err_val)
            else:
                z_err_val = None

            # Extract spectrum arrays
            flux = np.array(spectrum.get("flux", [])) if isinstance(spectrum, dict) else np.array([])
            wavelength = np.array(spectrum.get("lambda", [])) if isinstance(spectrum, dict) else np.array([])
            ivar = np.array(spectrum.get("ivar", [])) if isinstance(spectrum, dict) else np.array([])
            mask = np.array(spectrum.get("mask", [])) if isinstance(spectrum, dict) else np.array([])

            observations.append({
                "object_id": str(obj_id),
                "flux": flux,
                "lambda": wavelength,
                "ivar": ivar,
                "mask": mask,
                "z": z_val,
                "z_err": z_err_val,
                "ra": float(first_row.get("ra_spectra", first_row.get("ra_mentions", 0.0))),
                "dec": float(first_row.get("dec_spectra", first_row.get("dec_mentions", 0.0))),
            })

    output_section = caption_record.get("output", {})
    return {
        "index": index,
        "object_key": object_key,
        "dataset_source": dataset_source,
        "ra": caption_record.get("ra"),
        "dec": caption_record.get("dec"),
        "strategy": caption_record.get("strategy"),
        "model": caption_record.get("model"),
        "timestamp": caption_record.get("timestamp"),
        "caption": output_section.get("caption", ""),
        "thought_summaries": output_section.get("thought_summaries", []),
        "is_insufficient": output_section.get("is_insufficient", False),
        "evidence_quotes": evidence_quotes,
        "observations": observations,
    }
