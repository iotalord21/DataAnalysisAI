import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.agents.ml_agent import run_predictive_model, detect_target_column
from app.config import settings

client = TestClient(app)


def test_detect_target_column():
    import pandas as pd
    df1 = pd.DataFrame({"age": [20, 30], "churn": ["Yes", "No"]})
    assert detect_target_column(df1) == "churn"

    df2 = pd.DataFrame({"sales": [100, 200], "status": ["Active", "Cancelled"]})
    assert detect_target_column(df2) == "status"

    df3 = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert detect_target_column(df3, user_target="a") == "a"


def test_predictive_model_classification():
    sample_path = settings.sample_data_dir / "customer_churn.csv"
    assert sample_path.exists()

    result = run_predictive_model(str(sample_path), target_column="Churn")
    assert result["is_classification"] is True
    assert result["target_column"] == "Churn"
    assert "metrics" in result
    assert result["metrics"]["accuracy"] > 50.0
    assert len(result["feature_importances"]) >= 3
    assert "importance_chart" in result
    assert "data" in result["importance_chart"]
    assert len(result["actionable_takeaways"]) >= 1


def test_predictive_model_regression():
    sample_path = settings.sample_data_dir / "customer_churn.csv"
    assert sample_path.exists()

    result = run_predictive_model(str(sample_path), target_column="MonthlyCharges")
    assert result["is_classification"] is False
    assert result["target_column"] == "MonthlyCharges"
    assert "r2_score" in result["metrics"]
    assert len(result["feature_importances"]) >= 3


def test_api_predictive_endpoint():
    # Load sample dataset
    load_resp = client.post("/api/datasets/load-sample/customer_churn")
    assert load_resp.status_code == 200
    dataset_id = load_resp.json()["dataset_id"]

    # Call predictive analysis
    pred_resp = client.post("/api/analysis/predictive", json={"dataset_id": dataset_id, "target_column": "Churn"})
    assert pred_resp.status_code == 200
    data = pred_resp.json()
    assert data["success"] is True
    assert data["is_classification"] is True
    assert data["target_column"] == "Churn"
    assert len(data["feature_importances"]) > 0
