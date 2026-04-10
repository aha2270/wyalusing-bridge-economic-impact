import os
import duckdb
import requests
from dotenv import load_dotenv
import psycopg2
import cloudscraper
from bs4 import BeautifulSoup
import time
from playwright.sync_api import sync_playwright

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
def get_gas_price_patient(station_id):
    url = f"https://www.gasbuddy.com/station/{station_id}"
    
    with sync_playwright() as p:
        # 1. Launch a 'Headless' browser (no window pops up)
        browser = p.chromium.launch(headless=True)
        
        # 2. Create a new page with a realistic 'fake mustache' (User-Agent)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"Robot is sitting down at the table: {url}")

        try:
            # 3. Go to the URL
            page.goto(url)

            # 4. THE PATIENCE: Wait for the 'Waiter' to finish his job
            # 'networkidle' waits until there are no more network requests for 500ms
            print("Waiting for the waiter to bring the data...")
            page.wait_for_load_state("networkidle")
            
            # Additional safety: wait a couple extra seconds just in case
            time.sleep(2)

            # 5. Grab the finished 'Table' (HTML) now that the cup is on it
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # 6. Use our selector to find the price
            # We look for the span that contains the price digits
            price_tag = soup.select_one("span[class*='PriceDisplay-module__price']")

            if price_tag:
                raw_text = price_tag.text.strip().replace('$', '')
                
                # Check for the small 9 suffix or 'Cash' text
                clean_text = raw_text.split()[0]

                if clean_text == "---":
                    print("Station found, but no price reported yet.")
                    return None

                print(f"Success! Found the cup: ${clean_text}")
                return float(clean_text)
            else:
                print("Even with patience, the price tag didn't appear.")
                return None

        except Exception as e:
            print(f"The robot got tired of waiting: {e}")
            return None
        finally:
            browser.close()











if __name__ == "__main__":

    dandy_id = "61479"
    current_price = get_gas_price_patient(dandy_id)

    if current_price:
        print("\n--- SCRAPE SUCCESSFUL ---")
        print(f"Station: Dandy Mini Mart (Wyalusing)")
        print(f"Regular Gas Price: ${current_price}")
        print("--------------------------")
    else:
        print("\n--- SCRAPE FAILED ---")
        print("Check your connection or if the Station ID is still active.")


    """
    print("Starting ingestion worker...")
    gas, diesel = get_fuel_prices()
    
    last_price = get_latest_price_supabase()

    if last_price is None or gas != last_price:
        upload_to_supabase(gas, diesel)
    else:
        print(f"Price is still ${gas}. No update needed in Supabase")
    """