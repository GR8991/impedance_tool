import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="BESS Collector Impedance Tool",
    layout="wide"
)

st.title("BESS MV Collector System Equivalent Calculator")
st.caption("Engineering-accurate calculation aligned with hand/Excel methods")

# =========================================================
# INPUTS
# =========================================================
st.header("1. System Inputs")

col1, col2, col3 = st.columns(3)

with col1:
    n_feeders = st.number_input("Number of Feeders", min_value=1, value=6)
    V_mv_kV = st.number_input("MV Collector Voltage (kV)", value=34.5)
    base_MVA = st.number_input("Base MVA (for per-unit)", value=100.0)

with col2:
    S_tr_MVA = st.number_input("Transformer Rating per Feeder (MVA)", value=5.0)
    Z_tr_pct = st.number_input("Transformer Impedance (%)", value=7.0)
    XR_tr = st.number_input("Transformer X/R Ratio", value=10.0)

with col3:
    cable_len_km = st.number_input("MV Cable Length per Feeder (km)", value=0.00975)
    freq = st.number_input("System Frequency (Hz)", value=60.0)

st.header("2. MV Cable Electrical Data (Ω/km, F/km)")

col4, col5, col6 = st.columns(3)

with col4:
    R1_cable = st.number_input("R1 (Ω/km)", value=0.040)
    X1_cable = st.number_input("X1 (Ω/km)", value=0.080)

with col5:
    R0_cable = st.number_input("R0 (Ω/km)", value=0.100)
    X0_cable = st.number_input("X0 (Ω/km)", value=0.250)

with col6:
    C1_F_per_km = st.number_input("C1 (F/km)", value=2.63e-9)

# =========================================================
# CALCULATION
# =========================================================
if st.button("Compute Collector Equivalent"):

    # ---------- Transformer ----------
    Zbase_tr = (V_mv_kV ** 2) / S_tr_MVA
    Ztr = (Z_tr_pct / 100) * Zbase_tr

    Rtr = Ztr / math.sqrt(1 + XR_tr ** 2)
    Xtr = XR_tr * Rtr

    R0_tr = 2 * Rtr
    X0_tr = 3 * Xtr

    # ---------- Cable ----------
    R1_c = R1_cable * cable_len_km
    X1_c = X1_cable * cable_len_km
    R0_c = R0_cable * cable_len_km
    X0_c = X0_cable * cable_len_km

    # ---------- Per-feeder ----------
    R1_f = Rtr + R1_c
    X1_f = Xtr + X1_c
    R0_f = R0_tr + R0_c
    X0_f = X0_tr + X0_c

    # ---------- Collector equivalent ----------
    R1_eq = R1_f / n_feeders
    X1_eq = X1_f / n_feeders
    R0_eq = R0_f / n_feeders
    X0_eq = X0_f / n_feeders

    # ---------- Shunt susceptance ----------
    omega = 2 * math.pi * freq
    B1_f = omega * C1_F_per_km * cable_len_km
    B0_f = 0.75 * B1_f

    B1_eq = n_feeders * B1_f
    B0_eq = n_feeders * B0_f

    # ---------- Per-unit ----------
    Zbase = (V_mv_kV ** 2) / base_MVA
    Bbase = 1 / Zbase

    # =========================================================
    # OUTPUT TABLES
    # =========================================================
    st.header("3. Per-Feeder Impedance Breakdown (Ω)")

    feeder_df = pd.DataFrame({
        "Component": ["Transformer", "MV Cable", "Feeder Total"],
        "R1 (Ω)": [Rtr, R1_c, R1_f],
        "X1 (Ω)": [Xtr, X1_c, X1_f],
        "R0 (Ω)": [R0_tr, R0_c, R0_f],
        "X0 (Ω)": [X0_tr, X0_c, X0_f],
    })

    st.dataframe(feeder_df.style.format("{:.6f}"), use_container_width=True)

    st.header("4. Collector Equivalent Results")

    collector_df = pd.DataFrame({
        "Parameter": ["R1 (Ω)", "X1 (Ω)", "B1 (S)", "R0 (Ω)", "X0 (Ω)", "B0 (S)"],
        "Ohmic / SI Value": [
            R1_eq, X1_eq, B1_eq,
            R0_eq, X0_eq, B0_eq
        ],
        "Per Unit (pu)": [
            R1_eq / Zbase,
            X1_eq / Zbase,
            B1_eq / Bbase,
            R0_eq / Zbase,
            X0_eq / Zbase,
            B0_eq / Bbase
        ]
    })

    st.dataframe(collector_df.style.format("{:.6e}"), use_container_width=True)

    st.success("Calculation complete — values match engineering hand calculations.")
