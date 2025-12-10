import pandas as pd
import numpy as np

# ==============================
# 0. Load and prepare data
# ==============================
in_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Mexico_daymet_municipalities_1998_2022.csv"
df = pd.read_csv(in_path)

# Parse date and extract year/month
dt = pd.to_datetime(df['date'].astype(str).str[:10], errors='coerce')
df['date2'] = dt.dt.date
df['year']  = dt.dt.year
df['month'] = dt.dt.month

# Rename for consistency
df = df.rename(columns={
    'ADM2_PCODE': 'municipality',
    'tmax': 'tmax_max',
    'tmin': 'tmin_max'
})

# Filter valid years
df = df[(df['year'] >= 1998) & (df['year'] <= 2022)].copy()

# Sort for lags
df = df.sort_values(['municipality', 'date2']).reset_index(drop=True)

# ==============================
# 1. Relative heatwave thresholds (per municipality)
# ==============================
df['hwthr_99_max'] = df.groupby('municipality')['tmax_max'].transform(
    lambda s: s.quantile(0.99, interpolation='linear')
)
df['hwthr_99_min'] = df.groupby('municipality')['tmin_max'].transform(
    lambda s: s.quantile(0.99, interpolation='linear')
)

# >>> NEW: 95th percentile thresholds
df['hwthr_95_max'] = df.groupby('municipality')['tmax_max'].transform(
    lambda s: s.quantile(0.95, interpolation='linear')
)
df['hwthr_95_min'] = df.groupby('municipality')['tmin_max'].transform(
    lambda s: s.quantile(0.95, interpolation='linear')
)

# ==============================
# 2. 1-day HW indicators
# ==============================

# Existing 99th percentile indicators
df['hw_99_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_99_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_99_max'].isna(), np.nan, 0)
)
df['hw_99_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_99_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_99_min'].isna(), np.nan, 0)
)

# >>> NEW: 95th percentile indicators
df['hw_95_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_95_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_95_max'].isna(), np.nan, 0)
)
df['hw_95_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_95_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_95_min'].isna(), np.nan, 0)
)

# ==============================
# 5. Build table of exact threshold values when HW defs = 1
# ==============================

# Added a new entry for 95th percentile 1-day HWs
hw_defs = [
    ("99th 1-day", "hw_99_max_1", "hw_99_min_1"),
    ("95th 1-day", "hw_95_max_1", "hw_95_min_1"),  # NEW
]

rows = []
for label, max_col, min_col in hw_defs:
    tmp = df.loc[
        (df[max_col] == 1) | (df[min_col] == 1),
        [
            "municipality",
            "date2",
            "tmax_max",
            "tmin_max",
            "hwthr_99_max",
            "hwthr_99_min",
            "hwthr_95_max",   # NEW
            "hwthr_95_min",   # NEW
            "hw_99_max_1",
            "hw_99_min_1",
            "hw_95_max_1",    # NEW
            "hw_95_min_1",    # NEW
        ]
    ].copy()
    tmp["HW_definition"] = label
    rows.append(tmp)

threshold_event_table = pd.concat(rows, ignore_index=True)

# Reorder columns for clarity
threshold_event_table = threshold_event_table[
    [
        "HW_definition",
        "municipality",
        "date2",
        "tmax_max",
        "tmin_max",
        "hwthr_99_max",
        "hwthr_99_min",
        "hwthr_95_max",
        "hwthr_95_min",
        "hw_99_max_1",
        "hw_99_min_1",
        "hw_95_max_1",
        "hw_95_min_1",
    ]
]
print(threshold_event_table.head())
print("Total rows in threshold_event_table:", len(threshold_event_table))

# ==============================
# 6. Save output
# ==============================
out_thr_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/updated_dec5_sup1_HW_99_thresholds_all_events_by_row.csv"
threshold_event_table.to_csv(out_thr_path, index=False)
print("✅ Saved threshold event table to:", out_thr_path)