import datetime
import json
import os
import tempfile
from huggingface_hub import HfApi, hf_hub_download
import config


def submit_feedback(
    object_key: str,
    dataset_source: str,
    model: str,
    strategy: str,
    rating: str | None = None,
    note: str | None = None,
) -> tuple[bool, str]:
    """
    Submits feedback (thumbs up/down and/or note) for a given caption.
    Appends to HF dataset repo if HF_TOKEN is configured, and logs locally as fallback/cache.
    """
    if not rating and not (note and note.strip()):
        return False, "Please provide a rating (👍 / 👎) or write a note before submitting."

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    feedback_record = {
        "object_key": object_key,
        "dataset_source": dataset_source,
        "model": model,
        "strategy": strategy,
        "rating": rating,
        "note": note.strip() if note else None,
        "timestamp": timestamp,
    }

    # Always log locally first
    local_dir = "output"
    os.makedirs(local_dir, exist_ok=True)
    local_file = os.path.join(local_dir, "feedback.jsonl")

    try:
        with open(local_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_record) + "\n")
    except Exception as e:
        print(f"Warning: Failed to write local feedback log: {e}")

    # Push to HuggingFace dataset if HF token is present
    token = config.HF_TOKEN or os.getenv("HF_TOKEN")
    repo_id = config.FEEDBACK_DATASET_REPO

    if not token:
        return True, "Feedback saved locally. (Note: HF_TOKEN secret not configured for HF dataset push)."

    try:
        api = HfApi(token=token)

        # Download existing feedback.jsonl if it exists, or create new
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
                # File may not exist yet in the repo
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
