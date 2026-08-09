import os

import gradio as gr
import pandas as pd

import config
from data_loader import get_object_data, load_captions, load_parquet
from feedback import submit_feedback
from plotting import plot_spectrum

# Pre-load dataset at app launch
print("Loading captions and spectra datasets...")
CAPTIONS = load_captions(config.CAPTIONS_JSONL_PATH)
DESI_DF = load_parquet(config.DESI_PARQUET_PATH)
SDSS_DF = load_parquet(config.SDSS_PARQUET_PATH)
TOTAL_CAPTIONS = len(CAPTIONS)
print(
    f"Successfully loaded {TOTAL_CAPTIONS} captions, {len(DESI_DF)} DESI rows, and {len(SDSS_DF)} SDSS rows."
)


def update_ui(caption_index: int, obs_index: int):
    """
    Renders the UI elements for the given caption index and observation index.
    """
    # Ensure index bounds
    caption_index = max(0, min(caption_index, TOTAL_CAPTIONS - 1))

    # Fetch object data
    obj_data = get_object_data(CAPTIONS, DESI_DF, SDSS_DF, caption_index)

    observations = obj_data["observations"]
    total_obs = len(observations)
    obs_index = max(0, min(obs_index, total_obs - 1)) if total_obs > 0 else 0

    # 1. Navigation header counter text
    nav_text = f"<div class='nav-counter-text'>Caption {caption_index + 1} of {TOTAL_CAPTIONS}</div>"

    # 2. Spectrum Plot
    if total_obs > 0:
        current_obs = observations[obs_index]
        fig = plot_spectrum(
            current_obs,
            obj_data["object_key"],
            obj_data["dataset_source"],
            obs_index=obs_index,
            total_obs=total_obs,
        )
    else:
        fig = plot_spectrum({}, obj_data["object_key"], obj_data["dataset_source"])

    # 3. Observation navigation bar visibility & text
    obs_nav_visible = total_obs > 1
    obs_status = f"**Observation {obs_index + 1} of {total_obs}** (Object ID: `{current_obs['object_id']}`)" if total_obs > 1 else ""

    # 4. Caption Markdown display
    caption_text = obj_data["caption"]
    is_insufficient = obj_data["is_insufficient"]

    if is_insufficient:
        caption_md = (
            "<div style='background-color: #7F1D1D; border: 1px solid #EF4444; color: #FCA5A5; "
            "padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-weight: bold; font-size: 0.9em;'>"
            "INSUFFICIENT SPECTRAL DATA FOR CAPTION GENERATION"
            "</div>\n\n"
            f"{caption_text}"
        )
    else:
        caption_md = caption_text

    # 5. Metadata Bar HTML
    z_str = "N/A"
    if total_obs > 0 and current_obs.get("z") is not None:
        z_val = current_obs["z"]
        z_err = current_obs.get("z_err")
        z_str = f"{z_val:.4f} ± {z_err:.4f}" if z_err is not None else f"{z_val:.4f}"

    ra_val = obj_data.get("ra", "N/A")
    dec_val = obj_data.get("dec", "N/A")
    if isinstance(ra_val, float):
        ra_val = f"{ra_val:.5f}°"
    if isinstance(dec_val, float):
        dec_val = f"{dec_val:.5f}°"

    source_badge_color = "#3B82F6" if obj_data["dataset_source"] == "desi" else "#8B5CF6"

    metadata_html = f"""
    <div style="background-color: #1F2937; padding: 14px 18px; border-radius: 8px; border: 1px solid #374151;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
            <div><span style="color: #9CA3AF; font-size: 0.85em;">OBJECT KEY</span><br><strong style="color: #F9FAFB;">{obj_data['object_key']}</strong></div>
            <div><span style="color: #9CA3AF; font-size: 0.85em;">DATASET SOURCE</span><br><span style="background-color: {source_badge_color}; color: #FFF; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em;">{obj_data['dataset_source'].upper()}</span></div>
            <div><span style="color: #9CA3AF; font-size: 0.85em;">MODEL</span><br><strong style="color: #F9FAFB;">{obj_data.get('model', 'N/A')}</strong></div>
            <div><span style="color: #9CA3AF; font-size: 0.85em;">STRATEGY</span><br><strong style="color: #F9FAFB;">{obj_data.get('strategy', 'N/A')}</strong></div>
            <div><span style="color: #9CA3AF; font-size: 0.85em;">COORDINATES (RA, Dec)</span><br><strong style="color: #F9FAFB;">{ra_val}, {dec_val}</strong></div>
            <div><span style="color: #9CA3AF; font-size: 0.85em;">REDSHIFT (z ± σ_z)</span><br><strong style="color: #F9FAFB;">{z_str}</strong></div>
        </div>
    </div>
    """

    # 6. Model Reasoning (Chain of Thought)
    thoughts = obj_data.get("thought_summaries", [])
    if thoughts and len(thoughts) > 0:
        reasoning_html = "\n\n---\n\n".join([f"{t}" for t in thoughts])
        reasoning_visible = True
    else:
        reasoning_html = "*No model reasoning chain recorded for this object.*"
        reasoning_visible = False

    # 7. Evidence Quotes
    quotes = obj_data.get("evidence_quotes", [])
    if quotes:
        quotes_list_html = ""
        for idx, q in enumerate(quotes, 1):
            quotes_list_html += f"""
            <div style="background-color: #1F2937; border-left: 4px solid #3B82F6; padding: 10px 14px; margin-bottom: 10px; border-radius: 0 6px 6px 0;">
                <div style="font-size: 0.85em; color: #9CA3AF; margin-bottom: 4px;">
                    <strong>Quote #{idx}</strong> | arXiv ID: <a href="https://arxiv.org/abs/{q['arxiv_id']}" target="_blank" style="color: #60A5FA; text-decoration: underline;">{q['arxiv_id']}</a> | ID: <code>{q['quote_id']}</code>
                </div>
                <div style="font-size: 0.95em; color: #E5E7EB; font-style: italic;">"{q['quote']}"</div>
            </div>
            """
    else:
        quotes_list_html = "<div><em>No evidence quotes found for this entity.</em></div>"

    return (
        caption_index,
        obs_index,
        nav_text,
        fig,
        gr.update(visible=obs_nav_visible),
        obs_status,
        caption_md,
        metadata_html,
        gr.update(visible=reasoning_visible),
        reasoning_html,
        quotes_list_html,
    )


def handle_prev_caption(current_idx: int):
    new_idx = max(0, current_idx - 1)
    return update_ui(new_idx, 0) + (None, "")


def handle_next_caption(current_idx: int):
    new_idx = min(TOTAL_CAPTIONS - 1, current_idx + 1)
    return update_ui(new_idx, 0) + (None, "")


def handle_prev_obs(caption_idx: int, obs_idx: int):
    new_obs_idx = max(0, obs_idx - 1)
    res = update_ui(caption_idx, new_obs_idx)
    # Don't reset rating/note when switching spectra for the same caption
    return res + (gr.update(), gr.update())


def handle_next_obs(caption_idx: int, obs_idx: int):
    obj_data = get_object_data(CAPTIONS, DESI_DF, SDSS_DF, caption_idx)
    max_obs = len(obj_data["observations"]) - 1
    new_obs_idx = min(max_obs, obs_idx + 1)
    res = update_ui(caption_idx, new_obs_idx)
    return res + (gr.update(), gr.update())


def handle_feedback_submit(
    caption_idx: int, rating: str | None, note: str
):
    if caption_idx < 0 or caption_idx >= TOTAL_CAPTIONS:
        return "Invalid caption index."

    caption_record = CAPTIONS[caption_idx]
    success, msg = submit_feedback(
        object_key=caption_record["object_key"],
        dataset_source=caption_record["dataset_source"],
        model=caption_record.get("model", "N/A"),
        strategy=caption_record.get("strategy", "N/A"),
        rating=rating,
        note=note,
    )
    if success:
        return f"<div style='color: #34D399; font-weight: bold;'>{msg}</div>"
    else:
        return f"<div style='color: #F87171; font-weight: bold;'>{msg}</div>"


# Build Gradio UI with theme and layout
theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    font=[
        gr.themes.GoogleFont("Inter"),
        "system-ui",
        "-apple-system",
        "BlinkMacSystemFont",
        "Segoe UI",
        "Roboto",
        "Helvetica Neue",
        "Arial",
        "sans-serif",
    ],
    font_mono=[
        "ui-monospace",
        "SFMono-Regular",
        "Menlo",
        "Monaco",
        "Consolas",
        "monospace",
    ],
)

custom_css = """
body, input, button, textarea, select, .gradio-container, .gradio-container * {
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}

/* Constrain max width for clean, ergonomic centered layout */
.gradio-container {
    max-width: 1100px !important;
    margin: 0 auto !important;
    padding: 24px 16px !important;
}

/* Header text alignment */
.app-header {
    text-align: center;
    margin-bottom: 20px;
}

.app-header h1 {
    font-size: 1.8em !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
    color: #F9FAFB !important;
}

.app-header p {
    font-size: 0.95em !important;
    color: #9CA3AF !important;
}

/* Compact Navigation Bar */
.nav-toolbar {
    background-color: #1F2937 !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    margin-bottom: 10px !important;
    align-items: center !important;
}

.compact-btn button, button.compact-btn {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    font-size: 0.9em !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}

.nav-counter-text {
    text-align: center;
    font-size: 1.05em;
    font-weight: 600;
    color: #F9FAFB;
    line-height: 38px;
}

/* AI Caption Box styling */
.caption-box {
    background-color: #1F2937 !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 18px 22px !important;
    font-size: 1.08em !important;
    line-height: 1.7 !important;
    color: #F9FAFB !important;
}

.caption-box p {
    font-size: 1.08em !important;
    line-height: 1.7 !important;
    color: #F9FAFB !important;
    margin-bottom: 0 !important;
}
"""

LATEX_DELIMITERS = [
    {"left": "$$", "right": "$$", "display": True},
    {"left": "$", "right": "$", "display": False},
    {"left": "\\(", "right": "\\)", "display": False},
    {"left": "\\[", "right": "\\]", "display": True},
]

head_html = """
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" id="MathJax-script" async></script>
"""

with gr.Blocks(title="Spectra Captions Viewer") as app:
    # State tracking
    caption_idx_state = gr.State(0)
    obs_idx_state = gr.State(0)
    rating_state = gr.State(None)

    # Header
    gr.Markdown(
        """
        <div class="app-header">
            <h1>Astronomical Spectra & AI Caption Evaluator</h1>
            <p>Explore AI-generated captions for SDSS & DESI spectra alongside evidence quotes and interactive spectral observations.</p>
        </div>
        """
    )

    # Top Navigation Toolbar (Clean & Balanced: Previous | Caption X of 20 | Next)
    with gr.Row(variant="panel", elem_classes=["nav-toolbar"]):
        prev_btn = gr.Button("◄ Previous", variant="secondary", size="sm", scale=1, elem_classes=["compact-btn"])
        nav_counter = gr.Markdown(
            f"<div class='nav-counter-text'>Caption 1 of {TOTAL_CAPTIONS}</div>",
            scale=2,
        )
        next_btn = gr.Button("Next ►", variant="primary", size="sm", scale=1, elem_classes=["compact-btn"])

    # 1. AI-Generated Caption Card (Featured first)
    gr.Markdown("### AI-Generated Caption")
    caption_display = gr.Markdown(
        elem_classes=["caption-box"],
        latex_delimiters=LATEX_DELIMITERS,
    )

    # 2. Observed Spectrum Plot Card (Full width visual focus)
    gr.Markdown("### Observed Spectrum Plot")
    spectrum_plot = gr.Plot(show_label=False)

    # Observation Switcher (Hidden unless multi-observation)
    with gr.Row(visible=False) as obs_nav_row:
        prev_obs_btn = gr.Button("◄ Prev Observation", variant="secondary", size="sm", scale=1)
        obs_status_txt = gr.Markdown("", scale=2)
        next_obs_btn = gr.Button("Next Observation ►", variant="secondary", size="sm", scale=1)

    # 3. Metadata Section
    gr.Markdown("### Metadata")
    metadata_display = gr.HTML()

    # 4. Accordions: Model Reasoning & Evidence Quotes
    with gr.Accordion("Model Reasoning (Chain of Thought)", open=False, visible=True) as reasoning_accordion:
        reasoning_display = gr.Markdown(latex_delimiters=LATEX_DELIMITERS)

    with gr.Accordion("Linked Evidence Quotes", open=True):
        quotes_display = gr.HTML()

    # 5. User Feedback Panel
    gr.Markdown("### Expert Feedback")
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("**Rating:**")
            with gr.Row():
                thumbs_up_btn = gr.Button("👍 Good Caption", variant="secondary")
                thumbs_down_btn = gr.Button("👎 Needs Work", variant="secondary")
            rating_display = gr.Markdown("*No rating selected*")
        with gr.Column(scale=4):
            note_input = gr.Textbox(
                label="Reviewer Notes / Feedback",
                placeholder="Optional: Add feedback on accuracy, missing details, hallucinations, etc...",
                lines=2,
            )
            submit_btn = gr.Button("Submit Feedback", variant="primary")
            feedback_status = gr.HTML()

    # Event Handlers

    # 1. Navigation events
    nav_outputs = [
        caption_idx_state,
        obs_idx_state,
        nav_counter,
        spectrum_plot,
        obs_nav_row,
        obs_status_txt,
        caption_display,
        metadata_display,
        reasoning_accordion,
        reasoning_display,
        quotes_display,
        rating_state,
        note_input,
    ]

    prev_btn.click(
        fn=handle_prev_caption,
        inputs=[caption_idx_state],
        outputs=nav_outputs,
    )

    next_btn.click(
        fn=handle_next_caption,
        inputs=[caption_idx_state],
        outputs=nav_outputs,
    )

    # 2. Spectrum Observation switching
    obs_outputs = [
        caption_idx_state,
        obs_idx_state,
        nav_counter,
        spectrum_plot,
        obs_nav_row,
        obs_status_txt,
        caption_display,
        metadata_display,
        reasoning_accordion,
        reasoning_display,
        quotes_display,
        rating_state,
        note_input,
    ]

    prev_obs_btn.click(
        fn=handle_prev_obs,
        inputs=[caption_idx_state, obs_idx_state],
        outputs=obs_outputs,
    )

    next_obs_btn.click(
        fn=handle_next_obs,
        inputs=[caption_idx_state, obs_idx_state],
        outputs=obs_outputs,
    )

    # 3. Rating button handlers
    def select_thumbs_up():
        return "thumbs_up", "**Selected:** 👍 Good Caption"

    def select_thumbs_down():
        return "thumbs_down", "**Selected:** 👎 Needs Work"

    thumbs_up_btn.click(
        fn=select_thumbs_up,
        outputs=[rating_state, rating_display],
    )

    thumbs_down_btn.click(
        fn=select_thumbs_down,
        outputs=[rating_state, rating_display],
    )

    # 4. Submit feedback
    submit_btn.click(
        fn=handle_feedback_submit,
        inputs=[caption_idx_state, rating_state, note_input],
        outputs=[feedback_status],
    )

    # Initial load trigger on startup
    app.load(
        fn=update_ui,
        inputs=[caption_idx_state, obs_idx_state],
        outputs=[
            caption_idx_state,
            obs_idx_state,
            nav_counter,
            spectrum_plot,
            obs_nav_row,
            obs_status_txt,
            caption_display,
            metadata_display,
            reasoning_accordion,
            reasoning_display,
            quotes_display,
        ],
    )

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        theme=theme,
        css=custom_css,
        head=head_html,
        share=False,
    )

