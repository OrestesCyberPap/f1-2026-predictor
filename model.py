"""
model.py
========
XGBoost-based ranking model for F1 2026 race prediction.
Uses XGBRanker (pairwise learning-to-rank) with fallback to XGBRegressor.
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error

from data_collector import collect_all_data
from feature_engineering import (
    build_training_data,
    build_race_feature_matrix,
    FEATURE_COLS,
    normalise_driver_name,
)
from config_2026 import (
    NEXT_RACE_NAME, NEXT_RACE_ROUND, GRID_2026,
    DRIVER_TO_TEAM, REG_WEIGHTS, CALENDAR_2026,
)

MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)
MODEL_PATH = MODEL_DIR / "f1_xgb_model.pkl"


# ──────────────────────────────────────────────
# Train the model
# ──────────────────────────────────────────────
def train_model(results_df: pd.DataFrame) -> tuple:
    """
    Train the XGBoost model on historical race data.
    Returns (model, feature_importance_df, eval_metrics).

    We use XGBRegressor with target = finish_position.
    Lower predicted value = better predicted finish.
    This is simpler and more robust than XGBRanker for
    smaller datasets, while achieving the same ranking goal.
    """
    print("\n" + "=" * 60)
    print("MODEL TRAINING")
    print("=" * 60)

    # Build training data
    training_df = build_training_data(results_df)

    if training_df.empty or len(training_df) < 20:
        print("[WARN] Insufficient training data from APIs.")
        print("       Generating synthetic training data from 2026 config ratings...")
        training_df = _generate_synthetic_training_data()

    print(f"  Training samples: {len(training_df)}")
    print(f"  Features: {len(FEATURE_COLS)}")

    X = training_df[FEATURE_COLS].values
    y = training_df["target_position"].values

    # ── Cross-validation with GroupKFold (group by race) ──
    if "season" in training_df.columns and "round" in training_df.columns:
        groups = training_df["season"].astype(str) + "_" + training_df["round"].astype(str)
    else:
        groups = np.arange(len(training_df)) // 22  # approximate grouping

    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        objective="reg:squarederror",
    )

    # Train on all data (we'll use CV for evaluation metrics)
    n_unique_groups = groups.nunique() if hasattr(groups, 'nunique') else len(set(groups))
    if n_unique_groups >= 3:
        n_splits = min(5, n_unique_groups)
        gkf = GroupKFold(n_splits=n_splits)
        cv_scores = []
        for train_idx, val_idx in gkf.split(X, y, groups):
            model.fit(X[train_idx], y[train_idx],
                      eval_set=[(X[val_idx], y[val_idx])],
                      verbose=False)
            preds = model.predict(X[val_idx])
            mae = mean_absolute_error(y[val_idx], preds)
            cv_scores.append(mae)
        avg_mae = np.mean(cv_scores)
        print(f"  Cross-validation MAE: {avg_mae:.2f} positions")
    else:
        avg_mae = None
        print("  [INFO] Not enough groups for cross-validation")

    # Final fit on all data
    model.fit(X, y, verbose=False)
    print("  Model trained successfully.")

    # ── Feature importance ──
    importance = model.feature_importances_
    fi_df = pd.DataFrame({
        "feature": FEATURE_COLS,
        "importance": importance
    }).sort_values("importance", ascending=False)

    print("\n  Feature Importance (Top 10):")
    for _, row in fi_df.head(10).iterrows():
        bar = "#" * int(row["importance"] * 50)
        print(f"    {row['feature']:25s} {row['importance']:.4f} {bar}")

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"\n  Model saved to {MODEL_PATH}")

    eval_metrics = {"cv_mae": avg_mae, "n_training_samples": len(training_df)}
    return model, fi_df, eval_metrics


# ──────────────────────────────────────────────
# Generate synthetic training data when APIs
# don't return enough historical data
# ──────────────────────────────────────────────
def _generate_synthetic_training_data() -> pd.DataFrame:
    """
    Create synthetic training data based on the 2026 configuration
    ratings. This ensures the model can train even without API data.
    Each 'race' is a simulated event at each track profile.
    """
    from config_2026 import TRACK_PROFILES, DRIVER_RATINGS

    rows = []
    race_id = 0

    for track_name, track_info in TRACK_PROFILES.items():
        race_id += 1
        # Build feature matrix for this track
        matrix = build_race_feature_matrix(track_name, pd.DataFrame())

        # Create a composite score for ranking
        matrix["composite_score"] = (
            matrix["ice_power"]          * REG_WEIGHTS["pu_weight"] * 0.4 +
            matrix["mguk_advantage"]     * REG_WEIGHTS["pu_weight"] * 0.6 +
            matrix["aero_track_score"]   * REG_WEIGHTS["active_aero_weight"] +
            matrix["driver_skill"]       * REG_WEIGHTS["driver_skill_weight"] +
            matrix["override_adjusted"]  * REG_WEIGHTS["override_weight"] +
            matrix["chassis_score"]      * REG_WEIGHTS["chassis_agility_weight"] * 0.5 +
            matrix["tyre_mgmt"]          * REG_WEIGHTS["chassis_agility_weight"] * 0.5 +
            matrix["form_score"]         * REG_WEIGHTS["historical_form_weight"]
        )

        # Add controlled randomness for realistic variance
        np.random.seed(race_id * 42)
        matrix["composite_score"] += np.random.normal(0, 0.02, len(matrix))

        # Rank by composite score (higher = better) → assign finish positions
        matrix = matrix.sort_values("composite_score", ascending=False).reset_index(drop=True)
        matrix["target_position"] = range(1, len(matrix) + 1)
        matrix["season"] = 2025  # treat as pseudo-historical
        matrix["round"] = race_id

        rows.append(matrix)

    df = pd.concat(rows, ignore_index=True)
    print(f"  Generated {len(df)} synthetic training samples across {race_id} simulated races")
    return df


# ──────────────────────────────────────────────
# Predict next race
# ──────────────────────────────────────────────
def predict_race(
    model,
    track_name: str,
    results_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Predict finishing positions for all 2026 drivers at a given track.
    Returns a DataFrame sorted by predicted position.
    """
    print(f"\n{'=' * 60}")
    print(f"PREDICTING: {track_name} Grand Prix")
    print(f"{'=' * 60}")

    # Build feature matrix
    matrix = build_race_feature_matrix(track_name, results_df)
    X = matrix[FEATURE_COLS].values

    # Predict (lower value = better finish position)
    predicted_positions = model.predict(X)
    matrix["predicted_score"] = predicted_positions

    # Rank: lowest predicted position value gets P1
    matrix = matrix.sort_values("predicted_score", ascending=True).reset_index(drop=True)
    matrix["predicted_position"] = range(1, len(matrix) + 1)

    # Compute points (2026 points system, standard)
    points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
                  6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    matrix["predicted_points"] = matrix["predicted_position"].map(points_map).fillna(0)

    print("\n  Predicted Top 10:")
    for _, row in matrix.head(10).iterrows():
        pos = int(row["predicted_position"])
        pts = int(row["predicted_points"])
        print(f"    P{pos:2d}  {row['driver']:25s}  ({row['team']:20s})  {pts:2d} pts")

    return matrix


# ──────────────────────────────────────────────
# Predict entire remaining season
# ──────────────────────────────────────────────
def predict_remaining_season(
    model,
    results_df: pd.DataFrame,
    start_round: int,
) -> dict:
    """Predict results for all remaining races in the 2026 season."""
    predictions = {}
    for rnd, track in CALENDAR_2026.items():
        if rnd >= start_round:
            pred = predict_race(model, track, results_df)
            predictions[f"Round {rnd}: {track}"] = pred
    return predictions


# ──────────────────────────────────────────────
# Load model from disk
# ──────────────────────────────────────────────
def load_model():
    """Load a previously trained model from disk."""
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return None


# ──────────────────────────────────────────────
# Full pipeline: collect → train → predict
# ──────────────────────────────────────────────
def run_full_pipeline(force_refresh: bool = False) -> tuple:
    """
    Execute the complete pipeline:
    1. Collect data from all sources (loads from cache unless force_refresh=True)
    2. Train the XGBoost model
    3. Predict the next race
    Returns (model, predictions_df, feature_importance_df, eval_metrics)
    """
    # Step 1: Collect data
    dataset = collect_all_data(force_refresh=force_refresh)
    results_df = dataset["results"]

    # Step 2: Train model
    model, fi_df, eval_metrics = train_model(results_df)

    # Step 3: Predict next race
    predictions = predict_race(model, NEXT_RACE_NAME, results_df)

    return model, predictions, fi_df, eval_metrics


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    model, predictions, fi_df, eval_metrics = run_full_pipeline()
    print("\n\nDone. Predictions saved.")
    from pathlib import Path
    Path("data").mkdir(exist_ok=True)
    predictions.to_csv("data/predictions.csv", index=False)
    fi_df.to_csv("data/feature_importance.csv", index=False)
