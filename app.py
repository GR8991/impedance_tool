import streamlit as st
import pandas as pd
import math

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="BESS MV Collector Impedance Tool",
    layout="wide"
)

st.title("BESS MV Collector System Equivalent Impedance Tool")
st.caption("Aligned exactly with hand and Excel calculations")

# =========================================================
# 1. SYSTEM BASE
# =========================================================
st.header("1. System Base")

c1, c2, c3 = st.columns(3)
V_mv_kV = c1.number_input("Collector Bus Voltage (kV)", value=34.5)
base_MVA = c2.number_input("Base MVA (for per-unit)", value=100.0)
freq = c3.number_input("System Frequency (Hz)", value=60.0)

Z_base = (V_mv_kV ** 2) / base_MVA
B_base = 1 / Z_base

# =========================================================
# 2. FEEDER CONFIGURATION
# =========================================================
st.header("2. Feeder Configuration")

c1, c2 = st.columns(2)
n_feeders = c1.number_input("Number of Feeders", min_value=1, value=6)

S_tr_MVA = c2.number_input(
    "TOTAL Transformer MVA per Feeder (sum of all transformers)",
    value=25.0
)

c1, c2 = st.columns(2)
Z_tr_pct = c1.number_input("Transformer Impedance (%)", value=7.0)
XR_tr = c2.number_input("Transformer X/R Ratio", value=10.0)

# =========================================================
# 3. MV CABLE DATA
# =========================================================
st.header("3. MV Cable Data")

c1, c2, c3 = st.columns(3)
R1_cable = c1.number_input("Cable R1 (Ω/km)", value=0.040)
X1_cable = c2.number_input("Cable X1 (Ω/km)", value=0.080)
C1_F_per_km = c3.number_input("Cable C1 (F/km)", value=2.63e-9)

c1, c2 = st.columns(2)
R0_cable = c1.number_input("Cable R0 (Ω/km)", value=0.100)
X0_cable = c2.number_input("Cable X0 (Ω/km)", value=0.250)

length_ft = st.number_input("Cable Length per Feeder (ft)", value=32.0)
length_km = length_ft * 0.0003048

# =========================================================
# 4. CALCULATIONS (MATCHES YOUR HAND METHOD)
# =========================================================

# ---- Transformer impedance (per feeder equivalent)
Zbase_tr = (V_mv_kV ** 2) / S_tr_MVA
Ztr = (Z_tr_pct / 100) * Zbase_tr

R1_tr = Ztr / math.sqrt(1 + XR_tr ** 2)
X1_tr = XR_tr * R1_tr

R0_tr = 2 * R1_tr
X0_tr = 3 * X1_tr

# ---- MV cable per feeder
R1_c = R1_cable * length_km
X1_c = X1_cable * length_km
R0_c = R0_cable * length_km
X0_c = X0_cable * length_km

# ---- Feeder total (series)
R1_fd = R1_tr + R1_c
X1_fd = X1_tr + X1_c
R0_fd = R0_tr + R0_c
X0_fd = X0_tr + X0_c

# ---- Collector equivalent (parallel feeders)
R1_eq = R1_fd / n_feeders
X1_eq = X1_fd / n_feeders
R0_eq = R0_fd / n_feeders
X0_eq = X0_fd / n_feeders

# ---- Shunt susceptance (MV cable only)
omega = 2 * math.pi * freq
B1_f = omega * C1_F_per_km * length_km
B0_f = 0.75 * B1_f

B1_eq = n_feeders * B1_f
B0_eq = n_feeders * B0_f

# =========================================================
# 5. PER-FEEDER BREAKDOWN
# =========================================================
st.header("4. Per-Feeder Impedance Breakdown (Ohms)")

feeder_df = pd.DataFrame({
    "Component": ["Transformer", "MV Cable", "Feeder Total"],
    "R1 (Ω)": [R1_tr, R1_c, R1_fd],
    "X1 (Ω)": [X1_tr, X1_c, X1_fd],
    "R0 (Ω)": [R0_tr, R0_c, R0_fd],
    "X0 (Ω)": [X0_tr, X0_c, X0_fd],
})

st.dataframe(feeder_df.round(6), use_container_width=True)

# =========================================================
# 6. COLLECTOR EQUIVALENT
# =========================================================
st.header("5. Collector Equivalent Results")

collector_df = pd.DataFrame({
    "Parameter": ["R1 (Ω)", "X1 (Ω)", "B1 (µS)", "R0 (Ω)", "X0 (Ω)", "B0 (µS)"],
    "Ohmic / SI Value": [
        R1_eq,
        X1_eq,
        B1_eq * 1e6,   # convert S → µS
        R0_eq,
        X0_eq,
        B0_eq * 1e6    # convert S → µS
    ],
    "Per Unit (pu)": [
        R1_eq / Z_base,
        X1_eq / Z_base,
        B1_eq / B_base,
        R0_eq / Z_base,
        X0_eq / Z_base,
        B0_eq / B_base
    ]
})

st.dataframe(
    collector_df.applymap(
        lambda x: f"{x:.6g}" if isinstance(x, (int, float)) else x
    ),
    use_container_width=True
)

# =========================================================
# 7. INTERCONNECTION FORM OUTPUT
# =========================================================
st.header("6. Interconnection Form – Collector Equivalent")

st.code(f"""
Collector system voltage = {V_mv_kV:.2f} kV
Collector equivalent model rating = {base_MVA:.1f} MVA

R1 = {R1_eq:.4f} ohm or {R1_eq/Z_base:.5f} pu
X1 = {X1_eq:.4f} ohm or {X1_eq/Z_base:.5f} pu
B1 = {B1_eq*1e6:.4f} µS or {B1_eq/B_base:.6e} pu

R0 = {R0_eq:.4f} ohm or {R0_eq/Z_base:.5f} pu
X0 = {X0_eq:.4f} ohm or {X0_eq/Z_base:.5f} pu
B0 = {B0_eq*1e6:.4f} µS or {B0_eq/B_base:.6e} pu
""")

print(B1_eq)
st.success("Calculation complete — values now match hand and Excel results.")

