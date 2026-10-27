# =====================================================================
# Cognifyz Technologies - Data Analysis Internship
# LEVEL 3: Restaurant Reviews | Votes Analysis | Price Range vs Services
# =====================================================================
# How to run:  python level3_analysis.py   (from inside the "code" folder)
# Needs:       pandas, numpy, matplotlib, seaborn, scipy
# =====================================================================

# %% ---------- 0. Setup ----------
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

sns.set_theme(style="whitegrid")

# ---------- Rounding helper (used for EVERY rounded number in this project) ----------
# Python's built-in round() can round 4.475 down to 4.47 because decimals like 4.475 are stored
# slightly inaccurately in a computer. This helper rounds "half up" (4.475 -> 4.48), the way people
# expect. Values are always rounded ONCE, from the full-precision number (never from an already rounded one).
from decimal import Decimal, ROUND_HALF_UP

def round_half_up(value, decimals=2):
    """Round a number, Series, DataFrame or array half-up to `decimals` places."""
    if isinstance(value, pd.DataFrame):
        return value.map(lambda v: round_half_up(v, decimals))
    if isinstance(value, pd.Series):
        return value.map(lambda v: round_half_up(v, decimals))
    if isinstance(value, np.ndarray):
        return np.array([round_half_up(v, decimals) for v in value])
    if value is None or pd.isna(value):
        return value
    step = Decimal(1).scaleb(-decimals)
    return float(Decimal(repr(round(float(value), 10))).quantize(step, rounding=ROUND_HALF_UP))

rh = round_half_up   # short name
BASE = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path("..")
CHARTS, TABLES = BASE / "charts", BASE / "tables"
CHARTS.mkdir(exist_ok=True); TABLES.mkdir(exist_ok=True)

candidates = [BASE / "data" / "Dataset .csv", BASE / "data" / "Dataset_.csv", BASE / "data" / "Dataset.csv"]
DATA_FILE = next(p for p in candidates if p.exists())
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()
rated = df[df["Aggregate rating"] > 0].copy()
results = {}

# %% ---------- 1. TASK 1: Restaurant reviews ----------
# The PDF asks for TEXT reviews (keywords, review length). Check whether any such column exists.
text_like = [c for c in df.columns if any(w in c.lower() for w in ["review", "comment", "feedback", "text"])]
print("Columns that might hold review text:", text_like)
print("Rating text values (these are only 6 fixed labels, not customer reviews):")
print(df["Rating text"].value_counts())
print("Longest text in 'Rating text' (characters):", df["Rating text"].str.len().max())
results["t1"] = {"possible_text_columns": text_like, "rating_text_counts": df["Rating text"].value_counts().to_dict(),
                 "rating_text_unique": int(df["Rating text"].nunique())}
# CONCLUSION: the dataset has no written customer reviews, so keyword analysis, average review length
# and review-length-vs-rating CANNOT be calculated. We do not fake it with the rating labels.

# %% ---------- 2. TASK 2: Votes analysis ----------
cols = ["Restaurant Name", "City", "Votes", "Aggregate rating"]
top_votes = df.sort_values("Votes", ascending=False)[cols].head(10)
top_votes.to_csv(TABLES / "l3t2_top10_votes.csv", index=False)
print("\nTOP 10 BY VOTES"); print(top_votes.to_string(index=False))

zero_votes = int((df["Votes"] == 0).sum())
print("Restaurants with 0 votes:", zero_votes)
min_votes_rated = int(rated["Votes"].min())
rated_low = rated[rated["Votes"] == min_votes_rated]
print(f"Lowest vote count among RATED restaurants: {min_votes_rated} ({len(rated_low)} restaurants)")
low_sample = df[df["Votes"] == 0][cols].head(5)
results["t2"] = {"top10": top_votes.to_dict("records"), "zero_votes": zero_votes,
                 "zero_votes_pct": rh(zero_votes / len(df) * 100, 2),
                 "zero_votes_and_unrated": int(((df["Votes"] == 0) & (df["Aggregate rating"] == 0)).sum()),
                 "min_votes_rated": min_votes_rated, "n_min_votes_rated": int(len(rated_low)),
                 "median_votes": float(df["Votes"].median()), "low_sample": low_sample.to_dict("records")}

# Correlation. Method: rated restaurants only (rating 0 = "not rated", not a real score).
r_p, p_p = stats.pearsonr(rated["Votes"], rated["Aggregate rating"])
r_s, p_s = stats.spearmanr(rated["Votes"], rated["Aggregate rating"])
r_log, _ = stats.pearsonr(np.log1p(rated["Votes"]), rated["Aggregate rating"])
r_all, _ = stats.spearmanr(df["Votes"], df["Aggregate rating"])      # for comparison: includes unrated zeros
print(f"\nPearson r = {rh(r_p, 2):.2f} | Spearman rho = {rh(r_s, 2):.2f} | Pearson on log(votes+1) = {rh(r_log, 2):.2f} | n = {len(rated)}")
print(f"For comparison, Spearman with unrated included = {rh(r_all, 2):.2f}")
# average rating by vote bucket (easy to explain)
rated["Vote group"] = pd.cut(rated["Votes"], bins=[-1, 10, 50, 200, 1000, 100000],
                             labels=["0-10", "11-50", "51-200", "201-1000", "1000+"])
vote_group = rated.groupby("Vote group", observed=True)["Aggregate rating"].agg(["count", "mean"])
vote_group["mean"] = rh(vote_group["mean"], 2)
print(vote_group); vote_group.reset_index().to_csv(TABLES / "l3t2_rating_by_vote_group.csv", index=False)
results["t2"].update({"pearson": rh(r_p, 2), "spearman": rh(r_s, 2), "pearson_log": rh(r_log, 2),
                      "spearman_with_unrated": rh(r_all, 2), "n": int(len(rated)),
                      "p_pearson": float(p_p), "vote_group": vote_group.reset_index().astype({"Vote group": str}).to_dict("records")})

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
axes[0].scatter(rated["Votes"], rated["Aggregate rating"], s=8, alpha=0.3, color="#4c78a8")
axes[0].set_xscale("log"); axes[0].set_xlabel("Number of votes (log scale)"); axes[0].set_ylabel("Aggregate rating")
axes[0].set_title(f"Votes vs Rating (rated restaurants, n={len(rated):,})")
axes[0].text(0.03, 0.05, f"Spearman rho = {rh(r_s, 2):.2f}\nPearson r = {rh(r_p, 2):.2f}", transform=axes[0].transAxes, bbox=dict(fc="white", ec="grey"))
vg = vote_group.reset_index()
axes[1].bar(vg["Vote group"].astype(str), vg["mean"], color="#f28e2b")
for i, (m, n) in enumerate(zip(vg["mean"], vg["count"])): axes[1].text(i, m + 0.04, f"{m:.2f}\n(n={n:,})", ha="center")
axes[1].set_ylim(0, 5); axes[1].set_xlabel("Votes received (group)"); axes[1].set_ylabel("Average aggregate rating")
axes[1].set_title("Average Rating by Number of Votes")
plt.tight_layout(); plt.savefig(CHARTS / "l3t2_votes_vs_rating.png", dpi=150); plt.close()

# %% ---------- 3. TASK 3: Price range vs online delivery & table booking ----------
def service_table(col, name):
    counts = pd.crosstab(df["Price range"], df[col])
    pct = rh(counts.div(counts.sum(axis=1), axis=0) * 100, 2)      # denominator = restaurants in that price range
    out = pd.DataFrame({"Price range": counts.index, "Total": counts.sum(axis=1).values,
                        f"{name} Yes": counts["Yes"].values, f"{name} No": counts["No"].values,
                        f"{name} Yes %": pct["Yes"].values})
    chi2, p, _, _ = stats.chi2_contingency(counts)
    rho, p_rho = stats.spearmanr(df["Price range"], (df[col] == "Yes").astype(int))
    return out, chi2, p, rho

deliv, chi_d, p_d, rho_d = service_table("Has Online delivery", "Delivery")
book, chi_b, p_b, rho_b = service_table("Has Table booking", "Booking")
deliv.to_csv(TABLES / "l3t3_delivery_by_price.csv", index=False); book.to_csv(TABLES / "l3t3_booking_by_price.csv", index=False)
print("\nONLINE DELIVERY BY PRICE RANGE"); print(deliv.to_string(index=False))
print(f"chi-square = {chi_d:.1f}, p = {p_d:.2g}, Spearman rho = {rh(rho_d, 2):.2f}")
print("\nTABLE BOOKING BY PRICE RANGE"); print(book.to_string(index=False))
print(f"chi-square = {chi_b:.1f}, p = {p_b:.2g}, Spearman rho = {rh(rho_b, 2):.2f}")

# Robustness check: price range is relative to each country's currency, so repeat for India only (the biggest group)
ind = df[df["Country Code"] == 1]
ind_d = (pd.crosstab(ind["Price range"], ind["Has Online delivery"], normalize="index") * 100)["Yes"]
ind_b = (pd.crosstab(ind["Price range"], ind["Has Table booking"], normalize="index") * 100)["Yes"]
ind_d, ind_b = rh(ind_d, 2), rh(ind_b, 2)
print("India only - delivery Yes %:", ind_d.to_dict(), "| booking Yes %:", ind_b.to_dict())
results["t3"] = {"delivery": deliv.to_dict("records"), "booking": book.to_dict("records"),
                 "chi_d": rh(chi_d, 1), "p_d": float(p_d), "rho_d": rh(rho_d, 2),
                 "chi_b": rh(chi_b, 1), "p_b": float(p_b), "rho_b": rh(rho_b, 2),
                 "india_n": int(len(ind)), "india_delivery_pct": ind_d.to_dict(), "india_booking_pct": ind_b.to_dict(),
                 "overall_delivery_pct": rh((df["Has Online delivery"] == "Yes").mean() * 100, 2),
                 "overall_booking_pct": rh((df["Has Table booking"] == "Yes").mean() * 100, 2)}

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
for ax, tbl, col, title, color in [(axes[0], deliv, "Delivery Yes %", "Online Delivery by Price Range", "#4c78a8"),
                                   (axes[1], book, "Booking Yes %", "Table Booking by Price Range", "#59a14f")]:
    bars = ax.bar(tbl["Price range"].astype(str), tbl[col], color=color)
    for b, n in zip(bars, tbl["Total"]): ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.2, f"{b.get_height():.1f}%\n(of {n:,})", ha="center")
    ax.set_ylim(0, 100); ax.set_title(title); ax.set_xlabel("Price range (1 = lowest, 4 = highest)"); ax.set_ylabel("% of restaurants offering the service")
plt.tight_layout(); plt.savefig(CHARTS / "l3t3_price_vs_services.png", dpi=150); plt.close()

# %% ---------- 4. Save results ----------
(TABLES / "level3_results.json").write_text(json.dumps(results, indent=2, default=str))
print("\nLevel 3 finished.")
