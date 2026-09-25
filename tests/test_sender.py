import pytest
import requests

from app.sender import MetricsDeliveryError, send_metrics


class FakeResponse:
    status_code = 201

    def raise_for_status(self):
        return None

    def json(self):
        return {"status": "received"}


def test_send_metrics_returns_status_and_body(monkeypatch):
    def fake_post(endpoint, json, timeout):
        assert endpoint == "http://api:8000/metrics"
        assert json == {"agent": "test"}
        assert timeout == 3
        return FakeResponse()

    monkeypatch.setattr("app.sender.requests.post", fake_post)

    result = send_metrics("http://api:8000/metrics", {"agent": "test"}, timeout=3)

    assert result == {"status_code": 201, "response": {"status": "received"}}


def test_send_metrics_raises_delivery_error(monkeypatch):
    def fake_post(endpoint, json, timeout):
        raise requests.ConnectionError("api unavailable")

    monkeypatch.setattr("app.sender.requests.post", fake_post)

    with pytest.raises(MetricsDeliveryError):
        send_metrics("http://api:8000/metrics", {"agent": "test"})
