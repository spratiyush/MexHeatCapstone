# ==============================
# Combine subgroup results (Python)
# ==============================

import pandas as pd
import numpy as np

# --- 1) Define file paths ---
paths = [
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_98_02_subgroups.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_03_07_subgroups.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_08_12_subgroups.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_13_17_subgroups.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_18_22_subgroups.csv"
]

# --- 2) Read and combine safely ---
dfs = [pd.read_csv(p) for p in paths]
combined_df = pd.concat(dfs, ignore_index=True)

# --- 3) Check for completeness ---
print(f"Rows: {combined_df.shape[0]}")
print(f"Columns: {combined_df.shape[1]}")

# Check for empty rows (all NaN or blank)
empty_rows = combined_df.index[combined_df.isna().all(axis=1) | (combined_df.astype(str).apply(lambda x: x.str.strip()) == '').all(axis=1)]
print(f"Empty rows: {len(empty_rows)}")

# Check for empty columns (all NaN or blank)
empty_cols = [col for col in combined_df.columns if combined_df[col].isna().all() or (combined_df[col].astype(str).str.strip() == '').all()]
print(f"Empty columns: {len(empty_cols)}")
print(empty_cols)

# --- 4) Save output ---
out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_1998_2022_subgroups_combined.csv"
combined_df.to_csv(out_path, index=False)
print(f"✅ Combined file saved to: {out_path}")
