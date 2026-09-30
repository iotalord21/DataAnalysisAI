import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    r2_score,
    mean_squared_error,
    mean_absolute_error,
)
import plotly.express as px


def detect_target_column(df: pd.DataFrame, user_target: Optional[str] = None) -> str:
    """
    Intelligently identifies the target column if not explicitly provided.
    Looks for common names like 'churn', 'target', 'label', 'status', or low-cardinality categorical columns.
    """
    if user_target and user_target in df.columns:
        return user_target

    common_names = ["churn", "target", "label", "status", "fraud", "default", "class", "outcome", "converted"]
    col_map = {col.lower().strip(): col for col in df.columns}
    for name in common_names:
        if name in col_map:
            return col_map[name]

    # Look for binary categorical column
    for col in df.columns:
        if df[col].nunique() == 2 and not col.lower().startswith("id"):
            return col

    # Fallback to the last column
    return df.columns[-1]


def run_predictive_model(file_path: str, target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Automated Predictive Machine Learning pipeline:
    1. Loads dataset and detects problem type (Classification vs Regression).
    2. Performs clean preprocessing (handling missing values, encoding categoricals).
    3. Trains a Random Forest model with train/test validation.
    4. Computes model performance metrics.
    5. Calculates feature importances and crafts an interactive Plotly horizontal bar chart.
    6. Generates actionable predictive takeaways.
    """
    p = Path(file_path)
    if p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)

    target_col = detect_target_column(df, target_column)
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # Drop pure ID columns (high cardinality strings or identifier names)
    cols_to_drop = []
    for c in df.columns:
        if c == target_col:
            continue
        c_lower = c.lower()
        if "id" in c_lower and df[c].dtype == object and df[c].nunique() > len(df) * 0.5:
            cols_to_drop.append(c)

    cleaned_df = df.drop(columns=cols_to_drop).copy()

    # Determine task type
    target_series = cleaned_df[target_col].dropna()
    is_classification = False

    if pd.api.types.is_numeric_dtype(target_series):
        unique_vals = target_series.nunique()
        if unique_vals <= 10:
            is_classification = True
        else:
            is_classification = False
    else:
        is_classification = True

    # Prepare features (X) and target (y)
    df_valid = cleaned_df.dropna(subset=[target_col]).copy()
    y_raw = df_valid[target_col]
    X_raw = df_valid.drop(columns=[target_col])

    # Encode target if classification
    class_mapping = None
    if is_classification:
        if y_raw.dtype == object or str(y_raw.dtype) == "category" or y_raw.dtype == bool:
            unique_classes = sorted(list(y_raw.unique()))
            class_mapping = {val: idx for idx, val in enumerate(unique_classes)}
            y = y_raw.map(class_mapping).values
        else:
            y = y_raw.values
    else:
        y = y_raw.values

    # Preprocess features
    # Numeric: impute with median
    # Categorical: impute with mode, then pd.get_dummies
    numeric_features = [c for c in X_raw.columns if pd.api.types.is_numeric_dtype(X_raw[c])]
    categorical_features = [c for c in X_raw.columns if c not in numeric_features]

    X_processed = pd.DataFrame(index=X_raw.index)

    for col in numeric_features:
        median_val = X_raw[col].median() if len(X_raw[col].dropna()) > 0 else 0
        X_processed[col] = X_raw[col].fillna(median_val)

    for col in categorical_features:
        mode_series = X_raw[col].mode()
        mode_val = mode_series[0] if len(mode_series) > 0 else "Missing"
        filled_series = X_raw[col].fillna(mode_val).astype(str)
        # One-hot encode with drop_first to avoid multicollinearity
        dummies = pd.get_dummies(filled_series, prefix=col, drop_first=True)
        X_processed = pd.concat([X_processed, dummies], axis=1)

    if X_processed.shape[1] == 0:
        raise ValueError("No valid predictive features remaining after preprocessing.")

    feature_names = list(X_processed.columns)

    # Train / Test split
    test_size = 0.25 if len(df_valid) >= 40 else 0.2
    stratify = y if (is_classification and np.min(np.bincount(y.astype(int))) >= 2) else None

    X_train, X_test, y_train, y_test = train_test_split(
        X_processed, y, test_size=test_size, random_state=42, stratify=stratify
    )

    metrics = {}
    feature_importances = []

    if is_classification:
        n_classes = len(np.unique(y))
        model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
        prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))

        roc_auc = None
        if n_classes == 2:
            try:
                y_prob = model.predict_proba(X_test)[:, 1]
                roc_auc = round(float(roc_auc_score(y_test, y_prob)), 3)
            except Exception:
                roc_auc = None

        metrics = {
            "task": "classification",
            "classes_count": n_classes,
            "accuracy": round(acc * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "roc_auc": roc_auc,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }
    else:
        model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        r2 = float(r2_score(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mae = float(mean_absolute_error(y_test, y_pred))

        metrics = {
            "task": "regression",
            "r2_score": round(r2, 3),
            "rmse": round(rmse, 3),
            "mae": round(mae, 3),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

    # Extract feature importances
    raw_importances = model.feature_importances_
    sorted_idx = np.argsort(raw_importances)[::-1]

    for idx in sorted_idx[:15]:
        feature_importances.append({
            "feature": feature_names[idx],
            "importance": round(float(raw_importances[idx]) * 100, 2),
        })

    # Generate interactive Plotly horizontal bar chart
    top_10 = feature_importances[:10]
    top_10_reversed = top_10[::-1]

    fig = px.bar(
        x=[item["importance"] for item in top_10_reversed],
        y=[item["feature"] for item in top_10_reversed],
        orientation="h",
        labels={"x": "Predictive Weight / Importance (%)", "y": "Feature"},
        title=f"Top Predictive Drivers for Target: '{target_col}'",
        template="plotly_white",
        color=[item["importance"] for item in top_10_reversed],
        color_continuous_scale="Purp",
    )
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans, sans-serif"),
        coloraxis_showscale=False,
        margin=dict(l=150, r=30, t=50, b=50),
    )
    chart_json = json.loads(fig.to_json())

    # Formulate actionable takeaways based on top features
    top_driver_names = [f["feature"] for f in top_10[:3]]
    takeaways = [
        f"The primary driver determining '{target_col}' is '{top_driver_names[0]}', accounting for {top_10[0]['importance']}% of total model decision weight.",
    ]
    if len(top_driver_names) > 1:
        takeaways.append(
            f"Secondary critical factors include '{top_driver_names[1]}' ({top_10[1]['importance']}%) and '{top_driver_names[2]}' ({top_10[2]['importance']}%)."
        )

    if is_classification:
        takeaways.append(
            f"The Random Forest classifier achieved a test accuracy of {metrics['accuracy']}% with a balanced F1-score of {metrics['f1_score']}%."
        )
    else:
        takeaways.append(
            f"The Random Forest regression model explained {round(metrics['r2_score'] * 100, 1)}% of variance in '{target_col}' (R² = {metrics['r2_score']})."
        )

    return {
        "target_column": target_col,
        "is_classification": is_classification,
        "metrics": metrics,
        "feature_importances": top_10,
        "importance_chart": chart_json,
        "actionable_takeaways": takeaways,
        "available_columns": list(cleaned_df.columns),
    }
