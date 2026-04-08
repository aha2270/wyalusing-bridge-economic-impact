import duckdb
import os

# 1. Connect to (or create) the database file
# This will create 'impact_study.db' in your root folder
conn = duckdb.connect('impact_study.db')

print("Initializing database...")

# 2. Create the Bridge Traffic table
# We are defining the 'Schema'—the rules for how our data is stored.
conn.execute("""
    CREATE OR REPLACE TABLE bridge_traffic (
        brkey INTEGER,
        facility VARCHAR,
        location VARCHAR,
        adttotal DOUBLE,
        truckpct DOUBLE,
        suff_rate DOUBLE
    );
""")

# 3. Load the data from your CSV
# DuckDB is 'CSV-native' - it can read the file and insert it in one move.
# Adjust the path to match your actual CSV filename in the data folder.
csv_path = 'data/Pennsylvania_Bridges.csv'

if os.path.exists(csv_path):
    conn.execute(f"""
        INSERT INTO bridge_traffic 
        SELECT BRKEY, FACILITY, LOCATION, ADTTOTAL, TRUCKPCT, SUFF_RATE 
        FROM read_csv_auto('{csv_path}')
        WHERE LOCATION LIKE '%WYALUSING RIVER BRIDGE%';
    """)
    print(f"Successfully loaded Wyalusing Bridge data from {csv_path}")
else:
    print(f"Error: Could not find {csv_path}. Check your file name!")

# 4. Verify the data is there
result = conn.execute("SELECT * FROM bridge_traffic").fetchall()
print(f"Database contains {len(result)} record(s).")

conn.close()