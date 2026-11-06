import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from service import app as svc  # noqa: E402

GOOD = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'
client = TestClient(svc.app)  # no lifespan: the model is not loaded in unit tests


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setenv("MODEL_VERSION", "vtest")
    monkeypatch.setenv("HOSTNAME", "pod-1")
    monkeypatch.delenv("FAULT_INJECT", raising=False)
    svc.STATE.update(ready=False, generate=None)
    yield
    svc.STATE.update(ready=False, generate=None)


def test_health_and_readiness():
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503
    svc.STATE.update(ready=True, generate=lambda t: GOOD)
    assert client.get("/readyz").status_code == 200


def test_parse_success_headers_and_body():
    svc.STATE.update(ready=True, generate=lambda t: GOOD)
    r = client.post("/parse", json={"text": "what is the weather in london"})
    assert r.status_code == 200
    assert r.json() == {"intent": "weather_query", "date": None, "time": None, "place": "london"}
    assert r.headers["X-Model-Version"] == "vtest" and r.headers["X-Served-By"] == "pod-1"


def test_fault_injection_returns_500_with_exact_body(monkeypatch):
    svc.STATE.update(ready=True, generate=lambda t: GOOD)
    monkeypatch.setenv("FAULT_INJECT", "1")
    r = client.post("/parse", json={"text": "x"})
    assert r.status_code == 500 and r.json() == {"error": "invalid_model_output"}


def test_broken_model_output_never_returned_as_200():
    svc.STATE.update(ready=True, generate=lambda t: '{"intent": "alarm_set", "date": "tomor')
    assert client.post("/parse", json={"text": "x"}).status_code == 500
