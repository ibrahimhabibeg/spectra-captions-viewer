import os
import streamlit as st

import config
from data_loader import get_object_data, load_captions, load_parquet
from feedback import submit_feedback
from plotting import plot_spectrum

# Page configuration
st.set_page_config(
    page_title="Astronomical Spectra & AI Caption Evaluator",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Load datasets (cached with @st.cache_data inside data_loader)
captions = load_captions(config.CAPTIONS_JSONL_PATH)
desi_df = load_parquet(config.DESI_PARQUET_PATH)
sdss_df = load_parquet(config.SDSS_PARQUET_PATH)
total_captions = len(captions)

# Session state initialization
if "caption_idx" not in st.session_state:
    st.session_state.caption_idx = 0
if "obs_idx" not in st.session_state:
    st.session_state.obs_idx = 0

# App Header
st.title("Astronomical Spectra & AI Caption Evaluator")
st.caption(
    "Explore AI-generated captions for SDSS & DESI spectra alongside evidence quotes and interactive spectral observations."
)

# Top Navigation Toolbar (Symmetric: Previous | Caption X of N | Next)
with st.container(border=True):
    col1, col2, col3 = st.columns([1, 2, 1], vertical_alignment="center")
    with col1:
        if st.button(
            "Previous",
            icon=":material/arrow_back:",
            disabled=(st.session_state.caption_idx <= 0),
            key="prev_btn",
        ):
            st.session_state.caption_idx = max(0, st.session_state.caption_idx - 1)
            st.session_state.obs_idx = 0
            st.rerun()

    with col2:
        st.markdown(
            f"<h4 style='text-align: center; margin: 0; color: #F8FAFC;'>"
            f"Caption {st.session_state.caption_idx + 1} of {total_captions}</h4>",
            unsafe_allow_html=True,
        )

    with col3:
        if st.button(
            "Next",
            icon=":material/arrow_forward:",
            disabled=(st.session_state.caption_idx >= total_captions - 1),
            type="primary",
            key="next_btn",
        ):
            st.session_state.caption_idx = min(
                total_captions - 1, st.session_state.caption_idx + 1
            )
            st.session_state.obs_idx = 0
            st.rerun()

# Fetch object data for current index
obj_data = get_object_data(captions, desi_df, sdss_df, st.session_state.caption_idx)
observations = obj_data["observations"]
total_obs = len(observations)
current_obs = observations[min(st.session_state.obs_idx, total_obs - 1)] if total_obs > 0 else {}

# 1. AI-Generated Caption Card
st.subheader("AI-Generated Caption")
with st.container(border=True):
    if obj_data["is_insufficient"]:
        st.error(
            "INSUFFICIENT SPECTRAL DATA FOR CAPTION GENERATION",
            icon=":material/warning:",
        )
    st.markdown(obj_data["caption"])

# 2. Observed Spectrum Plot Card
st.subheader("Observed Spectrum Plot")
with st.container(border=True):
    if total_obs > 0:
        active_obs_idx = min(st.session_state.obs_idx, total_obs - 1)
        fig = plot_spectrum(
            current_obs,
            obj_data["object_key"],
            obj_data["dataset_source"],
            obs_index=active_obs_idx,
            total_obs=total_obs,
        )
        st.pyplot(fig, width="stretch")

        if total_obs > 1:
            ocol1, ocol2, ocol3 = st.columns([1, 2, 1], vertical_alignment="center")
            with ocol1:
                if st.button(
                    "Prev observation",
                    icon=":material/arrow_back:",
                    disabled=(st.session_state.obs_idx <= 0),
                    key="prev_obs_btn",
                ):
                    st.session_state.obs_idx = max(0, st.session_state.obs_idx - 1)
                    st.rerun()

            with ocol2:
                st.markdown(
                    f"<div style='text-align: center; font-weight: 600; color: #F8FAFC;'>"
                    f"Observation {active_obs_idx + 1} of {total_obs}<br>"
                    f"<small>Object ID: <code>{current_obs.get('object_id', 'N/A')}</code></small></div>",
                    unsafe_allow_html=True,
                )

            with ocol3:
                if st.button(
                    "Next observation",
                    icon=":material/arrow_forward:",
                    disabled=(st.session_state.obs_idx >= total_obs - 1),
                    key="next_obs_btn",
                ):
                    st.session_state.obs_idx = min(
                        total_obs - 1, st.session_state.obs_idx + 1
                    )
                    st.rerun()
    else:
        fig = plot_spectrum({}, obj_data["object_key"], obj_data["dataset_source"])
        st.pyplot(fig, width="stretch")

# 3. Metadata Section
st.subheader("Metadata")
source_bg = "#3B82F6" if obj_data["dataset_source"] == "desi" else "#8B5CF6"

z_str = "N/A"
if total_obs > 0 and current_obs.get("z") is not None:
    z_val = current_obs["z"]
    z_err = current_obs.get("z_err")
    z_str = f"{z_val:.4f} ± {z_err:.4f}" if z_err is not None else f"{z_val:.4f}"

ra_val = obj_data.get("ra", "N/A")
dec_val = obj_data.get("dec", "N/A")
coords_str = (
    f"{ra_val:.4f}°, {dec_val:.4f}°"
    if isinstance(ra_val, float) and isinstance(dec_val, float)
    else "N/A"
)

metadata_html = f"""
<div style="background-color: #1E293B; padding: 18px 20px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 16px;">
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px;">
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">OBJECT KEY</div>
            <div style="color: #F8FAFC; font-size: 1.05em; font-weight: 600; word-break: break-all;">{obj_data['object_key']}</div>
        </div>
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">DATASET SOURCE</div>
            <div><span style="background-color: {source_bg}; color: #FFFFFF; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 0.85em;">{obj_data['dataset_source'].upper()}</span></div>
        </div>
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">MODEL</div>
            <div style="color: #F8FAFC; font-size: 1.05em; font-weight: 600; word-break: break-all;">{obj_data.get('model', 'N/A')}</div>
        </div>
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">STRATEGY</div>
            <div style="color: #F8FAFC; font-size: 1.05em; font-weight: 600; word-break: break-all;">{obj_data.get('strategy', 'N/A')}</div>
        </div>
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">REDSHIFT (z)</div>
            <div style="color: #F8FAFC; font-size: 1.05em; font-weight: 600;">{z_str}</div>
        </div>
        <div>
            <div style="color: #94A3B8; font-size: 0.78em; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 4px;">COORDINATES</div>
            <div style="color: #F8FAFC; font-size: 1.05em; font-weight: 600;">{coords_str}</div>
        </div>
    </div>
</div>
"""

st.html(metadata_html)

# 4. Expanders: Model Reasoning & Linked Evidence Quotes
with st.expander("Model reasoning (Chain of Thought)", expanded=False):
    thought_summaries = obj_data.get("thought_summaries", [])
    if thought_summaries:
        for idx, summary in enumerate(thought_summaries, 1):
            st.markdown(f"**Step {idx}:** {summary}")
    else:
        st.info("No explicit chain of thought reasoning provided for this caption.")

with st.expander("Linked evidence quotes", expanded=True):
    quotes = obj_data.get("evidence_quotes", [])
    if quotes:
        for idx, q in enumerate(quotes, 1):
            with st.container(border=True):
                st.markdown(
                    f"**Quote #{idx}** | arXiv ID: [{q['arxiv_id']}](https://arxiv.org/abs/{q['arxiv_id']}) | ID: `{q['quote_id']}`"
                )
                st.markdown(f"*{q['quote']}*")
    else:
        st.info("No evidence quotes found for this entity.")

# 5. User Feedback Panel
st.subheader("Expert Feedback")
with st.container(border=True):
    fcol1, fcol2 = st.columns([2, 3])
    with fcol1:
        st.markdown("**Rating**")
        selected_rating = st.segmented_control(
            "Rating",
            options=[":material/thumb_up: Good Caption", ":material/thumb_down: Needs Work"],
            label_visibility="collapsed",
            key=f"rating_{st.session_state.caption_idx}",
        )

    with fcol2:
        note_input = st.text_area(
            "Reviewer Notes / Feedback",
            placeholder="Optional: Add feedback on accuracy, missing details, hallucinations, etc...",
            key=f"note_{st.session_state.caption_idx}",
            height=100,
        )

        if st.button("Submit feedback", type="primary", icon=":material/send:", key="submit_feedback_btn"):
            rating_key = (
                "thumbs_up"
                if selected_rating and "Good Caption" in selected_rating
                else ("thumbs_down" if selected_rating and "Needs Work" in selected_rating else None)
            )
            if not rating_key and not note_input.strip():
                st.warning("Please select a rating or provide a note before submitting.")
            else:
                success, msg = submit_feedback(
                    object_key=obj_data["object_key"],
                    dataset_source=obj_data["dataset_source"],
                    rating=rating_key,
                    note=note_input,
                    model=obj_data.get("model"),
                    strategy=obj_data.get("strategy"),
                )
                if success:
                    st.toast("Feedback submitted successfully!", icon="✅")
                    st.success(msg)
                else:
                    st.error(f"Error submitting feedback: {msg}")
