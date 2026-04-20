"""
data_collector.py
=================
Multi-source data acquisition for the F1 2026 Predictive Model.
Sources: Jolpica API (Ergast successor), OpenF1 API, FastF1, web scraping.
"""

import os
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path

# Optional imports — graceful degradation
try:
    import fastf1
    FASTF1_AVAILABLE = True
except ImportError:
    FASTF1_AVAILABLE = False
    print("[WARN] fastf1 not installed. Telemetry features will be unavailable.")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[WARN] beautifulsoup4 not installed. Web scraping will be unavailable.")

from config_2026 import (
    HISTORICAL_SEASONS, CURRENT_SEASON, GRID_2026,
    DRIVER_TO_TEAM, COMPLETED_ROUNDS_2026
)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
OPENF1_BASE = "https://api.openf1.org/v1"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

REQUEST_DELAY = 0.5  # polite rate-limiting (seconds)


# ──────────────────────────────────────────────
# Utility
# ──────────────────────────────────────────────
def _cached_get(url: str, cache_key: str, force_refresh: bool = False) -> dict | None:
    """GET with local JSON caching to avoid hammering APIs."""
    cache_path = CACHE_DIR / f"{cache_key}.json"
    if cache_path.exists() and not force_refresh:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
    except requests.RequestException as e:
        print(f"[ERROR] Request failed for {url}: {e}")
        return None


# ══════════════════════════════════════════════
# SOURCE 1: Jolpica API (Ergast successor)
# Historical race results, qualifying, standings
# ══════════════════════════════════════════════
def fetch_season_results_jolpica(season: int) -> pd.DataFrame:
    """Fetch all race results for a given season from Jolpica API."""
    url = f"{JOLPICA_BASE}/{season}/results.json?limit=1000"
    cache_key = f"jolpica_results_{season}"
    data = _cached_get(url, cache_key)
    if data is None:
        return pd.DataFrame()

    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    rows = []
    for race in races:
        round_num = int(race["round"])
        race_name = race["raceName"]
        circuit = race["Circuit"]["circuitName"]
        for result in race.get("Results", []):
            driver_name = f"{result['Driver']['givenName']} {result['Driver']['familyName']}"
            rows.append({
                "season": season,
                "round": round_num,
                "race_name": race_name,
                "circuit": circuit,
                "driver": driver_name,
                "driver_id": result["Driver"]["driverId"],
                "team": result["Constructor"]["name"],
                "grid_position": int(result.get("grid", 0)),
                "finish_position": int(result.get("position", 0)),
                "points": float(result.get("points", 0)),
                "status": result.get("status", "Unknown"),
                "laps": int(result.get("laps", 0)),
                "fastest_lap_rank": int(result.get("FastestLap", {}).get("rank", 99)),
            })
    df = pd.DataFrame(rows)
    print(f"  [Jolpica] {season}: {len(df)} result rows from {len(races)} races")
    return df


def fetch_qualifying_jolpica(season: int) -> pd.DataFrame:
    """Fetch qualifying results for a given season."""
    url = f"{JOLPICA_BASE}/{season}/qualifying.json?limit=1000"
    cache_key = f"jolpica_qualifying_{season}"
    data = _cached_get(url, cache_key)
    if data is None:
        return pd.DataFrame()

    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    rows = []
    for race in races:
        round_num = int(race["round"])
        for result in race.get("QualifyingResults", []):
            driver_name = f"{result['Driver']['givenName']} {result['Driver']['familyName']}"
            # Parse best qualifying time
            q_times = []
            for q in ["Q1", "Q2", "Q3"]:
                t = result.get(q, "")
                if t:
                    q_times.append(t)
            best_q = q_times[-1] if q_times else ""
            rows.append({
                "season": season,
                "round": round_num,
                "driver": driver_name,
                "driver_id": result["Driver"]["driverId"],
                "quali_position": int(result.get("position", 0)),
                "best_quali_time": best_q,
            })
    df = pd.DataFrame(rows)
    print(f"  [Jolpica] {season} Qualifying: {len(df)} rows")
    return df


def fetch_driver_standings_jolpica(season: int) -> pd.DataFrame:
    """Fetch end-of-season (or current) driver standings."""
    url = f"{JOLPICA_BASE}/{season}/driverStandings.json"
    cache_key = f"jolpica_standings_{season}"
    data = _cached_get(url, cache_key)
    if data is None:
        return pd.DataFrame()

    standings_lists = (data.get("MRData", {})
                           .get("StandingsTable", {})
                           .get("StandingsLists", []))
    rows = []
    for sl in standings_lists:
        for entry in sl.get("DriverStandings", []):
            driver = entry["Driver"]
            driver_name = f"{driver['givenName']} {driver['familyName']}"
            rows.append({
                "season": season,
                "driver": driver_name,
                "driver_id": driver["driverId"],
                "championship_position": int(entry["position"]),
                "championship_points": float(entry["points"]),
                "championship_wins": int(entry["wins"]),
            })
    df = pd.DataFrame(rows)
    print(f"  [Jolpica] {season} Standings: {len(df)} drivers")
    return df


# ══════════════════════════════════════════════
# SOURCE 2: OpenF1 API
# Recent/live race data, driver intervals
# ══════════════════════════════════════════════
def fetch_openf1_sessions(year: int) -> pd.DataFrame:
    """Fetch session data from OpenF1 for a given year."""
    url = f"{OPENF1_BASE}/sessions?year={year}"
    cache_key = f"openf1_sessions_{year}"
    data = _cached_get(url, cache_key)
    if data is None or not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)
    print(f"  [OpenF1] {year}: {len(df)} sessions found")
    return df


def fetch_openf1_positions(session_key: int) -> pd.DataFrame:
    """Fetch position data for a specific session from OpenF1."""
    url = f"{OPENF1_BASE}/position?session_key={session_key}"
    cache_key = f"openf1_positions_{session_key}"
    data = _cached_get(url, cache_key)
    if data is None or not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


def fetch_openf1_drivers(session_key: int) -> pd.DataFrame:
    """Fetch driver info for a specific session from OpenF1."""
    url = f"{OPENF1_BASE}/drivers?session_key={session_key}"
    cache_key = f"openf1_drivers_{session_key}"
    data = _cached_get(url, cache_key)
    if data is None or not isinstance(data, list):
        return pd.DataFrame()
    return pd.DataFrame(data)


# ══════════════════════════════════════════════
# SOURCE 3: FastF1
# Detailed telemetry, lap times, car data
# ══════════════════════════════════════════════
def fetch_fastf1_results(season: int, round_num: int) -> pd.DataFrame:
    """Fetch race results via FastF1 (includes detailed timing)."""
    if not FASTF1_AVAILABLE:
        return pd.DataFrame()
    try:
        ff1_cache = CACHE_DIR / "fastf1_cache"
        ff1_cache.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(ff1_cache))
        session = fastf1.get_session(season, round_num, "R")
        session.load(telemetry=False, weather=False, messages=False)
        results = session.results
        if results is None or results.empty:
            return pd.DataFrame()

        df = results[["DriverNumber", "Abbreviation", "FullName", "TeamName",
                       "GridPosition", "Position", "Points", "Status", "Time"]].copy()
        df.columns = ["driver_number", "abbreviation", "driver", "team",
                       "grid_position", "finish_position", "points", "status", "race_time"]
        df["season"] = season
        df["round"] = round_num
        print(f"  [FastF1] {season} R{round_num}: {len(df)} drivers")
        return df
    except Exception as e:
        print(f"  [FastF1] Failed for {season} R{round_num}: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════
# SOURCE 4: Web Scraping (Supplementary)
# Wikipedia F1 2026 season page for confirmation
# ══════════════════════════════════════════════
def scrape_f1_wiki_standings() -> pd.DataFrame:
    """Scrape the 2026 F1 season Wikipedia page for latest standings."""
    if not BS4_AVAILABLE:
        return pd.DataFrame()
    try:
        url = "https://en.wikipedia.org/wiki/2026_Formula_One_World_Championship"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Try to find the drivers' championship standings table
        tables = soup.find_all("table", class_="wikitable")
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Driver" in headers and ("Pts" in headers or "Points" in headers):
                rows = []
                for tr in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if len(cells) >= 3:
                        rows.append(cells)
                if rows:
                    df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
                    print(f"  [Wiki] Scraped standings table with {len(df)} rows")
                    return df
        print("  [Wiki] No standings table found")
        return pd.DataFrame()
    except Exception as e:
        print(f"  [Wiki] Scraping failed: {e}")
        return pd.DataFrame()


# ══════════════════════════════════════════════
# MASTER COLLECTION PIPELINE
# ══════════════════════════════════════════════
def collect_all_data(force_refresh: bool = False) -> dict:
    """
    Master function: collects data from all sources and returns
    a dict of DataFrames keyed by data type.
    """
    print("=" * 60)
    print("F1 2026 PREDICTIVE MODEL — DATA COLLECTION")
    print("=" * 60)

    output_dir = Path(__file__).parent / "data"
    
    # If force refresh, clear the local JSON cache to guarantee fresh API hits
    if force_refresh:
        print("[INFO] Force refresh enabled. Clearing local JSON caches...")
        import shutil
        if CACHE_DIR.exists():
            for item in CACHE_DIR.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
    
    # ── Try to load from static CSV cache first ──
    if not force_refresh:
        try:
            results_path = output_dir / "race_results.csv"
            quali_path = output_dir / "qualifying.csv"
            standings_path = output_dir / "standings.csv"
            
            if results_path.exists() and quali_path.exists() and standings_path.exists():
                print("\n[INFO] Loading pre-compiled datasets from CSV cache...")
                combined_results = pd.read_csv(results_path)
                combined_qualifying = pd.read_csv(quali_path)
                combined_standings = pd.read_csv(standings_path)
                
                # Fetch only minimal live OpenF1 data since it's fast
                print("[INFO] Fetching fast live data from OpenF1...")
                openf1_sessions = fetch_openf1_sessions(CURRENT_SEASON)
                
                dataset = {
                    "results": combined_results,
                    "qualifying": combined_qualifying,
                    "standings": combined_standings,
                    "openf1_sessions": openf1_sessions,
                    "fastf1_results": pd.DataFrame(),
                    "wiki_standings": pd.DataFrame(),
                }
                print("\n[INFO] Data loaded instantly from cache.")
                return dataset
        except Exception as e:
            print(f"[WARN] Failed to load from CSV cache: {e}. Falling back to API collection.")

    all_results = []
    all_qualifying = []
    all_standings = []

    # ── Historical data (2023-2025) from Jolpica ──
    print("\n[Phase 1] Fetching historical data from Jolpica API...")
    for season in HISTORICAL_SEASONS:
        results = fetch_season_results_jolpica(season)
        if not results.empty:
            all_results.append(results)

        quali = fetch_qualifying_jolpica(season)
        if not quali.empty:
            all_qualifying.append(quali)

        standings = fetch_driver_standings_jolpica(season)
        if not standings.empty:
            all_standings.append(standings)

    # ── 2026 data from Jolpica (if available) ──
    print(f"\n[Phase 2] Fetching {CURRENT_SEASON} data from Jolpica...")
    results_2026 = fetch_season_results_jolpica(CURRENT_SEASON)
    if not results_2026.empty:
        all_results.append(results_2026)

    quali_2026 = fetch_qualifying_jolpica(CURRENT_SEASON)
    if not quali_2026.empty:
        all_qualifying.append(quali_2026)

    standings_2026 = fetch_driver_standings_jolpica(CURRENT_SEASON)
    if not standings_2026.empty:
        all_standings.append(standings_2026)

    # ── 2026 data from OpenF1 ──
    print(f"\n[Phase 3] Fetching {CURRENT_SEASON} data from OpenF1...")
    openf1_sessions = fetch_openf1_sessions(CURRENT_SEASON)

    # ── 2026 data from FastF1 ──
    print(f"\n[Phase 4] Fetching {CURRENT_SEASON} data from FastF1...")
    fastf1_results = []
    for rnd in range(1, COMPLETED_ROUNDS_2026 + 1):
        ff1_df = fetch_fastf1_results(CURRENT_SEASON, rnd)
        if not ff1_df.empty:
            fastf1_results.append(ff1_df)

    # ── Supplementary Wikipedia scrape ──
    print(f"\n[Phase 5] Scraping Wikipedia for supplementary data...")
    wiki_standings = scrape_f1_wiki_standings()

    # ── Consolidate ──
    print("\n[Phase 6] Consolidating datasets...")
    combined_results = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
    combined_qualifying = pd.concat(all_qualifying, ignore_index=True) if all_qualifying else pd.DataFrame()
    combined_standings = pd.concat(all_standings, ignore_index=True) if all_standings else pd.DataFrame()
    combined_fastf1 = pd.concat(fastf1_results, ignore_index=True) if fastf1_results else pd.DataFrame()

    # Save consolidated data
    # Save consolidated data
    output_dir.mkdir(exist_ok=True)
    if not combined_results.empty:
        combined_results.to_csv(output_dir / "race_results.csv", index=False)
    if not combined_qualifying.empty:
        combined_qualifying.to_csv(output_dir / "qualifying.csv", index=False)
    if not combined_standings.empty:
        combined_standings.to_csv(output_dir / "standings.csv", index=False)

    dataset = {
        "results": combined_results,
        "qualifying": combined_qualifying,
        "standings": combined_standings,
        "openf1_sessions": openf1_sessions,
        "fastf1_results": combined_fastf1,
        "wiki_standings": wiki_standings,
    }

    total_rows = sum(len(v) for v in dataset.values() if isinstance(v, pd.DataFrame))
    print(f"\n{'=' * 60}")
    print(f"DATA COLLECTION COMPLETE — {total_rows} total rows across all sources")
    print(f"{'=' * 60}")

    return dataset


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    dataset = collect_all_data()
    for name, df in dataset.items():
        if isinstance(df, pd.DataFrame):
            print(f"  {name}: {df.shape}")
