---
title: Astronomical Spectra & AI Caption Evaluator
emoji: 🌌
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
license: cc-by-4.0
---

# Astronomical Spectra & AI Caption Evaluator 🌌

An interactive Python GUI built with **Gradio** for astronomy experts to browse, evaluate, and provide feedback on AI-generated captions for astronomical objects from **SDSS** and **DESI** spectral catalogs.

## Features

- **Frictionless Navigation**: Navigate through captions with Previous/Next buttons or jump directly to any index.
- **Spectrum Visualization**: High-resolution Matplotlib plots of flux vs. observed wavelength with pixel mask filtering.
- **Multi-Observation Support**: Automatic grouping by `object_id` when an astronomical object has multiple spectral observations.
- **Evidence Quotes**: View all crossmatched literature quotes from arXiv papers linked to the object.
- **Model Reasoning**: Inspect chain-of-thought summaries when available.
- **Anonymous Feedback**: Submit rating (👍 / 👎) and free-text notes directly pushed to HuggingFace dataset `ibrahimhabibeg/spectra-captions-feedback-test`.

## Local Setup

1. **Environment & Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Application**:
   ```bash
   python app.py
   ```
   Open `http://localhost:7860` in your browser.

## Configuration

Set environment variables to customize data file locations or HF feedback dataset repo:

- `DESI_PARQUET_PATH`: Path or URL to DESI crossmatch parquet file (default: `data/crossmatch_desi_1.0arcsec.parquet`)
- `SDSS_PARQUET_PATH`: Path or URL to SDSS crossmatch parquet file (default: `data/crossmatch_sdss_1.0arcsec.parquet`)
- `CAPTIONS_JSONL_PATH`: Path or URL to captions JSONL file (default: `output/captions.jsonl`)
- `FEEDBACK_DATASET_REPO`: HF dataset repository ID (default: `ibrahimhabibeg/spectra-captions-feedback-test`)
- `HF_TOKEN`: HuggingFace access token with write permission for feedback dataset commits
