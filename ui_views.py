import streamlit as st

from caption_annotator import render_caption_annotator
from plotting import create_lightcurve_figure, create_spectrum_figure

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
    key_prefix: str = "",
):
    """Render the branch's bordered object navigation and progress bar."""
    with st.container(border=True):
        previous_col, progress_col, next_col = st.columns(
            [1, 2, 1], vertical_alignment="center"
        )
        with previous_col:
            st.button(
                "Previous object",
                icon=":material/arrow_back:",
                disabled=current_idx <= 0,
                key=f"{key_prefix}_nav_prev_btn",
                on_click=on_prev,
            )
        with progress_col:
            st.markdown(
                "<div style='text-align:center;font-weight:600;'>"
                f"Object {current_idx + 1} of {total_objects}</div>",
                unsafe_allow_html=True,
            )
            st.progress((current_idx + 1) / max(total_objects, 1))
        with next_col:
            st.button(
                "Next object",
                icon=":material/arrow_forward:",
                disabled=current_idx >= total_objects - 1,
                type="secondary",
                key=f"{key_prefix}_nav_next_btn",
                on_click=on_next,
            )


def _render_reasoning(obj_data: dict, key_prefix: str):
    captions = obj_data.get("captions", [])
    if not captions:
        st.info("No captions available for this object.")
        return

    labels = [
        f"Candidate {chr(65 + index)} ({caption.get('model', 'Model')} / "
        f"{caption.get('strategy', 'N/A')})"
        for index, caption in enumerate(captions)
    ]
    selected = st.segmented_control(
        "Candidate reasoning selector",
        options=labels,
        default=labels[0],
        label_visibility="collapsed",
        key=f"{key_prefix}_reasoning_selector_{obj_data['index']}",
    )
    selected_index = labels.index(selected) if selected in labels else 0
    caption = captions[selected_index]
    thoughts = caption.get("thought_summaries", [])
    if not thoughts:
        st.info(f"No explicit reasoning summary provided for {labels[selected_index]}.")
        return

    st.caption(
        f"Reasoning for **Candidate {chr(65 + selected_index)}** "
        f"({caption.get('model', 'Model')}) • "
        f"Strategy: `{caption.get('strategy', 'N/A')}`"
    )
    for step_index, step in enumerate(thoughts, 1):
        st.markdown(f"- **Step {step_index}:** {step}")


def render_shared_evidence(
    obj_data: dict,
    current_obs_idx: int,
    on_prev_obs: callable,
    on_next_obs: callable,
    key_prefix: str = "",
):
    """Render spectral or lightcurve evidence in the existing two-column layout."""
    modality = obj_data.get("modality", "spectra")
    observations = obj_data.get("observations", [])
    total_observations = len(observations)
    active_index = (
        min(current_obs_idx, total_observations - 1) if total_observations else 0
    )
    current_observation = observations[active_index] if total_observations else {}
    quotes = obj_data.get("evidence_quotes", [])
    evidence_links = obj_data.get("evidence_links", {})

    plot_col, info_col = st.columns([1.15, 0.85], gap="medium")
    with plot_col, st.container(border=True):
        if modality == "lightcurves":
            figure = create_lightcurve_figure(
                obj_data.get("lightcurve", []), obj_data["object_key"]
            )
        else:
            figure = create_spectrum_figure(
                current_observation,
                obj_data["object_key"],
                obj_data["dataset_source"],
                obs_index=active_index,
                total_obs=total_observations,
            )
        st.plotly_chart(figure, width="stretch", config={"displaylogo": False})

        if modality == "spectra" and total_observations > 1:
            prev_col, status_col, next_col = st.columns(
                [1, 2, 1], vertical_alignment="center"
            )
            with prev_col:
                st.button(
                    "Prev obs",
                    icon=":material/arrow_back:",
                    disabled=current_obs_idx <= 0,
                    key=f"{key_prefix}_prev_obs_btn",
                    on_click=on_prev_obs,
                )
            with status_col:
                st.caption(
                    f"Observation {active_index + 1} of {total_observations} "
                    f"(ID: {current_observation.get('object_id', 'N/A')})"
                )
            with next_col:
                st.button(
                    "Next obs",
                    icon=":material/arrow_forward:",
                    disabled=current_obs_idx >= total_observations - 1,
                    key=f"{key_prefix}_next_obs_btn",
                    on_click=on_next_obs,
                )

    with info_col:
        with st.container(border=True):
            evidence_count = len(quotes) or len(evidence_links)
            metadata_tab, evidence_tab, reasoning_tab = st.tabs(
                [
                    "Target metadata",
                    f"Linked evidence ({evidence_count})",
                    "Model reasoning",
                ]
            )
            with metadata_tab:
                left, right = st.columns(2)
                with left:
                    st.caption("Object name")
                    st.markdown(f"**{obj_data.get('object_name') or 'N/A'}**")
                    st.caption("Object key")
                    st.code(obj_data["object_key"])
                    st.caption("Dataset source")
                    st.markdown(f"**{obj_data['dataset_source']}**")
                with right:
                    if modality == "lightcurves":
                        lightcurve = obj_data.get("lightcurve", [])
                        st.caption("Photometric observations")
                        st.markdown(f"**{len(lightcurve)}**")
                        st.caption("Filters")
                        filters = sorted({row["filter"] for row in lightcurve})
                        st.markdown(f"**{', '.join(filters) if filters else 'N/A'}**")
                    else:
                        z_value = current_observation.get("z")
                        z_error = current_observation.get("z_err")
                        z_text = "N/A"
                        if z_value is not None:
                            z_text = (
                                f"{z_value:.4f} ± {z_error:.4f}"
                                if z_error is not None
                                else f"{z_value:.4f}"
                            )
                        ra_value = obj_data.get("ra")
                        dec_value = obj_data.get("dec")
                        coordinates = (
                            f"{ra_value:.4f}°, {dec_value:.4f}°"
                            if isinstance(ra_value, float)
                            and isinstance(dec_value, float)
                            else "N/A"
                        )
                        st.caption("Redshift (z)")
                        st.markdown(f"**{z_text}**")
                        st.caption("Coordinates")
                        st.markdown(f"**{coordinates}**")

            with evidence_tab:
                if quotes:
                    for index, quote in enumerate(quotes, 1):
                        with st.container(border=True):
                            st.caption(
                                f"Quote #{index} • arXiv: "
                                f"[{quote['arxiv_id']}](https://arxiv.org/abs/{quote['arxiv_id']})"
                            )
                            st.markdown(f"*{quote['quote']}*")
                elif evidence_links:
                    for atel_id, url in evidence_links.items():
                        st.markdown(f"- [Astronomer's Telegram #{atel_id}]({url})")
                else:
                    st.info("No linked evidence is available for this object.")

            with reasoning_tab:
                _render_reasoning(obj_data, key_prefix)


def render_single_caption_eval(
    obj_data: dict, on_submit: callable, key_prefix: str = ""
):
    caption = obj_data["captions"][0]
    object_index = obj_data["index"]
    with st.container(border=True):
        st.caption(
            f"AI-Generated Caption • Model: **{caption.get('model', 'N/A')}** • "
            f"Strategy: `{caption.get('strategy', 'N/A')}` "
            f"(Source row #{caption['file_index']}) • "
            "*Select text with mouse to add span annotations*"
        )
        if caption.get("is_insufficient"):
            st.error(
                "Insufficient data for caption generation", icon=":material/warning:"
            )
        annotations = render_caption_annotator(
            caption_text=caption.get("caption", ""),
            key=f"{key_prefix}_annotator_single_{object_index}",
        )

    with st.container(border=True):
        rating_col, tags_col = st.columns([1.2, 1.8], gap="medium")
        with rating_col:
            st.caption("Rating")
            rating = st.segmented_control(
                "Rating",
                options=[
                    ":material/thumb_up: Good",
                    ":material/thumb_down: Needs work",
                ],
                label_visibility="collapsed",
                key=f"{key_prefix}_rating_single_{object_index}",
            )
        with tags_col:
            st.caption("Diagnostic tags (optional)")
            tags = st.pills(
                "Diagnostic tags",
                options=DIAGNOSTIC_TAGS,
                selection_mode="multi",
                label_visibility="collapsed",
                key=f"{key_prefix}_tags_single_{object_index}",
            )

        note_col, submit_col = st.columns(
            [2.5, 1], vertical_alignment="bottom", gap="medium"
        )
        with note_col:
            note = st.text_input(
                "Reviewer notes (optional)",
                placeholder="Optional feedback on accuracy or missing details...",
                key=f"{key_prefix}_note_single_{object_index}",
                label_visibility="collapsed",
            )
        with submit_col:
            if st.button(
                "Submit & next",
                type="primary",
                icon=":material/send:",
                key=f"{key_prefix}_submit_single_{object_index}",
                width="stretch",
            ):
                on_submit(
                    caption_file_index=caption["file_index"],
                    model=caption.get("model", ""),
                    strategy=caption.get("strategy", ""),
                    rating=(
                        "thumbs_up"
                        if rating and "Good" in rating
                        else "thumbs_down"
                        if rating
                        else None
                    ),
                    tags=tags or [],
                    span_annotations=annotations or [],
                    note=note,
                )


def _candidate_card(
    caption: dict, label: str, object_index: int, key_prefix: str
) -> dict:
    with st.container(border=True):
        st.caption(
            f"Candidate {label} • Model: **{caption.get('model', 'N/A')}** • "
            f"Strategy: `{caption.get('strategy', 'N/A')}`"
        )
        if caption.get("is_insufficient"):
            st.error("Insufficient data", icon=":material/warning:")
        annotations = render_caption_annotator(
            caption_text=caption.get("caption", ""),
            key=f"{key_prefix}_annotator_{label}_{object_index}",
        )
        st.divider()
        rating = st.segmented_control(
            f"Candidate {label} rating",
            options=[":material/thumb_up: Good", ":material/thumb_down: Flawed"],
            key=f"{key_prefix}_rating_{label}_{object_index}",
        )
        tags = st.pills(
            f"Candidate {label} tags",
            options=DIAGNOSTIC_TAGS,
            selection_mode="multi",
            key=f"{key_prefix}_tags_{label}_{object_index}",
        )
    return {
        "rating": (
            "thumbs_up"
            if rating and "Good" in rating
            else "thumbs_down"
            if rating
            else None
        ),
        "tags": tags or [],
        "span_annotations": annotations or [],
    }


ABC_PAIRS = (
    ("a_vs_b", "A", "B"),
    ("b_vs_c", "B", "C"),
    ("c_vs_a", "C", "A"),
)


def build_pairwise_matrix(captions: list[dict], comparisons: dict) -> list[dict]:
    """Build a row-oriented Better/Worse/Tie matrix for display and testing."""
    relations = {
        row: {column: "—" if row == column else "Pending" for column in "ABC"}
        for row in "ABC"
    }
    for key, left, right in ABC_PAIRS:
        outcome = comparisons.get(key)
        if outcome == "Tie":
            relations[left][right] = "Tie"
            relations[right][left] = "Tie"
        elif outcome == left:
            relations[left][right] = "Better"
            relations[right][left] = "Worse"
        elif outcome == right:
            relations[left][right] = "Worse"
            relations[right][left] = "Better"

    rows = []
    for label, caption in zip("ABC", captions):
        model = caption.get("model", "N/A")
        strategy = caption.get("strategy", "N/A")
        rows.append(
            {
                "Candidate": label,
                "Model / strategy": f"{model} / {strategy}",
                **relations[label],
            }
        )
    return rows


def render_abc_comparison_eval(
    obj_data: dict, on_submit: callable, key_prefix: str = ""
):
    """Render three candidates, three head-to-head outcomes, and a final matrix."""
    captions = obj_data["captions"]
    object_index = obj_data["index"]
    evaluations = {}
    columns = st.columns(3, gap="medium")
    for column, label, caption in zip(columns, ("A", "B", "C"), captions):
        with column:
            evaluations[label] = _candidate_card(
                caption, label, object_index, key_prefix
            )

    with st.container(border=True):
        st.caption("Required head-to-head comparisons")
        pair_columns = st.columns(3, gap="medium")
        comparisons = {}
        for column, (key, left, right) in zip(pair_columns, ABC_PAIRS):
            with column:
                comparisons[key] = st.segmented_control(
                    f"{left} vs {right} head-to-head",
                    options=[left, "Tie", right],
                    key=f"{key_prefix}_{key}_{object_index}",
                )

        st.caption("Final head-to-head matrix")
        st.table(build_pairwise_matrix(captions, comparisons))
        st.caption(
            "Each cell describes the row candidate relative to the column candidate."
        )

        note_col, submit_col = st.columns(
            [2.5, 1], vertical_alignment="bottom", gap="medium"
        )
        with note_col:
            note = st.text_input(
                "Comparative notes (optional)",
                placeholder="Optional notes on why candidates were preferred...",
                key=f"{key_prefix}_abc_note_{object_index}",
                label_visibility="collapsed",
            )
        with submit_col:
            clicked = st.button(
                "Submit & next",
                type="primary",
                icon=":material/send:",
                key=f"{key_prefix}_abc_submit_{object_index}",
                width="stretch",
                disabled=any(value is None for value in comparisons.values()),
            )

        if clicked:
            missing = [
                label
                for key, label in (
                    ("a_vs_b", "A vs B"),
                    ("b_vs_c", "B vs C"),
                    ("c_vs_a", "C vs A"),
                )
                if comparisons[key] is None
            ]
            if missing:
                st.error("Select an outcome for " + ", ".join(missing) + ".")
            else:
                on_submit(
                    candidate_file_indices={
                        label: caption["file_index"]
                        for label, caption in zip(("A", "B", "C"), captions)
                    },
                    candidates_info={
                        label: {
                            "model": caption.get("model", ""),
                            "strategy": caption.get("strategy", ""),
                            "caption": caption.get("caption", ""),
                        }
                        for label, caption in zip(("A", "B", "C"), captions)
                    },
                    comparisons=comparisons,
                    candidates_eval=evaluations,
                    note=note,
                )


def render_comparison_eval(obj_data: dict, on_submit: callable, key_prefix: str = ""):
    """Retain the branch's two-candidate evaluator for legacy datasets."""
    captions = obj_data["captions"][:2]
    object_index = obj_data["index"]
    evaluations = {}
    columns = st.columns(2, gap="medium")
    for column, label, caption in zip(columns, ("A", "B"), captions):
        with column:
            evaluations[label] = _candidate_card(
                caption, label, object_index, key_prefix
            )

    with st.container(border=True):
        vote = st.segmented_control(
            "Head-to-head winner",
            options=["A", "Tie", "B", "Both poor"],
            key=f"{key_prefix}_legacy_vote_{object_index}",
        )
        note_col, submit_col = st.columns(
            [2.5, 1], vertical_alignment="bottom", gap="medium"
        )
        with note_col:
            note = st.text_input(
                "Comparative notes (optional)",
                key=f"{key_prefix}_legacy_note_{object_index}",
                label_visibility="collapsed",
            )
        with submit_col:
            if st.button(
                "Submit & next",
                type="primary",
                icon=":material/send:",
                key=f"{key_prefix}_legacy_submit_{object_index}",
                width="stretch",
            ):
                on_submit(
                    candidate_file_indices={
                        label: caption["file_index"]
                        for label, caption in zip(("A", "B"), captions)
                    },
                    candidates_info={
                        label: {
                            "model": caption.get("model", ""),
                            "strategy": caption.get("strategy", ""),
                        }
                        for label, caption in zip(("A", "B"), captions)
                    },
                    vote=vote,
                    candidates_eval=evaluations,
                    note=note,
                )
