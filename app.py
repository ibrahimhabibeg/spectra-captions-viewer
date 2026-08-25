import streamlit as st

import config
from data_loader import get_object_eval_data, load_and_group_objects, load_parquet
from feedback import (
    submit_abc_feedback,
    submit_comparison_feedback,
    submit_single_feedback,
)
from ui_views import (
    render_abc_comparison_eval,
    render_comparison_eval,
    render_nav_header,
    render_shared_evidence,
    render_single_caption_eval,
)

st.set_page_config(
    page_title="Astronomy Caption Evaluator",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

spectra_objects = load_and_group_objects(
    config.SPECTRA_CAPTIONS_JSONL_PATH, modality="spectra"
)
lightcurve_objects = load_and_group_objects(
    config.LIGHTCURVE_CAPTIONS_JSONL_PATH, modality="lightcurves"
)
desi_df = load_parquet(config.DESI_PARQUET_PATH)
sdss_df = load_parquet(config.SDSS_PARQUET_PATH)


def render_modality(modality: str, objects: list[dict]):
    label = "spectra" if modality == "spectra" else "lightcurve"
    if not objects:
        st.warning(
            f"No {label} comparison data is available. "
            f"Add the configured {label} caption file to enable this tab."
        )
        return

    object_state = f"{modality}_object_idx"
    observation_state = f"{modality}_obs_idx"
    if object_state not in st.session_state:
        st.session_state[object_state] = 0
    if observation_state not in st.session_state:
        st.session_state[observation_state] = 0

    total_objects = len(objects)
    st.session_state[object_state] = min(
        st.session_state[object_state], total_objects - 1
    )

    def previous_object():
        st.session_state[object_state] = max(0, st.session_state[object_state] - 1)
        st.session_state[observation_state] = 0

    def next_object():
        st.session_state[object_state] = min(
            total_objects - 1, st.session_state[object_state] + 1
        )
        st.session_state[observation_state] = 0

    def previous_observation():
        st.session_state[observation_state] = max(
            0, st.session_state[observation_state] - 1
        )

    def next_observation():
        st.session_state[observation_state] += 1

    object_data = get_object_eval_data(
        objects,
        desi_df,
        sdss_df,
        st.session_state[object_state],
    )
    render_shared_evidence(
        obj_data=object_data,
        current_obs_idx=st.session_state[observation_state],
        on_prev_obs=previous_observation,
        on_next_obs=next_observation,
        key_prefix=modality,
    )

    def advance_after(success: bool, message: str):
        if not success:
            st.error(f"Submission failed: {message}")
            return
        st.toast("Feedback recorded; advanced to next object", icon="✅")
        if st.session_state[object_state] < total_objects - 1:
            st.session_state[object_state] += 1
            st.session_state[observation_state] = 0
        st.rerun()

    def on_single_submit(**feedback):
        success, message = submit_single_feedback(
            object_key=object_data["object_key"],
            dataset_source=object_data["dataset_source"],
            modality=modality,
            **feedback,
        )
        advance_after(success, message)

    def on_legacy_comparison_submit(**feedback):
        success, message = submit_comparison_feedback(
            object_key=object_data["object_key"],
            dataset_source=object_data["dataset_source"],
            modality=modality,
            **feedback,
        )
        advance_after(success, message)

    def on_abc_submit(**feedback):
        success, message = submit_abc_feedback(
            object_key=object_data["object_key"],
            dataset_source=object_data["dataset_source"],
            modality=modality,
            **feedback,
        )
        advance_after(success, message)

    captions = object_data.get("captions", [])
    if len(captions) == 3:
        render_abc_comparison_eval(
            object_data, on_submit=on_abc_submit, key_prefix=modality
        )
    elif len(captions) == 2:
        render_comparison_eval(
            object_data,
            on_submit=on_legacy_comparison_submit,
            key_prefix=modality,
        )
    elif len(captions) == 1:
        render_single_caption_eval(
            object_data, on_submit=on_single_submit, key_prefix=modality
        )
    else:
        st.info("No captions are available for this object.")

    render_nav_header(
        current_idx=st.session_state[object_state],
        total_objects=total_objects,
        on_prev=previous_object,
        on_next=next_object,
        key_prefix=modality,
    )


st.title("Astronomical Data & AI Caption Evaluator")
st.caption(
    "Evaluate A/B/C captions alongside the available spectra or lightcurve evidence."
)

spectra_tab, lightcurve_tab = st.tabs(["Spectra", "Lightcurves"])
with spectra_tab:
    render_modality("spectra", spectra_objects)
with lightcurve_tab:
    render_modality("lightcurves", lightcurve_objects)
