from app.api import MetricsPayload, get_metrics, health, latest_metrics, receive_metrics, received_metrics
from fastapi import HTTPException
import pytest


def test_health_endpoint_returns_ok():
    assert health() == {"status": "ok"}


def test_receive_and_read_latest_metric():
    received_metrics.clear()
    payload = MetricsPayload(
        agent="agent-test",
        event_type="system_metrics",
        data={"cpu": {"percent": 10}},
    )

    response = receive_metrics(payload)

    assert response["status"] == "received"
    assert response["total_received"] == 1
    assert get_metrics()["total"] == 1
    assert latest_metrics()["agent"] == "agent-test"


def test_latest_metric_returns_404_when_empty():
    received_metrics.clear()

    with pytest.raises(HTTPException) as exc_info:
        latest_metrics()

    assert exc_info.value.status_code == 404
