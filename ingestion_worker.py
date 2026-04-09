import os
import duckdb
import requests
from dotenv import load_dotenv

# Start by loading in secret key from .env
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")

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

def update_database():
    gas, diesel = fetch_pa_fuel_prices()


    if gas is not None and diesel is not None:
        conn = duckdb.connect('impact_study.db')
        conn.execute("INSERT INTO fuel_log (gas_price, diesel_price) VALUES (?, ?)", [gas, diesel])
        conn.close()
        print(f"Ingestion Successful: Recorded gas at ${gas} and diesel at ${diesel}")
    else:
        print("Data was not updated due to a connection or parsing error")

if __name__ == "__main__":
    update_database()