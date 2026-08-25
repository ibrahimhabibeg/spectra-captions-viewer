import json

import feedback
from data_loader import load_and_group_objects, parse_lightcurve_prompt
from plotting import create_lightcurve_figure


def test_negative_magnitude_errors_are_omitted_from_plot():
    prompt = """<light_curve>
MJD FLT FIELD FLUXCAL FLUXCALERR MAG MAGERR PHOTFLAG
60000.0 g NULL 10.0 2.0 20.0 -9.0 0
60001.0 r NULL 11.0 2.0 19.5 0.2 0
</light_curve>"""

    observations = parse_lightcurve_prompt(prompt)

    assert observations[0]["magnitude_error"] is None
    figure = create_lightcurve_figure(observations, "object-1")
    assert all(error >= 0 for trace in figure.data for error in trace.error_y.array)
    assert figure.layout.yaxis.autorange == "reversed"


def test_nested_comparison_is_normalized_to_abc(tmp_path):
    record = {
        "comparison_id": "comparison-1",
        "object_id": "object-1",
        "conditions": {
            "C_context": {"caption": "C", "prompt": ""},
            "A_context": {"caption": "A", "prompt": ""},
            "B_context": {"caption": "B", "prompt": ""},
        },
    }
    path = tmp_path / "comparisons.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    objects = load_and_group_objects(str(path), "lightcurves")

    assert [candidate["condition"] for candidate in objects[0]["captions"]] == [
        "A_context",
        "B_context",
        "C_context",
    ]


def test_missing_files_produce_empty_datasets(tmp_path):
    assert load_and_group_objects(str(tmp_path / "missing.jsonl"), "spectra") == []


def test_flat_spectral_captions_are_batched_without_dropping_rows(tmp_path):
    path = tmp_path / "spectra.jsonl"
    rows = [
        {
            "object_key": "object-1",
            "dataset_source": "sdss",
            "model": f"model-{index}",
            "strategy": f"strategy-{index}",
            "output": {"caption": f"Caption {index}"},
        }
        for index in range(7)
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    objects = load_and_group_objects(str(path), "spectra")

    assert [len(obj["captions"]) for obj in objects] == [3, 3, 1]
    assert sum(len(obj["captions"]) for obj in objects) == len(rows)
    assert [obj["comparison_batch"] for obj in objects] == [0, 1, 2]
    assert all(obj["comparison_batch_count"] == 3 for obj in objects)


def test_abc_feedback_requires_all_three_pairwise_choices(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(feedback.config, "HF_TOKEN", None)
    candidates = {label: {} for label in "ABC"}

    success, _ = feedback.submit_abc_feedback(
        object_key="object-1",
        dataset_source="test",
        candidate_file_indices={"A": 0, "B": 1, "C": 2},
        candidates_info=candidates,
        comparisons={"a_vs_b": "A", "b_vs_c": "B", "c_vs_a": None},
    )

    assert success is False
    assert not (tmp_path / "output" / "feedback.jsonl").exists()


def test_complete_abc_feedback_is_saved_atomically(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(feedback.config, "HF_TOKEN", None)

    success, _ = feedback.submit_abc_feedback(
        object_key="object-1",
        dataset_source="test",
        modality="lightcurves",
        candidate_file_indices={"A": 0, "B": 1, "C": 2},
        candidates_info={label: {} for label in "ABC"},
        comparisons={"a_vs_b": "A", "b_vs_c": "C", "c_vs_a": "A"},
    )

    assert success is True
    record = json.loads((tmp_path / "output" / "feedback.jsonl").read_text())
    assert record["evaluation_mode"] == "abc_pairwise_comparison"
    assert record["modality"] == "lightcurves"
    assert record["comparisons"] == {
        "a_vs_b": "A",
        "b_vs_c": "C",
        "c_vs_a": "A",
    }
