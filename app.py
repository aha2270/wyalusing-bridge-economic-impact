import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. SETUP & CLOUD CONNECTION ---
# Using Streamlit Secrets for the Git Push (Add these in Streamlit Cloud settings)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="PA Bridge Impact Calculator", layout="wide")

# --- 2. DATA FETCHING (CACHED) ---
@st.cache_data
def get_bridge_list():
    """Fetches a minimal list of bridges for the search dropdown."""
    # We only grab the identifiers to keep the initial load fast
    response = supabase.table("bridge_traffic_stats").select("location, facility, brkey").execute()
    df = pd.DataFrame(response.data)
    # Create a nice label for the dropdown
    df['display_name'] = df['location'] + " (" + df['facility'] + ")"
    return df

@st.cache_data(ttl=3600) # Refresh fuel price once per hour
def get_latest_fuel_benchmark():
    """Gets the most recent AAA state average from the cloud."""
    response = supabase.table("state_fuel_benchmarks").select("*").order("updated_at", desc=True).limit(1).execute()
    if response.data:
        return response.data[0]
    return {"gas_price": 3.50, "diesel_price": 4.10} # Fallback defaults

# --- 3. THE UI SIDEBAR (INPUTS) ---
st.sidebar.header("🛠️ Calculator Settings")

# Bridge Selection
bridge_df = get_bridge_list()
# Find Wyalusing index to make it the default
wyalusing_idx = bridge_df[bridge_df['location'].str.contains('Wyalusing', na=False)].index[0] if not bridge_df[bridge_df['location'].str.contains('Wyalusing', na=False)].empty else 0

selected_label = st.sidebar.selectbox(
    "Select a Bridge to Analyze", 
    options=bridge_df['display_name'],
    index=int(wyalusing_idx)
)

# Fetch full details for the selected bridge
selected_brkey = bridge_df[bridge_df['display_name'] == selected_label]['brkey'].values[0]
bridge_details = supabase.table("bridge_traffic_stats").select("*").eq("brkey", selected_brkey).execute().data[0]

# User Inputs for the specific scenario
st.sidebar.markdown("---")
detour_time = st.sidebar.number_input("Added Detour Time (Minutes)", min_value=1, value=20)
avg_speed = st.sidebar.slider("Avg Detour Speed (MPH)", 25, 55, 35)

# Fuel Benchmark
fuel = get_latest_fuel_benchmark()
st.sidebar.info(f"⛽ Using PA State Average:\nGas: ${fuel['gas_price']} | Diesel: ${fuel['diesel_price']}")

# --- 4. THE CALCULATION LOGIC ---
# Traffic Stats
adt = bridge_details['adttotal']
truck_pct = (bridge_details['truckpct'] or 0) / 100
truck_vol = int(adt * truck_pct)
car_vol = adt - truck_vol

# Economic Impact (Simplified model)
detour_miles = (detour_time / 60) * avg_speed
# Industry standards: 15 MPG for cars, 6 MPG for trucks
fuel_consumed = (car_vol * (detour_miles / 15)) + (truck_vol * (detour_miles / 6))
daily_cost = (car_vol * (detour_miles / 15) * fuel['gas_price']) + (truck_vol * (detour_miles / 6) * fuel['diesel_price'])

# --- 5. THE DASHBOARD DISPLAY ---
st.title("🌉 Pennsylvania Bridge Impact Calculator")
st.subheader(f"Scenario Analysis: {selected_label}")

col1, col2, col3 = st.columns(3)
col1.metric("Daily Traffic (ADT)", f"{adt:,}")
col2.metric("Commercial Volume", f"{truck_vol:,} trucks")
col3.metric("Est. Daily 'Bridge Tax'", f"${daily_cost:,.2f}")

st.markdown("---")

# Informative breakdown
st.write(f"### Economic Impact Summary")
st.write(f"""
If the **{bridge_details['facility']}** in **{bridge_details['location']}** were to close, 
forcing a **{detour_time} minute** detour, local commuters and logistics companies would 
spend an additional **${daily_cost:,.2f} per day** in fuel costs alone. 

Over a year, this results in an economic burden of **${(daily_cost * 365):,.2f}**.
""")

# Technical Details for the Portfolio
with st.expander("View Infrastructure & Technical Data"):
    st.json(bridge_details)