# 📊 Power BI Modeling & DAX Measures Guide
### Fintech & PPOB Transaction Operations Analytics

This guide provides the complete blueprint to build an interactive enterprise dashboard in **Microsoft Power BI Desktop**, matching the case study specifications of this portfolio project.

---

## 🏗 1. Data Model Architecture (Star-Schema)

To ensure optimal performance on 300k+ records, structure the Power BI semantic model as a Star-Schema:

* **Fact Table:** `Fact_Transactions` (from `Data_Rubik_Aug2026_Cleaned.db` or `Merged_Data_Rubik_01_05_06_August_2026_Masked.csv`)
* **Dimension Tables:**
  * `Dim_Date`: Extracted unique `transaction_date`, `day_of_week`.
  * `Dim_Time`: Hours `0` to `23` with Time Band grouping (`Peak Evening`, `Morning Rush`, `Off-Peak`).
  * `Dim_Biller`: Unique `biller_name`.
  * `Dim_Product`: Unique `product_code`.
  * `Dim_Partner`: Unique `partner_name`.

---

## 📐 2. Essential DAX Measures

Create a dedicated measure table `_Measures` and insert the following DAX calculations:

### 1. Volume & Baseline Totals
```dax
Total Transactions = 
COUNTROWS('Fact_Transactions')
```

```dax
Success Transactions = 
CALCULATE(
    COUNTROWS('Fact_Transactions'),
    LOWER('Fact_Transactions'[status]) = "success"
)
```

```dax
Failed Transactions = 
CALCULATE(
    COUNTROWS('Fact_Transactions'),
    LOWER('Fact_Transactions'[status]) = "failed"
)
```

---

### 2. SLA Performance Ratios
```dax
Success Rate % = 
DIVIDE([Success Transactions], [Total Transactions], 0)
```

```dax
Failure Rate % = 
DIVIDE([Failed Transactions], [Total Transactions], 0)
```

```dax
System Failure Contribution % = 
DIVIDE(
    [Failed Transactions],
    CALCULATE([Failed Transactions], ALL('Fact_Transactions')),
    0
)
```

---

### 3. Pareto 80/20 Cumulative Distribution
```dax
Cumulative Product Volume = 
VAR CurrentProductVolume = [Total Transactions]
RETURN
CALCULATE(
    [Total Transactions],
    FILTER(
        ALL('Fact_Transactions'[product_code]),
        [Total Transactions] >= CurrentProductVolume
    )
)
```

```dax
Cumulative Product Volume % = 
DIVIDE(
    [Cumulative Product Volume],
    CALCULATE([Total Transactions], ALL('Fact_Transactions')),
    0
)
```

---

### 4. Risk Threshold & Conditional Formatting
```dax
SLA Risk Status = 
SWITCH(
    TRUE(),
    [Failure Rate %] > 0.20, "Critical Risk (>20%)",
    [Failure Rate %] >= 0.10, "Warning (10-20%)",
    "Healthy (<10%)"
)
```

```dax
SLA Color Hex = 
SWITCH(
    TRUE(),
    [Failure Rate %] > 0.20, "#EF4444", -- Red
    [Failure Rate %] >= 0.10, "#F59E0B", -- Amber
    "#10B981"                          -- Green
)
```

---

## 🖥 3. Recommended Power BI Visual Layout

1. **Top Slicers:**
   * Date Hierarchy Slicer (`transaction_date`)
   * Biller Dropdown Slicer (`biller_name`)
   * SLA Risk Dropdown (`SLA Risk Status`)
2. **Top KPI Scorecard Cards:**
   * Multi-row card: `Total Transactions`, `Success Rate %`, `Failure Rate %`, `Unique Customers`.
3. **Main Visuals:**
   * **Visual 1 (Donut Chart):** Legend: `status`, Values: `Total Transactions`.
   * **Visual 2 (Line and Clustered Column Chart):** X-Axis: `transaction_hour`, Column Y-Axis: `Total Transactions`, Line Y-Axis: `Failure Rate %`.
   * **Visual 3 (Clustered Bar Chart):** Y-Axis: `biller_name`, X-Axis: `System Failure Contribution %`, Tooltips: `Failed Transactions`.
   * **Visual 4 (Scatter / Matrix Table):** Rows: `product_code`, Values: `Total Transactions`, `Success Rate %`, `Failure Rate %`, `SLA Risk Status`.
