"""
config_2026.py
==============
Central configuration for the 2026 F1 season: grid mappings,
power-unit ratings, regulation weights, and track profiles.
"""

# ──────────────────────────────────────────────
# 2026 Driver ↔ Team ↔ Engine Mappings
# ──────────────────────────────────────────────
GRID_2026 = {
    # team: {drivers, engine_supplier, is_works_team}
    "Ferrari": {
        "drivers": ["Lewis Hamilton", "Charles Leclerc"],
        "engine": "Ferrari",
        "is_works": True,
        "team_color": "#E8002D",
    },
    "Red Bull Racing": {
        "drivers": ["Max Verstappen", "Isack Hadjar"],
        "engine": "Red Bull Ford",
        "is_works": True,
        "team_color": "#3671C6",
    },
    "Mercedes": {
        "drivers": ["George Russell", "Andrea Kimi Antonelli"],
        "engine": "Mercedes",
        "is_works": True,
        "team_color": "#27F4D2",
    },
    "McLaren": {
        "drivers": ["Lando Norris", "Oscar Piastri"],
        "engine": "Mercedes",
        "is_works": False,
        "team_color": "#FF8000",
    },
    "Aston Martin": {
        "drivers": ["Fernando Alonso", "Lance Stroll"],
        "engine": "Honda",
        "is_works": True,
        "team_color": "#229971",
    },
    "Alpine": {
        "drivers": ["Pierre Gasly", "Jack Doohan"],
        "engine": "Mercedes",
        "is_works": False,
        "team_color": "#FF87BC",
    },
    "Haas": {
        "drivers": ["Esteban Ocon", "Oliver Bearman"],
        "engine": "Toyota",
        "is_works": False,
        "team_color": "#B6BABD",
    },
    "Racing Bulls": {
        "drivers": ["Yuki Tsunoda", "Liam Lawson"],
        "engine": "Red Bull Ford",
        "is_works": False,
        "team_color": "#6692FF",
    },
    "Williams": {
        "drivers": ["Alexander Albon", "Carlos Sainz"],
        "engine": "Mercedes",
        "is_works": False,
        "team_color": "#1868DB",
    },
    "Sauber (Audi)": {
        "drivers": ["Nico Hulkenberg", "Gabriel Bortoleto"],
        "engine": "Audi",
        "is_works": True,
        "team_color": "#52E252",
    },
    "Cadillac": {
        "drivers": ["Valtteri Bottas", "Sergio Perez"],
        "engine": "Ferrari",
        "is_works": False,
        "team_color": "#FFD700",
    },
}

# Flatten to quick look-ups
DRIVER_TO_TEAM = {}
DRIVER_TO_ENGINE = {}
TEAM_COLORS = {}
for team, info in GRID_2026.items():
    TEAM_COLORS[team] = info["team_color"]
    for d in info["drivers"]:
        DRIVER_TO_TEAM[d] = team
        DRIVER_TO_ENGINE[d] = info["engine"]


# ──────────────────────────────────────────────
# Power Unit (PU) Competitiveness Ratings
# Split into ICE (Internal Combustion), MGU-K Deployment (Boost),
# and MGU-K Recovery (Energy Harvesting). Scale 0-100.
# ──────────────────────────────────────────────
PU_RATINGS = {
    "Ferrari":        {"ice": 95, "mguk_deploy": 94, "mguk_recover": 88},
    "Mercedes":       {"ice": 92, "mguk_deploy": 90, "mguk_recover": 95},
    "Red Bull Ford":  {"ice": 89, "mguk_deploy": 96, "mguk_recover": 82},
    "Honda":          {"ice": 91, "mguk_deploy": 88, "mguk_recover": 93},
    "Audi":           {"ice": 75, "mguk_deploy": 70, "mguk_recover": 72},
    "Toyota":         {"ice": 78, "mguk_deploy": 76, "mguk_recover": 74},
}

# ──────────────────────────────────────────────
# Active Aero Efficiency Ratings (per team)
# Reflects how well each team is expected to
# exploit X-Mode (low drag) and Z-Mode (downforce).
# Scale 0-100.
# ──────────────────────────────────────────────
ACTIVE_AERO_RATINGS = {
    "Ferrari":             90,
    "Red Bull Racing":     93,
    "Mercedes":            88,
    "McLaren":             91,
    "Aston Martin":        83,
    "Alpine":              78,
    "Haas":                70,
    "Racing Bulls":        76,
    "Williams":            74,
    "Sauber (Audi)":       68,
    "Cadillac":            60,   # New team, least developed aero
}

# ──────────────────────────────────────────────
# Driver Skill Ratings (composite: racecraft,
# qualifying, tyre management, wet weather, overtaking)
# Scale 0-100.
# ──────────────────────────────────────────────
DRIVER_RATINGS = {
    "Max Verstappen":          98,
    "Lewis Hamilton":          96,
    "Charles Leclerc":         93,
    "Lando Norris":            92,
    "George Russell":          90,
    "Oscar Piastri":           89,
    "Carlos Sainz":            88,
    "Fernando Alonso":         87,
    "Pierre Gasly":            82,
    "Alexander Albon":         83,
    "Yuki Tsunoda":            80,
    "Liam Lawson":             78,
    "Esteban Ocon":            80,
    "Lance Stroll":            74,
    "Nico Hulkenberg":         79,
    "Valtteri Bottas":         78,
    "Sergio Perez":            77,
    "Andrea Kimi Antonelli":   76,
    "Jack Doohan":             73,
    "Oliver Bearman":          74,
    "Isack Hadjar":            75,
    "Gabriel Bortoleto":       72,
}

# ──────────────────────────────────────────────
# Override Potential & Tyre Management Skill
# override_pot: A driver's tendency to exploit close-following (0-1.0)
# battery_strat: How well they manage battery drain for the 350kW override (0-1.0)
# tyre_mgmt: Ability to preserve tyres, heavily affected by 30kg lighter cars (0-100)
# ──────────────────────────────────────────────
DRIVER_SPECIFICS = {
    "Max Verstappen":          {"override_pot": 0.95, "battery_strat": 0.94, "tyre_mgmt": 96},
    "Lewis Hamilton":          {"override_pot": 0.88, "battery_strat": 0.96, "tyre_mgmt": 98},
    "Charles Leclerc":         {"override_pot": 0.85, "battery_strat": 0.85, "tyre_mgmt": 89},
    "Lando Norris":            {"override_pot": 0.87, "battery_strat": 0.88, "tyre_mgmt": 90},
    "George Russell":          {"override_pot": 0.80, "battery_strat": 0.85, "tyre_mgmt": 88},
    "Oscar Piastri":           {"override_pot": 0.82, "battery_strat": 0.83, "tyre_mgmt": 87},
    "Carlos Sainz":            {"override_pot": 0.79, "battery_strat": 0.89, "tyre_mgmt": 94},
    "Fernando Alonso":         {"override_pot": 0.90, "battery_strat": 0.95, "tyre_mgmt": 93},
    "Pierre Gasly":            {"override_pot": 0.75, "battery_strat": 0.78, "tyre_mgmt": 82},
    "Alexander Albon":         {"override_pot": 0.74, "battery_strat": 0.75, "tyre_mgmt": 85},
    "Yuki Tsunoda":            {"override_pot": 0.78, "battery_strat": 0.70, "tyre_mgmt": 78},
    "Liam Lawson":             {"override_pot": 0.72, "battery_strat": 0.73, "tyre_mgmt": 79},
    "Esteban Ocon":            {"override_pot": 0.73, "battery_strat": 0.76, "tyre_mgmt": 83},
    "Lance Stroll":            {"override_pot": 0.65, "battery_strat": 0.68, "tyre_mgmt": 74},
    "Nico Hulkenberg":         {"override_pot": 0.70, "battery_strat": 0.75, "tyre_mgmt": 77},
    "Valtteri Bottas":         {"override_pot": 0.68, "battery_strat": 0.74, "tyre_mgmt": 81},
    "Sergio Perez":            {"override_pot": 0.71, "battery_strat": 0.82, "tyre_mgmt": 95},
    "Andrea Kimi Antonelli":   {"override_pot": 0.70, "battery_strat": 0.65, "tyre_mgmt": 75},
    "Jack Doohan":             {"override_pot": 0.66, "battery_strat": 0.68, "tyre_mgmt": 73},
    "Oliver Bearman":          {"override_pot": 0.69, "battery_strat": 0.70, "tyre_mgmt": 74},
    "Isack Hadjar":            {"override_pot": 0.71, "battery_strat": 0.65, "tyre_mgmt": 72},
    "Gabriel Bortoleto":       {"override_pot": 0.67, "battery_strat": 0.69, "tyre_mgmt": 75},
}

# ──────────────────────────────────────────────
# Track Profiles — characterize each 2026 circuit
# x_mode_weight: how much X-Mode (low drag) matters
# z_mode_weight: how much Z-Mode (downforce) matters
# mechanical_grip: how much the lighter chassis helps
# overtaking_opportunity: how many passing zones exist
# All scales 0-1.0
# ──────────────────────────────────────────────
TRACK_PROFILES = {
    "Albert Park": {
        "country": "Australia",
        "x_mode_weight": 0.55,
        "z_mode_weight": 0.45,
        "mechanical_grip": 0.60,
        "overtaking_opportunity": 0.65,
    },
    "Shanghai": {
        "country": "China",
        "x_mode_weight": 0.60,
        "z_mode_weight": 0.40,
        "mechanical_grip": 0.50,
        "overtaking_opportunity": 0.70,
    },
    "Suzuka": {
        "country": "Japan",
        "x_mode_weight": 0.40,
        "z_mode_weight": 0.60,
        "mechanical_grip": 0.70,
        "overtaking_opportunity": 0.45,
    },
    "Bahrain": {
        "country": "Bahrain",
        "x_mode_weight": 0.65,
        "z_mode_weight": 0.35,
        "mechanical_grip": 0.45,
        "overtaking_opportunity": 0.80,
    },
    "Jeddah": {
        "country": "Saudi Arabia",
        "x_mode_weight": 0.70,
        "z_mode_weight": 0.30,
        "mechanical_grip": 0.40,
        "overtaking_opportunity": 0.60,
    },
    "Miami": {
        "country": "USA",
        "x_mode_weight": 0.55,
        "z_mode_weight": 0.45,
        "mechanical_grip": 0.50,
        "overtaking_opportunity": 0.65,
    },
    "Imola": {
        "country": "Italy",
        "x_mode_weight": 0.45,
        "z_mode_weight": 0.55,
        "mechanical_grip": 0.65,
        "overtaking_opportunity": 0.40,
    },
    "Monaco": {
        "country": "Monaco",
        "x_mode_weight": 0.15,
        "z_mode_weight": 0.85,
        "mechanical_grip": 0.90,
        "overtaking_opportunity": 0.10,
    },
    "Barcelona": {
        "country": "Spain",
        "x_mode_weight": 0.50,
        "z_mode_weight": 0.50,
        "mechanical_grip": 0.55,
        "overtaking_opportunity": 0.55,
    },
    "Montreal": {
        "country": "Canada",
        "x_mode_weight": 0.65,
        "z_mode_weight": 0.35,
        "mechanical_grip": 0.50,
        "overtaking_opportunity": 0.70,
    },
    "Silverstone": {
        "country": "UK",
        "x_mode_weight": 0.45,
        "z_mode_weight": 0.55,
        "mechanical_grip": 0.60,
        "overtaking_opportunity": 0.55,
    },
    "Spa": {
        "country": "Belgium",
        "x_mode_weight": 0.60,
        "z_mode_weight": 0.40,
        "mechanical_grip": 0.55,
        "overtaking_opportunity": 0.70,
    },
    "Hungaroring": {
        "country": "Hungary",
        "x_mode_weight": 0.25,
        "z_mode_weight": 0.75,
        "mechanical_grip": 0.75,
        "overtaking_opportunity": 0.25,
    },
    "Zandvoort": {
        "country": "Netherlands",
        "x_mode_weight": 0.30,
        "z_mode_weight": 0.70,
        "mechanical_grip": 0.70,
        "overtaking_opportunity": 0.30,
    },
    "Monza": {
        "country": "Italy",
        "x_mode_weight": 0.85,
        "z_mode_weight": 0.15,
        "mechanical_grip": 0.30,
        "overtaking_opportunity": 0.85,
    },
    "Baku": {
        "country": "Azerbaijan",
        "x_mode_weight": 0.70,
        "z_mode_weight": 0.30,
        "mechanical_grip": 0.45,
        "overtaking_opportunity": 0.75,
    },
    "Singapore": {
        "country": "Singapore",
        "x_mode_weight": 0.20,
        "z_mode_weight": 0.80,
        "mechanical_grip": 0.85,
        "overtaking_opportunity": 0.20,
    },
    "COTA": {
        "country": "USA",
        "x_mode_weight": 0.55,
        "z_mode_weight": 0.45,
        "mechanical_grip": 0.55,
        "overtaking_opportunity": 0.65,
    },
    "Mexico City": {
        "country": "Mexico",
        "x_mode_weight": 0.60,
        "z_mode_weight": 0.40,
        "mechanical_grip": 0.50,
        "overtaking_opportunity": 0.70,
    },
    "Interlagos": {
        "country": "Brazil",
        "x_mode_weight": 0.55,
        "z_mode_weight": 0.45,
        "mechanical_grip": 0.60,
        "overtaking_opportunity": 0.70,
    },
    "Las Vegas": {
        "country": "USA",
        "x_mode_weight": 0.75,
        "z_mode_weight": 0.25,
        "mechanical_grip": 0.35,
        "overtaking_opportunity": 0.75,
    },
    "Lusail": {
        "country": "Qatar",
        "x_mode_weight": 0.50,
        "z_mode_weight": 0.50,
        "mechanical_grip": 0.55,
        "overtaking_opportunity": 0.55,
    },
    "Yas Marina": {
        "country": "Abu Dhabi",
        "x_mode_weight": 0.55,
        "z_mode_weight": 0.45,
        "mechanical_grip": 0.50,
        "overtaking_opportunity": 0.65,
    },
}

# ──────────────────────────────────────────────
# 2026 Regulation Weight Multipliers
# These scale the influence of each regulation
# change in the feature vector.
# ──────────────────────────────────────────────
REG_WEIGHTS = {
    "pu_weight":              0.35,   # Highly car dependent (ICE + MGU-K)
    "active_aero_weight":     0.30,   # Highly car dependent (X/Z modes)
    "driver_skill_weight":    0.10,   # Reduced raw driver talent impact
    "override_weight":        0.05,   # Driver battery management
    "chassis_agility_weight": 0.15,   # Car mechanical advantage
    "historical_form_weight": 0.05,   # Suppressed historical bias (prevents past form from dictating 2026)
}

# ──────────────────────────────────────────────
# Seasons to pull historical data from
# ──────────────────────────────────────────────
HISTORICAL_SEASONS = [2023, 2024, 2025]
CURRENT_SEASON = 2026

# ──────────────────────────────────────────────
# 2026 Calendar (round → track name)
# ──────────────────────────────────────────────
CALENDAR_2026 = {
    1:  "Albert Park",
    2:  "Shanghai",
    3:  "Suzuka",
    4:  "Bahrain",
    5:  "Jeddah",
    6:  "Miami",
    7:  "Imola",
    8:  "Monaco",
    9:  "Barcelona",
    10: "Montreal",
    11: "Silverstone",
    12: "Spa",
    13: "Hungaroring",
    14: "Zandvoort",
    15: "Monza",
    16: "Baku",
    17: "Singapore",
    18: "COTA",
    19: "Mexico City",
    20: "Interlagos",
    21: "Las Vegas",
    22: "Lusail",
    23: "Yas Marina",
}

# How many completed rounds so far in 2026 (update as season progresses)
COMPLETED_ROUNDS_2026 = 5    # Aus, China, Suzuka, Bahrain, Jeddah
NEXT_RACE_ROUND = 6          # Miami
NEXT_RACE_NAME = "Miami"
