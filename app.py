"""
app.py
======
Streamlit dashboard for the F1 2026 Predictive Model.
Displays predicted race results, feature importance, and team analytics.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config_2026 import (
    GRID_2026, TEAM_COLORS, DRIVER_TO_TEAM, DRIVER_TO_ENGINE,
    PU_RATINGS, ACTIVE_AERO_RATINGS, DRIVER_RATINGS,
    DRIVER_SPECIFICS, TRACK_PROFILES, REG_WEIGHTS,
    CALENDAR_2026, NEXT_RACE_NAME, NEXT_RACE_ROUND,
    COMPLETED_ROUNDS_2026,
)
from model import run_full_pipeline, predict_race, load_model, predict_remaining_season
from data_collector import collect_all_data
from feature_engineering import build_race_feature_matrix, FEATURE_COLS

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="F1 2026 Predictive Engine",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS for premium dark theme
# ──────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* Main background */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #111122 50%, #0a0a1a 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d1a 0%, #15152a 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    /* Hero title */
    .hero-title {
        font-size: 3.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #E8002D 0%, #FF6B35 40%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
        line-height: 1.1;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.5);
        text-align: center;
        margin-top: 4px;
        font-weight: 300;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    /* Glass card */
    .glass-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(255,255,255,0.15);
        background: rgba(255,255,255,0.05);
    }

    /* Podium cards */
    .podium-card {
        text-align: center;
        padding: 28px 16px;
        border-radius: 20px;
        margin: 4px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .podium-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }
    .p1-card {
        background: linear-gradient(180deg, rgba(255,215,0,0.15) 0%, rgba(255,215,0,0.03) 100%);
        border: 1px solid rgba(255,215,0,0.3);
    }
    .p2-card {
        background: linear-gradient(180deg, rgba(192,192,192,0.12) 0%, rgba(192,192,192,0.03) 100%);
        border: 1px solid rgba(192,192,192,0.25);
    }
    .p3-card {
        background: linear-gradient(180deg, rgba(205,127,50,0.12) 0%, rgba(205,127,50,0.03) 100%);
        border: 1px solid rgba(205,127,50,0.2);
    }
    .position-num {
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 4px;
    }
    .driver-name {
        font-size: 1.25rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 4px;
    }
    .team-name {
        font-size: 0.85rem;
        font-weight: 400;
        opacity: 0.6;
    }

    /* Results table row */
    .result-row {
        display: flex;
        align-items: center;
        padding: 10px 16px;
        border-radius: 10px;
        margin: 4px 0;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.04);
        transition: all 0.2s ease;
    }
    .result-row:hover {
        background: rgba(255,255,255,0.06);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 16px;
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.06);
        padding: 8px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(232,0,45,0.2), rgba(255,107,53,0.15));
        border-color: rgba(232,0,45,0.4);
    }

    /* Separator */
    .separator {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 32px 0;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    selected_track = st.selectbox(
        "🏁 Select Track",
        options=list(CALENDAR_2026.values()),
        index=list(CALENDAR_2026.values()).index(NEXT_RACE_NAME)
        if NEXT_RACE_NAME in CALENDAR_2026.values() else 0,
        key="track_select",
    )

    st.markdown("---")
    st.markdown("### 📊 Data Sources")
    st.markdown("""
    <div class="glass-card" style="padding:12px 16px; font-size:0.82rem;">
        ✅ Jolpica API (Ergast)<br>
        ✅ OpenF1 API<br>
        ✅ FastF1 Telemetry<br>
        ✅ Wikipedia Scraping
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔧 2026 Regulation Weights")
    for key, val in REG_WEIGHTS.items():
        nice_key = key.replace("_weight", "").replace("_", " ").title()
        st.slider(nice_key, 0.0, 1.0, val, 0.05, key=f"w_{key}", disabled=True)

    st.markdown("---")
    force_refresh = st.checkbox("🔄 Force Fetch New Data (APIs)", value=False, help="Enable this to download the latest race results from the internet instead of using cached data.")
    run_button = st.button("🚀 Run Prediction Pipeline", type="primary", use_container_width=True)


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown('<p class="hero-title">F1 2026 PREDICTIVE ENGINE</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">XGBoost · Active Aero · 350kW MGU-K · Multi-Source Intelligence</p>',
            unsafe_allow_html=True)
st.markdown('<div class="separator"></div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Run pipeline
# ──────────────────────────────────────────────
def run_pipeline(force: bool = False):
    """Run the full ML pipeline."""
    return run_full_pipeline(force_refresh=force)


def get_track_prediction(_model, track_name, _results_df):
    """Get prediction for a specific track."""
    return predict_race(_model, track_name, _results_df)


# State initialization
if "pipeline_run" not in st.session_state:
    st.session_state.pipeline_run = False
if "model" not in st.session_state:
    st.session_state.model = None

if run_button or st.session_state.pipeline_run:
    if not st.session_state.pipeline_run or run_button:
        with st.spinner("🔄 Loading datasets & running XGBoost model..."):
            try:
                model, predictions, fi_df, eval_metrics = run_pipeline(force=force_refresh)
                st.session_state.model = model
                st.session_state.predictions = predictions
                st.session_state.fi_df = fi_df
                st.session_state.eval_metrics = eval_metrics
                st.session_state.pipeline_run = True
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

    # If user changed the track, re-predict
    if selected_track != NEXT_RACE_NAME and st.session_state.model is not None:
        with st.spinner(f"Predicting {selected_track}..."):
            dataset = collect_all_data()
            predictions = predict_race(st.session_state.model, selected_track, dataset["results"])
            st.session_state.predictions = predictions

    predictions = st.session_state.predictions
    fi_df = st.session_state.fi_df
    eval_metrics = st.session_state.eval_metrics

    # ── Metrics row ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏁 Track", selected_track)
    with col2:
        st.metric("📈 Model MAE",
                   f"{eval_metrics['cv_mae']:.2f} pos" if eval_metrics.get('cv_mae') else "N/A")
    with col3:
        st.metric("📊 Training Samples", eval_metrics.get("n_training_samples", 0))
    with col4:
        st.metric("👥 Grid Size", len(predictions))

    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏆 Race Prediction", "📊 Feature Analysis",
        "🔬 Team Comparison", "📅 Season Outlook"
    ])

    # ──────────────────────────────────────────
    # TAB 1: Race Prediction
    # ──────────────────────────────────────────
    with tab1:
        st.markdown(f"### 🏆 Predicted Result — {selected_track} Grand Prix")

        # Podium
        top3 = predictions.head(3)
        pcols = st.columns([1, 1.3, 1])

        # P2 - left
        with pcols[0]:
            d = top3.iloc[1]
            team_color = TEAM_COLORS.get(d["team"], "#666")
            st.markdown(f"""
            <div class="podium-card p2-card">
                <div class="position-num" style="color: silver;">P2</div>
                <div class="driver-name">{d['driver']}</div>
                <div class="team-name" style="color: {team_color};">{d['team']}</div>
                <div style="margin-top:8px; font-size:1.1rem; font-weight:600;">18 PTS</div>
            </div>
            """, unsafe_allow_html=True)

        # P1 - center (larger)
        with pcols[1]:
            d = top3.iloc[0]
            team_color = TEAM_COLORS.get(d["team"], "#666")
            st.markdown(f"""
            <div class="podium-card p1-card">
                <div class="position-num" style="color: gold;">👑 P1</div>
                <div class="driver-name" style="font-size:1.5rem;">{d['driver']}</div>
                <div class="team-name" style="color: {team_color}; font-size:0.95rem;">{d['team']}</div>
                <div style="margin-top:8px; font-size:1.3rem; font-weight:700; color: gold;">25 PTS</div>
            </div>
            """, unsafe_allow_html=True)

        # P3 - right
        with pcols[2]:
            d = top3.iloc[2]
            team_color = TEAM_COLORS.get(d["team"], "#666")
            st.markdown(f"""
            <div class="podium-card p3-card">
                <div class="position-num" style="color: #CD7F32;">P3</div>
                <div class="driver-name">{d['driver']}</div>
                <div class="team-name" style="color: {team_color};">{d['team']}</div>
                <div style="margin-top:8px; font-size:1.1rem; font-weight:600;">15 PTS</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Full results table
        st.markdown("### 📋 Full Predicted Grid")
        display_df = predictions[["predicted_position", "driver", "team", "engine",
                                   "predicted_points", "predicted_score"]].copy()
        display_df.columns = ["Pos", "Driver", "Team", "Engine", "Points", "Model Score"]
        display_df["Pos"] = display_df["Pos"].astype(int)
        display_df["Points"] = display_df["Points"].astype(int)
        display_df["Model Score"] = display_df["Model Score"].round(2)

        # Color-code by team
        def color_team(row):
            color = TEAM_COLORS.get(row["Team"], "#666666")
            return [f"border-left: 4px solid {color}; background: rgba(255,255,255,0.02);"] * len(row)

        styled = display_df.style.apply(color_team, axis=1)
        st.dataframe(styled, use_container_width=True, height=600, hide_index=True)

    # ──────────────────────────────────────────
    # TAB 2: Feature Analysis
    # ──────────────────────────────────────────
    with tab2:
        st.markdown("### 📊 Feature Importance — What Drives the Predictions?")

        # Horizontal bar chart
        fig_fi = px.bar(
            fi_df,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale=["#1a1a2e", "#E8002D", "#FFD700"],
            labels={"importance": "Importance Score", "feature": "Feature"},
        )
        fig_fi.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=13),
            height=500,
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_fi, use_container_width=True)

        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Radar chart: top 5 drivers' feature profiles
        st.markdown("### 🎯 Driver Feature Radar — Top 5")
        top5 = predictions.head(5)
        radar_features = ["ice_power", "mguk_advantage", "aero_track_score",
                          "override_adjusted", "tyre_mgmt", "form_score"]
        radar_labels = ["ICE Power", "MGU-K Advantage", "Active Aero",
                        "Override Mode", "Tyre Mgmt", "Historical Form"]

        # Helper to convert hex to rgba
        def hex_to_rgba(hex_color, alpha=0.15):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                return f"rgba({r}, {g}, {b}, {alpha})"
            return hex_color

        fig_radar = go.Figure()
        for _, row in top5.iterrows():
            values = [row[f] for f in radar_features]
            values.append(values[0])  # close the polygon
            team_color = TEAM_COLORS.get(row["team"], "#666")
            fig_radar.add_trace(go.Scatterpolar(
                r=values,
                theta=radar_labels + [radar_labels[0]],
                fill="toself",
                name=row["driver"],
                line=dict(color=team_color, width=2),
                fillcolor=hex_to_rgba(team_color, 0.15),
            ))

        fig_radar.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=12),
            height=500,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(range=[0, 1], showticklabels=False),
            ),
            legend=dict(font=dict(size=13)),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ──────────────────────────────────────────
    # TAB 3: Team Comparison
    # ──────────────────────────────────────────
    with tab3:
        st.markdown("### 🔬 2026 Team Power Analysis")

        # PU Ratings chart
        pu_rows = []
        for eng, stats in PU_RATINGS.items():
            pu_rows.append({"Engine": eng, "Component": "ICE Power", "Rating": stats["ice"]})
            pu_rows.append({"Engine": eng, "Component": "MGU-K Deploy", "Rating": stats["mguk_deploy"]})
            pu_rows.append({"Engine": eng, "Component": "MGU-K Recover", "Rating": stats["mguk_recover"]})
        pu_df = pd.DataFrame(pu_rows)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### ⚡ 2026 Power Unit (ICE vs MGU-K)")
            fig_pu = px.bar(
                pu_df, x="Rating", y="Engine", color="Component", orientation="h",
                barmode="group",
                color_discrete_sequence=["#E8002D", "#27F4D2", "#FFD700"],
                range_x=[60, 100],
            )
            fig_pu.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_pu, use_container_width=True)

        with col_right:
            st.markdown("#### 🌀 Active Aero Efficiency")
            aero_df = pd.DataFrame([
                {"Team": team, "Rating": rating}
                for team, rating in ACTIVE_AERO_RATINGS.items()
            ]).sort_values("Rating", ascending=True)

            fig_aero = px.bar(
                aero_df, x="Rating", y="Team", orientation="h",
                color="Rating",
                color_continuous_scale=["#1a1a2e", "#FF8000", "#FFD700"],
                range_x=[50, 100],
            )
            fig_aero.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter"),
                height=350,
                showlegend=False,
            )
            st.plotly_chart(fig_aero, use_container_width=True)

        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Driver ratings scatter
        from config_2026 import DRIVER_SPECIFICS
        st.markdown("#### 🏎️ Tyre Management vs Override Potential")
        driver_comp = pd.DataFrame([
            {
                "Driver": driver,
                "Team": DRIVER_TO_TEAM.get(driver, "?"),
                "TyreMgmt": DRIVER_SPECIFICS.get(driver, {}).get("tyre_mgmt", 70),
                "Override": DRIVER_SPECIFICS.get(driver, {}).get("override_pot", 0.5) * 100,
                "Color": TEAM_COLORS.get(DRIVER_TO_TEAM.get(driver, ""), "#666"),
            }
            for driver in DRIVER_SPECIFICS.keys()
        ])

        fig_scatter = px.scatter(
            driver_comp, x="TyreMgmt", y="Override",
            text="Driver", color="Team",
            color_discrete_map={t: c for t, c in TEAM_COLORS.items()},
            size=[20] * len(driver_comp),
        )
        fig_scatter.update_traces(textposition="top center", textfont_size=10)
        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
            height=500,
            xaxis_title="Tyre Management Skill (1-100)",
            yaxis_title="Override Mode Potential (%)",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ──────────────────────────────────────────
    # TAB 4: Season Outlook
    # ──────────────────────────────────────────
    with tab4:
        st.markdown("### 📅 Track-by-Track Analysis")

        # Show track profiles
        track_df = pd.DataFrame([
            {
                "Track": track,
                "Country": info["country"],
                "X-Mode": info["x_mode_weight"],
                "Z-Mode": info["z_mode_weight"],
                "Mech Grip": info["mechanical_grip"],
                "Overtaking": info["overtaking_opportunity"],
            }
            for track, info in TRACK_PROFILES.items()
        ])

        fig_tracks = px.bar(
            track_df.melt(id_vars=["Track", "Country"],
                          value_vars=["X-Mode", "Z-Mode", "Mech Grip", "Overtaking"]),
            x="Track", y="value", color="variable",
            barmode="group",
            color_discrete_sequence=["#E8002D", "#3671C6", "#27F4D2", "#FF8000"],
            labels={"value": "Weight", "variable": "Characteristic"},
        )
        fig_tracks.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
            height=450,
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig_tracks, use_container_width=True)

        st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

        # Calendar with status
        st.markdown("### 🗓️ 2026 Calendar Status")
        cal_rows = []
        for rnd, track in CALENDAR_2026.items():
            status = "✅ Completed" if rnd <= COMPLETED_ROUNDS_2026 else (
                "🔮 Next Race" if rnd == NEXT_RACE_ROUND else "⏳ Upcoming"
            )
            country = TRACK_PROFILES.get(track, {}).get("country", "")
            cal_rows.append({
                "Round": rnd,
                "Track": track,
                "Country": country,
                "Status": status,
            })
        cal_df = pd.DataFrame(cal_rows)
        st.dataframe(cal_df, use_container_width=True, hide_index=True, height=400)

else:
    # ── Landing page when pipeline hasn't run yet ──
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 60px 40px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">🏎️</div>
        <h2 style="color: #fff; margin-bottom: 8px;">Ready to Predict</h2>
        <p style="color: rgba(255,255,255,0.5); font-size: 1.1rem; max-width: 500px; margin: 0 auto;">
            Click <strong>"Run Prediction Pipeline"</strong> in the sidebar to collect data
            from 4 sources, train the XGBoost model, and generate race predictions.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)

    # Show the 2026 grid
    st.markdown("### 🏁 2026 Grid Overview")
    grid_cols = st.columns(3)
    for i, (team, info) in enumerate(GRID_2026.items()):
        with grid_cols[i % 3]:
            color = info["team_color"]
            drivers = " & ".join(info["drivers"])
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid {color};">
                <div style="font-weight: 700; font-size: 1rem; color: {color};">{team}</div>
                <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7); margin-top: 4px;">{drivers}</div>
                <div style="font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 4px;">🔧 {info['engine']}</div>
            </div>
            """, unsafe_allow_html=True)
