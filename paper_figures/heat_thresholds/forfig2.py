import pandas as pd

in_path  = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/updated_dec5_sup1_HW_99_thresholds_all_events_by_row.csv"
out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/thresholds_by_municipality.csv"

# Load
df = pd.read_csv(in_path)

# Select only the columns you want
keep_cols = ["municipality", "hwthr_99_max", "hwthr_99_min", "hwthr_95_max", "hwthr_95_min"]

# Keep ONE row per municipality
final = (
    df[keep_cols]
    .drop_duplicates(subset=["municipality"])
)

# Save
final.to_csv(out_path, index=False)
