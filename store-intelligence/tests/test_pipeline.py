import pytest

from pipeline.run_pipeline import is_detection_available, is_tracking_available, main


def test_pipeline_smoke_run():
    if not (is_detection_available() and is_tracking_available()):
        pytest.skip("CV dependencies not installed for pipeline smoke test")

    result = main([
        "--layout",
        "data/layouts/store_layout.json",
        "--videos-dir",
        "data/videos",
        "--max-frames",
        "1",
        "--no-debug",
    ])
    assert result == 0
