# =====================================================================
# verify_results.py - INDEPENDENT CHECK of the saved results
# =====================================================================
# This script recalculates the key numbers from the raw CSV using a different method
# (Python's csv module and exact fractions, not pandas groupby) and compares them with
# the tables/JSON files created by level1/2/3_analysis.py.
# Run AFTER the three analysis scripts:   python verify_results.py
# It prints "OK" for every match and "MISMATCH" for any difference.
# =====================================================================
import csv, json
from collections import Counter, defaultdict
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

BASE = Path(__file__).resolve().parent.parent
TABLES = BASE / "tables"
data_file = next(p for p in [BASE / "data" / "Dataset .csv", BASE / "data" / "Dataset_.csv", BASE / "data" / "Dataset.csv"] if p.exists())

with open(data_file, newline="", encoding="utf-8-sig", errors="replace") as fh:
    rows = list(csv.DictReader(fh))
rows = [{k.strip(): v for k, v in r.items()} for r in rows]

problems = []
def check(label, expected, saved):
    ok = (abs(float(expected) - float(saved)) < 1e-9)
    print(("OK       " if ok else "MISMATCH ") + f"{label}: recalculated={expected} saved={saved}")
    if not ok: problems.append(label)

def half_up(fr, nd=2):
    """Exact half-up rounding of a Fraction (no floating-point error)."""
    scaled = fr * (10 ** nd)
    return float((Decimal(scaled.numerator) / Decimal(scaled.denominator)).quantize(Decimal(1), rounding=ROUND_HALF_UP)) / 10 ** nd

def mean_fraction(values):               # exact mean of ratings given with one decimal
    return Fraction(sum(int(round(float(v) * 10)) for v in values), 10 * len(values))

n = len(rows)
rating = [float(r["Aggregate rating"]) for r in rows]
votes = [int(r["Votes"]) for r in rows]
rated_idx = [i for i, x in enumerate(rating) if x > 0]

# ---- dataset basics ----
L1 = json.load(open(TABLES / "level1_results.json")); L2 = json.load(open(TABLES / "level2_results.json")); L3 = json.load(open(TABLES / "level3_results.json"))
check("rows", n, L1["rows"]); check("columns", len(rows[0]), L1["columns"])
check("rated restaurants", len(rated_idx), L1["rated_restaurants"])
check("blank cuisines", sum(1 for r in rows if not r["Cuisines"].strip()), 9)
check("duplicate Restaurant IDs", n - len({r["Restaurant ID"] for r in rows}), 0)

# ---- Level 1 Task 1: cuisines ----
has_c = [r for r in rows if r["Cuisines"].strip()]
cc = Counter(c for r in has_c for c in {x.strip() for x in r["Cuisines"].split(",")})
saved = pd.read_csv(TABLES / "l1t1_top_cuisines.csv")
for _, s in saved.iterrows():
    check(f"cuisine count {s.Cuisine}", cc[s.Cuisine], s.Restaurants)
    check(f"cuisine % {s.Cuisine}", half_up(Fraction(cc[s.Cuisine] * 100, len(has_c))), s.Percentage)

# ---- Level 1 Task 2: ALL cities (count, rated count, exact average) ----
city_rows = defaultdict(list)
for i, r in enumerate(rows): city_rows[r["City"]].append(i)
saved = pd.read_csv(TABLES / "l1t2_city_table_all.csv")
bad = 0
for _, s in saved.iterrows():
    idx = city_rows[s.City]; ridx = [i for i in idx if rating[i] > 0]
    exp_avg = half_up(mean_fraction([rating[i] for i in ridx])) if ridx else None
    ok = (len(idx) == s.Restaurants and len(ridx) == s.Rated_Restaurants and
          ((exp_avg is None and pd.isna(s.Avg_Rating)) or (exp_avg is not None and abs(exp_avg - s.Avg_Rating) < 1e-9)))
    if not ok: bad += 1; print("MISMATCH city", s.City, exp_avg, s.Avg_Rating)
print(("OK       " if bad == 0 else "MISMATCH ") + f"all {len(saved)} cities (count, rated count, half-up average)")
if bad: problems.append("cities")
print("         Orlando average =", saved.loc[saved.City == "Orlando", "Avg_Rating"].iloc[0], "(exact 4.475 -> 4.48)")

# ---- Level 1 Task 3 & 4 ----
pr = Counter(r["Price range"] for r in rows)
for rec in L1["t3_price"]:
    check(f"price range {rec['Price range']} count", pr[str(rec["Price range"])], rec["Restaurants"])
    check(f"price range {rec['Price range']} %", half_up(Fraction(pr[str(rec["Price range"])] * 100, n)), rec["Percentage"])
yes = [i for i, r in enumerate(rows) if r["Has Online delivery"] == "Yes"]
no = [i for i, r in enumerate(rows) if r["Has Online delivery"] == "No"]
check("delivery yes %", half_up(Fraction(len(yes) * 100, n)), L1["t4"]["yes_pct"])
check("avg rating with delivery", half_up(mean_fraction([rating[i] for i in yes if rating[i] > 0])), L1["t4"]["avg_yes"])
check("avg rating without delivery", half_up(mean_fraction([rating[i] for i in no if rating[i] > 0])), L1["t4"]["avg_no"])
check("avg with delivery incl. zeros", half_up(mean_fraction([rating[i] for i in yes])), L1["t4"]["avg_yes_with_zero"])
check("avg without delivery incl. zeros", half_up(mean_fraction([rating[i] for i in no])), L1["t4"]["avg_no_with_zero"])

# ---- Level 2 Task 1 ----
check("mean rating (rated)", half_up(mean_fraction([rating[i] for i in rated_idx])), L2["t1"]["mean_rating"])
check("avg votes all", half_up(Fraction(sum(votes), n)), L2["t1"]["avg_votes_all"])
check("avg votes rated", half_up(Fraction(sum(votes[i] for i in rated_idx), len(rated_idx))), L2["t1"]["avg_votes_rated"])
for rec in L2["t1"]["ranges"]:
    lo = float(rec["Rating range"].split("-")[0]); cnt = sum(1 for i in rated_idx if lo <= rating[i] < lo + 0.5)
    check(f"rating range {rec['Rating range']}", cnt, rec["Restaurants"])

# ---- Level 2 Task 2: combinations ----
combo_rows = defaultdict(list)
for i, r in enumerate(rows):
    if r["Cuisines"].strip():
        parts = sorted({x.strip() for x in r["Cuisines"].split(",")})
        if len(parts) >= 2: combo_rows[" + ".join(parts)].append(i)
for rec in L2["t2"]["most_common"] + L2["t2"]["best"] + L2["t2"]["worst"]:
    idx = combo_rows[rec["Combination"]]; ridx = [i for i in idx if rating[i] > 0]
    check(f"combo {rec['Combination']} count/rated/avg", 1, int(len(idx) == rec["Restaurants"] and len(ridx) == rec["Rated"] and
          abs(half_up(mean_fraction([rating[i] for i in ridx])) - rec["Avg_Rating"]) < 1e-9))
eligible = sorted(((mean_fraction([rating[i] for i in idx if rating[i] > 0]), k) for k, idx in combo_rows.items()
                   if sum(1 for i in idx if rating[i] > 0) >= 20), reverse=True)
check("combinations with >=20 rated", len(eligible), L2["t2"]["n_combos_min20"])
check("best combination is", 1, int(eligible[0][1] == L2["t2"]["best"][0]["Combination"]))
multi_rated = [rating[i] for idx in combo_rows.values() for i in idx if rating[i] > 0]
check("average of multi-cuisine restaurants", half_up(mean_fraction(multi_rated)), L2["t2"]["overall_avg_multi"])

# ---- Level 2 Task 3: geography ----
valid = [i for i, r in enumerate(rows) if not (float(r["Longitude"]) == 0 and float(r["Latitude"]) == 0)]
check("plotted restaurants", len(valid), L2["t3"]["plotted"])
ncr = [i for i in valid if 28.2 <= float(rows[i]["Latitude"]) <= 28.95 and 76.8 <= float(rows[i]["Longitude"]) <= 77.7]
check("Delhi NCR points", len(ncr), L2["t3"]["ncr_points"])
check("India share of plotted %", half_up(Fraction(sum(1 for i in valid if rows[i]["Country Code"] == "1") * 100, len(valid))), L2["t3"]["india_pct"])

# ---- Level 2 Task 4: chains ----
names = Counter(r["Restaurant Name"].strip() for r in rows)
chain_names = {k for k, v in names.items() if v >= 2}
check("chain names", len(chain_names), L2["t4"]["n_chain_names"])
check("chain outlets", sum(names[k] for k in chain_names), L2["t4"]["chain_outlets"])
for rec in L2["t4"]["top10"] + L2["t4"]["best_min10"] + L2["t4"]["worst_min10"]:
    idx = [i for i, r in enumerate(rows) if r["Restaurant Name"].strip() == rec["Restaurant Name"]]
    ridx = [i for i in idx if rating[i] > 0]
    check(f"chain {rec['Restaurant Name']} outlets/votes/avg", 1, int(len(idx) == rec["Outlets"] and sum(votes[i] for i in idx) == rec["Total_Votes"]
          and abs(half_up(mean_fraction([rating[i] for i in ridx])) - rec["Avg_Rating"]) < 1e-9))

# ---- Level 3 Task 2: votes ----
check("max votes", max(votes), L3["t2"]["top10"][0]["Votes"])
check("zero-vote restaurants", sum(1 for v in votes if v == 0), L3["t2"]["zero_votes"])
rv = np.array([votes[i] for i in rated_idx], float); rr = np.array([rating[i] for i in rated_idx])
pear = float(np.corrcoef(rv, rr)[0, 1])                                          # Pearson by formula
spear = float(np.corrcoef(stats.rankdata(rv), stats.rankdata(rr))[0, 1])        # Spearman = Pearson of ranks
check("Pearson r (rounded)", half_up(Fraction(pear).limit_denominator(10**9)), L3["t2"]["pearson"])
check("Spearman rho (rounded)", half_up(Fraction(spear).limit_denominator(10**9)), L3["t2"]["spearman"])

# ---- Level 3 Task 3: price vs services ----
for key, col, name in [("delivery", "Has Online delivery", "Delivery"), ("booking", "Has Table booking", "Booking")]:
    for rec in L3["t3"][key]:
        grp = [r for r in rows if r["Price range"] == str(rec["Price range"])]
        y = sum(1 for r in grp if r[col] == "Yes")
        check(f"{name} price {rec['Price range']}: yes count", y, rec[f"{name} Yes"])
        check(f"{name} price {rec['Price range']}: %", half_up(Fraction(y * 100, len(grp))), rec[f"{name} Yes %"])

print("\n" + ("ALL CHECKS PASSED" if not problems else f"{len(problems)} PROBLEM(S): {problems}"))
