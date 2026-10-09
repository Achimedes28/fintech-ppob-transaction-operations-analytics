"""Step 2 of the pipeline: compute the headline metrics and draw the six report charts.

Reads the cleaned SQLite database (falls back to the raw CSV if the database is missing) and writes:
  visualizations/01..06_*.png   charts used in the README and the slide deck
  metrics/summary_metrics.json  every number quoted in the README, deck and dashboard

Run from the project root:  python src/analysis_and_charts.py
"""
import json
import os
import sqlite3

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

fig_dir = os.path.join(project_root, 'visualizations')
os.makedirs(fig_dir, exist_ok=True)

metrics_dir = os.path.join(project_root, 'metrics')
os.makedirs(metrics_dir, exist_ok=True)

db_path = os.path.join(project_root, 'data', 'database', 'ppob_transactions_aug2026.db')
raw_csv_path = os.path.join(project_root, 'data', 'raw', 'ppob_transactions_aug2026_masked.csv')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query('SELECT product_code, biller_name, status, partner_name, customer_number, transaction_hour FROM transactions', conn)
    conn.close()
elif os.path.exists(raw_csv_path):
    df = pd.read_csv(raw_csv_path)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    df['transaction_hour'] = pd.to_datetime(df['request_timestamp']).dt.hour
else:
    raise FileNotFoundError(f"Neither SQLite DB ({db_path}) nor CSV ({raw_csv_path}) found.")

# Standardize product codes: the source mixes upper and lower case for the same SKU
# (e.g. 'XDG1' and 'xdg1'), so codes are upper-cased before any grouping.
df['product_code'] = df['product_code'].astype(str).str.strip().str.upper()

df['status'] = df['status'].astype(str).str.lower()
df['is_success'] = (df['status'] == 'success').astype(int)
df['is_failed'] = (df['status'] == 'failed').astype(int)

# ---------------------------------------------------------
# CHART STYLE: one palette and one font across every chart
# ---------------------------------------------------------
NAVY, BLUE, LIGHT = '#1E3A5F', '#4F7CAC', '#C9D6E5'
RED, AMBER, GREEN = '#E5484D', '#F59E0B', '#12A594'
INK, MUTED, GRID = '#0F172A', '#64748B', '#E6E8EC'

plt.rcParams.update({
    'font.family': ['Inter', 'DejaVu Sans'],
    'font.size': 10,
    'text.color': INK,
    'axes.edgecolor': GRID,
    'axes.labelcolor': MUTED,
    'axes.labelsize': 10,
    'axes.titlesize': 13,
    'axes.titleweight': 'semibold',
    'axes.titlelocation': 'left',
    'axes.titlepad': 14,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': False,
    'grid.color': GRID,
    'grid.linewidth': 0.8,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'legend.frameon': False,
    'legend.fontsize': 9,
    'figure.facecolor': 'white',
    'savefig.facecolor': 'white',
    'savefig.dpi': 200,
})

thousands = ticker.FuncFormatter(lambda v, p: f'{int(v):,}')
k_format = ticker.FuncFormatter(lambda v, p: f'{v / 1000:,.0f}K' if v else '0')
pct0 = ticker.FuncFormatter(lambda v, p: f'{v:.0f}%')


def subtitle(ax, text):
    """Grey one-line takeaway under the chart title."""
    ax.text(0, 1.015, text, transform=ax.transAxes, fontsize=9.5, color=MUTED, va='bottom')


def save(fig, name):
    fig.savefig(os.path.join(fig_dir, name), bbox_inches='tight', pad_inches=0.25)
    plt.close(fig)


# ---------------------------------------------------------
# 1. OVERALL TRANSACTION STATUS (DONUT)
# ---------------------------------------------------------
n_success = int(df['is_success'].sum())
n_failed = int(df['is_failed'].sum())
n_total = int(len(df))

fig, ax = plt.subplots(figsize=(8, 6))
ax.pie([n_success, n_failed], colors=[NAVY, RED], startangle=90, counterclock=False,
       wedgeprops=dict(width=0.32, edgecolor='white', linewidth=3))
ax.text(0, 0.08, f'{n_success / n_total * 100:.2f}%', ha='center', va='center', fontsize=30, weight='semibold', color=INK)
ax.text(0, -0.16, 'success rate', ha='center', va='center', fontsize=11, color=MUTED)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=NAVY), plt.Rectangle((0, 0), 1, 1, color=RED)],
          labels=[f'Success  {n_success:,}  ({n_success / n_total * 100:.2f}%)',
                  f'Failed  {n_failed:,}  ({n_failed / n_total * 100:.2f}%)'],
          loc='upper center', bbox_to_anchor=(0.5, 0.02), ncol=2, fontsize=10, handlelength=1, handleheight=1)
ax.set_title(f'Transaction status, {n_total:,} transactions', loc='center', pad=10)
ax.set_aspect('equal')
save(fig, '01_overall_status_distribution.png')

# ---------------------------------------------------------
# 2. TOP 10 PRODUCTS: VOLUME VS FAILURE RATE
# ---------------------------------------------------------
prod_grp = df.groupby('product_code').agg(
    total=('status', 'count'),
    success=('is_success', 'sum'),
    failed=('is_failed', 'sum')
)
prod_grp['fail_rate'] = (prod_grp['failed'] / prod_grp['total']) * 100
prod_grp['success_rate'] = (prod_grp['success'] / prod_grp['total']) * 100
top10_prod = prod_grp.sort_values(by='total', ascending=False).head(10).reset_index()
overall_fail = n_failed / n_total * 100

fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()
x = np.arange(len(top10_prod))
ax1.bar(x, top10_prod['total'], 0.6, color=LIGHT, label='Transactions')
ax2.plot(x, top10_prod['fail_rate'], color=RED, marker='o', linewidth=2, markersize=6, label='Failure rate')
ax2.axhline(overall_fail, color=RED, linewidth=1, linestyle=':', alpha=0.7)
ax2.text(len(x) - 0.5, overall_fail, f'overall {overall_fail:.1f}%', color=RED, fontsize=8.5, ha='right', va='bottom')
for i, v in enumerate(top10_prod['fail_rate']):
    ax2.annotate(f'{v:.1f}%', (i, v), textcoords='offset points', xytext=(0, 9), ha='center', fontsize=8.5,
                 color=RED, weight='semibold', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
ax1.set_xticks(x)
ax1.set_xticklabels([f'{c}\n{t:,} tx' for c, t in zip(top10_prod['product_code'], top10_prod['total'])], fontsize=9)
ax1.yaxis.set_major_formatter(k_format)
ax1.set_ylim(0, top10_prod['total'].max() * 1.15)
ax1.grid(axis='y')
ax1.set_axisbelow(True)
ax1.set_ylabel('Transactions')
ax2.set_ylim(0, max(top10_prod['fail_rate'].max() * 1.25, 1))
ax2.yaxis.set_major_formatter(pct0)
ax2.set_ylabel('Failure rate', color=RED)
ax2.tick_params(axis='y', colors=RED)
ax2.spines['right'].set_visible(False)
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper right', ncol=2, bbox_to_anchor=(1, 1.1))
ax1.set_title('Top 10 SKUs by volume', pad=26)
top10_share = top10_prod['total'].sum() / n_total * 100
subtitle(ax1, f'These 10 SKUs carry {top10_share:.1f}% of all transactions')
save(fig, '02_top10_products_volume_and_failure_rate.png')

# ---------------------------------------------------------
# 3. CRITICAL FAILURE HOTSPOTS (SKUs WITH AT LEAST 1,000 TRANSACTIONS)
# ---------------------------------------------------------
high_fail_prod = prod_grp[prod_grp['total'] >= 1000].sort_values(by='fail_rate', ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
plot_df = high_fail_prod[::-1]
bar_colors = [RED if fr >= 30 else AMBER for fr in plot_df['fail_rate']]
ax.barh(plot_df['product_code'], plot_df['fail_rate'], color=bar_colors, height=0.62)
for y, (fr, tot) in enumerate(zip(plot_df['fail_rate'], plot_df['total'])):
    ax.text(fr + 0.8, y, f'{fr:.1f}%', va='center', fontsize=9.5, weight='semibold', color=INK)
    ax.text(fr + 6.3, y, f'of {tot:,} tx', va='center', fontsize=8.5, color=MUTED)
ax.axvline(overall_fail, color=MUTED, linewidth=1, linestyle=':')
ax.text(overall_fail + 0.5, -0.9, f'overall {overall_fail:.1f}%', fontsize=8.5, color=MUTED, va='center')
ax.set_xlim(0, 75)
ax.set_ylim(-1.2, len(plot_df) - 0.4)
ax.xaxis.set_major_formatter(pct0)
ax.grid(axis='x')
ax.set_axisbelow(True)
ax.spines['left'].set_visible(False)
ax.set_xlabel('Failure rate')
ax.set_title('Highest failure rates among SKUs with at least 1,000 transactions', pad=26)
subtitle(ax, 'Red: failure rate of 30% or more.  Amber: below 30%, still about twice the overall rate or higher')
save(fig, '03_critical_high_failure_products.png')

# ---------------------------------------------------------
# 4. BILLER VOLUME VS SHARE OF FAILURES
# ---------------------------------------------------------
biller_grp = df.groupby('biller_name').agg(
    total=('status', 'count'),
    success=('is_success', 'sum'),
    failed=('is_failed', 'sum')
)
biller_grp['fail_rate'] = (biller_grp['failed'] / biller_grp['total']) * 100
biller_grp['failure_contribution'] = (biller_grp['failed'] / df['is_failed'].sum()) * 100
top_billers = biller_grp.sort_values(by='total', ascending=False).head(8).reset_index()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True, gridspec_kw=dict(wspace=0.08))
plot_df = top_billers[::-1].reset_index(drop=True)
y = np.arange(len(plot_df))
hot = plot_df['fail_rate'] >= 2 * overall_fail  # billers failing at twice the overall rate or worse

ax1.barh(y, plot_df['total'], color=[NAVY if h else LIGHT for h in hot], height=0.62)
for i, (tot, share) in enumerate(zip(plot_df['total'], plot_df['total'] / n_total * 100)):
    ax1.text(tot + 2500, i, f'{tot:,}  ({share:.1f}%)', va='center', fontsize=9, color=INK)
ax1.set_xlim(0, plot_df['total'].max() * 1.45)
ax1.xaxis.set_major_formatter(k_format)
ax1.set_yticks(y)
ax1.set_yticklabels(plot_df['biller_name'])
ax1.set_title('Transactions (share of traffic)', fontsize=11.5)

ax2.barh(y, plot_df['failure_contribution'], color=[RED if h else LIGHT for h in hot], height=0.62)
for i, (fc, fl, fr) in enumerate(zip(plot_df['failure_contribution'], plot_df['failed'], plot_df['fail_rate'])):
    ax2.text(fc + 0.6, i, f'{fc:.1f}%  ({fl:,} failed, {fr:.1f}% fail rate)', va='center', fontsize=9, color=INK)
ax2.set_xlim(0, 62)
ax2.xaxis.set_major_formatter(pct0)
ax2.set_title(f'Share of all {n_failed:,} failures', fontsize=11.5)

for ax in (ax1, ax2):
    ax.grid(axis='x')
    ax.set_axisbelow(True)
    ax.spines['left'].set_visible(False)
hot_df = top_billers[top_billers['fail_rate'] >= 2 * overall_fail]
fig.suptitle('Top 8 billers: volume vs failures', x=0.125, ha='left', fontsize=14, weight='semibold', y=1.04)
fig.text(0.125, 0.975,
         f"{' and '.join(hot_df['biller_name'])} handle {hot_df['total'].sum() / n_total * 100:.1f}% of traffic "
         f"but cause {hot_df['failure_contribution'].sum():.1f}% of all failures. "
         f"{top_billers.loc[0, 'biller_name']}'s share comes from volume, not reliability "
         f"({top_billers.loc[0, 'fail_rate']:.1f}% fail rate)",
         fontsize=10, color=MUTED, ha='left')
save(fig, '04_biller_performance_and_sla.png')

# ---------------------------------------------------------
# 5. HOURLY TRAFFIC & FAILURE RATE (24 HOURS)
# ---------------------------------------------------------
hourly_grp = df.groupby('transaction_hour').agg(
    total=('status', 'count'),
    failed=('is_failed', 'sum')
).reset_index()
hourly_grp['fail_rate'] = (hourly_grp['failed'] / hourly_grp['total']) * 100
peak = hourly_grp.loc[hourly_grp['total'].idxmax()]

fig, ax1 = plt.subplots(figsize=(13, 6))
ax2 = ax1.twinx()
x = hourly_grp['transaction_hour']
ax1.axvspan(16.5, 19.5, color='#FEF3C7', alpha=0.7, zorder=0)
ax1.bar(x, hourly_grp['total'], 0.7, color=[NAVY if h == peak['transaction_hour'] else LIGHT for h in x],
        label='Transactions (3 days combined)', zorder=2)
ax1.annotate(f"Peak {int(peak['transaction_hour']):02d}:00\n{int(peak['total']):,} tx",
             (peak['transaction_hour'], peak['total']), textcoords='offset points', xytext=(0, 8),
             ha='center', fontsize=9, weight='semibold', color=NAVY)
ax2.plot(x, hourly_grp['fail_rate'], color=RED, marker='o', markersize=4, linewidth=1.8, label='Failure rate', zorder=3)
ax1.text(18, hourly_grp['total'].max() * 1.17, 'Evening rush 17:00-19:00', ha='center', fontsize=8.5, color='#92400E')
ax1.set_xticks(range(24))
ax1.set_xticklabels([f'{h:02d}' for h in range(24)])
ax1.set_xlim(-0.6, 23.6)
ax1.set_xlabel('Hour of day (WIB)')
ax1.set_ylim(0, hourly_grp['total'].max() * 1.25)
ax1.yaxis.set_major_formatter(k_format)
ax1.set_ylabel('Transactions')
ax1.grid(axis='y')
ax1.set_axisbelow(True)
ax2.set_ylim(0, 20)
ax2.set_yticks([0, 5, 10, 15, 20])
ax2.yaxis.set_major_formatter(pct0)
ax2.set_ylabel('Failure rate', color=RED)
ax2.tick_params(axis='y', colors=RED)
ax2.spines['right'].set_visible(False)
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper right', ncol=2, bbox_to_anchor=(1, 1.1))
ax1.set_title('Hourly load and failure rate (1, 5 and 6 Aug 2026 combined)', pad=26)
subtitle(ax1, f"Failure rate stays between {hourly_grp['fail_rate'].min():.1f}% and {hourly_grp['fail_rate'].max():.1f}% "
              f"across the day; the peak hour does not raise it")
save(fig, '05_hourly_traffic_load_and_failure_trend.png')

# ---------------------------------------------------------
# 6. PARETO CONCENTRATION (SKUs)
# ---------------------------------------------------------
pareto_prod = prod_grp.sort_values(by='total', ascending=False).reset_index()
pareto_prod['cum_vol'] = pareto_prod['total'].cumsum()
pareto_prod['cum_pct'] = (pareto_prod['cum_vol'] / pareto_prod['total'].sum()) * 100
n_to_80 = int((pareto_prod['cum_pct'] < 80).sum()) + 1  # first SKU count whose cumulative share passes 80%
pareto_top = pareto_prod.head(20)

fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()
xs = np.arange(len(pareto_top))
ax1.bar(xs, pareto_top['total'], 0.65, color=[NAVY if i < n_to_80 else LIGHT for i in xs])
ax2.plot(xs, pareto_top['cum_pct'], color=AMBER, marker='o', markersize=4.5, linewidth=2)
ax2.axhline(80, color=MUTED, linestyle=':', linewidth=1)
ax2.text(len(pareto_top) - 0.4, 77, '80%', fontsize=8.5, color=MUTED, ha='right', va='top')
cut = n_to_80 - 1
ax2.annotate(f'{n_to_80} SKUs reach {pareto_prod.loc[cut, "cum_pct"]:.1f}%',
             (cut, pareto_prod.loc[cut, 'cum_pct']), textcoords='offset points', xytext=(-30, -38),
             ha='right', fontsize=9, weight='semibold', color=INK,
             arrowprops=dict(arrowstyle='-', color=MUTED, linewidth=0.8))
ax1.set_xticks(xs)
ax1.set_xticklabels(pareto_top['product_code'], rotation=45, ha='right', fontsize=8.5)
ax1.yaxis.set_major_formatter(k_format)
ax1.set_ylabel('Transactions')
ax1.grid(axis='y')
ax1.set_axisbelow(True)
ax2.set_ylim(0, 105)
ax2.yaxis.set_major_formatter(pct0)
ax2.set_ylabel('Cumulative share of volume', color='#B45309')
ax2.tick_params(axis='y', colors='#B45309')
ax2.spines['right'].set_visible(False)
ax1.set_title(f'Volume concentration: top 20 of {len(pareto_prod)} SKUs', pad=26)
subtitle(ax1, f"Top 5 SKUs carry {pareto_prod.loc[4, 'cum_pct']:.1f}% of volume; "
              f"{n_to_80} of {len(pareto_prod)} SKUs ({n_to_80 / len(pareto_prod) * 100:.1f}%) pass 80%")
save(fig, '06_pareto_volume_concentration.png')

# ---------------------------------------------------------
# EXPORT METRICS JSON
# ---------------------------------------------------------
summary_metrics = {
    'total_transactions': n_total,
    'total_success': n_success,
    'total_failed': n_failed,
    'success_rate_pct': float(round(n_success / n_total * 100, 2)),
    'failure_rate_pct': float(round(n_failed / n_total * 100, 2)),
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

with open(os.path.join(metrics_dir, 'summary_metrics.json'), 'w') as f:
    json.dump(summary_metrics, f, indent=2)

print(f'Charts written to {fig_dir}; metrics written to {metrics_dir}')
