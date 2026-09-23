import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "provider" in data


def test_system_info_endpoint():
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert "providers_available" in data
    assert "gemini" in data["providers_available"]
    assert "openai" in data["providers_available"]
    assert "anthropic" in data["providers_available"]
    assert "ollama" in data["providers_available"]
    assert "sandbox" in data


def test_get_samples():
    response = client.get("/api/datasets/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 1
    assert any(s["sample_id"] == "customer_churn" for s in samples)


def test_load_sample_and_preview():
    # Load customer churn sample
    load_resp = client.post("/api/datasets/load-sample/customer_churn")
    assert load_resp.status_code == 200
    dataset_info = load_resp.json()
    assert "dataset_id" in dataset_info
    assert dataset_info["total_rows"] > 0
    assert dataset_info["total_columns"] > 0
    assert "MonthlyCharges" in dataset_info["numeric_columns"]

    # Preview endpoint
    dataset_id = dataset_info["dataset_id"]
    prev_resp = client.get(f"/api/datasets/{dataset_id}/preview")
    assert prev_resp.status_code == 200
    prev_data = prev_resp.json()
    assert prev_data["dataset_id"] == dataset_id
    assert "profile" in prev_data
    assert prev_data["profile"]["total_rows"] == dataset_info["total_rows"]
