import streamlit as st
from caption_annotator import render_caption_annotator
from plotting import create_spectrum_figure

# Standard diagnostic tags for single and comparative evaluation
DIAGNOSTIC_TAGS = [
    "Accurate lines",
    "Correct class",
    "Hallucinated line",
    "Redshift mismatch",
    "Literature conflict",
    "Missing key feature",
]


def render_nav_header(
    current_idx: int,
    total_objects: int,
    on_prev: callable,
    on_next: callable,
):
    """Renders the top navigation toolbar with object counter and progress indicator."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 2, 1], vertical_alignment="center")
        with col1:
            st.button(
                "Previous object",
                icon=":material/arrow_back:",
                disabled=(current_idx <= 0),
                key="nav_prev_btn",
                on_click=on_prev,
            )

        with col2:
            progress_ratio = (current_idx + 1) / max(total_objects, 1)
            st.markdown(
                f"<div style='text-align: center; font-weight: 600;'>"
                f"Object {current_idx + 1} of {total_objects}</div>",
                unsafe_allow_html=True,
            )
            st.progress(progress_ratio)

        with col3:
            st.button(
                "Next object",
                icon=":material/arrow_forward:",
                disabled=(current_idx >= total_objects - 1),
                type="secondary",
                key="nav_next_btn",
                on_click=on_next,
            )


def render_shared_evidence(
    obj_data: dict,
    current_obs_idx: int,
    on_prev_obs: callable,
    on_next_obs: callable,
):
    """
    Renders Top Section (Option B):
    Left: Interactive Plotly Spectrum plot.
    Right: Compact Tabbed Evidence & Target Information.
    """
    observations = obj_data.get("observations", [])
    total_obs = len(observations)
    current_obs = observations[min(current_obs_idx, total_obs - 1)] if total_obs > 0 else {}
    quotes = obj_data.get("evidence_quotes", [])

    col_plot, col_info = st.columns([1.15, 0.85], gap="medium")

    # 1. Left: Interactive Spectral Observation
    with col_plot:
        with st.container(border=True):
            active_obs_idx = min(current_obs_idx, total_obs - 1) if total_obs > 0 else 0
            fig = create_spectrum_figure(
                current_obs,
                obj_data["object_key"],
                obj_data["dataset_source"],
                obs_index=active_obs_idx,
                total_obs=total_obs,
            )
            st.plotly_chart(fig, width="stretch", config={"displaylogo": False})

            # Observation pager for multi-observation targets
            if total_obs > 1:
                ocol1, ocol2, ocol3 = st.columns([1, 2, 1], vertical_alignment="center")
                with ocol1:
                    st.button(
                        "Prev obs",
                        icon=":material/arrow_back:",
                        disabled=(current_obs_idx <= 0),
                        key="prev_obs_btn",
                        on_click=on_prev_obs,
                    )
                with ocol2:
                    st.caption(
                        f"Observation {active_obs_idx + 1} of {total_obs} (ID: {current_obs.get('object_id', 'N/A')})"
                    )
                with ocol3:
                    st.button(
                        "Next obs",
                        icon=":material/arrow_forward:",
                        disabled=(current_obs_idx >= total_obs - 1),
                        key="next_obs_btn",
                        on_click=on_next_obs,
                    )

    # 2. Right: Evidence Tabs (Metadata, Literature Quotes, Model Reasoning)
    with col_info:
        with st.container(border=True):
            tab_meta, tab_quotes, tab_reasoning = st.tabs([
                "Target metadata",
                f"Literature quotes ({len(quotes)})",
                "Model reasoning",
            ])

            with tab_meta:
                z_val = current_obs.get("z")
                z_err = current_obs.get("z_err")
                z_str = "N/A"
                if z_val is not None:
                    z_str = f"{z_val:.4f} ± {z_err:.4f}" if z_err is not None else f"{z_val:.4f}"

                ra_val = obj_data.get("ra", "N/A")
                dec_val = obj_data.get("dec", "N/A")
                coords_str = (
                    f"{ra_val:.4f}°, {dec_val:.4f}°"
                    if isinstance(ra_val, float) and isinstance(dec_val, float)
                    else "N/A"
                )

                mcol1, mcol2 = st.columns(2)
                with mcol1:
                    st.caption("Object key")
                    st.code(obj_data["object_key"])
                    st.caption("Dataset source")
                    st.markdown(f"**{obj_data['dataset_source'].upper()}**")
                with mcol2:
                    st.caption("Redshift (z)")
                    st.markdown(f"**{z_str}**")
                    st.caption("Coordinates")
                    st.markdown(f"**{coords_str}**")

            with tab_quotes:
                if quotes:
                    for idx, q in enumerate(quotes, 1):
                        with st.container(border=True):
                            st.caption(
                                f"Quote #{idx} • arXiv: [{q['arxiv_id']}](https://arxiv.org/abs/{q['arxiv_id']})"
                            )
                            st.markdown(f"*{q['quote']}*")
                else:
                    st.info("No crossmatched literature quotes found for this object.")

            with tab_reasoning:
                captions = obj_data.get("captions", [])
                has_reasoning = False
                for c_idx, c in enumerate(captions, 1):
                    thought_summaries = c.get("thought_summaries", [])
                    if thought_summaries:
                        has_reasoning = True
                        label = f"Caption {c_idx} ({c.get('model', 'Model')})" if len(captions) > 1 else "Reasoning steps"
                        st.markdown(f"**{label}:**")
                        for s_idx, step in enumerate(thought_summaries, 1):
                            st.markdown(f"- **Step {s_idx}:** {step}")
                if not has_reasoning:
                    st.info("No explicit chain of thought reasoning provided.")


def render_single_caption_eval(obj_data: dict, on_submit: callable):
    """
    Renders evaluation interface for single-caption objects.
    Features: Interactive text span highlighter + inline evaluation bar with Submit & Next.
    """
    caption_obj = obj_data["captions"][0]
    obj_idx = obj_data["index"]

    # 1. Interactive Caption Card with Google Docs-style Highlighting
    with st.container(border=True):
        st.caption(
            f"AI-Generated Caption • Model: **{caption_obj.get('model', 'N/A')}** • "
            f"Strategy: `{caption_obj.get('strategy', 'N/A')}` "
            f"(Source row #{caption_obj['file_index']}) • *Select text with mouse to add span annotations*"
        )
        if caption_obj.get("is_insufficient"):
            st.error("Insufficient spectral data for caption generation", icon=":material/warning:")

        # Bi-directional CCv2 text annotator
        annotations = render_caption_annotator(
            caption_text=caption_obj.get("caption", ""),
            key=f"annotator_single_{obj_idx}",
        )

    # 2. Evaluation Action Bar
    with st.container(border=True):
        eval_col1, eval_col2 = st.columns([1.2, 1.8], gap="medium")

        with eval_col1:
            st.caption("Rating")
            selected_rating = st.segmented_control(
                "Rating",
                options=[":material/thumb_up: Good", ":material/thumb_down: Needs work"],
                label_visibility="collapsed",
                key=f"rating_single_{obj_idx}",
            )

        with eval_col2:
            st.caption("Diagnostic tags (optional)")
            selected_tags = st.pills(
                "Diagnostic tags",
                options=DIAGNOSTIC_TAGS,
                selection_mode="multi",
                label_visibility="collapsed",
                key=f"tags_single_{obj_idx}",
            )

        # Notes and Submit Button Row
        note_col, submit_col = st.columns([2.5, 1], vertical_alignment="bottom", gap="medium")
        with note_col:
            note_input = st.text_input(
                "Reviewer notes (optional)",
                placeholder="Optional feedback on accuracy, hallucinations, missing details...",
                key=f"note_single_{obj_idx}",
                label_visibility="collapsed",
            )

        with submit_col:
            if st.button(
                "Submit & next",
                type="primary",
                icon=":material/send:",
                key=f"submit_single_btn_{obj_idx}",
                width="stretch",
            ):
                rating_val = None
                if selected_rating:
                    rating_val = "thumbs_up" if "Good" in selected_rating else "thumbs_down"

                on_submit(
                    caption_file_index=caption_obj["file_index"],
                    model=caption_obj.get("model", ""),
                    strategy=caption_obj.get("strategy", ""),
                    rating=rating_val,
                    tags=selected_tags or [],
                    span_annotations=annotations or [],
                    note=note_input,
                )


def render_comparison_eval(obj_data: dict, on_submit: callable):
    """
    Renders comparative evaluation interface for 2+ candidate captions.
    Features: Side-by-side candidate cards with span highlighters + independent ratings/tags + Head-to-Head vote.
    """
    captions = obj_data["captions"]
    cand_a = captions[0]
    cand_b = captions[1]
    obj_idx = obj_data["index"]

    # 1. Side-by-Side Candidate Cards
    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        with st.container(border=True):
            st.caption(
                f"Candidate A • **{cand_a.get('model', 'Model A')}** (Row #{cand_a['file_index']}) • *Select text to highlight*"
            )
            annotations_a = render_caption_annotator(
                caption_text=cand_a.get("caption", ""),
                key=f"annotator_comp_a_{obj_idx}",
            )

            st.divider()
            st.caption("Candidate A rating")
            rating_a = st.segmented_control(
                "Candidate A rating",
                options=[":material/thumb_up: Good", ":material/thumb_down: Flawed"],
                label_visibility="collapsed",
                key=f"rating_comp_a_{obj_idx}",
            )
            st.caption("Candidate A tags")
            tags_a = st.pills(
                "Candidate A tags",
                options=DIAGNOSTIC_TAGS,
                selection_mode="multi",
                label_visibility="collapsed",
                key=f"tags_comp_a_{obj_idx}",
            )

    with col_b:
        with st.container(border=True):
            st.caption(
                f"Candidate B • **{cand_b.get('model', 'Model B')}** (Row #{cand_b['file_index']}) • *Select text to highlight*"
            )
            annotations_b = render_caption_annotator(
                caption_text=cand_b.get("caption", ""),
                key=f"annotator_comp_b_{obj_idx}",
            )

            st.divider()
            st.caption("Candidate B rating")
            rating_b = st.segmented_control(
                "Candidate B rating",
                options=[":material/thumb_up: Good", ":material/thumb_down: Flawed"],
                label_visibility="collapsed",
                key=f"rating_comp_b_{obj_idx}",
            )
            st.caption("Candidate B tags")
            tags_b = st.pills(
                "Candidate B tags",
                options=DIAGNOSTIC_TAGS,
                selection_mode="multi",
                label_visibility="collapsed",
                key=f"tags_comp_b_{obj_idx}",
            )

    # 2. Head-to-Head Comparative Vote & Submission
    with st.container(border=True):
        st.caption("Head-to-head winner")
        vote_choice = st.segmented_control(
            "Comparative vote",
            options=[
                ":material/arrow_back: Candidate A is better",
                ":material/handshake: Both equal / tie",
                ":material/arrow_forward: Candidate B is better",
                ":material/thumb_down: Both poor",
            ],
            label_visibility="collapsed",
            key=f"vote_choice_{obj_idx}",
        )

        note_col, submit_col = st.columns([2.5, 1], vertical_alignment="bottom", gap="medium")
        with note_col:
            comp_note = st.text_input(
                "Comparative notes (optional)",
                placeholder="Optional notes on why one candidate was preferred over the other...",
                key=f"note_comp_{obj_idx}",
                label_visibility="collapsed",
            )

        with submit_col:
            if st.button(
                "Submit & next",
                type="primary",
                icon=":material/send:",
                key=f"submit_comp_btn_{obj_idx}",
                width="stretch",
            ):
                vote_val = None
                if vote_choice:
                    if "A is better" in vote_choice:
                        vote_val = "candidate_a"
                    elif "B is better" in vote_choice:
                        vote_val = "candidate_b"
                    elif "equal" in vote_choice or "tie" in vote_choice:
                        vote_val = "tie"
                    elif "Both poor" in vote_choice:
                        vote_val = "both_poor"

                rating_a_val = "thumbs_up" if rating_a and "Good" in rating_a else ("thumbs_down" if rating_a else None)
                rating_b_val = "thumbs_up" if rating_b and "Good" in rating_b else ("thumbs_down" if rating_b else None)

                on_submit(
                    candidate_file_indices={"A": cand_a["file_index"], "B": cand_b["file_index"]},
                    candidates_info={
                        "A": {"model": cand_a.get("model", ""), "strategy": cand_a.get("strategy", "")},
                        "B": {"model": cand_b.get("model", ""), "strategy": cand_b.get("strategy", "")},
                    },
                    vote=vote_val,
                    candidates_eval={
                        "A": {"rating": rating_a_val, "tags": tags_a or [], "span_annotations": annotations_a or []},
                        "B": {"rating": rating_b_val, "tags": tags_b or [], "span_annotations": annotations_b or []},
                    },
                    note=comp_note,
                )
