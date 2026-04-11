# Wyalusing Bridge Impact Study: Fuel Price Ingestion Pipeline

## 📌 Project Goal
This project aims to quantify the economic "Bridge Tax" imposed on the local community of Wyalusing, PA, following the closure of the main bridge. By monitoring real-time fuel price fluctuations at local stations vs. state-wide averages, this study will provide a data-driven look at how logistical detours impact local commerce.

## 🚀 What We Are Doing
We are building a "Smart" Data Pipeline that automates the collection of fuel prices to build a longitudinal dataset for analysis.

* **Ingestion:** A browser-automation script (using Playwright) handles dynamic web content to scrape live prices from GasBuddy station IDs.
* **Storage:** Data is normalized and stored in a **Supabase (PostgreSQL)** cloud database.
* **Logic:** The system utilizes Change Data Capture (CDC) logic to compare live prices against the most recent database entry, preventing redundant writes.
* **Automation:** Over the next few months, **GitHub Actions** will trigger this pipeline daily.
* **Visualization:** A **Streamlit** dashboard will be developed to display these findings and perform final analytical comparisons.

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
This project is compatible with any PostgreSQL database. To set up your cloud and local database, execute the commands found in `schema.sql` within you SQL editor to initalize the `fuel_log` table

---

## 🔐 Configuration
To run this project loccally, you must stup up your environment variables:

1. Copy the `.env.example` file and rename it to `.env`
2. Fill in your specific **DB_URL** (PostgreSQL connection string) and API_KEY (RapidAPI key).

Note: The `.env` file is ignored by Git to ensure your credentials remain secure.

---

## 📈 Roadmap
* [x] Web Scraper (Playwright/BeautifulSoup)
* [x] Cloud Database Integration (PostgreSQL)
* [x] Change Data Capture (CDC) Logic
* [ ] Manual Diesel Input (Hybrid Path)
* [ ] Automated Scheduling (GitHub Actions)
* [ ] Data Analysis & Findings