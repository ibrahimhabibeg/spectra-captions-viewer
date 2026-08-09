import json
import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

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


def load_captions(path: str) -> list[dict]:
    """Load JSONL captions from a local file path."""
    print(f"[data_loader] Loading captions from: {path}", flush=True)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Captions file not found at: {path}")

    captions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                captions.append(json.loads(line))
    print(f"[data_loader] Successfully loaded {len(captions)} captions.", flush=True)
    return captions


def load_parquet(path: str) -> pd.DataFrame:
    """
    Load a Parquet file from a local file path.
    Uses PyArrow column filtering to keep memory footprint under 5 MB.
    """
    print(f"[data_loader] Loading parquet file: {path}", flush=True)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Parquet file not found at: {path}")

    table = pq.read_table(path)
    available_cols = [c for c in NEEDED_COLS if c in table.schema.names]
    df = table.select(available_cols).to_pandas()

    ram_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(
        f"[data_loader] Loaded Parquet ({path}): {len(df)} rows, {len(available_cols)} columns, RAM: {ram_mb:.2f} MB",
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
