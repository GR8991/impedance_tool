import streamlit as st
import numpy as np
import pandas as pd

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="BESS MV Collector Impedance Tool",
    layout="wide"
)

st.title("BESS MV Collector System Equivalent Impedance Tool")
st.caption("Utility-grade calculation aligned with ETAP / PSS®E practices")

# -------------------------------------------------
# Base Inputs
# -------------------------------------------------
st.header("1. System Base")

c1, c2, c3 = st.columns(3)
V_kV = c1.number_input("Collector Bus Voltage (kV)", value=34.5)
S_base = c2.number_input("System Base MVA", value=100.0)
freq = c3.number_input("Frequency (Hz)", value=60.0)

Z_base = (V_kV ** 2) / S_base
B_base = 1 / Z_base

# -------------------------------------------------
# Feeder Inputs
# -------------------------------------------------
st.header("2. Feeder Configuration")

c1, c2, c3 = st.columns(3)
n_feeders = c1.number_input("Number of Feeders", min_value=1, step=1, value=6)
n_tr = c2.number_input("Transformers per Feeder", min_value=1, step=1, value=5)
tr_mva = c3.number_input("Transformer Rating (MVA)", value=5.0)

c1, c2 = st.columns(2)
tr_z_pct = c1.number_input("Transformer Impedance (%)", value=7.0)
tr_xr = c2.number_input("Transformer X/R Ratio", value=10.0)

# -------------------------------------------------
# MV Cable Inputs
# -------------------------------------------------
st.header("3. MV Cable Data")

c1, c2, c3 = st.columns(3)
R1_km = c1.number_input("Cable R1 (Ω/km)", value=0.040)
X1_km = c2.number_input("Cable X1 (Ω/km)", value=0.080)
C1_km = c3.number_input("Cable Capacitance C1 (µF/km)", value=0.27)

c1, c2 = st.columns(2)
R0_km = c1.number_input("Cable R0 (Ω/km)", value=0.100)
X0_km = c2.number_input("Cable X0 (Ω/km)", value=0.250)

length_unit = st.selectbox("Cable Length Unit", ["km", "ft"])
length_val = st.number_input("Cable Length", value=32.0)

if length_unit == "ft":
    length_km = length_val * 0.0003048
else:
    length_km = length_val

# -------------------------------------------------
# Calculations
# -------------------------------------------------
# Transformer impedance
Z_tr_base = (V_kV ** 2) / tr_mva
Z_tr = (tr_z_pct / 100) * Z_tr_base

R_tr = Z_tr / np.sqrt(1 + tr_xr ** 2)
X_tr = R_tr * tr_xr

# Per feeder impedance
R1_feeder = n_tr * R_tr + R1_km * length_km
X1_feeder = n_tr * X_tr + X1_km * length_km

# Zero sequence assumptions (utility-standard)
R0_feeder = 2 * R1_feeder + R0_km * length_km
X0_feeder = 3 * X1_feeder + X0_km * length_km

# Collector equivalent (parallel feeders)
R1_eq = R1_feeder / n_feeders
X1_eq = X1_feeder / n_feeders
R0_eq = R0_feeder / n_feeders
X0_eq = X0_feeder / n_feeders

# Shunt susceptance (cable only)
C_total = C1_km * 1e-6 * length_km
omega = 2 * np.pi * freq

B1 = omega * C_total * n_feeders
B0 = 0.75 * B1

# Per-unit
R1_pu = R1_eq / Z_base
X1_pu = X1_eq / Z_base
R0_pu = R0_eq / Z_base
X0_pu = X0_eq / Z_base
B1_pu = B1 / B_base
B0_pu = B0 / B_base

# -------------------------------------------------
# Results
# -------------------------------------------------
st.header("4. Collector Equivalent Results")

df = pd.DataFrame({
    "Parameter": [
        "R1 (Ω)", "X1 (Ω)", "B1 (S)",
        "R0 (Ω)", "X0 (Ω)", "B0 (S)"
    ],
    "Ohmic Value": [
        R1_eq, X1_eq, B1,
        R0_eq, X0_eq, B0
    ],
    "Per Unit (pu)": [
        R1_pu, X1_pu, B1_pu,
        R0_pu, X0_pu, B0_pu
    ]
})

st.table(df)

# -------------------------------------------------
# Interconnection Form Block
# -------------------------------------------------
st.header("5. Interconnection Form (Copy–Paste)")

st.code(f"""
Collector Voltage = {V_kV:.2f} kV
Collector Rating  = {S_base:.1f} MVA

R1 = {R1_eq:.4f} Ω  ({R1_pu:.5f} pu)
X1 = {X1_eq:.4f} Ω  ({X1_pu:.5f} pu)
B1 = {B1:.3e} S  ({B1_pu:.3e} pu)

R0 = {R0_eq:.4f} Ω  ({R0_pu:.5f} pu)
X0 = {X0_eq:.4f} Ω  ({X0_pu:.5f} pu)
B0 = {B0:.3e} S  ({B0_pu:.3e} pu)
""")
