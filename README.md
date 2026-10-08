# Fintech PPOB Transaction Operations Analytics

End-to-end analysis of **316,376 transactions** from an Indonesian PPOB (Payment Point Online Bank) switching gateway,
covering failure root causes, biller performance, demand concentration and peak-load behaviour. Delivered as a Power BI
dashboard, a SQL and Python analysis, and an executive deck.

![Power BI](https://img.shields.io/badge/Power%20BI-PBIP-F2C811?logo=powerbi&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-SQLite-003B57?logo=sqlite&logoColor=white)
![Python](https://img.shields.io/badge/Python-pandas-3776AB?logo=python&logoColor=white)

![Power BI dashboard overview](powerbi/preview/01_overview.png)

## Key findings

| Metric | Value |
|---|---|
| Transactions analysed | 316,376 (1, 5 and 6 August 2026) |
| Success rate | 89.84% |
| Failed transactions | 32,150 (10.16%) |
| Failures from just two billers | 60.9% (`Biller_29`, `Biller_26`) on 19.6% of traffic |
| Busiest hour | 18:00 WIB, 24,787 transactions over the three days (about 8.3K per day) |
| Active ecosystem | 46 partners · 31 billers · 294 SKUs · 291,662 customers |

1. **Failures are a vendor problem, not a capacity problem.** `Biller_29` (39.4% failure rate) and `Biller_26` (26.0%)
   produce 60.9% of all failures. The hourly failure rate stays between 7.0% and 13.4% and does not rise at peak load
   (18:00 is 9.1%).
2. **A few denominations are broken.** Among SKUs with at least 1,000 transactions, `XDF1000` fails 58.7% of the time,
   `XDF2000` 53.5% and `XDF3000` 48.3%, all through `Biller_29`. This points to a denomination mismatch or a stock and
   balance problem upstream.
3. **There is no backup route for the worst billers.** The SKUs sold through `Biller_29` and `Biller_26` are not served
   by any other biller in this data (only 2 of their 19,585 failures were on a SKU another biller also carries), so
   automatic rerouting is only possible after a second supplier is onboarded.
4. **Demand is highly concentrated.** The top 5 SKUs carry 57.3% of volume and it takes 20 SKUs to pass 80% (81.4%).
   `TNP23`, the #3 SKU by volume, fails 22.8% of the time.
5. **Two daily peaks.** Morning (07:00–09:00, about 6.7K transactions per hour per day) and evening (17:00–19:00,
   21.3% of volume). 01:00–04:00 is the quietest window and suits batch reconciliation.

## Recommendations

| Priority | Action | Why |
|---|---|---|
| P1 | Onboard a second supplier for the XDF and TNP product lines, then switch traffic automatically when a biller's failure rate passes 10% in a 5-minute window | The two worst billers cause 19,585 failures and currently have no alternative route |
| P2 | Agree a success-rate target with `Biller_29` and `Biller_26`, review it weekly, and add deposit-balance alerts | Vendor accountability for the largest failure source |
| P3 | Retry transient errors on top SKUs (`TNP23`, `STU15`) with backoff before returning a final failure | Fewer failed purchases on high-volume products |
| P4 | Validate product codes at input (reject or upper-case lower-case codes) | Lower-case codes fail 34.9% of the time vs 10.0% |

The data has no transaction value, so revenue impact is not estimated.

## Data quality

- The source mixes upper- and lower-case product codes for the same SKU (`XDG1` and `xdg1`, `TNP13` and `tnp13`).
  There are 318 raw codes but only 294 real SKUs. All outputs upper-case the codes before grouping, including the
  Power BI query, because Power BI treats keys as case-insensitive and the product dimension would otherwise contain
  duplicates.
- 1,923 transactions (0.6%) used a lower-case code. They failed 34.9% of the time, compared with 10.0% for standard
  codes.
- Hourly figures add up the three days. Divide by three for a typical day.

## Deliverables

| Deliverable | Location | How to use |
|---|---|---|
| Power BI dashboard (2 pages) | [`powerbi/`](powerbi/) | Open `PPOB_Transaction_Operations.pbip` in Power BI Desktop, see [setup](powerbi/README.md) |
| Interactive web dashboard | [`dashboard/index.html`](dashboard/index.html) | Open the file in any browser |
| SQL analysis | [`sql/queries.sql`](sql/queries.sql) | CTEs, window functions, Pareto queries on the SQLite DB |
| Python analysis and charts | [`src/`](src/), [`visualizations/`](visualizations/) | `pip install -r requirements.txt` then `python src/analysis_and_charts.py` |
| Rebuild dashboard data | [`src/build_dashboard_data.py`](src/build_dashboard_data.py) | Regenerates `dashboard/data.json` and the data embedded in `index.html` |
| Executive deck | [`presentations/`](presentations/) | 10-slide summary for stakeholders |

<details>
<summary>Analysis charts</summary>

![Status distribution](visualizations/01_overall_status_distribution.png)
![Top 10 products](visualizations/02_top10_products_volume_and_failure_rate.png)
![Critical failure products](visualizations/03_critical_high_failure_products.png)
![Biller performance](visualizations/04_biller_performance_and_sla.png)
![Hourly traffic](visualizations/05_hourly_traffic_load_and_failure_trend.png)
![Pareto](visualizations/06_pareto_volume_concentration.png)

</details>

## Project structure

```
.
├── powerbi/          Power BI project: semantic model (TMDL), report (PBIR), theme, previews
├── dashboard/        Standalone HTML dashboard
├── data/
│   ├── raw/          Masked transaction data (CSV, XLSX)
│   └── database/     Cleaned SQLite database with indexes and views
├── sql/              Analytical SQL queries
├── src/              Python analysis and deck generator
├── visualizations/   Exported charts
├── metrics/          KPI summary (JSON)
└── presentations/    Executive deck (PPTX)
```

## Data and privacy

Customer numbers, biller, partner and personal names are pseudonymised with deterministic hashing. The mapping file
is excluded from version control.

## Author

**Novaldi Ramadhan Waluyo**, Data & Operations Analyst
[novaldiramadhan28@gmail.com](mailto:novaldiramadhan28@gmail.com) · [github.com/Achimedes28](https://github.com/Achimedes28)
