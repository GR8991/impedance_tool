import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="BESS MV Collector Tool", layout="wide")
st.title("BESS MV Collector System Impedance Tool")

# ======================================================
# 1. SYSTEM BASE
# ======================================================
st.header("1. System Base")

c1, c2, c3 = st.columns(3)
V_kV = c1.number_input("Collector Bus Voltage (kV)", value=34.5)
S_base = c2.number_input("System Base MVA", value=100.0)
freq = c3.number_input("Frequency (Hz)", value=60.0)

Z_base = (V_kV**2) / S_base
B_base = 1 / Z_base

# ======================================================
# 2. FEEDER CONFIGURATION
# ======================================================
st.header("2. Feeder Configuration")

c1, c2, c3 = st.columns(3)
n_feeders = c1.number_input("Number of Feeders", value=6, step=1)
n_tr = c2.number_input("Transformers per Feeder", value=5, step=1)
tr_mva = c3.number_input("Transformer Rating (MVA)", value=5.0)

c1, c2 = st.columns(2)
tr_z_pct = c1.number_input("Transformer Impedance (%)", value=7.0)
tr_xr = c2.number_input("Transformer X/R Ratio", value=10.0)

# ======================================================
# 3. MV CABLE DATA
# ======================================================
st.header("3. MV Cable Data")

c1, c2, c3 = st.columns(3)
R1_km = c1.number_input("Cable R1 (Ω/km)", value=0.040)
X1_km = c2.number_input("Cable X1 (Ω/km)", value=0.080)
C1_km = c3.number_input("Cable Capacitance C1 (µF/km)", value=0.27)

c1, c2 = st.columns(2)
R0_km = c1.number_input("Cable R0 (Ω/km)", value=0.100)
X0_km = c2.number_input("Cable X0 (Ω/km)", value=0.250)

length_ft = st.number_input("Cable Length (ft)", value=32.0)
length_km = length_ft * 0.0003048

# ======================================================
# 4. CALCULATIONS
# ======================================================

# Transformer impedance (per transformer)
Z_tr_base = (V_kV**2) / tr_mva
Z_tr = (tr_z_pct / 100) * Z_tr_base

R_tr = Z_tr / np.sqrt(1 + tr_xr**2)
X_tr = R_tr * tr_xr

# Transformer per feeder
R1_tr = n_tr * R_tr
X1_tr = n_tr * X_tr
R0_tr = 2 * R1_tr
X0_tr = 3 * X1_tr

# MV cable per feeder
R1_cab = R1_km * length_km
X1_cab = X1_km * length_km
R0_cab = R0_km * length_km
X0_cab = X0_km * length_km

# Feeder equivalent (series)
R1_fd = R1_tr + R1_cab
X1_fd = X1_tr + X1_cab
R0_fd = R0_tr + R0_cab
X0_fd = X0_tr + X0_cab

# Collector equivalent (parallel feeders)
R1_eq = R1_fd / n_feeders
X1_eq = X1_fd / n_feeders
R0_eq = R0_fd / n_feeders
X0_eq = X0_fd / n_feeders

# Shunt susceptance (MV cable only)
omega = 2 * np.pi * freq
C_total = C1_km * 1e-6 * length_km
B1 = omega * C_total * n_feeders
B0 = 0.75 * B1

# ======================================================
# 5. RESULTS – PER FEEDER BREAKDOWN
# ======================================================
st.header("4. Per-Feeder Impedance Breakdown (Ohms)")

df_feeder = pd.DataFrame({
    "Component": ["Transformer", "MV Cable", "Feeder Total"],
    "R1 (Ω)": [R1_tr, R1_cab, R1_fd],
    "X1 (Ω)": [X1_tr, X1_cab, X1_fd],
    "R0 (Ω)": [R0_tr, R0_cab, R0_fd],
    "X0 (Ω)": [X0_tr, X0_cab, X0_fd],
})

st.dataframe(df_feeder, use_container_width=True)

# ======================================================
# 6. RESULTS – COLLECTOR EQUIVALENT
# ======================================================
st.header("5. Collector Equivalent Results")

df_col = pd.DataFrame({
    "Parameter": ["R1 (Ω)", "X1 (Ω)", "B1 (S)", "R0 (Ω)", "X0 (Ω)", "B0 (S)"],
    "Ohmic Value": [R1_eq, X1_eq, B1, R0_eq, X0_eq, B0],
    "Per Unit (pu)": [
        R1_eq / Z_base,
        X1_eq / Z_base,
        B1 / B_base,
        R0_eq / Z_base,
        X0_eq / Z_base,
        B0 / B_base
    ]
})

st.dataframe(df_col, use_container_width=True)

# ======================================================
# 7. INTERCONNECTION FORM BLOCK
# ======================================================
st.header("6. Interconnection Form (Copy & Paste) — Collector Equivalent")

st.code(f"""
Collector system voltage = {V_kV:.2f} kV
Collector equivalent rating = {S_base:.1f} MVA

R1 = {R1_eq:.4f} ohm or {R1_eq/Z_base:.5f} pu
X1 = {X1_eq:.4f} ohm or {X1_eq/Z_base:.5f} pu
B1 = {B1*1e6:.4f} µF or {B1/B_base:.5e} pu

R0 = {R0_eq:.4f} ohm or {R0_eq/Z_base:.5f} pu
X0 = {X0_eq:.4f} ohm or {X0_eq/Z_base:.5f} pu
B0 = {B0*1e6:.4f} µF or {B0/B_base:.5e} pu
""")
