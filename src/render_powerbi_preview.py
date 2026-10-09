"""Step 5 of the pipeline (optional): render static PNG previews of the two Power BI report pages from the cleaned database.

The .pbip report is the real deliverable; these images exist so the README can show the
pages without Power BI Desktop. Output: powerbi/preview/*.png. Run from the project root: python src/render_powerbi_preview.py
"""
import os
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "powerbi", "preview")
df = pd.read_sql_query(
    "SELECT request_timestamp, product_code, biller_name, status, customer_number FROM transactions",
    sqlite3.connect(os.path.join(ROOT, "data", "database", "ppob_transactions_aug2026.db")),
)
df["product_code"] = df["product_code"].str.strip().str.upper()
df["failed"] = (df["status"].str.lower() != "success").astype(int)
df["hour"] = pd.to_datetime(df["request_timestamp"]).dt.hour
N, F = len(df), int(df["failed"].sum())

INK, MUTED, GRID, RED, AMBER, BLUE, NAVY = "#0f172a", "#64748b", "#e2e8f0", "#e5484d", "#f59e0b", "#5b7fb0", "#1e3a5f"
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False})


def kfmt(v):
    return f"{v/1000:.1f}K" if v >= 1000 else f"{v:.0f}"


def card(fig, x, y, w, h):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
                                      transform=fig.transFigure, fc="white", ec=GRID, lw=1.2, zorder=-5))


def header(fig, subtitle):
    fig.text(0.02, 0.945, "PPOB Transaction Operations", fontsize=24, weight="bold", color=INK)
    fig.text(0.02, 0.91, subtitle, fontsize=12, color=MUTED)
    for x, lab in [(0.655, "Date"), (0.825, "Biller")]:
        fig.text(x, 0.955, lab, fontsize=10, color=MUTED)
        card(fig, x, 0.895, 0.155, 0.045)
        fig.text(x + 0.008, 0.912, "All", fontsize=11, color=INK)
        fig.text(x + 0.14, 0.912, "▾", fontsize=11, color=MUTED)


def panel(fig, rect, title, sub=None):
    x, y, w, h = rect
    card(fig, x, y, w, h)
    fig.text(x + 0.012, y + h - 0.035, title, fontsize=13, weight="bold", color=INK)
    if sub:
        fig.text(x + 0.012, y + h - 0.06, sub, fontsize=9.5, color=MUTED)


def table(fig, x0, y0, cols, xs, rows, colors=None, rowh=0.027):
    for c, x in zip(cols, xs):
        fig.text(x, y0, c, fontsize=10, weight="bold", color=MUTED, ha="left" if x == xs[0] else "right")
    for i, r in enumerate(rows):
        y = y0 - (i + 1) * rowh
        for j, (v, x) in enumerate(zip(r, xs)):
            col = (colors[i][j] if colors else None) or INK
            fig.text(x, y, v, fontsize=10, color=col, ha="left" if j == 0 else "right")
        fig.lines.append(plt.Line2D([x0, xs[-1] + 0.005], [y - 0.008] * 2, transform=fig.transFigure, color=GRID, lw=0.8))


def status(fr):
    return ("Critical", RED) if fr > 20 else ("Warning", AMBER) if fr >= 10 else ("Healthy", MUTED)


# ---------------- Page 1: overview ----------------
fig = plt.figure(figsize=(25.6, 14.4), dpi=100, facecolor="#f5f6f8")
header(fig, f"{N/1000:.0f}K transactions across 1, 5 and 6 August 2026 · Indonesian PPOB switching gateway")
kpis = [(kfmt(N), "Transactions", INK), (f"{(N-F)/N*100:.2f}%", "Success rate", INK), (kfmt(F), "Failed transactions", RED),
        (f"{F/N*100:.2f}%", "Failure rate", RED), (kfmt(df['customer_number'].nunique()), "Unique customers", INK)]
for i, (v, lab, c) in enumerate(kpis):
    x = 0.02 + i * 0.193
    card(fig, x, 0.75, 0.18, 0.125)
    fig.text(x + 0.09, 0.815, v, fontsize=30, weight="bold", color=c, ha="center")
    fig.text(x + 0.09, 0.772, lab, fontsize=12, color=MUTED, ha="center")

h = df.groupby("hour").agg(n=("failed", "size"), f=("failed", "mean"))
panel(fig, (0.02, 0.385, 0.585, 0.34), "Hourly load vs failure rate", "Transactions per hour, 3 days combined; the failure rate does not rise with volume")
ax = fig.add_axes([0.06, 0.42, 0.5, 0.225]); ax.bar(h.index, h.n, color="#9fb3cf", width=0.75)
ax.set_xticks(range(0, 24, 2)); ax.set_xticklabels([f"{x:02d}:00" for x in range(0, 24, 2)])
ax.yaxis.set_major_formatter(lambda v, _: kfmt(v)); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
ax2 = ax.twinx(); ax2.plot(h.index, h.f * 100, color=RED, marker="o", ms=4, lw=2); ax2.set_ylim(0, 20); ax2.set_yticks([0, 5, 10, 15, 20])
ax2.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%"); ax2.spines[:].set_visible(False)

b = df.groupby("biller_name").failed.sum().sort_values(ascending=False).head(8) / F * 100
panel(fig, (0.615, 0.385, 0.365, 0.34), "Where failures come from", "Share of all failed transactions by biller")
ax = fig.add_axes([0.665, 0.41, 0.28, 0.24]); y = range(len(b))[::-1]
ax.barh(list(y), b.values, color=[RED if n in ("Biller_29", "Biller_26") else BLUE for n in b.index], height=0.6)
ax.set_yticks(list(y)); ax.set_yticklabels(b.index); ax.set_xticks([]); ax.spines[:].set_visible(False)
for yy, v in zip(y, b.values):
    ax.text(v + 0.5, yy, f"{v:.1f}%", va="center", fontsize=10, color=INK)

p = df.groupby("product_code").agg(n=("failed", "size"), f=("failed", "mean")).sort_values("n", ascending=False)
top20 = p.head(20); cum = top20.n.cumsum() / N * 100
panel(fig, (0.02, 0.025, 0.585, 0.345), "SKU demand concentration (top 20)",
      f"Top 5 SKUs carry {p.n.head(5).sum()/N*100:.0f}% of volume; {int((p.n.cumsum()/N*100 < 80).sum()) + 1} SKUs pass 80%")
ax = fig.add_axes([0.06, 0.085, 0.5, 0.2]); ax.bar(range(20), top20.n, color=NAVY, width=0.6)
ax.set_xticks(range(20)); ax.set_xticklabels(top20.index, rotation=45, fontsize=9)
ax.yaxis.set_major_formatter(lambda v, _: kfmt(v)); ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
ax2 = ax.twinx(); ax2.plot(range(20), cum.values, color=AMBER, marker="o", ms=4, lw=2); ax2.set_ylim(0, 100)
ax2.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%"); ax2.spines[:].set_visible(False)

panel(fig, (0.615, 0.025, 0.365, 0.345), "Top 10 SKUs by volume")
rows, cols = [], []
for code, r in p.head(10).iterrows():
    s, c = status(r.f * 100)
    rows.append([code, f"{int(r.n):,}", f"{r.f*100:.2f}%", s]); cols.append([None, None, c if c != MUTED else None, c])
table(fig, 0.627, 0.3, ["SKU", "Transactions", "Failure rate", "Status"], [0.627, 0.74, 0.84, 0.965], rows, cols, rowh=0.025)
fig.savefig(os.path.join(OUT, "01_overview.png"), facecolor=fig.get_facecolor())
plt.close(fig)

# ---------------- Page 2: biller and SKU diagnostics ----------------
fig = plt.figure(figsize=(25.6, 14.4), dpi=100, facecolor="#f5f6f8")
header(fig, "Biller performance, failure concentration and SKU-level anomalies")
bl = df.groupby("biller_name").agg(n=("failed", "size"), f=("failed", "mean"), fails=("failed", "sum"))
panel(fig, (0.02, 0.45, 0.47, 0.425), "Biller volume vs failure rate", "Top-left = small billers with outsized failure rates")
ax = fig.add_axes([0.06, 0.48, 0.41, 0.31])
ax.scatter(bl.n, bl.f * 100, c=[RED if v > 0.2 else BLUE for v in bl.f], s=45, zorder=3)
for nme in ["Biller_29", "Biller_26", "Biller_31", "Biller_27"]:
    ax.annotate(nme, (bl.loc[nme, "n"], bl.loc[nme, "f"] * 100), xytext=(6, 6), textcoords="offset points", fontsize=10)
ax.xaxis.set_major_formatter(lambda v, _: kfmt(v)); ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
ax.grid(color=GRID); ax.set_axisbelow(True)

crit = p[p.n >= 1000].sort_values("f", ascending=False).head(12)
panel(fig, (0.505, 0.45, 0.475, 0.425), "Failure rate by SKU (min. 1,000 transactions)", "Red = critical (>20%), amber = warning (10–20%)")
ax = fig.add_axes([0.56, 0.47, 0.38, 0.33]); y = list(range(len(crit)))[::-1]
ax.barh(y, crit.f * 100, color=[RED if v > 0.2 else AMBER for v in crit.f], height=0.65)
ax.set_yticks(y); ax.set_yticklabels(crit.index); ax.set_xticks([]); ax.spines[:].set_visible(False)
for yy, v in zip(y, crit.f * 100):
    ax.text(v + 0.6, yy, f"{v:.1f}%", va="center", fontsize=10, color=INK)

panel(fig, (0.02, 0.025, 0.96, 0.41), "Biller scorecard")
rows, cols = [], []
for nme, r in bl.sort_values("fails", ascending=False).head(9).iterrows():
    s, c = status(r.f * 100)
    rows.append([nme, f"{int(r.n):,}", f"{r.n/N*100:.1f}%", f"{int(r.fails):,}", f"{r.f*100:.2f}%", f"{r.fails/F*100:.1f}%", s])
    cols.append([None, None, None, None, c if c != MUTED else None, None, c])
table(fig, 0.03, 0.37, ["Biller", "Transactions", "Volume share", "Failed", "Failure rate", "Share of failures", "Status"],
      [0.03, 0.26, 0.39, 0.51, 0.65, 0.8, 0.9], rows, cols, rowh=0.035)
fig.savefig(os.path.join(OUT, "02_biller_sku_diagnostics.png"), facecolor=fig.get_facecolor())
print("Previews written to", OUT)
