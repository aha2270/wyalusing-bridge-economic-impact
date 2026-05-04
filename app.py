import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from supabase import create_client, Client

# --- 1. SETUP & CLOUD CONNECTION ---
# Using Streamlit Secrets for the Git Push (Add these in Streamlit Cloud settings)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="PA Bridge Impact Calculator", layout="wide")

def get_historical_trends():
    # Pulling the key metrics ordered by time
    response = supabase.table("state_fuel_benchmarks") \
        .select("updated_at, gas_price, diesel_price") \
        .order("updated_at", desc=False) \
        .execute()
    
    return pd.DataFrame(response.data)

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


st.divider()
st.header("📊 State-Wide Fuel Price Trends")
st.caption("Tracking daily benchmarks to quantify infrastructure economic shifts over time.")

# Pull the real data
df_trends = get_historical_trends()

if not df_trends.empty:
    # 1. Prepare the data
    df_trends['updated_at'] = pd.to_datetime(df_trends['updated_at'])
    
    # 2. Melt for Plotly (Fuel Type becomes a category)
    df_melted = df_trends.melt(
        id_vars='updated_at', 
        value_vars=['gas_price', 'diesel_price'],
        var_name='Fuel Type', 
        value_name='Price ($)'
    )

    df_melted['Fuel Type'] = df_melted['Fuel Type'].map({
    "gas_price": "Gasoline",
    "diesel_price": "Diesel"
    })

    # 3. Create the Visual
    fig = px.line(
        df_melted, 
        x='updated_at', 
        y='Price ($)', 
        color='Fuel Type',
        # Industry Standard Palette: Deep Blue and Safety Orange
        color_discrete_map={
            "Gasoline": "#0072B2", 
            "Diesel": "#E69F00"
        },
        template="plotly_dark",
        markers=True
    )

    # 4. Apply the Double-Encoding (Solid vs Dashed)
    fig.update_traces(line=dict(dash='solid'), selector={"name": "Gasoline"})
    fig.update_traces(line=dict(dash='dash'), selector={"name": "Diesel"})

    # 5. Final Styling
    fig.update_layout(
        hovermode="x unified",
        xaxis_title="Date Collected",
        yaxis_title="Price per Gallon ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_xaxes(
    # 1. Label Positioning & Readability
    tickangle=45,           # Dynamically angles text only if it gets crowded
    tickfont=dict(size=10),     # Keeps it professional and non-distracting
    automargin=True,            # Prevents labels from being cut off by the container
    tickformat="%b %d",         # Minimalist 'Month Day' format
    nticks=10,                  # Prevents initial load 'clumping'

    # 2. Interactive Navigation (The Range Slider)
    rangeslider_visible=True,
    
    # 3. Quick-Action Zoom Buttons
    rangeselector=dict(
        buttons=list([
            dict(count=7, label="1 WEEK", step="day", stepmode="backward"),
            dict(count=1, label="1 MONTH", step="month", stepmode="backward"),
            dict(label="ALL", step="all")
        ]),
        x=0.05,
        y=1.1,
        activecolor="#0072B2",
        bgcolor="rgba(0,0,0,0)", # Transparent background to match dark mode
        font=dict(color="white")  # Ensures buttons pop against the dark theme
        )
    )

    fig.update_yaxes(
    range=[3.5, 6.5], 
    tickformat="$.2f", 
    gridcolor='rgba(255, 255, 255, 0.1)'
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Trend analysis will appear here as more daily data is collected.")