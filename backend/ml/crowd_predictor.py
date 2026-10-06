"""
OURS TTD — ML Crowd Predictor Service
======================================
Loads the pre-trained model (crowd_model.joblib) and provides a
predict() function for the FastAPI prediction endpoint.

The model is loaded once on first call and cached for reuse.
"""

import json
import logging
import pathlib
from datetime import date as dt_date
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
MODELS_DIR  = SCRIPT_DIR / "models"
MODEL_FILE  = MODELS_DIR / "crowd_model.joblib"
META_FILE   = MODELS_DIR / "model_meta.json"

# Feature column order must exactly match train_crowd_model.py
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

# ── Module-level cache ─────────────────────────────────────────────────────
_model_cache  = None   # dict with "model" and "scaler"
_meta_cache   = None   # dict with metadata / thresholds


def _load_model_and_meta():
    """Load model and metadata from disk (once per process)."""
    global _model_cache, _meta_cache

    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_FILE}. "
            "Please run: python -m backend.ml.train_crowd_model"
        )
    if not META_FILE.exists():
        raise FileNotFoundError(
            f"Model metadata not found at {META_FILE}. "
            "Please run: python -m backend.ml.train_crowd_model"
        )

    try:
        import joblib
        bundle = joblib.load(MODEL_FILE)
        _model_cache = bundle  # {"model": ..., "scaler": ...}
    except Exception as e:
        raise RuntimeError(f"Failed to load crowd model: {e}") from e

    try:
        with open(META_FILE, "r") as f:
            _meta_cache = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load model metadata: {e}") from e

    logger.info(
        "Crowd prediction model loaded: %s (R²=%.4f)",
        _meta_cache.get("best_model", "Unknown"),
        _meta_cache.get("best_model_r2", 0.0),
    )


def get_model_meta() -> dict:
    """Return metadata dict (loads once from disk)."""
    if _meta_cache is None:
        _load_model_and_meta()
    return _meta_cache


def classify_crowd(predicted: float, thresholds: dict) -> str:
    """Map predicted darshan count to crowd status label."""
    if predicted < thresholds["LOW_MAX"]:
        return "LOW"
    elif predicted < thresholds["MODERATE_MAX"]:
        return "MODERATE"
    elif predicted < thresholds["HIGH_MAX"]:
        return "HIGH"
    else:
        return "VERY HIGH"


def derive_date_features(target_date: dt_date) -> dict:
    """Auto-derive day, month, weekday, weekend, summer from a date object."""
    weekday_num = target_date.weekday()   # 0=Mon … 6=Sun
    is_weekend  = 1 if weekday_num >= 5 else 0
    is_weekday  = 1 - is_weekend          # binary mirror
    is_summer   = 1 if target_date.month in (4, 5, 6) else 0
    return {
        "day":     target_date.day,
        "month":   target_date.month,
        "weekday": is_weekday,
        "weekend": is_weekend,
        "summer":  is_summer,
    }


def predict(
    target_date: dt_date,
    temp_max: float,
    temp_min: float,
    humidity: int,
    rainfall: float,
    google_trend_score: int,
    is_public_holiday: int,
    is_festival: int,
    is_brahmostavam: int,
) -> dict:
    """
    Generate a real crowd prediction from the trained ML model.

    Parameters correspond to actual columns in final_data.csv.
    Date-derived features (day, month, weekday, weekend, summer) are
    computed automatically from target_date.

    Returns a dict with:
      predicted_crowd, crowd_status, model, analysis, disclaimer, meta
    """
    # Ensure model is loaded
    if _model_cache is None:
        _load_model_and_meta()

    model  = _model_cache["model"]
    scaler = _model_cache["scaler"]
    meta   = _meta_cache

    # Auto-derive date features
    date_feats = derive_date_features(target_date)

    # Build feature vector in exact training order
    feature_values = [
        date_feats["weekend"],
        date_feats["weekday"],
        date_feats["summer"],
        float(temp_max),
        float(temp_min),
        float(humidity),
        float(rainfall),
        float(google_trend_score),
        float(is_public_holiday),
        float(is_festival),
        float(is_brahmostavam),
        float(date_feats["day"]),
        float(date_feats["month"]),
    ]

    import pandas as pd
    X = pd.DataFrame([feature_values], columns=FEATURE_COLS)
    X_scaled = scaler.transform(X)

    raw_prediction = float(model.predict(X_scaled)[0])
    predicted_crowd = max(0, int(round(raw_prediction)))

    thresholds    = meta["crowd_thresholds"]
    crowd_status  = classify_crowd(raw_prediction, thresholds)

    # Build human-readable analysis
    conditions = []
    if is_festival:
        conditions.append("a festival day")
    if is_brahmostavam:
        conditions.append("Brahmotsavam")
    if is_public_holiday:
        conditions.append("a public holiday")
    if date_feats["weekend"]:
        conditions.append("a weekend")
    if date_feats["summer"]:
        conditions.append("summer season")

    cond_str = " and ".join(conditions) if conditions else "typical weekday conditions"
    status_lower = crowd_status.lower().replace("_", " ")

    analysis = (
        f"Based on {meta.get('total_historical_rows', 3572):,} historical darshan records "
        f"and the entered conditions ({cond_str}), the model predicts a "
        f"{status_lower} pilgrim crowd of approximately {predicted_crowd:,} darshans."
    )

    return {
        "predicted_crowd":     predicted_crowd,
        "crowd_status":        crowd_status,
        "model":               meta.get("best_model", "Unknown"),
        "analysis":            analysis,
        "disclaimer": (
            "Prediction is based on available project historical data "
            "and is not an official TTD guarantee."
        ),
        "model_meta": {
            "historical_records": meta.get("total_historical_rows"),
            "target_column":      meta.get("target_column"),
            "best_model":         meta.get("best_model"),
            "best_model_r2":      meta.get("best_model_r2"),
            "best_model_mae":     meta.get("best_model_mae"),
            "best_model_rmse":    meta.get("best_model_rmse"),
            "lr_r2":              meta.get("lr_r2"),
            "lr_mae":             meta.get("lr_mae"),
            "lr_rmse":            meta.get("lr_rmse"),
            "rf_r2":              meta.get("rf_r2"),
            "rf_mae":             meta.get("rf_mae"),
            "rf_rmse":            meta.get("rf_rmse"),
            "crowd_thresholds":   thresholds,
        },
        "input_features": {
            "date":               str(target_date),
            "day":                date_feats["day"],
            "month":              date_feats["month"],
            "weekday_num":        target_date.weekday(),
            "is_weekend":         date_feats["weekend"],
            "is_summer":          date_feats["summer"],
            "temp_max":           temp_max,
            "temp_min":           temp_min,
            "humidity":           humidity,
            "rainfall":           rainfall,
            "google_trend_score": google_trend_score,
            "is_public_holiday":  is_public_holiday,
            "is_festival":        is_festival,
            "is_brahmostavam":    is_brahmostavam,
        },
    }
