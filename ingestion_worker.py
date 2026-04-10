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

# API call for gas and diesel prices
def fetch_pa_fuel_prices():
    """
    Retrieves the current average gasoline and diesel prices for the state of Pennsylvania.
    
    This function serves as the 'Control Data' source, allowing for a comparison 
    between hyper-local Wyalusing prices and the broader state-wide economic baseline.
    Note: Depends on the RapidAPI 'gas-price' endpoint.

    Returns:
        tuple: (gas_price, diesel_price) as floats. 
               Returns (None, None) if the API call fails or limits are reached.
    """

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


def get_latest_price_supabase():
    """
    Queries the Supabase (PostgreSQL) production database for the most recent 
    gasoline price record.

    This function establishes the 'Current State' of the data warehouse, 
    enabling validation checks and preventing redundant data ingestion. 
    It uses a DESC LIMIT 1 optimization for high-performance retrieval.

    Returns:
        float: The most recent gas_price entry.
        None: If the database is empty, the table is missing, or a connection error occurs.
    """
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


def upload_to_supabase(gas, diesel):
    """
    Orchestrates the 'Load' phase of the ETL pipeline by inserting 
    fuel price data into the Supabase cloud database.

    Args:
        gas (float): The cleaned gasoline price to be stored.
        diesel (float): The cleaned diesel price (manual or baseline) to be stored.

    Note:
        Requires a valid DB_URL environment variable and the psycopg2 driver.
        Implements transaction management to ensure data persistence.
    """
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

def main():
    """
    Main Orchestrator:
    1. Scrapes real-time data using the 'Patient' Playwright robot.
    2. Queries the cloud for the most recent historical record.
    3. Performs a Change Data Capture (CDC) check.
    4. Executes the cloud upload only if a price shift is detected.
    """
    dandy_id = "61479"
    current_gas = get_gas_price_patient(dandy_id)
    current_diesel = 5.99

    if current_gas is None:
        print("Error: Scraper failed to find a price. Aborting run")
        return None 

    last_cloud_price = get_latest_price_supabase()

    if last_cloud_price is None or current_gas != last_cloud_price:
        print(f"Change Detected: Live (${current_gas}) vs Cloud (${last_cloud_price})")

        upload_to_supabase(current_gas, current_diesel)
    else:
        print(f"Data Synchronized: Real-time price (${current_gas}) matches Supabase record. No upload required.")




if __name__ == "__main__":
    main()