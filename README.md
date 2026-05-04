# 🌉 Pennsylvania Bridge Economic Impact & Fuel Trend Analyzer

View the live dashboard here: https://pa-bridge-impact-calculator.streamlit.app/

A production-ready data pipeline that quantifies the daily economic burden of infrastructure failure in Pennsylvania by integrating real-time market benchmarks

---

# 🏗️ System Architecture

This project is an end-to-end data engineering solution that automates the lifecycle of a record from ingestion to visualization

* **Ingestion Layer**: An automated web-scraper built with **Playwright** that triggers daily via **GitHub Actions**.
* **Storage Layer**: A **PostgreSQL** database hosted on **Supabase** that maintains historical records and handles time-series data integrity
* **Application Layer**: A **Streamlit** dashboard that performs real-time economic calculations based on live fuel benchmarks and bridge-specific traffic data
* **Visualization Layer**: Interactive trend analysis using **Plotly**, featuring double-encoding visuals for accessibility

---

# 🚀 Key Engineering Features

1. **Automated ETL Pipeline**

    The system uses **GitHub Actions** to run a "headless" browser daily, scraping state-wide fuel averages and loading them directly into the PostgreSQL backend. This ensures the "Daily Bridge Tax" calculation is always reflecting current market conditions without manual intervention.

2. **Accessible Time-Series Analysis**

    The new Fuel Price Trends module allows users to explore price volatility over 7-day and 30-day windows.

    - **Inclusive Design**: Implemented "Double Encoding" (varying both color and line styles) to ensure data remains legible for users with color-blindness
    - **Performance**: Utilizes server-side sorting (`.order()` in Supabase) to minimize client-side processing and maintain a fast UX.

3. **Dynamic Economic Modeling**

    The app calculates the economic impact by cross-referencing:

    - **Annual Average Daily Traffic (AADT)**
    - **Commercial Truck Volume**
    - **Real-time Fuel Benchmarks (Gasoline/Diesel)**
    - **Variable Detour Metrics**

---

# 🛠️ Tech Stack

* **Language**: Python
* **Cloud Backend**: Supabase (PostgreSQL)
* **Automation**: GitHub Actions, Playwright
* **Data Analysis**: Pandas, NumPy
* **Visualization**: Plotly, Streamlit

---

# 🗺️ Roadmap & Future Scope

* **Predictive Modeling**: Using historical data to forecast future economic burdens based on price trend

---

# ⚙️ Local Deployment

To run this project locally for testing or development:

**Clone the Repository**:

```bash
git clone https://github.com/aha2270/wyalusing-bridge-economic-impact
```

**Install Dependencies**:

```bash
pip install -r requirements.txt
```

**Set up Environment Variables**:

Ensure you have a `.env` or Streamlit `secrets.toml` file with your database credentials

**Launch the App**:

```bash
streamlit run app.py
```
---