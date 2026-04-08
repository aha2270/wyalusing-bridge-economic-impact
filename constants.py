# constants.py
# Centralized source of truth for the Wyalusing Bridge Economic Impact Study

# --- Bridge & Route Metadata ---
BRIDGE_TARGET = 'WYALUSING RIVER BRIDGE'
DETOUR_TIME_MINS = 25
DETOUR_TIME_HOURS = DETOUR_TIME_MINS / 60
DETOUR_DISTANCE_MILES = 12.5

# --- Economic Constants: Value of Time (VOT) ---
# Rates derived from industry standards for regional economic impact modeling.
PASSENGER_TIME_VALUE = 25.00  # USD per hour
COMMERCIAL_TIME_VALUE = 75.00 # USD per hour

# --- Vehicle Operational Costs (VOC): Efficiency ---
# Fleet averages for 2025-2026 real-world conditions.
PASSENGER_MPG = 26.5
COMMERCIAL_MPG = 6.5

# --- Fuel Market Data ---
# April 2026 Average Pricing (Bradford County, PA region)
AVG_GAS_PRICE = 4.19
AVG_DIESEL_PRICE = 5.99