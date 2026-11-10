from fastapi.testclient import TestClient

from main import app, risk_band

SAMPLE = {
    "income": 1200,
    "loan_amount": 5000,
    "term_months": 24,
    "credit_score": 680,
    "employment_years": 4,
}


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["model_loaded"] is True


def test_predict_returns_score():
    with TestClient(app) as client:
        response = client.post("/predict", json=SAMPLE)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["score"] <= 1
    assert body["risk_band"] in {"low", "medium", "high"}
    assert body["model_version"] == "1.0.0"


def test_predict_rejects_bad_input():
    with TestClient(app) as client:
        response = client.post("/predict", json={**SAMPLE, "credit_score": 50})
    assert response.status_code == 422


def test_risk_band():
    assert risk_band(0.1) == "low"
    assert risk_band(0.45) == "medium"
    assert risk_band(0.9) == "high"
