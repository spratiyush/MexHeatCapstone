import pandas as pd
import numpy as np

# --- 1. Load the heatwave indicators file (with tmax_max, tmin_max, and HW columns) ---
in_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Heatwave_Indicators_Mexico_1998_2022.csv"
df = pd.read_csv(in_path)

# --- 2. Define which columns correspond to each HW definition ---
# For each row: (label, max-indicator-column, min-indicator-column)
hw_defs = [
    ("99th 1-day", "hw_99_max_1", "hw_99_min_1"),
    ("99th 2-day", "hw_99_max_2", "hw_99_min_2"),
    ("99th 3-day", "hw_99_max_3", "hw_99_min_3"),
]

rows = []

#collapse by municipality
#for each hw days, the minimum temp when heatwave is 1 (For max temp definition, use max and for min temp, use minimum when hw_99 = 1)
#for each municipality, the threshold of max temp and min temp
#then we take the mean and sd across municipalities

for label, max_col, min_col in hw_defs:
    # Days where that HW definition is "on" (== 1)
    max_vals = df.loc[df[max_col] == 1, "tmax_max"]
    min_vals = df.loc[df[min_col] == 1, "tmin_max"]

    max_mean = max_vals.mean()
    max_sd   = max_vals.std()

    min_mean = min_vals.mean()
    min_sd   = min_vals.std()

    rows.append({
        "HW_definition": label,
        "Maximum temperature mean (SD), °C": f"{max_mean:.2f} ({max_sd:.2f})",
        "Minimum temperature mean (SD), °C": f"{min_mean:.2f} ({min_sd:.2f})",
    })

# --- 3. Build summary table ---
summary_table = pd.DataFrame(rows)

print(summary_table)

# Optional: save to CSV
out_table_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/fig2_HW_99_threshold_summary_table__event_temps.csv"
summary_table.to_csv(out_table_path, index=False)
print("✅ Saved summary table to:", out_table_path)
