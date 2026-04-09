import streamlit as st
import duckdb
import constants as c

# --- DATABASE CONNECTION ---
def get_bridge_data():
    conn = duckdb.connect('impact_study.db')
    # Fetch the specific bridge data from our new table
    df = conn.execute("SELECT * FROM bridge_traffic LIMIT 1").df()
    conn.close()
    return df

def get_latest_fuel():
    conn = duckdb.connect('impact_study.db')
    row = conn.execute("SELECT gas_price, diesel_price FROM fuel_log ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()

    # Fallback to use hardcoded number if DB is empty
    return row if row else (c.AVG_GAS_PRICE, c.AVG_DIESEL_PRICE)

# Load the data from the DB
bridge_df = get_bridge_data()
passenger_vol = (bridge_df['adttotal'].iloc[0] * (100 - bridge_df['truckpct'].iloc[0])) / 100
commercial_vol = (bridge_df['adttotal'].iloc[0] * bridge_df['truckpct'].iloc[0]) / 100
live_gas, live_diesel = get_latest_fuel()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Wyalusing Bridge Impact", page_icon="🌉", layout="wide")

# --- HEADER SECTION ---
st.title("🌉 Wyalusing River Bridge: Economic Impact Study")
st.markdown(f"""
This dashboard quantifies the economic burden caused by the closure of the **{c.BRIDGE_TARGET}**. 
By utilizing PennDOT traffic data and regional economic constants, we can visualize the real-world cost of this infrastructure failure.
""")

st.divider()

# --- INPUT SIDEBAR ---
with st.sidebar:
    st.header("Adjust Assumptions")
    st.info("Change these values to see how the total economic impact shifts.")
    
    # These sliders allow the user to perform their own 'Sensitivity Analysis'
    gas_price = st.sidebar.slider("Local Gas Price ($)", 3.00, 6.00, float(live_gas))
    detour_time = st.number_input("Detour Time (Minutes)", value=c.DETOUR_TIME_MINS)
    
    st.write("---")
    st.caption("Data source: PennDOT Open Data Portal")

# --- CALCULATION LOGIC (Simplified for initialization) ---
# For now, we'll use the hardcoded counts from your verified math. 
# Later, we will make these dynamic.
passenger_vol = 4839  # Baseline from your reconciled data
commercial_vol = 723  # Baseline from your reconciled data

detour_hours = detour_time / 60
total_daily_impact = (
    (passenger_vol * detour_hours * c.PASSENGER_TIME_VALUE) + 
    (commercial_vol * detour_hours * c.COMMERCIAL_TIME_VALUE) +
    (passenger_vol * (c.DETOUR_DISTANCE_MILES / c.PASSENGER_MPG) * gas_price) +
    (commercial_vol * (c.DETOUR_DISTANCE_MILES / c.COMMERCIAL_MPG) * c.AVG_DIESEL_PRICE)
)

# --- IMPACT METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Daily Impact", f"${total_daily_impact:,.2f}", delta="- (Community Loss)")

with col2:
    st.metric("Projected Monthly Cost", f"${(total_daily_impact * 30.42):,.2f}")

with col3:
    st.metric("Annualized Economic Bill", f"${(total_daily_impact * 365):,.2f}")

st.success(f"Finding: Every day this bridge remains closed, the community 'pays' roughly **${total_daily_impact:,.0f}** in time and fuel.")

st.divider()

# --- PERSONAL IMPACT CALCULATOR ---
st.header("🚗 Calculate Your Personal Impact")
st.write("Enter your typical travel habits to see how much this closure is costing you personally.")

p_col1, p_col2 = st.columns(2)

with p_col1:
    trips_per_week = st.number_input("Round trips across the bridge per week", min_value=1, value=5)
    vehicle_type = st.radio("Primary Vehicle Type", ["Passenger Car/SUV", "Commercial Truck"])

# Logic for personal calculation
personal_vot = c.PASSENGER_TIME_VALUE if vehicle_type == "Passenger Car/SUV" else c.COMMERCIAL_TIME_VALUE
personal_mpg = c.PASSENGER_MPG if vehicle_type == "Passenger Car/SUV" else c.COMMERCIAL_MPG
personal_fuel = c.AVG_GAS_PRICE if vehicle_type == "Passenger Car/SUV" else c.AVG_DIESEL_PRICE

# Weekly Cost = (Time Cost + Fuel Cost) * Trips
weekly_personal_time = (personal_vot * (detour_time / 60)) * trips_per_week
weekly_personal_fuel = (personal_fuel * (c.DETOUR_DISTANCE_MILES / personal_mpg)) * trips_per_week
weekly_total = weekly_personal_time + weekly_personal_fuel

with p_col2:
    st.subheader("Your Estimated 'Closure Tax'")
    st.metric("Weekly Added Cost", f"${weekly_total:,.2f}")
    st.metric("Monthly Added Cost", f"${(weekly_total * 4.33):,.2f}")

st.markdown(f"""
---
### 📉 **The Bottom Line**
Over a 4-month closure, your personal commute will cost you an extra **${(weekly_total * 17.3):,.2f}**.
""")

st.divider()

# --- THE OPTIMIZED SOLUTION: ROI OF SPEED ---
st.header("💡 The Solution: Incentive-Based Construction")
st.write("""
What is it worth to finish the bridge early? By using a 'Speed Bonus,' the Commonwealth can 
incentivize contractors to reduce the closure window, saving millions for the local economy.
""")

days_early = st.slider("Days finished ahead of schedule", 1, 30, 14)

# Calculate savings based on the LIVE daily impact from your sliders
total_community_savings = total_daily_impact * days_early
# Proposed split: 50% bonus to contractor, 50% stays with the taxpayers
suggested_bonus = total_community_savings * 0.5

s_col1, s_col2 = st.columns(2)

with s_col1:
    st.metric("Community Savings", f"${total_community_savings:,.2f}", help="Total money saved by local residents and businesses.")
    
with s_col2:
    st.metric("Max Viable Bonus", f"${suggested_bonus:,.2f}", help="The amount the state could pay a contractor while still breaking even.")

st.markdown("---")
st.subheader("💡 Key Insight")

community_gain = total_community_savings - suggested_bonus

# We use a simple string to avoid any "ghost" spaces or tab issues from VS Code
msg = f"**Key Insight:** By finishing {days_early} days early, the contractor earns a ${suggested_bonus:,.0f} bonus, while the community keeps ${community_gain:,.0f} in their pockets."

st.success(msg)

st.divider()

# --- FOOTER / DATA TRANSPARENCY ---
with st.expander("📝 About the Data & Methodology"):
    st.write(f"""
    This study utilizes **PennDOT Annual Average Daily Traffic (AADT)** data for the {c.BRIDGE_TARGET}. 
    Economic impact is calculated based on standard US DOT 'Value of Time' (VOT) and 'Vehicle Operating Cost' (VOC) metrics.
    
    For a full breakdown of the math, constants, and data sources, please refer to the **methodology.md** file in the project repository.
    """)
    st.caption("Developed by Alexander Harvey | 2026 Bridge Impact Study")