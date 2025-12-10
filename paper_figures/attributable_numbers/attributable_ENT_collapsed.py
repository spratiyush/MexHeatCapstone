import pandas as pd

in_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/95_attributable_numbers_by_muni_period_simple.csv"
out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/95_attributable_numbers_by_state_period_simple.csv"

# Load muni-level results
df = pd.read_csv(in_path)

# Columns to sum
sum_cols = [
    "deaths_total",
    "AN_deaths_est",
    "AN_deaths_est_lcl",
    "AN_deaths_est_ucl",
]

# Group by state (ENT_OCURR) and time period, sum the selected columns
state_period = (
    df.groupby(["ENT_OCURR", "year_period"], as_index=False)[sum_cols]
      .sum()
)

# (Optional) sort for nice ordering
state_period = state_period.sort_values(["year_period", "ENT_OCURR"]).reset_index(drop=True)

state_period = state_period.drop(columns=["deaths_total"])

# Save
state_period.to_csv(out_path, index=False)
print(f"✅ Saved state-period totals to: {out_path}")
print(state_period.head(12))


