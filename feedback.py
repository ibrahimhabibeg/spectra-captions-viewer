import datetime
import json
import os
import tempfile

import config


def _save_and_upload_record(feedback_record: dict, object_key: str) -> tuple[bool, str]:
    """Persist feedback locally and optionally sync it to Hugging Face."""
    timestamp = feedback_record.get(
        "timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    os.makedirs("output", exist_ok=True)
    local_file = os.path.join("output", "feedback.jsonl")
    try:
        with open(local_file, "a", encoding="utf-8") as file:
            file.write(json.dumps(feedback_record) + "\n")
    except Exception as error:
        print(f"Warning: Failed to write local feedback log: {error}")

    token = config.HF_TOKEN or os.getenv("HF_TOKEN")
    if not token:
        return True, "Feedback saved locally. HF_TOKEN is not configured."

    try:
        from huggingface_hub import HfApi, hf_hub_download

        api = HfApi(token=token)
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_file = os.path.join(temporary_directory, "feedback.jsonl")
            existing_content = ""
            try:
                downloaded_path = hf_hub_download(
                    repo_id=config.FEEDBACK_DATASET_REPO,
                    filename="feedback.jsonl",
                    repo_type="dataset",
                    token=token,
                )
                with open(downloaded_path, encoding="utf-8") as file:
                    existing_content = file.read()
            except Exception:
                pass

            with open(temporary_file, "w", encoding="utf-8") as file:
                file.write(existing_content + json.dumps(feedback_record) + "\n")
            api.upload_file(
                path_or_fileobj=temporary_file,
                path_in_repo="feedback.jsonl",
                repo_id=config.FEEDBACK_DATASET_REPO,
                repo_type="dataset",
                commit_message=f"Add feedback for {object_key} ({timestamp[:19]})",
            )
        return True, "Thank you! Your feedback has been recorded."
    except Exception as error:
        return True, f"Feedback saved locally, but remote sync failed: {error}"


def submit_single_feedback(
    object_key: str,
    dataset_source: str,
    caption_file_index: int,
    model: str,
    strategy: str,
    rating: str | None = None,
    tags: list[str] | None = None,
    span_annotations: list[dict] | None = None,
    note: str | None = None,
    modality: str | None = None,
) -> tuple[bool, str]:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "evaluation_mode": "single_caption",
        "modality": modality,
        "object_key": object_key,
        "dataset_source": dataset_source,
        "caption_file_index": caption_file_index,
        "model": model,
        "strategy": strategy,
        "rating": rating,
        "tags": tags or [],
        "span_annotations": span_annotations or [],
        "note": note.strip() if note else None,
        "timestamp": timestamp,
    }
    return _save_and_upload_record(record, object_key)


def submit_comparison_feedback(
    object_key: str,
    dataset_source: str,
    candidate_file_indices: dict[str, int],
    candidates_info: dict[str, dict],
    vote: str | None = None,
    candidates_eval: dict[str, dict] | None = None,
    note: str | None = None,
    modality: str | None = None,
) -> tuple[bool, str]:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "evaluation_mode": "multi_caption_comparison",
        "modality": modality,
        "object_key": object_key,
        "dataset_source": dataset_source,
        "candidate_file_indices": candidate_file_indices,
        "candidates_info": candidates_info,
        "vote": vote,
        "candidates_eval": candidates_eval or {},
        "note": note.strip() if note else None,
        "timestamp": timestamp,
    }
    return _save_and_upload_record(record, object_key)


def submit_abc_feedback(
    object_key: str,
    dataset_source: str,
    candidate_file_indices: dict[str, int],
    candidates_info: dict[str, dict],
    comparisons: dict[str, str | None],
    candidates_eval: dict[str, dict] | None = None,
    note: str | None = None,
    modality: str | None = None,
) -> tuple[bool, str]:
    """Validate and atomically persist all three required pairwise outcomes."""
    required = {
        "a_vs_b": {"A", "B", "Tie"},
        "b_vs_c": {"B", "C", "Tie"},
        "c_vs_a": {"C", "A", "Tie"},
    }
    for comparison, allowed in required.items():
        if comparisons.get(comparison) not in allowed:
            return False, (
                f"Select a valid outcome for {comparison.replace('_', ' ').upper()}."
            )
    if set(candidates_info) != {"A", "B", "C"}:
        return False, "Candidates A, B, and C are required."

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "evaluation_mode": "abc_pairwise_comparison",
        "modality": modality,
        "object_key": object_key,
        "dataset_source": dataset_source,
        "candidate_file_indices": candidate_file_indices,
        "candidates_info": candidates_info,
        "comparisons": comparisons,
        "candidates_eval": candidates_eval or {},
        "note": note.strip() if note else None,
        "timestamp": timestamp,
    }
    return _save_and_upload_record(record, object_key)


def submit_feedback(
    object_key: str,
    dataset_source: str,
    model: str,
    strategy: str,
    rating: str | None = None,
    note: str | None = None,
    caption_file_index: int = 0,
    tags: list[str] | None = None,
    span_annotations: list[dict] | None = None,
    modality: str | None = None,
) -> tuple[bool, str]:
    """Backward-compatible single-feedback wrapper."""
    return submit_single_feedback(
        object_key=object_key,
        dataset_source=dataset_source,
        caption_file_index=caption_file_index,
        model=model,
        strategy=strategy,
        rating=rating,
        tags=tags,
        span_annotations=span_annotations,
        note=note,
        modality=modality,
    )
