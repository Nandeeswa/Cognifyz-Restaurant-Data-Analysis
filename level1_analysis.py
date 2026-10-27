# =====================================================================
# Cognifyz Technologies - Data Analysis Internship
# LEVEL 1: Top Cuisines | City Analysis | Price Range | Online Delivery
# =====================================================================
# How to run:  python level1_analysis.py   (from inside the "code" folder)
# Needs:       pandas, numpy, matplotlib, seaborn
# Output:      charts in ../charts, tables in ../tables, results in ../tables/level1_results.json
# =====================================================================

# %% ---------- 0. Setup ----------
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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

# The CSV is called "Dataset .csv" (with a space). Put it in the "data" folder.
candidates = [BASE / "data" / "Dataset .csv", BASE / "data" / "Dataset_.csv", BASE / "data" / "Dataset.csv"]
DATA_FILE = next(p for p in candidates if p.exists())
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()          # remove accidental spaces in column names

results = {}

# %% ---------- 1. Understand the data ----------
print("Rows, columns:", df.shape)
print("Columns:", list(df.columns))
print("Missing values (only columns with gaps):")
print(df.isna().sum()[df.isna().sum() > 0])
print("Duplicate rows:", df.duplicated().sum())
print("Duplicate Restaurant IDs:", df["Restaurant ID"].duplicated().sum())

# "Aggregate rating" = 0 together with Rating text "Not rated" means NO rating exists.
# These 0s are NOT real scores, so average-rating calculations use rated restaurants only.
rated = df[df["Aggregate rating"] > 0].copy()
results["rows"] = int(len(df)); results["columns"] = int(df.shape[1])
results["rated_restaurants"] = int(len(rated)); results["unrated_restaurants"] = int(len(df) - len(rated))
print(f"Rated: {len(rated)} | Not rated (rating = 0): {len(df) - len(rated)}")

# %% ---------- 2. TASK 1: Top cuisines ----------
# A restaurant can list several cuisines ("Chinese, North Indian").
# We split the list, so one restaurant counts once for EACH cuisine it serves.
# Denominator = restaurants that have cuisine information (9 are blank).
has_cuisine = df.dropna(subset=["Cuisines"]).copy()
n_cuisine = len(has_cuisine)
cuisine_lists = has_cuisine["Cuisines"].str.split(",").apply(lambda lst: sorted(set(c.strip() for c in lst)))
cuisine_counts = cuisine_lists.explode().value_counts()
cuisine_tbl = pd.DataFrame({"Cuisine": cuisine_counts.index,
                            "Restaurants": cuisine_counts.values,
                            "Percentage": rh(cuisine_counts.values / n_cuisine * 100, 2)})
cuisine_tbl.head(10).to_csv(TABLES / "l1t1_top_cuisines.csv", index=False)
top3 = cuisine_tbl.head(3)
print("\nTOP 3 CUISINES (denominator =", n_cuisine, "restaurants with cuisine data)")
print(top3.to_string(index=False))
results["t1_denominator"] = int(n_cuisine)
results["t1_unique_cuisines"] = int(len(cuisine_counts))
results["t1_top10"] = cuisine_tbl.head(10).to_dict("records")

top10 = cuisine_tbl.head(10)
plt.figure(figsize=(10, 6))
colors = ["#d95f02" if i < 3 else "#8fa8c8" for i in range(len(top10))]
ax = plt.barh(top10["Cuisine"][::-1], top10["Restaurants"][::-1], color=colors[::-1])
for rect, pct in zip(ax, top10["Percentage"][::-1]):
    plt.text(rect.get_width() + 30, rect.get_y() + rect.get_height() / 2, f"{pct:.2f}%", va="center")
plt.title("Top 10 Cuisines by Number of Restaurants (top 3 highlighted)")
plt.xlabel("Number of restaurants serving the cuisine"); plt.ylabel("Cuisine")
plt.xlim(0, top10["Restaurants"].max() * 1.12)
plt.tight_layout(); plt.savefig(CHARTS / "l1t1_top_cuisines.png", dpi=150); plt.close()

# %% ---------- 3. TASK 2: City analysis ----------
city_counts = df["City"].value_counts()
top_city = city_counts.index[0]
print(f"\nCity with most restaurants: {top_city} ({city_counts.iloc[0]})")

city_tbl = (df.groupby("City").agg(Restaurants=("Restaurant ID", "count")).join(
            rated.groupby("City").agg(Rated_Restaurants=("Aggregate rating", "count"),
                                      Avg_Rating=("Aggregate rating", "mean"))).reset_index())
city_tbl["Rated_Restaurants"] = city_tbl["Rated_Restaurants"].fillna(0).astype(int)
city_tbl = city_tbl.sort_values("Restaurants", ascending=False)   # Avg_Rating keeps full precision here; it is rounded only when saved
# Sorting and filtering use the exact averages; the saved/printed copies are rounded once (half-up, 2 decimals)
def rounded_city(t):
    return t.assign(Avg_Rating=rh(t["Avg_Rating"], 2))

rounded_city(city_tbl).to_csv(TABLES / "l1t2_city_table_all.csv", index=False)

# (a) Highest average with NO filter - may be misleading for tiny samples
raw_best = city_tbl.dropna(subset=["Avg_Rating"]).sort_values(["Avg_Rating", "Rated_Restaurants"], ascending=False)
print("Highest average rating, no minimum sample (top 5):")
print(rounded_city(raw_best.head(5)).to_string(index=False))
# (b) Highest average with a minimum of 20 rated restaurants (fairer comparison)
MIN_RATED = 20
fair = city_tbl[city_tbl["Rated_Restaurants"] >= MIN_RATED].sort_values("Avg_Rating", ascending=False)
rounded_city(fair).to_csv(TABLES / "l1t2_city_avg_rating_min20.csv", index=False)
print(f"Highest average rating with >= {MIN_RATED} rated restaurants (top 5):")
print(rounded_city(fair.head(5)).to_string(index=False))
results["t2_top_city"] = {"city": top_city, "restaurants": int(city_counts.iloc[0]),
                          "share_pct": rh(city_counts.iloc[0] / len(df) * 100, 2)}
results["t2_n_cities"] = int(df["City"].nunique())
results["t2_top5_by_count"] = rounded_city(city_tbl.head(5)).to_dict("records")
results["t2_raw_best_top5"] = rounded_city(raw_best.head(5)).to_dict("records")
results["t2_fair_best_top5"] = rounded_city(fair.head(5)).to_dict("records")
results["t2_n_cities_min20"] = int(len(fair))
results["t2_cities_with_1_rated"] = int((city_tbl["Rated_Restaurants"] <= 1).sum())

plt.figure(figsize=(10, 6))
c10 = city_counts.head(10)
sns.barplot(x=c10.values, y=c10.index, color="#4c78a8")
for i, v in enumerate(c10.values): plt.text(v + 40, i, f"{v:,}", va="center")
plt.title("Top 10 Cities by Number of Restaurants"); plt.xlabel("Number of restaurants"); plt.ylabel("City")
plt.xlim(0, c10.max() * 1.1)
plt.tight_layout(); plt.savefig(CHARTS / "l1t2_restaurants_by_city.png", dpi=150); plt.close()

plt.figure(figsize=(10, 6))
f10 = rounded_city(fair.head(10))
sns.barplot(x=f10["Avg_Rating"], y=f10["City"], color="#59a14f")
for i, (v, n) in enumerate(zip(f10["Avg_Rating"], f10["Rated_Restaurants"])): plt.text(v + 0.02, i, f"{v:.2f}  (n={n})", va="center")
plt.title(f"Top 10 Cities by Average Rating (minimum {MIN_RATED} rated restaurants)")
plt.xlabel("Average aggregate rating (rated restaurants only)"); plt.ylabel("City")
plt.xlim(0, 5.2)
plt.tight_layout(); plt.savefig(CHARTS / "l1t2_avg_rating_by_city.png", dpi=150); plt.close()

# %% ---------- 4. TASK 3: Price range distribution ----------
price_counts = df["Price range"].value_counts().sort_index()
price_tbl = pd.DataFrame({"Price range": price_counts.index, "Restaurants": price_counts.values,
                          "Percentage": rh(price_counts.values / len(df) * 100, 2)})
price_tbl.to_csv(TABLES / "l1t3_price_range.csv", index=False)
print("\nPRICE RANGE DISTRIBUTION (denominator =", len(df), ")")
print(price_tbl.to_string(index=False))
results["t3_price"] = price_tbl.to_dict("records")

plt.figure(figsize=(8, 5.5))
bars = plt.bar(price_tbl["Price range"].astype(str), price_tbl["Restaurants"], color="#f28e2b")
for b, p in zip(bars, price_tbl["Percentage"]):
    plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 60, f"{int(b.get_height()):,}\n({p:.2f}%)", ha="center")
plt.title("Distribution of Restaurant Price Ranges (1 = lowest, 4 = highest)")
plt.xlabel("Price range category"); plt.ylabel("Number of restaurants")
plt.ylim(0, price_counts.max() * 1.18)
plt.tight_layout(); plt.savefig(CHARTS / "l1t3_price_range.png", dpi=150); plt.close()

# %% ---------- 5. TASK 4: Online delivery ----------
delivery_counts = df["Has Online delivery"].value_counts()
yes_pct = delivery_counts["Yes"] / len(df) * 100
avg_by_delivery = rated.groupby("Has Online delivery")["Aggregate rating"].agg(["count", "mean", "median"])
avg_by_delivery["mean"] = rh(avg_by_delivery["mean"], 2)   # round once, from the exact mean
avg_all_zero_incl = rh(df.groupby("Has Online delivery")["Aggregate rating"].mean(), 2)  # for comparison only
print(f"\nOnline delivery: {delivery_counts['Yes']} of {len(df)} = {yes_pct:.2f}%")
print("Average rating (rated restaurants only):"); print(avg_by_delivery)
print("For comparison - average if unrated (0) rows were wrongly included:"); print(avg_all_zero_incl)
unrated_share = df.groupby("Has Online delivery")["Aggregate rating"].apply(lambda s: rh((s == 0).mean() * 100, 2))
print("Share of unrated restaurants:"); print(unrated_share)
avg_by_delivery.reset_index().to_csv(TABLES / "l1t4_delivery_rating.csv", index=False)
results["t4"] = {"yes": int(delivery_counts["Yes"]), "no": int(delivery_counts["No"]), "yes_pct": rh(yes_pct, 2),
                 "avg_yes": float(avg_by_delivery.loc["Yes", "mean"]), "avg_no": float(avg_by_delivery.loc["No", "mean"]),
                 "n_yes_rated": int(avg_by_delivery.loc["Yes", "count"]), "n_no_rated": int(avg_by_delivery.loc["No", "count"]),
                 "median_yes": float(avg_by_delivery.loc["Yes", "median"]), "median_no": float(avg_by_delivery.loc["No", "median"]),
                 "avg_yes_with_zero": float(avg_all_zero_incl["Yes"]), "avg_no_with_zero": float(avg_all_zero_incl["No"]),
                 "unrated_pct_yes": float(unrated_share["Yes"]), "unrated_pct_no": float(unrated_share["No"])}

# Extra check: compare ratings with and without delivery INSIDE each price range, to see whether the overall gap is consistent
by_price = rated.groupby(["Price range", "Has Online delivery"])["Aggregate rating"].mean().unstack()
by_price = rh(by_price, 2)
print("Average rating by price range and delivery:"); print(by_price)
by_price.reset_index().to_csv(TABLES / "l1t4_delivery_rating_by_price.csv", index=False)
results["t4_by_price"] = by_price.reset_index().to_dict("records")

fig, axes = plt.subplots(1, 2, figsize=(11, 5))
axes[0].bar(["Without delivery", "With delivery"], [avg_by_delivery.loc["No", "mean"], avg_by_delivery.loc["Yes", "mean"]],
            color=["#9d9d9d", "#4c78a8"])
for i, v in enumerate([avg_by_delivery.loc["No", "mean"], avg_by_delivery.loc["Yes", "mean"]]): axes[0].text(i, v + 0.05, f"{v:.2f}", ha="center")
axes[0].set_ylim(0, 5); axes[0].set_title("Average Rating by Online Delivery"); axes[0].set_ylabel("Average aggregate rating (rated only)")
axes[0].set_xlabel("Online delivery availability")
axes[1].pie([delivery_counts["No"], delivery_counts["Yes"]], labels=["No online delivery", "Online delivery"], autopct="%1.2f%%",
            colors=["#9d9d9d", "#4c78a8"], startangle=90)
axes[1].set_title("Share of Restaurants Offering Online Delivery")
plt.tight_layout(); plt.savefig(CHARTS / "l1t4_online_delivery.png", dpi=150); plt.close()

# %% ---------- 6. Save results ----------
(TABLES / "level1_results.json").write_text(json.dumps(results, indent=2, default=str))
print("\nLevel 1 finished. Charts and tables saved.")
