import pandas as pd
import numpy as np
from datetime import datetime

# ------------------------------------------------
# USER INPUTS
# ------------------------------------------------
# Heatwave summary (one row per municipality-period, with hw_99_max_1 etc.)
heatwave_summary_path = (
    "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/"
    "Heatwave_Summary_ByPeriod_Municipality.csv"

)
# State-level case-crossover results (ORs and CI by ENT_OCURR + year_period)
cc_results_path = (
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/"
    "combined_heatwave_case_crossover_results_STATE_hw99max1.csv"
)
# Period-level deaths by municipality and period
# Required columns: municipality, year_period, deaths_total
period_deaths_path = (
    "/Users/pratiyush/Desktop/MexicoHeatMortality/"
    "Heatwave_Summary_hw99max1_deaths_total.csv"
)

# Heatwave metric and CC type to attribute
HW_VARIABLE = "hw_99_max_1"
CC_TYPE = "Same Day"

# Output
save_path = (
    "/Users/pratiyush/Desktop/MexicoHeatMortality/"
    "attributable_numbers_by_muni_period_simple.csv"
)

# ------------------------------------------------
# HELPERS
# ------------------------------------------------
def infer_state_from_muni(muni_code: str) -> int:
    """Infer ENT_OCURR (state code) from municipality string like 'MX01001'."""
    digits = "".join(ch for ch in str(muni_code) if ch.isdigit())
    if len(digits) < 2:
        raise ValueError(f"Cannot infer state from municipality code: {muni_code}")
    return int(digits[:2])


def period_to_num_days(period: str) -> int:
    """Convert 'YYYY-YYYY' into inclusive number of days."""
    start_year, end_year = map(int, period.split("-"))
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return (end - start).days + 1


def paf_from_or(or_value: float) -> float:
    """
    Population attributable fraction under rare-outcome assumption:
    PAF = 1 - 1 / OR
    """
    if pd.isna(or_value) or or_value <= 0:
        return np.nan
    return 1.0 - 1.0 / or_value


# ------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------
hw = pd.read_csv(heatwave_summary_path)

needed_hw_cols = {"year_period", "municipality", HW_VARIABLE}
missing_hw = needed_hw_cols - set(hw.columns)
if missing_hw:
    raise ValueError(f"Heatwave summary missing columns: {missing_hw}")

hw = hw[["year_period", "municipality", HW_VARIABLE]]

# Add state code for merge with state-level CC results
hw["ENT_OCURR"] = hw["municipality"].apply(infer_state_from_muni)

# Case-crossover results
cc = pd.read_csv(cc_results_path)

required_cc = {"ENT_OCURR", "year_period", "variable", "type", "or", "or_low", "or_high"}
missing_cc = required_cc - set(cc.columns)
if missing_cc:
    raise ValueError(f"Case-crossover results missing columns: {missing_cc}")

# Keep only the rows for the chosen HW variable and type
cc_hw = (
    cc.query("variable == @HW_VARIABLE and type == @CC_TYPE")
      .sort_values(["ENT_OCURR", "year_period"])
      .drop_duplicates(["ENT_OCURR", "year_period"], keep="first")
      .rename(columns={
          "or":      "OR_point",
          "or_low":  "OR_lcl",
          "or_high": "OR_ucl"
      })
      [["ENT_OCURR", "year_period", "OR_point", "OR_lcl", "OR_ucl"]]
)

# ------------------------------------------------
# 2. MERGE ORs TO MUNICIPALITY-LEVEL HEATWAVE COUNTS
# ------------------------------------------------
df = hw.merge(cc_hw, on=["ENT_OCURR", "year_period"], how="left")

# Compute PAFs
df["PAF_point"] = df["OR_point"].apply(paf_from_or)
df["PAF_lcl"]   = df["OR_lcl"].apply(paf_from_or)
df["PAF_ucl"]   = df["OR_ucl"].apply(paf_from_or)

# ------------------------------------------------
# 3. MERGE PERIOD DEATHS + COMPUTE AN
# ------------------------------------------------
period_deaths = pd.read_csv(period_deaths_path)

need_pd = {"municipality", "year_period", "deaths_total"}
missing_pd = need_pd - set(period_deaths.columns)
if missing_pd:
    raise ValueError(f"Period deaths file missing columns: {missing_pd}")

df = df.merge(
    period_deaths[["municipality", "year_period", "deaths_total"]],
    on=["municipality", "year_period"],
    how="left",
)

# Number of days in the period (e.g., 1998-2002)
df["period_days"] = df["year_period"].apply(period_to_num_days)

# Fraction of days exposed to heatwave in that period
df["frac_exposed"] = df[HW_VARIABLE] / df["period_days"]

# Estimated deaths on exposed days
df["deaths_exposed_est"] = df["deaths_total"] * df["frac_exposed"]

# Attributable numbers: AN ≈ deaths_on_exposed_days × PAF
df["AN_deaths_est"]     = df["deaths_exposed_est"] * df["PAF_point"]
df["AN_deaths_est_lcl"] = df["deaths_exposed_est"] * df["PAF_lcl"]
df["AN_deaths_est_ucl"] = df["deaths_exposed_est"] * df["PAF_ucl"]

# ------------------------------------------------
# 4. SELECT COLUMNS + SAVE
# ------------------------------------------------
out_cols = [
    "municipality",
    "year_period",
    "ENT_OCURR",
    HW_VARIABLE,
    "deaths_total",
    "OR_point",
    "OR_lcl",
    "OR_ucl",
    "PAF_point",
    "PAF_lcl",
    "PAF_ucl",
    "AN_deaths_est",
    "AN_deaths_est_lcl",
    "AN_deaths_est_ucl",
]

out = (
    df[out_cols]
    .sort_values(["year_period", "municipality"])
    .reset_index(drop=True)
)

out.to_csv(save_path, index=False)
print(f"✅ Saved attributable numbers to: {save_path}")
print(out.head(12))

print(df.columns)