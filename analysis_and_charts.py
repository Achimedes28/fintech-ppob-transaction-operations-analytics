import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import json

workdir = '/Users/novaldiramadhanwaluyo/Desktop/Certificate and portfolio/Portoflio 3'
fig_dir = os.path.join(workdir, 'visualizations')
os.makedirs(fig_dir, exist_ok=True)

db_path = os.path.join(workdir, 'Data_Rubik_Aug2026_Cleaned.db')
conn = sqlite3.connect(db_path)
df = pd.read_sql_query('SELECT * FROM transactions', conn)

# Standardize status
df['status'] = df['status'].str.lower()
df['is_success'] = (df['status'] == 'success').astype(int)
df['is_failed'] = (df['status'] == 'failed').astype(int)

# ---------------------------------------------------------
# 1. OVERALL KPI & STATUS DONUT CHART
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
colors = ['#10B981', '#EF4444']
status_counts = df['status'].value_counts()
labels = [f'Success\n{status_counts["success"]:,} ({status_counts["success"]/len(df)*100:.1f}%)',
          f'Failed\n{status_counts["failed"]:,} ({status_counts["failed"]/len(df)*100:.1f}%)']

wedges, texts, autotexts = ax.pie(
    status_counts, 
    labels=labels, 
    autopct='%1.2f%%', 
    pctdistance=0.75,
    colors=colors, 
    startangle=140,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2),
    textprops=dict(fontsize=11, weight='bold', color='#1E293B')
)
for at in autotexts:
    at.set_color('white')
    at.set_fontsize(12)
    at.set_weight('bold')

ax.set_title('Overall Transaction Volume & SLA Health\nTotal Volume: 316,376 Transactions', fontsize=14, weight='bold', pad=20, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '01_overall_status_distribution.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# 2. TOP 10 PRODUCTS VOLUME & FAILURE RATE (DUAL AXIS)
# ---------------------------------------------------------
prod_grp = df.groupby('product_code').agg(
    total=('status', 'count'),
    success=('is_success', 'sum'),
    failed=('is_failed', 'sum')
)
prod_grp['fail_rate'] = (prod_grp['failed'] / prod_grp['total']) * 100
prod_grp['success_rate'] = (prod_grp['success'] / prod_grp['total']) * 100
top10_prod = prod_grp.sort_values(by='total', ascending=False).head(10).reset_index()

fig, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
ax2 = ax1.twinx()

x = np.arange(len(top10_prod))
width = 0.55

bars = ax1.bar(x, top10_prod['total'], width, color='#3B82F6', alpha=0.9, label='Transaction Volume', edgecolor='#1D4ED8')
lines = ax2.plot(x, top10_prod['fail_rate'], color='#EF4444', marker='o', linewidth=2.5, markersize=8, label='Failure Rate (%)')

ax1.set_xlabel('Product Code', fontsize=12, weight='bold', labelpad=10, color='#1E293B')
ax1.set_ylabel('Total Transaction Volume', fontsize=12, weight='bold', color='#1D4ED8')
ax2.set_ylabel('Failure Rate (%)', fontsize=12, weight='bold', color='#EF4444')
ax1.set_xticks(x)
ax1.set_xticklabels(top10_prod['product_code'], fontsize=11, rotation=25)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.1f}%'))
ax2.grid(False)

# Data labels
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f'{height:,}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9, weight='bold', color='#1E293B')

for i, txt in enumerate(top10_prod['fail_rate']):
    ax2.annotate(f'{txt:.1f}%', (x[i], top10_prod['fail_rate'].iloc[i]),
                 textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold', color='#DC2626')

plt.title('Top 10 Most Demanded Products: Volume vs Failure Rate', fontsize=14, weight='bold', pad=20, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '02_top10_products_volume_and_failure_rate.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# 3. CRITICAL FAILURE HOTSPOTS (PRODUCTS WITH HIGHEST FAILURE RATES)
# ---------------------------------------------------------
high_fail_prod = prod_grp[prod_grp['total'] >= 1000].sort_values(by='fail_rate', ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
colors_fail = ['#B91C1C' if fr > 30 else '#EF4444' if fr > 15 else '#F59E0B' for fr in high_fail_prod['fail_rate']]
bars = ax.barh(high_fail_prod['product_code'][::-1], high_fail_prod['fail_rate'][::-1], color=colors_fail[::-1], height=0.6)

for bar in bars:
    w = bar.get_width()
    ax.text(w + 1, bar.get_y() + bar.get_height()/2, f'{w:.1f}%', ha='left', va='center', fontsize=10, weight='bold', color='#1E293B')

ax.set_xlim(0, 70)
ax.set_xlabel('Failure Rate (%)', fontsize=12, weight='bold', labelpad=10, color='#1E293B')
ax.set_ylabel('Product Code (Min. 1,000 Transactions)', fontsize=12, weight='bold', color='#1E293B')
ax.set_title('Operational SLA Risk: Top High-Failure Products (>1,000 tx)', fontsize=14, weight='bold', pad=20, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '03_critical_high_failure_products.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# 4. BILLER PERFORMANCE & SLA MATRIX
# ---------------------------------------------------------
biller_grp = df.groupby('biller_name').agg(
    total=('status', 'count'),
    success=('is_success', 'sum'),
    failed=('is_failed', 'sum')
)
biller_grp['fail_rate'] = (biller_grp['failed'] / biller_grp['total']) * 100
biller_grp['failure_contribution'] = (biller_grp['failed'] / df['is_failed'].sum()) * 100
top_billers = biller_grp.sort_values(by='total', ascending=False).head(8).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

# Volume & Failure Rate
sns.barplot(data=top_billers, x='total', y='biller_name', ax=ax1, palette='Blues_r', edgecolor='#1E293B', orient='h')
ax1.set_title('Top Billers by Total Volume', fontsize=13, weight='bold', pad=15)
ax1.set_xlabel('Total Transactions', fontsize=11, weight='bold')
ax1.set_ylabel('Biller Name', fontsize=11, weight='bold')
ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x/1000):,}k'))

# Failure Contribution
colors_contrib = ['#EF4444' if fc > 25 else '#F97316' if fc > 10 else '#64748B' for fc in top_billers['failure_contribution']]
sns.barplot(data=top_billers, x='failure_contribution', y='biller_name', ax=ax2, palette=colors_contrib, edgecolor='#1E293B', orient='h')
ax2.set_title('Failure Contribution (% of All System Failures)', fontsize=13, weight='bold', pad=15)
ax2.set_xlabel('% of System Failures (Total 32,150 Failures)', fontsize=11, weight='bold')
ax2.set_ylabel('')

for i, p in enumerate(ax2.patches):
    w = p.get_width()
    ax2.annotate(f'{w:.1f}% ({top_billers["failed"].iloc[i]:,} fail)',
                 (w + 0.5, p.get_y() + p.get_height() / 2),
                 ha='left', va='center', fontsize=9, weight='bold', color='#0F172A')

ax2.set_xlim(0, 45)
plt.suptitle('Biller SLA Breakdown: Volume vs Failure Bottlenecks', fontsize=15, weight='bold', y=1.02, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '04_biller_performance_and_sla.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# 5. HOURLY TRAFFIC & FAILURE RATE TREND (24 HOURS)
# ---------------------------------------------------------
hourly_grp = df.groupby('transaction_hour').agg(
    total=('status', 'count'),
    failed=('is_failed', 'sum')
).reset_index()
hourly_grp['fail_rate'] = (hourly_grp['failed'] / hourly_grp['total']) * 100

fig, ax1 = plt.subplots(figsize=(13, 6), dpi=300)
ax2 = ax1.twinx()

x = hourly_grp['transaction_hour']
ax1.plot(x, hourly_grp['total'], color='#2563EB', marker='o', linewidth=2.5, label='Hourly Volume')
ax1.fill_between(x, hourly_grp['total'], color='#93C5FD', alpha=0.3)

ax2.plot(x, hourly_grp['fail_rate'], color='#DC2626', marker='s', linewidth=2, linestyle='--', label='Failure Rate (%)')

ax1.set_xlabel('Hour of Day (00:00 - 23:00 WIB)', fontsize=12, weight='bold', labelpad=10)
ax1.set_ylabel('Transaction Volume', fontsize=12, weight='bold', color='#2563EB')
ax2.set_ylabel('Failure Rate (%)', fontsize=12, weight='bold', color='#DC2626')
ax1.set_xticks(range(0, 24))
ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 24)], rotation=45, fontsize=9)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.1f}%'))
ax2.grid(False)

# Highlight Peak Hours
ax1.axvspan(17, 19, color='#FEF08A', alpha=0.4, label='Peak Evening Rush (17:00-19:00)')

# Combined Legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

plt.title('24-Hour Operational Load & Failure Dynamics', fontsize=14, weight='bold', pad=20, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '05_hourly_traffic_load_and_failure_trend.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# 6. PARETO CONCENTRATION ANALYSIS (PRODUCTS)
# ---------------------------------------------------------
pareto_prod = prod_grp.sort_values(by='total', ascending=False).reset_index()
pareto_prod['cum_vol'] = pareto_prod['total'].cumsum()
pareto_prod['cum_pct'] = (pareto_prod['cum_vol'] / pareto_prod['total'].sum()) * 100
pareto_top15 = pareto_prod.head(15)

fig, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
ax2 = ax1.twinx()

bars = ax1.bar(pareto_top15['product_code'], pareto_top15['total'], color='#0284C7', alpha=0.85, edgecolor='#0369A1')
ax2.plot(pareto_top15['product_code'], pareto_top15['cum_pct'], color='#D97706', marker='D', linewidth=2.5, markersize=6)
ax2.axhline(80, color='#DC2626', linestyle='--', linewidth=1.5, label='80% Pareto Threshold')

ax1.set_xlabel('Product Code', fontsize=12, weight='bold', labelpad=10)
ax1.set_ylabel('Transaction Volume', fontsize=12, weight='bold', color='#0284C7')
ax2.set_ylabel('Cumulative Percentage (%)', fontsize=12, weight='bold', color='#D97706')
ax1.set_xticklabels(pareto_top15['product_code'], rotation=30, fontsize=10)
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'{x:.0f}%'))
ax2.set_ylim(0, 105)
ax2.grid(False)
ax2.legend(loc='lower right')

plt.title('Pareto Analysis: Product Volume Concentration (80/20 Rule)', fontsize=14, weight='bold', pad=20, color='#0F172A')
plt.tight_layout()
fig.savefig(os.path.join(fig_dir, '06_pareto_volume_concentration.png'), bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# EXPORT METRICS JSON FOR PPTX & MARKDOWN
# ---------------------------------------------------------
summary_metrics = {
    'total_transactions': int(len(df)),
    'total_success': int(status_counts['success']),
    'total_failed': int(status_counts['failed']),
    'success_rate_pct': float(round(status_counts['success']/len(df)*100, 2)),
    'failure_rate_pct': float(round(status_counts['failed']/len(df)*100, 2)),
    'top_products': top10_prod.to_dict(orient='records'),
    'critical_fail_products': high_fail_prod.to_dict(orient='records'),
    'top_billers': top_billers.to_dict(orient='records'),
    'hourly_traffic': hourly_grp.to_dict(orient='records'),
    'peak_hour': int(hourly_grp.sort_values(by='total', ascending=False).iloc[0]['transaction_hour']),
    'peak_hour_volume': int(hourly_grp.sort_values(by='total', ascending=False).iloc[0]['total']),
    'unique_customers': int(df['customer_number'].nunique()),
    'unique_partners': int(df['partner_name'].nunique()),
    'unique_billers': int(df['biller_name'].nunique()),
    'unique_products': int(df['product_code'].nunique())
}

with open(os.path.join(workdir, 'summary_metrics.json'), 'w') as f:
    json.dump(summary_metrics, f, indent=2)

print('Analysis & 6 Charts generated successfully!')
