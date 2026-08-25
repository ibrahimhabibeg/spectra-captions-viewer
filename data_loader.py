import json
import math
import os
import re

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import streamlit as st

METADATA_COLS = [
    "name",
    "wiki_entity_id",
    "object_id",
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


@st.cache_data
def load_captions(path: str | None) -> list[dict]:
    """Load JSONL records, returning an empty dataset when the file is absent."""
    print(f"[data_loader] Loading captions from: {path}", flush=True)
    if not path or not os.path.isfile(path):
        print(
            "[data_loader] Caption file unavailable; using an empty dataset.",
            flush=True,
        )
        return []

    captions = []
    with open(path, "r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            if line.strip():
                record = json.loads(line)
                record["file_index"] = index
                captions.append(record)
    print(f"[data_loader] Successfully loaded {len(captions)} rows.", flush=True)
    return captions


def parse_lightcurve_prompt(prompt: str) -> list[dict]:
    """Extract valid SNANA photometry from an embedded light_curve block."""
    match = re.search(r"<light_curve>\s*(.*?)\s*</light_curve>", prompt or "", re.DOTALL)
    if not match:
        return []

    observations = []
    for line in match.group(1).splitlines():
        fields = line.split()
        if len(fields) < 8 or fields[0].upper() == "MJD":
            continue
        try:
            mjd = float(fields[0])
            magnitude = float(fields[5])
            magnitude_error = float(fields[6])
            if not math.isfinite(mjd) or not math.isfinite(magnitude):
                continue
            if not math.isfinite(magnitude_error) or magnitude_error < 0:
                magnitude_error = None
            observations.append(
                {
                    "mjd": mjd,
                    "filter": fields[1],
                    "flux": float(fields[3]),
                    "flux_error": float(fields[4]),
                    "magnitude": magnitude,
                    "magnitude_error": magnitude_error,
                    "flag": fields[7],
                }
            )
        except ValueError:
            continue
    return observations


def _nested_lightcurve_object(record: dict, row_index: int) -> dict:
    conditions = record.get("conditions", {})
    by_label = {}
    for condition_name, output in conditions.items():
        label = condition_name[:1].upper()
        if label in {"A", "B", "C"}:
            by_label[label] = (condition_name, output)

    if set(by_label) != {"A", "B", "C"}:
        identifier = record.get("comparison_id", record.get("object_id", row_index))
        raise ValueError(
            f"Lightcurve comparison {identifier} must contain A, B, and C conditions."
        )

    candidates = []
    source_names = []
    evidence_links = {}
    lightcurve = []
    for offset, label in enumerate(("A", "B", "C")):
        condition_name, output = by_label[label]
        source = record.get("dataset_sources", {}).get(condition_name, "unknown")
        source_values = source if isinstance(source, list) else [source]
        for source_value in source_values:
            source_text = str(source_value)
            if source_text not in source_names:
                source_names.append(source_text)

        inputs = record.get("inputs", {}).get(condition_name, {})
        for atel_id, url in zip(
            inputs.get("atel_ids", []), inputs.get("atel_urls", [])
        ):
            evidence_links[str(atel_id)] = str(url)

        if not lightcurve:
            lightcurve = parse_lightcurve_prompt(output.get("prompt", ""))

        candidates.append(
            {
                "file_index": row_index * 3 + offset,
                "source_file_index": row_index,
                "condition": condition_name,
                "object_key": record.get(
                    "object_id", record.get("comparison_id", f"row-{row_index}")
                ),
                "dataset_source": " + ".join(str(value) for value in source_values),
                "model": record.get("model", "Unknown"),
                "strategy": condition_name,
                "comparison_strategy": record.get("strategy"),
                "timestamp": record.get("timestamp"),
                "output": output,
            }
        )

    return {
        "object_key": candidates[0]["object_key"],
        "dataset_source": " / ".join(source_names),
        "ra": None,
        "dec": None,
        "captions": candidates,
        "modality": "lightcurves",
        "lightcurve": lightcurve,
        "evidence_links": evidence_links,
    }


@st.cache_data
def load_and_group_objects(path: str | None, modality: str = "spectra") -> list[dict]:
    """Load flat spectral captions or nested A/B/C lightcurve comparisons."""
    raw_captions = load_captions(path)
    if not raw_captions:
        return []

    nested = [record for record in raw_captions if "conditions" in record]
    flat = [record for record in raw_captions if "conditions" not in record]
    objects = [
        _nested_lightcurve_object(record, record["file_index"]) for record in nested
    ]

    grouped_map = {}
    ordered_keys = []
    for caption in flat:
        object_key = caption.get("object_key")
        group_key = (
            str(caption.get("dataset_source", "sdss")).lower(),
            object_key,
        )
        if group_key not in grouped_map:
            grouped_map[group_key] = {
                "object_key": object_key,
                "dataset_source": group_key[0],
                "ra": caption.get("ra"),
                "dec": caption.get("dec"),
                "captions": [],
                "modality": modality,
                "lightcurve": [],
                "evidence_links": {},
            }
            ordered_keys.append(group_key)
        grouped_map[group_key]["captions"].append(caption)

    for key in ordered_keys:
        grouped = grouped_map[key]
        captions = grouped["captions"]
        for batch_index, start in enumerate(range(0, len(captions), 3)):
            batch = grouped.copy()
            batch["captions"] = captions[start : start + 3]
            batch["comparison_batch"] = batch_index
            batch["comparison_batch_count"] = math.ceil(len(captions) / 3)
            objects.append(batch)
    return objects


@st.cache_data
def load_parquet(path: str | None) -> pd.DataFrame:
    """Load spectral metadata or return an empty compatible dataframe."""
    print(f"[data_loader] Loading parquet metadata file: {path}", flush=True)
    if not path or not os.path.isfile(path):
        print("[data_loader] Parquet unavailable; spectra will be empty.", flush=True)
        empty = pd.DataFrame(columns=METADATA_COLS)
        empty.attrs["parquet_path"] = None
        return empty

    parquet_file = pq.ParquetFile(path)
    available_columns = [
        column
        for column in METADATA_COLS
        if column in parquet_file.schema.to_arrow_schema().names
    ]
    dataframe = pq.read_table(path, columns=available_columns).to_pandas()
    dataframe.attrs["parquet_path"] = path
    return dataframe


def fetch_spectrum_dict(parquet_path: str | None, object_id_value) -> dict:
    if not parquet_path or not os.path.isfile(parquet_path):
        return {}

    dataset = ds.dataset(parquet_path, format="parquet")
    column_type = dataset.schema.field("object_id").type
    if str(column_type).startswith("int"):
        try:
            target_value = int(object_id_value)
        except (ValueError, TypeError):
            target_value = object_id_value
    else:
        target_value = str(object_id_value)

    table = dataset.to_table(
        filter=(ds.field("object_id") == target_value),
        columns=["object_id", "spectrum"],
    )
    return table.column("spectrum")[0].as_py() if len(table) else {}


def _format_captions(caption_records: list[dict]) -> list[dict]:
    formatted = []
    for record in caption_records:
        output = record.get("output", {})
        formatted.append(
            {
                "file_index": record.get("file_index", 0),
                "source_file_index": record.get("source_file_index"),
                "condition": record.get("condition"),
                "model": record.get("model", "Unknown"),
                "strategy": record.get("strategy", "Unknown"),
                "comparison_strategy": record.get("comparison_strategy"),
                "timestamp": record.get("timestamp"),
                "caption": output.get("caption", ""),
                "thought_summaries": output.get("thought_summaries", []),
                "is_insufficient": output.get("is_insufficient", False),
            }
        )
    return formatted


def get_object_eval_data(
    objects: list[dict],
    desi_df: pd.DataFrame,
    sdss_df: pd.DataFrame,
    index: int,
) -> dict:
    """Build the shared evidence and candidate payload for one object."""
    if index < 0 or index >= len(objects):
        raise IndexError(f"Object index {index} out of bounds.")

    summary = objects[index]
    if summary.get("modality") == "lightcurves":
        return {
            "index": index,
            "object_key": summary["object_key"],
            "object_name": None,
            "dataset_source": summary["dataset_source"],
            "ra": None,
            "dec": None,
            "evidence_quotes": [],
            "evidence_links": summary.get("evidence_links", {}),
            "observations": [],
            "lightcurve": summary.get("lightcurve", []),
            "captions": _format_captions(summary["captions"]),
            "modality": "lightcurves",
        }

    object_key = summary["object_key"]
    dataset_source = str(summary["dataset_source"]).lower()
    dataframe = desi_df if dataset_source == "desi" else sdss_df
    parquet_path = dataframe.attrs.get("parquet_path")
    matches = (
        dataframe[dataframe["wiki_entity_id"] == object_key]
        if "wiki_entity_id" in dataframe.columns
        else pd.DataFrame()
    )

    evidence_quotes = []
    seen_quote_ids = set()
    for _, row in matches.iterrows():
        arxiv_id = str(row.get("arxiv_id", "Unknown"))
        evidence = row.get("evidence_quotes", {})
        if not isinstance(evidence, dict):
            continue
        quote_ids = evidence.get("quote_id", [])
        quotes = evidence.get("quote", [])
        if hasattr(quote_ids, "tolist"):
            quote_ids = quote_ids.tolist()
        if hasattr(quotes, "tolist"):
            quotes = quotes.tolist()
        for quote_id, quote in zip(quote_ids, quotes):
            quote_id = str(quote_id)
            if quote_id not in seen_quote_ids:
                seen_quote_ids.add(quote_id)
                evidence_quotes.append(
                    {
                        "quote_id": quote_id,
                        "arxiv_id": arxiv_id,
                        "quote": str(quote),
                    }
                )

    observations = []
    if not matches.empty:
        for object_id, group in matches.groupby("object_id", sort=False):
            first_row = group.iloc[0]
            spectrum = (
                fetch_spectrum_dict(parquet_path, object_id)
                if parquet_path
                else first_row.get("spectrum", {})
            )
            z_value = first_row.get("Z")
            z_value = (
                float(z_value) if z_value is not None and pd.notna(z_value) else None
            )
            error_column = "ZERR" if dataset_source == "desi" else "Z_ERR"
            z_error = first_row.get(error_column)
            z_error = (
                float(z_error) if z_error is not None and pd.notna(z_error) else None
            )
            observations.append(
                {
                    "object_id": str(object_id),
                    "flux": np.asarray(spectrum.get("flux", []))
                    if isinstance(spectrum, dict)
                    else np.asarray([]),
                    "lambda": np.asarray(spectrum.get("lambda", []))
                    if isinstance(spectrum, dict)
                    else np.asarray([]),
                    "ivar": np.asarray(spectrum.get("ivar", []))
                    if isinstance(spectrum, dict)
                    else np.asarray([]),
                    "mask": np.asarray(spectrum.get("mask", []))
                    if isinstance(spectrum, dict)
                    else np.asarray([]),
                    "z": z_value,
                    "z_err": z_error,
                }
            )

    object_name = None
    if "name" in matches.columns and not matches["name"].dropna().empty:
        names = [
            str(name).strip()
            for name in matches["name"].dropna()
            if str(name).strip() and str(name).strip().lower() != "nan"
        ]
        object_name = names[0] if names else None

    return {
        "index": index,
        "object_key": object_key,
        "object_name": object_name,
        "dataset_source": dataset_source,
        "ra": summary.get("ra"),
        "dec": summary.get("dec"),
        "evidence_quotes": evidence_quotes,
        "evidence_links": {},
        "observations": observations,
        "lightcurve": [],
        "captions": _format_captions(summary["captions"]),
        "modality": "spectra",
    }
