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
# Scale 0-100.
# ──────────────────────────────────────────────
PU_RATINGS = {
    "Ferrari":        95,
    "Mercedes":       92,
    "Red Bull Ford":  89,
    "Honda":          91,
    "Audi":           75,
    "Toyota":         78,
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
# Override Potential
# override_pot: A driver's tendency to exploit close-following (0-1.0)
# ──────────────────────────────────────────────
OVERRIDE_POTENTIAL = {
    "Max Verstappen":          0.95,
    "Lewis Hamilton":          0.88,
    "Charles Leclerc":         0.85,
    "Lando Norris":            0.87,
    "George Russell":          0.80,
    "Oscar Piastri":           0.82,
    "Carlos Sainz":            0.79,
    "Fernando Alonso":         0.90,
    "Pierre Gasly":            0.75,
    "Alexander Albon":         0.74,
    "Yuki Tsunoda":            0.78,
    "Liam Lawson":             0.72,
    "Esteban Ocon":            0.73,
    "Lance Stroll":            0.65,
    "Nico Hulkenberg":         0.70,
    "Valtteri Bottas":         0.68,
    "Sergio Perez":            0.71,
    "Andrea Kimi Antonelli":   0.70,
    "Jack Doohan":             0.66,
    "Oliver Bearman":          0.69,
    "Isack Hadjar":            0.71,
    "Gabriel Bortoleto":       0.67,
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
    "pu_weight":              0.25,   # How much PU competitiveness affects outcome
    "active_aero_weight":     0.20,   # How much active aero mastery affects outcome
    "driver_skill_weight":    0.25,   # Raw driver talent
    "override_weight":        0.10,   # Manual overtake button exploitation
    "chassis_agility_weight": 0.10,   # Lighter/shorter car advantage
    "historical_form_weight": 0.10,   # Rolling form from recent races
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
