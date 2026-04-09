import os
import duckdb
import requests
from dotenv import load_dotenv
import psycopg2

# Start by loading in secret key from .env
load_dotenv()

# Hidden passwords used for database and API calls
DB_URL = os.getenv("SUPABASE_CONN_STRING")
API_KEY = os.getenv("RAPIDAPI_KEY")

# Toccgle between cloud and local
USE_CLOUD = True




# TODO: Add Comment Blocks For Each Function



# API call for gas and diesel prices
def fetch_pa_fuel_prices():

    # Targeting endpoint for just PA
    url = "https://gas-price.p.rapidapi.com/stateUsaPrice"
    querystring = {"state": "PA"}

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "gas-price.p.rapidapi.com"
    }

    try: 
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status() # Triggers if API is down
        data = response.json()

        # Debugging
        state_list = data['result']['state']

        # Since API gives data as string, we must convert to floats
        gas = float(state_list[0]['gasoline'])
        diesel = float(state_list[0]['diesel'])

        return gas, diesel
    except Exception as e:
        print(f"API Call Failed: {e}")
        return None, None








# Hard coded numbers for testing (will be removed)
def get_fuel_prices():
    gas_price = 4.19
    diesel_price = 5.99
    return gas_price, diesel_price









def get_latest_price_duckdb():
    conn = duckdb.connect('impact_study.db')

    # Checks if table exists before making call
    table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fuel_log'").fetchone()

    if not table_check:
        conn.close()
        return None
    
    result = conn.execute("SELECT gas_price FROM fuel_log ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()
    return result[0] if result else None





def get_latest_price_supabase():

    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Query to grab most recent entry in database
        query = "SELECT gas_price FROM fuel_log ORDER BY timestamp DESC LIMIT 1;"
        cur.execute(query)

        result = cur.fetchone()
        cur.close()

        return float(result[0]) if result else None
    except Exception as e:
        print(f"Cloud Lookup Error: {e}")
        return None
    finally:
        if conn:
            conn.close()







def upload_to_duckdb():
    # 1. Extraction (Raw Data)
    raw_gas, raw_diesel = fetch_pa_fuel_prices()
    
    if raw_gas is None:
        return

    # 2. Transformation (Normalization)
    # We round once here. These are now our "Clean" variables.
    current_gas = round(raw_gas, 3)
    current_diesel = round(raw_diesel, 3)

    # 3. Lookup (Historical Context)
    last_raw_gas = get_latest_price_duckdb()
    historical_gas = round(last_raw_gas, 3) if last_raw_gas else None

    # 4. Comparison & Load
    if historical_gas is None or current_gas != historical_gas:
        conn = duckdb.connect('impact_study.db')
        # We insert the ALREADY ROUNDED variables to keep the DB clean
        conn.execute("INSERT INTO fuel_log (gas_price, diesel_price) VALUES (?, ?)", 
                     [current_gas, current_diesel])
        conn.close()
        
        print(f"Change detected! New price: ${current_gas} (Previous: ${historical_gas})")
    else:
        print(f"No price change detected (${current_gas}). Skipping database update.")









def upload_to_supabase(gas, diesel):
    conn = None

    try:
        # Establish connection
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()

        # Prepare the SQL
        insert_query = """
        INSERT INTO fuel_log (gas_price, diesel_price)
        VALUES (%s, %s);
        """

        cur.execute(insert_query, (gas, diesel))
        conn.commit()

        print(f"Success! Ingested Gas: ${gas}, Diesel: ${diesel}")

        cur.close()
    
    except Exception as e:
        print(f"Database Error: {e}")
    
    finally:
        if conn:
            conn.close()









# Saves data to either cloud or local depedning on the toggle at top of script
def save_data(gas,diesel):
    if USE_CLOUD:
        upload_to_supabase(gas, diesel)
    else:
        upload_to_duckdb(gas, diesel)


if __name__ == "__main__":
    print("Starting ingestion worker...")
    gas, diesel = get_fuel_prices()
    
    last_price = get_latest_price_supabase()

    if last_price is None or gas != last_price:
        upload_to_supabase(gas, diesel)
    else:
        print(f"Price is still ${gas}. No update needed in Supabase")