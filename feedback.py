import datetime
import json
import os
import tempfile
from huggingface_hub import HfApi, hf_hub_download
import config


def _save_and_upload_record(feedback_record: dict, object_key: str) -> tuple[bool, str]:
    """Helper to persist feedback locally and push to HuggingFace dataset."""
    timestamp = feedback_record.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Always log locally
    local_dir = "output"
    os.makedirs(local_dir, exist_ok=True)
    local_file = os.path.join(local_dir, "feedback.jsonl")

    try:
        with open(local_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_record) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write local feedback log: {e}")

    # Push to HuggingFace dataset if HF token is configured
    token = config.HF_TOKEN or os.getenv("HF_TOKEN")
    repo_id = config.FEEDBACK_DATASET_REPO

    if not token:
        return True, "Feedback saved locally. (Note: HF_TOKEN not configured for remote dataset sync)."

    try:
        api = HfApi(token=token)

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_filepath = os.path.join(tmpdir, "feedback.jsonl")
            existing_content = ""
            try:
                downloaded_path = hf_hub_download(
                    repo_id=repo_id,
                    filename="feedback.jsonl",
                    repo_type="dataset",
                    token=token,
                )
                with open(downloaded_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            except Exception:
                existing_content = ""

            new_line = json.dumps(feedback_record) + "\n"
            updated_content = existing_content + new_line

            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)

            api.upload_file(
                path_or_fileobj=temp_filepath,
                path_in_repo="feedback.jsonl",
                repo_id=repo_id,
                repo_type="dataset",
                commit_message=f"Add feedback for {object_key} ({timestamp[:19]})",
            )

        return True, "Thank you! Your feedback has been recorded."
    except Exception as e:
        return True, f"Feedback saved locally, but HF Hub push encountered an issue: {e}"


def submit_single_feedback(
    object_key: str,
    dataset_source: str,
    caption_file_index: int,
    model: str,
    strategy: str,
    rating: str | None = None,
    tags: list[str] | None = None,
    note: str | None = None,
) -> tuple[bool, str]:
    """Submits feedback for a single-caption evaluation, including caption_file_index."""
    if not rating and not tags and not (note and note.strip()):
        return False, "Please select a rating, tags, or add notes before submitting."

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "evaluation_mode": "single_caption",
        "object_key": object_key,
        "dataset_source": dataset_source,
        "caption_file_index": caption_file_index,
        "model": model,
        "strategy": strategy,
        "rating": rating,
        "tags": tags or [],
        "note": note.strip() if note else None,
        "timestamp": timestamp,
    }
    return _save_and_upload_record(record, object_key)


def submit_comparison_feedback(
    object_key: str,
    dataset_source: str,
    candidate_file_indices: dict[str, int],
    candidates_info: dict[str, dict],
    vote: str | None,
    candidates_eval: dict[str, dict] | None = None,
    note: str | None = None,
) -> tuple[bool, str]:
    """Submits comparative feedback and head-to-head vote for multiple candidate captions."""
    if not vote and not candidates_eval and not (note and note.strip()):
        return False, "Please select a vote preference or evaluate candidate captions before submitting."

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "evaluation_mode": "multi_caption_comparison",
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


def submit_feedback(
    object_key: str,
    dataset_source: str,
    model: str,
    strategy: str,
    rating: str | None = None,
    note: str | None = None,
    caption_file_index: int = 0,
    tags: list[str] | None = None,
) -> tuple[bool, str]:
    """Backward-compatible single feedback wrapper."""
    return submit_single_feedback(
        object_key=object_key,
        dataset_source=dataset_source,
        caption_file_index=caption_file_index,
        model=model,
        strategy=strategy,
        rating=rating,
        tags=tags,
        note=note,
    )
