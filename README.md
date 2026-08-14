# Astronomical Spectra & AI Caption Evaluator

An interactive Python GUI built with **Streamlit** for astronomy experts to browse, evaluate, and provide feedback on AI-generated captions for astronomical objects from **SDSS** and **DESI** spectral catalogs.

## Features

- **Frictionless Navigation**: Navigate through captions with Previous/Next buttons.
- **Spectrum Visualization**: High-resolution Matplotlib plots of flux vs. observed wavelength with pixel mask filtering.
- **Multi-Observation Support**: Automatic grouping by `object_id` when an astronomical object has multiple spectral observations.
- **Evidence Quotes**: View all crossmatched literature quotes from arXiv papers linked to the object.
- **Model Reasoning**: Inspect chain-of-thought summaries when available.
- **Anonymous Feedback**: Submit rating (👍 Good Caption / 👎 Needs Work) and free-text notes directly pushed to HuggingFace dataset `ibrahimhabibeg/spectra-captions-feedback-test`.
- **Automatic HF Storage Bucket Pre-loading**: Automatically downloads data files from a Hugging Face Storage Bucket on first startup if local files are missing.

## Local Setup

1. **Environment & Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Application**:
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

## Configuration

Set environment variables to customize data directory locations or HF Storage Bucket settings:

- `DATA_DIR`: Directory containing `captions.jsonl`, `crossmatch_desi.parquet`, and `crossmatch_sdss.parquet` (default: `data`)
- `HF_BUCKET`: Hugging Face Storage Bucket ID containing data files (default: `ibrahimhabibeg/spectra-captions-bucket`)
- `FEEDBACK_DATASET_REPO`: HF feedback dataset repository ID (default: `ibrahimhabibeg/spectra-captions-feedback-test`)
- `HF_TOKEN`: HuggingFace access token with write/read permissions
