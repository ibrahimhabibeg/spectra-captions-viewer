import streamlit as st

import config
from data_loader import get_object_eval_data, load_and_group_objects, load_parquet
from feedback import submit_comparison_feedback, submit_single_feedback
from ui_views import (
    render_comparison_eval,
    render_nav_header,
    render_shared_evidence,
    render_single_caption_eval,
)

# Page configuration
st.set_page_config(
    page_title="Astronomical Spectra & AI Caption Evaluator",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load datasets (cached with @st.cache_data inside data_loader)
objects = load_and_group_objects(config.CAPTIONS_JSONL_PATH)
desi_df = load_parquet(config.DESI_PARQUET_PATH)
sdss_df = load_parquet(config.SDSS_PARQUET_PATH)
total_objects = len(objects)

# Session state initialization
if "object_idx" not in st.session_state:
    st.session_state.object_idx = 0
if "obs_idx" not in st.session_state:
    st.session_state.obs_idx = 0

# App Header
st.title("Astronomical Spectra & AI Caption Evaluator")
st.caption(
    "Evaluate AI-generated captions for SDSS & DESI spectra alongside evidence quotes and interactive spectral observations."
)

if total_objects == 0:
    st.warning("No astronomical objects found in the dataset.")
    st.stop()


# Navigation Callbacks
def handle_prev_object():
    st.session_state.object_idx = max(0, st.session_state.object_idx - 1)
    st.session_state.obs_idx = 0


def handle_next_object():
    st.session_state.object_idx = min(total_objects - 1, st.session_state.object_idx + 1)
    st.session_state.obs_idx = 0


def handle_prev_obs():
    st.session_state.obs_idx = max(0, st.session_state.obs_idx - 1)


def handle_next_obs():
    st.session_state.obs_idx = st.session_state.obs_idx + 1


# Fetch object data for current index
obj_data = get_object_eval_data(
    objects, desi_df, sdss_df, st.session_state.object_idx
)

# 1. Top Shared Evidence Section (Plotly Spectrum + Tabs)
render_shared_evidence(
    obj_data=obj_data,
    current_obs_idx=st.session_state.obs_idx,
    on_prev_obs=handle_prev_obs,
    on_next_obs=handle_next_obs,
)


# Feedback Submission Handlers with "Submit & Advance"
def on_single_submit(
    caption_file_index: int,
    model: str,
    strategy: str,
    rating: str | None,
    tags: list[str],
    span_annotations: list[dict],
    note: str,
):
    success, msg = submit_single_feedback(
        object_key=obj_data["object_key"],
        dataset_source=obj_data["dataset_source"],
        caption_file_index=caption_file_index,
        model=model,
        strategy=strategy,
        rating=rating,
        tags=tags,
        span_annotations=span_annotations,
        note=note,
    )
    if success:
        st.toast("Advanced to next object", icon="✅")
        # Auto-advance to next object
        if st.session_state.object_idx < total_objects - 1:
            st.session_state.object_idx += 1
            st.session_state.obs_idx = 0
        st.rerun()
    else:
        st.error(f"Submission failed: {msg}")


def on_comparison_submit(
    candidate_file_indices: dict[str, int],
    candidates_info: dict[str, dict],
    vote: str | None,
    candidates_eval: dict[str, dict],
    note: str,
):
    success, msg = submit_comparison_feedback(
        object_key=obj_data["object_key"],
        dataset_source=obj_data["dataset_source"],
        candidate_file_indices=candidate_file_indices,
        candidates_info=candidates_info,
        vote=vote,
        candidates_eval=candidates_eval,
        note=note,
    )
    if success:
        st.toast("Advanced to next object", icon="✅")
        # Auto-advance to next object
        if st.session_state.object_idx < total_objects - 1:
            st.session_state.object_idx += 1
            st.session_state.obs_idx = 0
        st.rerun()
    else:
        st.error(f"Submission failed: {msg}")


# 2. Bottom Evaluation Section (Single vs Multi-Caption Routing)
captions = obj_data.get("captions", [])
if len(captions) == 1:
    render_single_caption_eval(obj_data, on_submit=on_single_submit)
elif len(captions) > 1:
    render_comparison_eval(obj_data, on_submit=on_comparison_submit)
else:
    st.info("No captions available for this object.")

# 3. Bottom Navigation Toolbar
render_nav_header(
    current_idx=st.session_state.object_idx,
    total_objects=total_objects,
    on_prev=handle_prev_object,
    on_next=handle_next_object,
)
