# 💳 Fintech & PPOB Transaction Operations Analytics
### High-Volume Transaction Analysis, Pareto Volume Skew, Vendor SLA Bottlenecks & Smart Routing Strategy

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-11557C?style=for-the-badge)
![PowerPoint](https://img.shields.io/badge/PowerPoint-Executive%20Deck-D24726?style=for-the-badge&logo=microsoftpowerpoint&logoColor=white)
![Status](https://img.shields.io/badge/Status-Completed%20Portfolio-10B981?style=for-the-badge)

---

## 📌 Executive Summary

This project conducts an end-to-end operational data analysis on **316,376 live financial transactions** from an Indonesian Fintech / PPOB (Payment Point Online Bank) switchboard gateway. 

The primary business objective is to diagnose transaction failure root causes, evaluate vendor (biller) SLA compliance, uncover product demand concentrations, and formulate high-impact operational recommendations to recover lost revenue and enhance end-user customer satisfaction.

### 🎯 Key Performance Indicators (KPI Scorecard)
* **Total Transactions Processed:** `316,376` records
* **Overall Success Rate:** `89.84%` (`284,226` successful transactions)
* **System Failure SLA Gap:** `10.16%` (`32,150` failed transactions)
* **Failure Concentration Risk:** **60.9%** of all system failures originate from just **2 vendor billers** (`Biller_29` and `Biller_26`).
* **Active Ecosystem Scale:** `46` B2B Partners, `31` Upstream Billers, `318` Unique Product SKUs, `291,662` Unique End-Customers.

---

## 📊 Visual Insights & Findings

### 1. Overall System Health & Status Distribution
The baseline system achieves an 89.84% success rate. However, the 10.16% failure rate represents over 32,000 failed transactions across just 3 operational days, creating customer support friction and potential GMV leakage.

<p align="center">
  <img src="visualizations/01_overall_status_distribution.png" width="550" alt="Overall Status Distribution" />
</p>

---

### 2. Product Volume Demand vs Failure Rates
Demand follows a sharp Pareto curve where the top products generate the majority of volume, but several high-demand products suffer severe failure rates.

* **Star Performer (`SB20`):** Dominates with **79,184 transactions** (25.03% total system volume) with a healthy **94.70%** success rate.
* **Volume Runner-Up (`XDG1`):** **40,640 transactions** (12.85% total volume) with an excellent **97.05%** success rate.
* **High-Volume Bottleneck (`TNP23`):** Ranked #3 in demand (**22,334 transactions**) but plagued by a **22.75% failure rate** (5,082 failed recharges).

<p align="center">
  <img src="visualizations/02_top10_products_volume_and_failure_rate.png" width="850" alt="Top 10 Products Volume and Failure Rate" />
</p>

---

### 3. Critical Failure Hotspots (Micro-SKU SLA Anomalies)
Analyzing products with at least 1,000 transactions reveals catastrophic operational anomalies in specific denominations:

* **`XDF1000`:** **58.73% Failure Rate** (Only 41.27% success out of 6,203 transactions).
* **`TNP13`:** **35.00% Failure Rate** (1,640 failures out of 4,686 transactions).
* **`XDF500`:** **32.26% Failure Rate** (1,289 failures out of 3,996 transactions).

> **Root Cause Diagnostic:** Severe failure spikes on specific denominations (such as the `XDF` and `TNP` series) point to upstream vendor catalog desynchronization, unannounced denomination retirement by telco providers, or depleted partner switchboard deposit balances.

<p align="center">
  <img src="visualizations/03_critical_high_failure_products.png" width="750" alt="Critical High Failure Products" />
</p>

---

### 4. Vendor (Biller) SLA Breakdown & Failure Concentration
Vendor performance is severely asymmetric. While primary billers maintain solid SLA, two specific billers are responsible for the vast majority of operational failures:

* **`Biller_27` (Core Backbone):** Processes **159,402 transactions** (50.38% of total volume) with a reliable **94.32%** SLA.
* **`Biller_31`:** Processes **59,239 transactions** (18.72% share) with a strong **95.92%** SLA.
* **`Biller_29` (Critical Risk):** Generates a **39.38% Failure Rate** (10,099 failed transactions), contributing **31.4% of all failures across the entire system**.
* **`Biller_26` (Critical Risk):** Generates a **26.04% Failure Rate** (9,486 failed transactions), contributing **29.5% of all failures**.

Together, **`Biller_29` and `Biller_26` generate 60.9% (19,585 transactions) of all platform errors** despite only handling 19.6% of overall traffic.

<p align="center">
  <img src="visualizations/04_biller_performance_and_sla.png" width="900" alt="Biller Performance and SLA" />
</p>

---

### 5. 24-Hour Temporal Load Dynamics & Peak Traffic Sizing
Transaction flow exhibits distinct temporal cycles across the 24-hour window:

* **Evening Prime Peak (17:00 – 19:00 WIB):** Maximum load reaches **24,787 tx/hour at 18:00 WIB**, followed by 21,792 tx/hour at 19:00 WIB. This 3-hour window accounts for **21.3% of daily transaction volume**.
* **Morning Commute Rush (07:00 – 09:00 WIB):** High sustained traffic averaging ~20,000 tx/hour.
* **Off-Peak Maintenance Window (01:00 – 04:00 WIB):** Lowest volume (<1,600 tx/hour). Ideal for automated batch reconciliation and system updates.
* **Failure Correlation:** Failure percentages remain relatively consistent across hours (~9.5% to 11.0%), proving that failures are driven by vendor SLA degradation and SKU errors rather than local network bandwidth saturation.

<p align="center">
  <img src="visualizations/05_hourly_traffic_load_and_failure_trend.png" width="850" alt="Hourly Traffic and Failure Trend" />
</p>

---

### 6. Pareto 80/20 Volume Distribution
* **Top 5 SKUs** generate **57.0%** of total transaction volume.
* **Top 15 SKUs** generate **82.4%** of total system volume.
* **Operational Takeaway:** Securing high-availability routing and monitoring for just the top 15 SKUs safeguards over 80% of company revenue and transaction traffic.

<p align="center">
  <img src="visualizations/06_pareto_volume_concentration.png" width="800" alt="Pareto Volume Concentration" />
</p>

---

## 🚀 Strategic Recommendations & Action Plan

| Priority | Strategy | Description | Expected Impact |
|:---|:---|:---|:---|
| **P1** | **Dynamic Smart Fallback Routing** | Automatically monitor biller error rates. If `Biller_29` or `Biller_26` error rates exceed 10% in a 5-minute rolling window, instantly reroute traffic to secondary backup billers (e.g. `Biller_27`). | Recovers up to **70% of failed transactions (~22,500 tx per 3-day cycle)**. |
| **P2** | **Automated Retry with Exponential Backoff** | Implement a 3-attempt automated background retry queue for transient timeout errors on top SKUs (`TNP23`, `STU15`) before returning a hard failure. | Improves checkout conversion by **3.5% - 5.0%**. |
| **P3** | **Vendor SLA Enforcement & Penalties** | Formally renegotiate vendor contracts with `Biller_29` and `Biller_26`. Implement contractual penalty rebates for SLA dips below 95% and mandate minimum deposit balance alerts. | Offsets operational loss and enforces supplier accountability. |
| **P4** | **Peak Hours Infrastructure Auto-Scaling** | Dynamically scale API gateway worker pods by +35% during the 16:30 – 20:00 WIB window. | Eliminates gateway latency bottlenecks during peak evening bursts. |

---

## 🗂 Project Structure

```
.
├── Data_Rubik_Aug2026_Cleaned.db             # Indexed SQLite Database (316k+ records)
├── Merged_Data_Rubik_Masked.csv               # Cleaned & Masked Transaction Log CSV
├── Merged_Data_Rubik_Masked.xlsx              # Multi-sheet Excel with Aggregated Pivot Tables
├── anonymization_mapping.json                 # Verification mapping for masked entities
├── analysis_and_charts.py                     # Python EDA & High-Res Chart Generation Script
├── generate_pptx.py                           # Python Automated PowerPoint Deck Builder
├── queries.sql                                # Advanced SQL Queries (CTEs, Window Functions, Pareto)
├── summary_metrics.json                       # Extracted KPI & Summary Metric Payload
├── Fintech_PPOB_Transaction_Operations_Analytics.pptx # Executive 10-Slide Widescreen Deck
├── visualizations/                            # Generated High-Resolution 300 DPI Figures
│   ├── 01_overall_status_distribution.png
│   ├── 02_top10_products_volume_and_failure_rate.png
│   ├── 03_critical_high_failure_products.png
│   ├── 04_biller_performance_and_sla.png
│   ├── 05_hourly_traffic_load_and_failure_trend.png
│   └── 06_pareto_volume_concentration.png
└── README.md                                  # Portfolio Documentation & Business Case Study
```

---

## 🛠 Tech Stack & Analytical Methods

* **Database & SQL:** SQLite3, SQL CTEs (`WITH` clauses), Window Functions (`RANK()`, `SUM() OVER`), Aggregation & Grouping Views.
* **Data Manipulation:** Python, Pandas, NumPy (Vectorized metrics, temporal extraction, outlier filtering).
* **Data Visualization:** Matplotlib, Seaborn (Custom themes, dual-axis charts, Pareto curves, 300 DPI exports).
* **Presentation Engineering:** `python-pptx` (Automated 16:9 executive deck generation with structured layout cards and embedded visuals).
* **Data Privacy:** Deterministic PII hashing and synthetic ID generation compliant with privacy and NDA standards.

---

## 👨‍💻 Author & Contact

**Novaldi Ramadhan Waluyo**  
*Data & Operations Analyst*  
* 📧 Email: [novaldiramadhan28@gmail.com](mailto:novaldiramadhan28@gmail.com)  
* 🐙 GitHub: [@Achimedes28](https://github.com/Achimedes28)  
* 💼 Portfolio Project: Fintech & PPOB Transaction Operations Analytics
