"""
feature_engineering.py
======================
Constructs the feature matrix for the XGBoost model by combining
historical race data with 2026 regulation modifiers, driver ratings,
power-unit indices, active aero efficiency, and track profiles.
"""

import pandas as pd
import numpy as np
from config_2026 import (
    GRID_2026, DRIVER_TO_TEAM, DRIVER_TO_ENGINE,
    PU_RATINGS, ACTIVE_AERO_RATINGS, DRIVER_RATINGS,
    DRIVER_SPECIFICS, TRACK_PROFILES, REG_WEIGHTS,
    HISTORICAL_SEASONS, CURRENT_SEASON, CALENDAR_2026,
    NEXT_RACE_NAME, NEXT_RACE_ROUND
)


# ──────────────────────────────────────────────
# Name normalisation helpers
# ──────────────────────────────────────────────
_NAME_MAP = {
    # Handle common Jolpica/Ergast name mismatches
    "Andrea Kimi Antonelli": ["Andrea Kimi Antonelli", "Kimi Antonelli"],
    "Max Verstappen":        ["Max Verstappen"],
    "Lewis Hamilton":        ["Lewis Hamilton"],
    "Charles Leclerc":       ["Charles Leclerc"],
    "Lando Norris":          ["Lando Norris"],
    "George Russell":        ["George Russell"],
    "Oscar Piastri":         ["Oscar Piastri"],
    "Carlos Sainz":          ["Carlos Sainz"],
    "Fernando Alonso":       ["Fernando Alonso"],
    "Pierre Gasly":          ["Pierre Gasly"],
    "Alexander Albon":       ["Alexander Albon"],
    "Yuki Tsunoda":          ["Yuki Tsunoda"],
    "Liam Lawson":           ["Liam Lawson"],
    "Esteban Ocon":          ["Esteban Ocon"],
    "Lance Stroll":          ["Lance Stroll"],
    "Nico Hulkenberg":       ["Nico Hulkenberg", "Nico Hülkenberg"],
    "Valtteri Bottas":       ["Valtteri Bottas"],
    "Sergio Perez":          ["Sergio Perez", "Sergio Pérez"],
    "Jack Doohan":           ["Jack Doohan"],
    "Oliver Bearman":        ["Oliver Bearman"],
    "Isack Hadjar":          ["Isack Hadjar"],
    "Gabriel Bortoleto":     ["Gabriel Bortoleto"],
}

def _build_reverse_name_map():
    rmap = {}
    for canonical, aliases in _NAME_MAP.items():
        for alias in aliases:
            rmap[alias.lower()] = canonical
    return rmap

_REVERSE_NAME = _build_reverse_name_map()

def normalise_driver_name(name: str) -> str:
    """Return the canonical 2026-grid driver name."""
    return _REVERSE_NAME.get(name.lower().strip(), name.strip())


# ──────────────────────────────────────────────
# Rolling driver form from historical data
# ──────────────────────────────────────────────
def compute_rolling_form(results_df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Compute a rolling-average finishing position and points
    for each driver over the last `window` races.
    Returns a DataFrame with one row per driver.
    """
    if results_df.empty:
        return pd.DataFrame()

    df = results_df.copy()
    df["driver"] = df["driver"].apply(normalise_driver_name)
    df = df.sort_values(["season", "round"])

    form_rows = []
    for driver, grp in df.groupby("driver"):
        recent = grp.tail(window)
        form_rows.append({
            "driver": driver,
            "avg_finish": recent["finish_position"].mean(),
            "avg_grid":   recent["grid_position"].mean(),
            "avg_points": recent["points"].mean(),
            "dnf_rate":   (recent["status"] != "Finished").mean(),
            "races_completed": len(grp),
            "best_finish": grp["finish_position"].min(),
        })
    return pd.DataFrame(form_rows)


# ──────────────────────────────────────────────
# Qualifying pace delta (how much a driver
# typically gains/loses from grid → finish)
# ──────────────────────────────────────────────
def compute_quali_to_race_delta(results_df: pd.DataFrame) -> pd.DataFrame:
    """Positive delta = driver typically gains positions on race day."""
    if results_df.empty:
        return pd.DataFrame()

    df = results_df.copy()
    df["driver"] = df["driver"].apply(normalise_driver_name)
    df["position_delta"] = df["grid_position"] - df["finish_position"]

    delta = (df.groupby("driver")["position_delta"]
               .mean()
               .reset_index()
               .rename(columns={"position_delta": "avg_position_gain"}))
    return delta


# ──────────────────────────────────────────────
# Construct feature vector for a single driver
# at a specific track
# ──────────────────────────────────────────────
def build_driver_features(
    driver: str,
    track_name: str,
    rolling_form: pd.DataFrame,
    quali_delta: pd.DataFrame,
) -> dict:
    """
    Build the feature dict for one driver at one track.
    Combines: PU rating, Active Aero, Driver Skill, Override,
    Chassis Agility, historical rolling form, and track profile.
    """
    team = DRIVER_TO_TEAM.get(driver, "Unknown")
    engine = DRIVER_TO_ENGINE.get(driver, "Unknown")
    track = TRACK_PROFILES.get(track_name, {})

    # ── Base attributes ──
    # MGU-K / ICE splits
    engine_stats    = PU_RATINGS.get(engine, {"ice": 80, "mguk_deploy": 80, "mguk_recover": 80})
    ice_power       = engine_stats["ice"] / 100.0
    mguk_deploy     = engine_stats["mguk_deploy"] / 100.0
    mguk_recover    = engine_stats["mguk_recover"] / 100.0

    aero_rating     = ACTIVE_AERO_RATINGS.get(team, 65) / 100.0
    driver_skill    = DRIVER_RATINGS.get(driver, 70) / 100.0
    
    # Driver Specifics
    ds = DRIVER_SPECIFICS.get(driver, {"override_pot": 0.5, "battery_strat": 0.5, "tyre_mgmt": 70})
    override_pot    = ds["override_pot"]
    battery_strat   = ds["battery_strat"]
    tyre_mgmt       = ds["tyre_mgmt"] / 100.0

    # ── Track-specific modifiers ──
    x_mode   = track.get("x_mode_weight", 0.5)
    z_mode   = track.get("z_mode_weight", 0.5)
    mech_grip = track.get("mechanical_grip", 0.5)
    overtake_opp = track.get("overtaking_opportunity", 0.5)

    # Straight-line dominance: Heavily favors high X-Mode tracks (Monza, Vegas, Miami)
    straight_line_dominance = x_mode / (x_mode + z_mode + 0.001)

    # Active Aero composite: team's aero rating weighted by track profile
    aero_track_score = aero_rating * (x_mode * straight_line_dominance + z_mode * (1 - straight_line_dominance))

    # Chassis agility advantage: 30kg lighter car helps mechanically, 
    # but tyre whisperers lose some of their historical advantage
    chassis_score = mech_grip * tyre_mgmt * 1.2  

    # MGU-K Advantage: High overtake tracks demand heavy deployment and recovery
    mguk_advantage = (mguk_deploy * overtake_opp) + (mguk_recover * (1 - straight_line_dominance))

    # Override potential adjusted by track overtaking opportunity and driver's battery strategy
    override_adjusted = override_pot * battery_strat * overtake_opp

    # ── Rolling form (from historical data) ──
    form_row = rolling_form[rolling_form["driver"] == driver] if not rolling_form.empty else pd.DataFrame()
    if not form_row.empty:
        avg_finish  = form_row.iloc[0].get("avg_finish", 10)
        avg_grid    = form_row.iloc[0].get("avg_grid", 10)
        avg_points  = form_row.iloc[0].get("avg_points", 5)
        dnf_rate    = form_row.iloc[0].get("dnf_rate", 0.1)
        best_finish = form_row.iloc[0].get("best_finish", 5)
    else:
        # New driver or no data — use moderate defaults
        avg_finish, avg_grid, avg_points = 12, 12, 3
        dnf_rate, best_finish = 0.1, 8

    # Normalise rolling form to 0-1 (lower finish position = better)
    form_score = 1.0 - (min(avg_finish, 20) / 20.0)

    # ── Quali-to-race delta ──
    delta_row = quali_delta[quali_delta["driver"] == driver] if not quali_delta.empty else pd.DataFrame()
    position_gain = delta_row.iloc[0]["avg_position_gain"] if not delta_row.empty else 0.0
    # Normalise: typical range is -5 to +5
    position_gain_norm = np.clip((position_gain + 5) / 10.0, 0, 1)

    # ── Build feature dict ──
    features = {
        "driver":               driver,
        "team":                 team,
        "engine":               engine,
        "track":                track_name,
        # Core 2026 regulation features
        "ice_power":            ice_power,
        "mguk_deploy":          mguk_deploy,
        "mguk_recover":         mguk_recover,
        "mguk_advantage":       mguk_advantage,
        "aero_track_score":     aero_track_score,
        "straight_line_dom":    straight_line_dominance,
        "driver_skill":         driver_skill,
        "override_adjusted":    override_adjusted,
        "chassis_score":        chassis_score,
        "tyre_mgmt":            tyre_mgmt,
        # Historical features
        "form_score":           form_score,
        "avg_finish":           avg_finish,
        "avg_grid":             avg_grid,
        "avg_points":           avg_points,
        "dnf_rate":             dnf_rate,
        "best_finish":          best_finish,
        "position_gain_norm":   position_gain_norm,
        # Track features
        "x_mode_weight":        x_mode,
        "z_mode_weight":        z_mode,
        "mechanical_grip":      mech_grip,
        "overtaking_opp":       overtake_opp,
        # Works team flag
        "is_works_team":        1 if GRID_2026.get(team, {}).get("is_works", False) else 0,
    }
    return features


# ──────────────────────────────────────────────
# Build the complete feature matrix for all
# drivers at a given track
# ──────────────────────────────────────────────
def build_race_feature_matrix(
    track_name: str,
    results_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the feature matrix for all 2026 drivers at a given track.
    Returns a DataFrame where each row is a driver's feature vector.
    """
    # Compute rolling form & quali delta from historical data
    rolling_form = compute_rolling_form(results_df)
    quali_delta  = compute_quali_to_race_delta(results_df)

    rows = []
    for team, info in GRID_2026.items():
        for driver in info["drivers"]:
            feat = build_driver_features(driver, track_name, rolling_form, quali_delta)
            rows.append(feat)

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# Build training data from historical races
# Each row: driver features + actual finish position
# ──────────────────────────────────────────────
def build_training_data(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each historical race, build feature vectors for every driver
    and attach the actual finish position as the target label.
    """
    if results_df.empty:
        return pd.DataFrame()

    df = results_df.copy()
    df["driver"] = df["driver"].apply(normalise_driver_name)

    rolling_form = compute_rolling_form(df)
    quali_delta  = compute_quali_to_race_delta(df)

    training_rows = []

    # Group by (season, round) — each group is one race
    for (season, rnd), race_group in df.groupby(["season", "round"]):
        # Try to match track from race_name or circuit
        race_name = race_group.iloc[0].get("race_name", "")
        circuit   = race_group.iloc[0].get("circuit", "")

        # Simple track matching
        track_name = _match_track(race_name, circuit)

        for _, row in race_group.iterrows():
            driver = row["driver"]
            if driver not in DRIVER_RATINGS:
                # Only include 2026-grid drivers in training
                continue

            feat = build_driver_features(driver, track_name, rolling_form, quali_delta)
            feat["target_position"] = row["finish_position"]
            feat["season"]          = season
            feat["round"]           = rnd
            training_rows.append(feat)

    return pd.DataFrame(training_rows)


def _match_track(race_name: str, circuit: str) -> str:
    """Best-effort matching of a race/circuit name to our TRACK_PROFILES keys."""
    combined = (race_name + " " + circuit).lower()
    mapping = {
        "albert park": "Albert Park",
        "melbourne": "Albert Park",
        "australia": "Albert Park",
        "shanghai": "Shanghai",
        "china": "Shanghai",
        "suzuka": "Suzuka",
        "japan": "Suzuka",
        "bahrain": "Bahrain",
        "sakhir": "Bahrain",
        "jeddah": "Jeddah",
        "saudi": "Jeddah",
        "miami": "Miami",
        "imola": "Imola",
        "emilia": "Imola",
        "monaco": "Monaco",
        "monte": "Monaco",
        "barcelona": "Barcelona",
        "catalunya": "Barcelona",
        "spain": "Barcelona",
        "montreal": "Montreal",
        "canada": "Montreal",
        "silverstone": "Silverstone",
        "british": "Silverstone",
        "spa": "Spa",
        "belgium": "Spa",
        "hungaroring": "Hungaroring",
        "hungary": "Hungaroring",
        "zandvoort": "Zandvoort",
        "netherlands": "Zandvoort",
        "dutch": "Zandvoort",
        "monza": "Monza",
        "italian": "Monza",
        "baku": "Baku",
        "azerbaijan": "Baku",
        "singapore": "Singapore",
        "marina bay": "Singapore",
        "cota": "COTA",
        "austin": "COTA",
        "americas": "COTA",
        "mexico": "Mexico City",
        "interlagos": "Interlagos",
        "brazil": "Interlagos",
        "sao paulo": "Interlagos",
        "las vegas": "Las Vegas",
        "lusail": "Lusail",
        "qatar": "Lusail",
        "yas marina": "Yas Marina",
        "abu dhabi": "Yas Marina",
    }
    for keyword, track in mapping.items():
        if keyword in combined:
            return track
    return "Barcelona"  # Default to a balanced circuit


# ──────────────────────────────────────────────
# Feature columns used by the model
# ──────────────────────────────────────────────
FEATURE_COLS = [
    "ice_power",
    "mguk_deploy",
    "mguk_recover",
    "mguk_advantage",
    "aero_track_score",
    "straight_line_dom",
    "driver_skill",
    "override_adjusted",
    "chassis_score",
    "tyre_mgmt",
    "form_score",
    "avg_finish",
    "avg_grid",
    "avg_points",
    "dnf_rate",
    "best_finish",
    "position_gain_norm",
    "x_mode_weight",
    "z_mode_weight",
    "mechanical_grip",
    "overtaking_opp",
    "is_works_team",
]


if __name__ == "__main__":
    # Quick test with empty data
    matrix = build_race_feature_matrix("Suzuka", pd.DataFrame())
    print(f"Feature matrix shape: {matrix.shape}")
    print(matrix[["driver", "team", "ice_power", "driver_skill", "aero_track_score"]].to_string())
