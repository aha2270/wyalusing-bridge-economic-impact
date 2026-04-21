# Pennsylvania Bridge Economic Impact Dashboard

## 📌 Project Overview
This project provides a state-wide analytical tool to quantify the economic "Bridge Tax" resulting from infrastructure failures. Originally conceived as a study for Wyalusing, PA, the platform has evolved into a **Universal Bridge Impact Calculator** covering 56,000+ bridges across the Commonwealth of Pennsylvania.

By integrating PennDOT traffic data with automated AAA fuel benchmarks, the dashboard calculates the real-time daily cost burden placed on local economies when a bridge closure forces logistical detours.

## 🚀 The Data Engineering Pipeline
We have built a resilient, cloud-native ETL pipeline designed for high uptime and minimal technical debt.

* **Ingestion:** An automated **Playwright** harvester scrapes daily state-wide fuel benchmarks from AAA. To ensure resilience against upstream UI changes, the pipeline utilizes a heuristic "search and rescue" logic to identify data anchors within dynamic iframes.
* **Storage:** A normalized **Supabase (PostgreSQL)** database houses 56,000+ bridge infrastructure records and a historical log of fuel benchmarks.
* **Analysis:** The system calculates economic impact using a dual-vehicle modal:
    $$\text{Daily Cost} = \left(\text{Car Vol} \times \frac{\text{Miles}}{\text{15 MPG}} \times \text{Gas Price}\right) + \left(\text{Truck Vol} \times \frac{\text{Miles}}{\text{6 MPG}} \times \text{Diesel Price}\right)$$
* **Visualization:** A **Streamlit** dashboard allows users to search any bridge in PA and perform real-time "What-If" scenario analysis.

---

## 🛠️ Installation & Setup

### 1. Requirements
Ensure you have Python 3.x installed, then install the necessary dependencies:
```bash
pip install -r requirements.txt
```

### 2. Playwright Browser Setup
This project uses a headless browswer to handle JavaScript-rendered content. You must install the Chromium binary after installing the Python package:

```bash
playwright install chromium 
```

### 3. Database Initialization
This project is compatible with any PostgreSQL database. To set up your cloud and local database, execute the commands found in `schema.sql` within you SQL editor to initalize the `bridge_traffic_stats` and `state_fuel_benchmark` tables

---

## 🔐 Configuration (Secrets Management)
This project uses Streamlit Secrets to protect sensitive cloud credentials.

1. Create a folder named `.streamlit` in the root directory.
2. Create a file named `secrets.toml` inside that folder.
3. Add your credentials:

```
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_anon_key"
```

Note: The `.env` file is ignored by Git to ensure your credentials remain secure.

---

## 📈 Roadmap
- [x] Phase 1: Local Case Study (Wyalusing, PA)

- [x] Phase 2: Cloud Database Integration & ETL Refactoring

- [x] Phase 3: Automated AAA State-Wide Harvester (Resilient Scraping)

- [x] Phase 4: Universal Dashboard Deployment (56k Bridges)

- [ ] Phase 5: Historical Trend Analysis (Time-Series Fuel Tracking)

- [ ] Phase 6: Automated CI/CD (GitHub Actions)