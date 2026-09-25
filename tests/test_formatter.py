import pytest

from app.formatter import format_metrics


def sample_metrics():
    return {
        "timestamp": "2026-09-25T20:00:00+00:00",
        "hostname": "test-host",
        "cpu": {"percent": 12.5, "logical_cores": 4},
        "memory": {
            "total_bytes": 1000,
            "available_bytes": 400,
            "used_bytes": 600,
            "percent": 60.0,
        },
        "system": {"load_1m": 0.1, "load_5m": 0.2, "load_15m": 0.3},
    }


def test_format_metrics_wraps_collected_data():
    payload = format_metrics(sample_metrics(), agent_name="agent-test")

    assert payload["agent"] == "agent-test"
    assert payload["event_type"] == "system_metrics"
    assert payload["data"]["hostname"] == "test-host"


def test_format_metrics_rejects_incomplete_metrics():
    metrics = sample_metrics()
    metrics.pop("memory")

    with pytest.raises(ValueError, match="memory"):
        format_metrics(metrics)
