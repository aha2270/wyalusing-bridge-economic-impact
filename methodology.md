# Methodology: Economic Impact Analysis

## **Data Sources**
The primary infrastructure and traffic data were retrieved from the **PennDOT Open Data Portal**. Specifically, traffic volume metrics were isolated using the following attributes:
* `ADTTOTAL`: Annual Average Daily Traffic (Total Volume)
* `TRUCK_VOLUME`: Average Daily Truck Traffic (Commercial Volume)

## **Economic Assumptions**
To quantify the impact of the **25-minute detour**, this model utilizes two primary cost vectors:

### **1. Opportunity Cost (Value of Time)**
We apply a bimodal Value of Time (VOT) constant to distinguish between personal and commercial transit. 
* **Passenger VOT:** $25.00/hr
* **Commercial VOT:** $75.00/hr

### **2. Operational Cost (Fuel Consumption)**
Fuel consumption is calculated based on the detour distance ($12.5$ miles) relative to the energy intensity of the vehicle class.
* **Passenger Efficiency:** $26.5$ MPG (Gasoline)
* **Commercial Efficiency:** $6.5$ MPG (Diesel)

---

## **Calculation Logic**

The total daily economic impact is derived from the summation of Time Loss ($TL$) and Fuel Expense ($FE$) across both vehicle categories ($p$ for Passenger, $c$ for Commercial).

### **Total Economic Impact Formula:**
$$Total Daily Impact = (TL_p + TL_c) + (FE_p + FE_c)$$

**Where:**
* Time Loss: $TL = \text{Volume} \times \text{Detour Hours} \times \text{VOT}$
* Fuel Expense: $FE = \text{Volume} \times \left( \frac{\text{Detour Distance}}{\text{MPG}} \right) \times \text{Fuel Price}$

---

## **Model Limitations & Sensitivity**
This model represents a baseline estimate. Real-world costs may fluctuate based on:
1. **Seasonal Traffic:** Traffic volumes may vary during agricultural or holiday seasons.
2. **Fuel Volatility:** Rapid changes in local energy markets.
3. **Vehicle Wear:** This model does not currently account for tire wear or mechanical maintenance associated with increased mileage.