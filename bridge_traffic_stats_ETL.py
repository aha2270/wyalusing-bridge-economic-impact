import pandas as pd
import numpy as np
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Setup & Credentials
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def migrate_penndot_data(csv_file_path):
    print(f"🚀 Starting ETL process for: {csv_file_path}")
    
    # --- EXTRACT ---
    try:
        # Added low_memory=False to handle those DtypeWarnings you saw earlier
        df = pd.read_csv(csv_file_path, low_memory=False)
        print(f"📥 Successfully loaded {len(df)} rows from local file.")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return

    # --- TRANSFORM ---
    mapping = {
        'BRKEY': 'brkey',
        'FACILITY': 'facility',
        'LOCATION': 'location',
        'YEARBUILT': 'yearbuilt',
        'ADTTOTAL': 'adttotal',
        'TRUCKPCT': 'truckpct',
        'VCLROVER': 'vclrover',
        'MIN_OVER_VERT_CLEAR_LEFT': 'min_over_vert_clear_left',
        'MIN_OVER_VERT_CLEAR_RIGHT': 'min_over_vert_clear_right',
        'SUFF_RATE': 'suff_rate',
        'DKRATING': 'dkrating',
        'SUPRATING': 'suprating',
        'SUBRATING': 'subrating',
        'CONDITION': 'condition',
        'CTY_CODE': 'cty_code'
    }

    # 1. Filter and rename
    df_transformed = df[list(mapping.keys())].rename(columns=mapping)

    # 2. DEFENSIVE TYPE CASTING
    # This prevents the "invalid input syntax for type integer: '473.0'" error
    int_cols = ['yearbuilt', 'adttotal', 'dkrating', 'suprating', 'subrating']
    float_cols = ['truckpct', 'vclrover', 'min_over_vert_clear_left', 'min_over_vert_clear_right', 'suff_rate']

    for col in int_cols:
        # Force to numeric first, fill missing with 0, then cast to pure int
        df_transformed[col] = pd.to_numeric(df_transformed[col], errors='coerce').fillna(0).astype(int)

    for col in float_cols:
        # Force to numeric to ensure they are float objects
        df_transformed[col] = pd.to_numeric(df_transformed[col], errors='coerce')

    # 3. THE JSON-READY CONVERSION
    # This replaces NaN (math object) with None (Python object), making the API happy
    df_transformed = df_transformed.replace({np.nan: None})

    # --- LOAD ---
    records = df_transformed.to_dict(orient='records')
    print(f"📤 Preparing to upload {len(records)} records to Supabase...")

    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            # Using .upsert() handles conflicts automatically
            supabase.table("bridge_traffic_stats").upsert(batch).execute()
            if (i // batch_size) % 10 == 0:  # Print progress every 10 batches to keep terminal clean
                print(f"✅ Progress: Uploaded batch {i // batch_size + 1}...")
        except Exception as e:
            print(f"❌ Error in batch {i // batch_size + 1}: {e}")

    print("🎊 ETL Migration Complete! Check your Supabase Table Editor.")

if __name__ == "__main__":
    # Ensure this matches your folder structure: ./data/Pennsylvania_Bridges.csv
    FILE_PATH = "./data/Pennsylvania_Bridges.csv"
    migrate_penndot_data(FILE_PATH)