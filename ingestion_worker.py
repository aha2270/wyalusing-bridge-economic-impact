import os
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

import subprocess

# This command ensures the Playwright browsers are installed in the cloud environment
try:
    import playwright
except ImportError:
    subprocess.run(["pip", "install", "playwright"])

# This tells the server to download the necessary browser binaries
subprocess.run(["playwright", "install", "chromium"])

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def harvest_state_benchmark():
    print(f"📡 Harvesting PA State Benchmark: {datetime.now().strftime('%H:%M:%S')}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto("https://gasprices.aaa.com/?state=PA", wait_until="domcontentloaded")
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the 'Current Avg.' row in the main state table
            anchor = soup.find('td', string='Current Avg.')
            if anchor:
                cells = anchor.find_next_siblings('td')
                gas_avg = float(cells[0].text.strip().replace('$', ''))
                diesel_avg = float(cells[3].text.strip().replace('$', ''))

                # Push the single benchmark record
                # Note: We use .insert() here so you can build a history log over time!
                payload = {
                    "gas_price": gas_avg,
                    "diesel_price": diesel_avg
                }
                
                supabase.table("state_fuel_benchmarks").insert(payload).execute()
                print(f"✅ Success! State Benchmark Updated: Gas ${gas_avg}, Diesel ${diesel_avg}")
            else:
                print("❌ Failure: Could not locate the 'Current Avg.' row.")

        except Exception as e:
            print(f"❌ Harvester Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    harvest_state_benchmark()