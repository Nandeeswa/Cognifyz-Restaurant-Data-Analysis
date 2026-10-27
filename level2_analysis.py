# =====================================================================
# Cognifyz Technologies - Data Analysis Internship
# LEVEL 2: Restaurant Ratings | Cuisine Combination | Geographic | Chains
# =====================================================================
# How to run:  python level2_analysis.py   (from inside the "code" folder)
# Needs:       pandas, numpy, matplotlib, seaborn, folium
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

candidates = [BASE / "data" / "Dataset .csv", BASE / "data" / "Dataset_.csv", BASE / "data" / "Dataset.csv"]
DATA_FILE = next(p for p in candidates if p.exists())
df = pd.read_csv(DATA_FILE)
df.columns = df.columns.str.strip()

# Rating 0 / "Not rated" means no rating exists -> excluded from every average rating below.
df["Restaurant Name"] = df["Restaurant Name"].str.strip()   # clean restaurant names once, so chains are matched correctly
rated = df[df["Aggregate rating"] > 0].copy()
results = {}

# %% ---------- 1. TASK 1: Restaurant ratings ----------
# Rated restaurants are grouped into 0.5-wide bins: 1.5-1.9, 2.0-2.4, ... 4.5-4.9
bins = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.01]   # 5.01 so that a rating of exactly 5.0 would still be counted
labels = ["1.5-1.9", "2.0-2.4", "2.5-2.9", "3.0-3.4", "3.5-3.9", "4.0-4.4", "4.5-4.9"]
print("Lowest / highest rating among rated restaurants:", rated["Aggregate rating"].min(), rated["Aggregate rating"].max())
rated["Rating range"] = pd.cut(rated["Aggregate rating"], bins=bins, labels=labels, right=False)
range_counts = rated["Rating range"].value_counts().reindex(labels)
range_tbl = pd.DataFrame({"Rating range": labels, "Restaurants": range_counts.values,
                          "Percent of rated": rh(range_counts.values / len(rated) * 100, 2)})
range_tbl.to_csv(TABLES / "l2t1_rating_ranges.csv", index=False)
print(range_tbl.to_string(index=False))
common_range = range_tbl.sort_values("Restaurants", ascending=False).iloc[0]
exact_mode = rated["Aggregate rating"].mode().iloc[0]

votes_all = df["Votes"].mean(); votes_rated = rated["Votes"].mean()
print(f"Average votes - all {len(df)} restaurants: {votes_all:.2f} | rated only: {votes_rated:.2f} | median all: {df['Votes'].median()}")
results["t1"] = {"rated": int(len(rated)), "unrated": int(len(df) - len(rated)),
                 "mean_rating": rh(rated["Aggregate rating"].mean(), 2), "median_rating": float(rated["Aggregate rating"].median()),
                 "common_range": common_range["Rating range"], "common_range_n": int(common_range["Restaurants"]),
                 "common_range_pct": float(common_range["Percent of rated"]), "exact_mode": float(exact_mode),
                 "exact_mode_n": int((rated["Aggregate rating"] == exact_mode).sum()),
                 "avg_votes_all": rh(votes_all, 2), "avg_votes_rated": rh(votes_rated, 2),
                 "median_votes_all": float(df["Votes"].median()), "median_votes_rated": float(rated["Votes"].median()),
                 "max_votes": int(df["Votes"].max()), "ranges": range_tbl.to_dict("records"),
                 "unrated_max_votes": int(df.loc[df["Aggregate rating"] == 0, "Votes"].max())}

fig, ax = plt.subplots(figsize=(10, 5.5))
bars = ax.bar(range_tbl["Rating range"], range_tbl["Restaurants"], color="#4c78a8")
bars[range_tbl["Restaurants"].idxmax()].set_color("#d95f02")
for b in bars: ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 25, f"{int(b.get_height()):,}", ha="center")
ax.set_title(f"Distribution of Aggregate Ratings ({len(rated):,} rated restaurants; {len(df) - len(rated):,} unrated excluded)")
ax.set_xlabel("Aggregate rating range"); ax.set_ylabel("Number of restaurants"); ax.set_ylim(0, range_counts.max() * 1.12)
plt.tight_layout(); plt.savefig(CHARTS / "l2t1_rating_distribution.png", dpi=150); plt.close()

# %% ---------- 2. TASK 2: Cuisine combinations ----------
# Combination = the full set of cuisines a restaurant lists, sorted A-Z so that
# "Chinese, North Indian" and "North Indian, Chinese" are the same combination.
# Only restaurants listing 2 OR MORE cuisines are treated as a "combination".
cu = df.dropna(subset=["Cuisines"]).copy()
cu["cuisine_list"] = cu["Cuisines"].str.split(",").apply(lambda l: sorted(set(c.strip() for c in l)))
cu["n_cuisines"] = cu["cuisine_list"].apply(len)
cu["Combination"] = cu["cuisine_list"].apply(lambda l: " + ".join(l))
multi = cu[cu["n_cuisines"] >= 2]
print(f"\nRestaurants with cuisine data: {len(cu)} | with 2+ cuisines: {len(multi)} | single cuisine: {len(cu) - len(multi)}")

combo = multi.groupby("Combination").agg(Restaurants=("Restaurant ID", "count")).join(
        multi[multi["Aggregate rating"] > 0].groupby("Combination")["Aggregate rating"].agg(Rated="count", Avg_Rating="mean")).reset_index()
combo["Rated"] = combo["Rated"].fillna(0).astype(int)
# Avg_Rating stays exact for sorting/filtering; it is rounded once (half-up, 2 decimals) in the saved/printed copies
def rounded_avg(t):
    return t.assign(Avg_Rating=rh(t["Avg_Rating"], 2))

common = combo.sort_values("Restaurants", ascending=False)
rounded_avg(common.head(10)).to_csv(TABLES / "l2t2_common_combinations.csv", index=False)
print("Most common combinations:"); print(rounded_avg(common.head(10)).to_string(index=False))

MIN_RATED_COMBO = 20        # a combination needs at least 20 RATED restaurants to be ranked
reliable = combo[combo["Rated"] >= MIN_RATED_COMBO].sort_values("Avg_Rating", ascending=False)
rounded_avg(reliable).to_csv(TABLES / "l2t2_combinations_min20_by_rating.csv", index=False)
print(f"\nCombinations with >= {MIN_RATED_COMBO} rated restaurants: {len(reliable)}")
print(rounded_avg(reliable.head(8)).to_string(index=False)); print(rounded_avg(reliable.tail(3)).to_string(index=False))
overall_avg_multi = multi.loc[multi["Aggregate rating"] > 0, "Aggregate rating"].mean()
results["t2"] = {"n_cuisine_rows": int(len(cu)), "n_multi": int(len(multi)), "n_single": int(len(cu) - len(multi)),
                 "n_combos_total": int(len(combo)), "n_combos_min20": int(len(reliable)),
                 "overall_avg_multi": rh(overall_avg_multi, 2), "overall_avg_rated": rh(rated["Aggregate rating"].mean(), 2),
                 "most_common": rounded_avg(common.head(10)).to_dict("records"),
                 "best": rounded_avg(reliable.head(8)).to_dict("records"), "worst": rounded_avg(reliable.tail(3)).to_dict("records"),
                 "min_threshold": MIN_RATED_COMBO}

fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
c10 = common.head(10).iloc[::-1]
axes[0].barh(c10["Combination"], c10["Restaurants"], color="#4c78a8")
for i, v in enumerate(c10["Restaurants"]): axes[0].text(v + 5, i, str(v), va="center")
axes[0].set_title("10 Most Common Cuisine Combinations"); axes[0].set_xlabel("Number of restaurants"); axes[0].set_ylabel("Cuisine combination")
axes[0].set_xlim(0, c10["Restaurants"].max() * 1.12)
r10 = rounded_avg(reliable.head(10)).iloc[::-1]
axes[1].barh(r10["Combination"], r10["Avg_Rating"], color="#59a14f")
for i, (v, n) in enumerate(zip(r10["Avg_Rating"], r10["Rated"])): axes[1].text(v + 0.02, i, f"{v:.2f} (n={n})", va="center")
axes[1].axvline(overall_avg_multi, color="red", ls="--", label=f"Average of all multi-cuisine = {rh(overall_avg_multi, 2):.2f}")
axes[1].set_title(f"Highest-Rated Combinations\n(minimum {MIN_RATED_COMBO} rated restaurants)")
axes[1].set_xlabel("Average aggregate rating"); axes[1].set_ylabel("Cuisine combination"); axes[1].set_xlim(0, 5.8); axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.12))
plt.tight_layout(); plt.savefig(CHARTS / "l2t2_cuisine_combinations.png", dpi=150); plt.close()

# %% ---------- 3. TASK 3: Geographic analysis ----------
# 497 restaurants have Longitude = 0 and Latitude = 0 (a missing-value placeholder in the
# Gulf of Guinea, not a real location). They are excluded from maps.
bad = (df["Longitude"] == 0) & (df["Latitude"] == 0)
geo = df[~bad].copy()
print(f"\nInvalid (0,0) coordinates: {bad.sum()} | plotted: {len(geo)}")
ncr = geo[(geo["Latitude"].between(28.2, 28.95)) & (geo["Longitude"].between(76.8, 77.7))]
print("Points in Delhi-NCR box:", len(ncr), f"({len(ncr) / len(geo) * 100:.1f}% of plotted)")

fig, ax = plt.subplots(figsize=(12, 6))
ax.scatter(geo["Longitude"], geo["Latitude"], s=6, alpha=0.4, c="#d95f02")
ax.set_title(f"Restaurant Locations Worldwide in the Dataset ({len(geo):,} plotted)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
plt.tight_layout(); plt.savefig(CHARTS / "l2t3_geo_world.png", dpi=150); plt.close()

fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
axes[0].scatter(ncr["Longitude"], ncr["Latitude"], s=5, alpha=0.35, c="#4c78a8")
axes[0].set_title(f"Delhi-NCR Restaurant Locations ({len(ncr):,} points)"); axes[0].set_xlabel("Longitude"); axes[0].set_ylabel("Latitude")
hb = axes[1].hexbin(ncr["Longitude"], ncr["Latitude"], gridsize=45, cmap="YlOrRd", mincnt=1)
plt.colorbar(hb, ax=axes[1], label="Restaurants per hexagon")
axes[1].set_title("Delhi-NCR Density of Restaurants (hexbin)"); axes[1].set_xlabel("Longitude"); axes[1].set_ylabel("Latitude")
plt.tight_layout(); plt.savefig(CHARTS / "l2t3_geo_ncr_density.png", dpi=150); plt.close()

# Where are the clusters? Count by city and by locality
city_geo = geo["City"].value_counts().head(8)
loc_tbl = (geo.groupby(["Locality", "City"]).size().reset_index(name="Restaurants").sort_values("Restaurants", ascending=False).head(10))
loc_tbl.to_csv(TABLES / "l2t3_top_localities.csv", index=False)
country_share = (geo["Country Code"] == 1).mean() * 100
print(loc_tbl.to_string(index=False)); print("Share of plotted points in India:", rh(country_share, 2))
# Densest 0.01-degree grid cell (about 1 km x 1 km) as a simple 'hotspot' measure
cell = (ncr["Latitude"].round(2).astype(str) + "," + ncr["Longitude"].round(2).astype(str)).value_counts()
top_cell = cell.head(3)
print("Densest ~1 km grid cells (lat,lon: count):"); print(top_cell)
results["t3"] = {"plotted": int(len(geo)), "invalid_zero": int(bad.sum()), "ncr_points": int(len(ncr)),
                 "ncr_pct": rh(len(ncr) / len(geo) * 100, 2), "india_pct": rh(country_share, 2),
                 "n_countries": int(df["Country Code"].nunique()), "top_localities": loc_tbl.to_dict("records"),
                 "densest_cells": {k: int(v) for k, v in top_cell.items()},
                 "city_top": {k: int(v) for k, v in city_geo.items()},
                 "invalid_in_country": df[bad]["Country Code"].value_counts().head(5).to_dict()}

# Interactive map (opens in any web browser). Needs: pip install folium
try:
    import folium
    from folium.plugins import HeatMap, MarkerCluster
    m = folium.Map(location=[28.6139, 77.2090], zoom_start=10, tiles="OpenStreetMap")
    HeatMap(geo[["Latitude", "Longitude"]].values.tolist(), radius=8, blur=10, name="Density heatmap").add_to(m)
    sample = ncr.sample(1500, random_state=42)       # sample keeps the file light
    mc = MarkerCluster(name="Restaurant markers (sample of 1,500)").add_to(m)
    for _, r in sample.iterrows():
        folium.Marker([r["Latitude"], r["Longitude"]], popup=f"{r['Restaurant Name']} | rating {r['Aggregate rating']}").add_to(mc)
    folium.LayerControl().add_to(m)
    m.save(str(CHARTS / "l2t3_restaurant_map.html")); print("Interactive map saved.")
except ImportError:
    print("folium not installed - skipped interactive map (pip install folium)")

# %% ---------- 4. TASK 4: Restaurant chains ----------
# Chain = the same Restaurant Name appearing 2+ times in the dataset (name-based rule).
# Limitation: two unrelated restaurants can share a name; outlets are counted by dataset rows.
name_counts = df["Restaurant Name"].value_counts()   # names were already cleaned (spaces removed) at the top
chains_names = name_counts[name_counts >= 2].index
ch = df[df["Restaurant Name"].isin(chains_names)].copy()
chain_tbl = ch.groupby("Restaurant Name").agg(Outlets=("Restaurant ID", "count"), Total_Votes=("Votes", "sum"),
                                              Cities=("City", "nunique")).join(
            ch[ch["Aggregate rating"] > 0].groupby("Restaurant Name")["Aggregate rating"].agg(Rated_Outlets="count", Avg_Rating="mean")).reset_index()
chain_tbl["Rated_Outlets"] = chain_tbl["Rated_Outlets"].fillna(0).astype(int)
chain_tbl["Avg_Votes_per_Outlet"] = chain_tbl["Total_Votes"] / chain_tbl["Outlets"]
# Exact values are used for sorting/filtering; saved and printed copies are rounded once (half-up)
def rounded_chain(t):
    return t.assign(Avg_Rating=rh(t["Avg_Rating"], 2), Avg_Votes_per_Outlet=rh(t["Avg_Votes_per_Outlet"], 1))

rounded_chain(chain_tbl.sort_values("Outlets", ascending=False)).to_csv(TABLES / "l2t4_all_chains.csv", index=False)

# Ranking rule: (1) number of outlets; ties are broken by total votes (popularity).
lead = chain_tbl.sort_values(["Outlets", "Total_Votes"], ascending=False).head(10)
rounded_chain(lead).to_csv(TABLES / "l2t4_top10_chains.csv", index=False)
print(f"\nNames with 2+ outlets: {len(chains_names)} | outlets in those chains: {len(ch)} ({rh(len(ch) / len(df) * 100, 2):.2f}% of rows)")
print(rounded_chain(lead).to_string(index=False))
by_votes = chain_tbl.sort_values("Total_Votes", ascending=False).head(5)
big = chain_tbl[chain_tbl["Rated_Outlets"] >= 10].sort_values("Avg_Rating", ascending=False)   # fair quality comparison
print("Most total votes:"); print(rounded_chain(by_votes).to_string(index=False))
print("Best average rating among chains with >=10 rated outlets:"); print(rounded_chain(big.head(5)).to_string(index=False)); print(rounded_chain(big.tail(3)).to_string(index=False))
rounded_chain(big).to_csv(TABLES / "l2t4_chains_min10_by_rating.csv", index=False)
non_chain_avg = df[(~df["Restaurant Name"].isin(chains_names)) & (df["Aggregate rating"] > 0)]["Aggregate rating"].mean()
chain_avg = ch[ch["Aggregate rating"] > 0]["Aggregate rating"].mean()
results["t4"] = {"n_chain_names": int(len(chains_names)), "chain_outlets": int(len(ch)), "chain_outlets_pct": rh(len(ch) / len(df) * 100, 2),
                 "unique_names": int(df["Restaurant Name"].nunique()),
                 "top10": rounded_chain(lead).to_dict("records"), "by_votes": rounded_chain(by_votes).to_dict("records"),
                 "best_min10": rounded_chain(big.head(5)).to_dict("records"), "worst_min10": rounded_chain(big.tail(3)).to_dict("records"),
                 "n_min10": int(len(big)), "chain_avg": rh(chain_avg, 2), "non_chain_avg": rh(non_chain_avg, 2)}

fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)
l = rounded_chain(lead).iloc[::-1]
axes[0].barh(l["Restaurant Name"], l["Outlets"], color="#4c78a8"); axes[0].set_title("Number of Outlets"); axes[0].set_xlabel("Outlets"); axes[0].set_ylabel("Restaurant chain")
axes[1].barh(l["Restaurant Name"], l["Avg_Rating"], color="#59a14f"); axes[1].set_title("Average Rating (rated outlets)"); axes[1].set_xlabel("Average rating"); axes[1].set_xlim(0, 5)
axes[2].barh(l["Restaurant Name"], l["Total_Votes"], color="#f28e2b"); axes[2].set_title("Total Votes (popularity)"); axes[2].set_xlabel("Total votes")
fig.suptitle("Top 10 Restaurant Chains (ranked by number of outlets, ties by total votes)")
plt.tight_layout(); plt.savefig(CHARTS / "l2t4_restaurant_chains.png", dpi=150); plt.close()

# %% ---------- 5. Save results ----------
(TABLES / "level2_results.json").write_text(json.dumps(results, indent=2, default=str))
print("\nLevel 2 finished.")
