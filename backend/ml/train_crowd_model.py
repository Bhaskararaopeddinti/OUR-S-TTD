"""
OURS TTD — ML Crowd Prediction Training Script
=================================================
Trains Linear Regression and Random Forest Regression models on
the real historical darshan dataset (backend/data/final_data.csv).

Usage (from project root):
    python -m backend.ml.train_crowd_model

Or directly:
    python backend/ml/train_crowd_model.py
"""

import os
import sys
import json
import pathlib
import logging
import warnings

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

# ── Resolve paths from project root regardless of CWD ──────────────────────
# This file lives at: PROJECT_ROOT/backend/ml/train_crowd_model.py
SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent          # backend/ml/
BACKEND_DIR  = SCRIPT_DIR.parent                                # backend/
PROJECT_ROOT = BACKEND_DIR.parent                               # project root

DATA_PATH    = BACKEND_DIR / "data" / "final_data.csv"
MODELS_DIR   = SCRIPT_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE     = MODELS_DIR / "crowd_model.joblib"
META_FILE      = MODELS_DIR / "model_meta.json"

TARGET_COL     = "darshans"

# Features that exist in the dataset and are useful for prediction.
# Rolling-average columns are excluded to avoid data-leakage into future dates.
# The 'date' column is excluded (raw string) — date-derived features are used instead.
FEATURE_COLS = [
    "weekend",
    "weekday",
    "summer",
    "temp_max",
    "temp_min",
    "humidity",
    "rainfall",
    "google_trend_score",
    "is_public_holiday",
    "is_festival",
    "is_brahmostavam",
    "day",
    "month",
]


# ────────────────────────────────────────────────────────────────────────────
def load_and_inspect(path: pathlib.Path) -> pd.DataFrame:
    """Load the CSV and print a comprehensive inspection report."""
    if not path.exists():
        logger.error("Dataset not found at: %s", path)
        sys.exit(1)

    df = pd.read_csv(path)
    n_rows, n_cols = df.shape

    print("\n" + "="*60)
    print("  DATASET INSPECTION REPORT")
    print("="*60)
    print(f"  File            : {path}")
    print(f"  Rows            : {n_rows:,}")
    print(f"  Columns         : {n_cols}")
    print(f"\n  Column Details:")
    for col in df.columns:
        missing = df[col].isnull().sum()
        unique  = df[col].nunique()
        dtype   = df[col].dtype
        print(f"    {col:<25} dtype={str(dtype):<10} missing={missing:<5} unique={unique}")
    print(f"\n  Duplicate rows  : {df.duplicated().sum()}")
    print(f"  Target column   : {TARGET_COL}")
    print(f"\n  {TARGET_COL} distribution:")
    print(f"    min     : {df[TARGET_COL].min():,.0f}")
    print(f"    25%     : {df[TARGET_COL].quantile(0.25):,.0f}")
    print(f"    median  : {df[TARGET_COL].median():,.0f}")
    print(f"    75%     : {df[TARGET_COL].quantile(0.75):,.0f}")
    print(f"    90%     : {df[TARGET_COL].quantile(0.90):,.0f}")
    print(f"    max     : {df[TARGET_COL].max():,.0f}")
    print(f"    mean    : {df[TARGET_COL].mean():,.0f}")
    print(f"    std     : {df[TARGET_COL].std():,.0f}")
    print("="*60 + "\n")
    return df


def compute_crowd_thresholds(df: pd.DataFrame) -> dict:
    """Derive data-driven crowd status thresholds from the actual distribution."""
    q25 = float(df[TARGET_COL].quantile(0.25))
    q50 = float(df[TARGET_COL].quantile(0.50))
    q75 = float(df[TARGET_COL].quantile(0.75))
    # VERY HIGH = anything above 75th percentile
    return {
        "LOW_MAX":       q25,   # < 25th pct  -> LOW
        "MODERATE_MAX":  q50,   # 25-50th pct -> MODERATE
        "HIGH_MAX":      q75,   # 50-75th pct -> HIGH
        # >= 75th pct                            -> VERY HIGH
    }


def classify_crowd(predicted: float, thresholds: dict) -> str:
    """Return crowd status string from a predicted darshan count."""
    if predicted < thresholds["LOW_MAX"]:
        return "LOW"
    elif predicted < thresholds["MODERATE_MAX"]:
        return "MODERATE"
    elif predicted < thresholds["HIGH_MAX"]:
        return "HIGH"
    else:
        return "VERY HIGH"


def preprocess(df: pd.DataFrame):
    """Clean and prepare features and target."""
    from sklearn.preprocessing import StandardScaler

    # Drop rows missing key columns
    df = df.dropna(subset=[TARGET_COL] + FEATURE_COLS).copy()
    # Remove duplicates (safety)
    df = df.drop_duplicates().copy()

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    # Fill any remaining NaNs in features with column median
    for col in X.columns:
        if X[col].isnull().any():
            X[col] = X[col].fillna(X[col].median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y.values, scaler


def train_models(X_train, y_train):
    """Train Linear Regression and Random Forest Regressor."""
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    logger.info("Linear Regression trained.")

    rf = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    logger.info("Random Forest trained (n_estimators=200).")

    return lr, rf


def evaluate(model, X_test, y_test, name: str) -> dict:
    """Evaluate a model and print real metrics."""
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_pred = model.predict(X_test)
    mae  = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2   = float(r2_score(y_test, y_pred))

    print(f"\n  {name}")
    print(f"    MAE  : {mae:,.0f}")
    print(f"    RMSE : {rmse:,.0f}")
    print(f"    R2   : {r2:.4f}")

    return {"model_name": name, "mae": mae, "rmse": rmse, "r2": r2}


# ────────────────────────────────────────────────────────────────────────────
def main():
    import joblib
    from sklearn.model_selection import train_test_split

    # 1. Load + inspect
    df = load_and_inspect(DATA_PATH)

    # 2. Compute crowd thresholds
    thresholds = compute_crowd_thresholds(df)
    print(f"  Crowd-status thresholds (from actual data):")
    print(f"    LOW      : < {thresholds['LOW_MAX']:,.0f}")
    print(f"    MODERATE : {thresholds['LOW_MAX']:,.0f} - {thresholds['MODERATE_MAX']:,.0f}")
    print(f"    HIGH     : {thresholds['MODERATE_MAX']:,.0f} - {thresholds['HIGH_MAX']:,.0f}")
    print(f"    VERY HIGH: >= {thresholds['HIGH_MAX']:,.0f}\n")

    # 3. Preprocess
    X, y, scaler = preprocess(df)

    # 4. Train / test split (80/20, chronological order preserved via shuffle=False)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, shuffle=False
    )
    logger.info("Train size: %d  |  Test size: %d", len(X_train), len(X_test))

    # 5. Train
    lr, rf = train_models(X_train, y_train)

    # 6. Evaluate
    print("\n" + "="*60)
    print("  MODEL EVALUATION")
    print("="*60)
    lr_metrics = evaluate(lr, X_test, y_test, "Linear Regression")
    rf_metrics = evaluate(rf, X_test, y_test, "Random Forest Regression")
    print("="*60)

    # 7. Select best model by R2
    if rf_metrics["r2"] >= lr_metrics["r2"]:
        best_model      = rf
        best_name       = "Random Forest Regression"
        best_metrics    = rf_metrics
        lr_is_best      = False
    else:
        best_model      = lr
        best_name       = "Linear Regression"
        best_metrics    = lr_metrics
        lr_is_best      = True

    print(f"\n  [OK] Best model selected: {best_name}")
    print(f"    R2 = {best_metrics['r2']:.4f}  |  MAE = {best_metrics['mae']:,.0f}  |  RMSE = {best_metrics['rmse']:,.0f}\n")

    # 8. Save best model + scaler
    joblib.dump({"model": best_model, "scaler": scaler}, MODEL_FILE)
    logger.info("Model saved: %s", MODEL_FILE)

    # 9. Save metadata (for API & frontend display)
    meta = {
        "target_column":         TARGET_COL,
        "feature_columns":       FEATURE_COLS,
        "best_model":            best_name,
        "best_model_mae":        round(best_metrics["mae"], 2),
        "best_model_rmse":       round(best_metrics["rmse"], 2),
        "best_model_r2":         round(best_metrics["r2"], 4),
        "lr_mae":                round(lr_metrics["mae"], 2),
        "lr_rmse":               round(lr_metrics["rmse"], 2),
        "lr_r2":                 round(lr_metrics["r2"], 4),
        "rf_mae":                round(rf_metrics["mae"], 2),
        "rf_rmse":               round(rf_metrics["rmse"], 2),
        "rf_r2":                 round(rf_metrics["r2"], 4),
        "crowd_thresholds":      {k: round(v, 2) for k, v in thresholds.items()},
        "train_rows":            int(len(X_train)),
        "test_rows":             int(len(X_test)),
        "total_historical_rows": int(len(df)),
        "dataset_file":          str(DATA_PATH.relative_to(PROJECT_ROOT)),
    }
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)
    logger.info("Metadata saved: %s", META_FILE)

    print("="*60)
    print("  TRAINING COMPLETE")
    print("  Model file : " + str(MODEL_FILE))
    print("  Meta file  : " + str(META_FILE))
    print("="*60 + "\n")

    return meta


if __name__ == "__main__":
    main()
