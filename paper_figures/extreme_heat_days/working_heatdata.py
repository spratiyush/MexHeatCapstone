import pandas as pd

# --- File path ---
path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Heatwave_Indicators_Mexico_1998_2022.csv"

# --- Load CSV ---
df = pd.read_csv(path)


df = df.drop(columns=['tmin_max', 'vp', 'prcp', 'tmax_max', 'date2'], errors='ignore')

# --- Columns to sum ---
cols_to_sum = [
    'hw_99_min_1', 'hw_abs_30', 'hw_abs_35', 'hw_abs_30_lag1', 'hw_abs_35_lag1',
    'hw_99_max_lag1', 'hw_99_min_lag1', 'hw_99_max_2', 'hw_99_min_2',
    'hw_99_max_lag2', 'hw_99_min_lag2', 'hw_99_max_lag3', 'hw_99_min_lag3',
    'hw_99_max_3', 'hw_99_min_3','hw_99_max_1'
]

# --- Group by year and municipality, summing numeric values ---
summary_df = df.groupby(['year', 'municipality'])[cols_to_sum].sum().reset_index()

# --- Display first few rows ---
print(summary_df.head())

# --- Ensure 'year' is numeric (from summary_df) ---
summary_df["year"] = pd.to_numeric(summary_df["year"], errors="coerce")

# --- Define 5-year periods and labels ---
bins = [1997, 2002, 2007, 2012, 2017, 2022]  # right-closed intervals
labels = ["1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022"]

# --- Create ordered categorical 'year_period' from 'year' ---
summary_df["year_period"] = pd.cut(summary_df["year"], bins=bins, labels=labels, right=True)
summary_df["year_period"] = summary_df["year_period"].astype(
    pd.CategoricalDtype(categories=labels, ordered=True)
)

# --- Collapse to period x municipality sums ---
period_summary = (
    summary_df.dropna(subset=["year_period"])
              .groupby(["year_period", "municipality"], observed=True)[cols_to_sum]
              .sum()
              .reset_index()
)

print(period_summary.head())

# --- (Optional) save ---
period_summary.to_csv("/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Heatwave_Summary_ByPeriod_Municipality.csv", index=False)


