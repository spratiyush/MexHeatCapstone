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

# ==============================
# 2. 1-day HW indicators (same as your original definition)
# ==============================
df['hw_99_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_99_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_99_max'].isna(), np.nan, 0)
)
df['hw_99_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_99_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_99_min'].isna(), np.nan, 0)
)

# ==============================
# 3. Lags needed for 2-day / 3-day HWs
# ==============================
df['hw_99_max_lag1'] = df.groupby('municipality')['hw_99_max_1'].shift(1)
df['hw_99_min_lag1'] = df.groupby('municipality')['hw_99_min_1'].shift(1)
df['hw_99_max_lag2'] = df.groupby('municipality')['hw_99_max_1'].shift(2)
df['hw_99_min_lag2'] = df.groupby('municipality')['hw_99_min_1'].shift(2)

# ==============================
# 4. 2-day and 3-day HW indicators
# ==============================
df['hw_99_max_2'] = np.select(
    [
        (df['hw_99_max_1'] == 1) & (df['hw_99_max_lag1'] == 1),
        (df['hw_99_max_1'] == 0) | (df['hw_99_max_lag1'] == 0),
    ],
    [1, 0],
    default=np.nan
)
df['hw_99_min_2'] = np.select(
    [
        (df['hw_99_min_1'] == 1) & (df['hw_99_min_lag1'] == 1),
        (df['hw_99_min_1'] == 0) | (df['hw_99_min_lag1'] == 0),
    ],
    [1, 0],
    default=np.nan
)

df['hw_99_max_3'] = np.select(
    [
        (df['hw_99_max_1'] == 1) & (df['hw_99_max_lag1'] == 1) & (df['hw_99_max_lag2'] == 1),
        (df['hw_99_max_1'] == 0) | (df['hw_99_max_lag1'] == 0) | (df['hw_99_max_lag2'] == 0),
    ],
    [1, 0],
    default=np.nan
)
df['hw_99_min_3'] = np.select(
    [
        (df['hw_99_min_1'] == 1) & (df['hw_99_min_lag1'] == 1) & (df['hw_99_min_lag2'] == 1),
        (df['hw_99_min_1'] == 0) | (df['hw_99_min_lag1'] == 0) | (df['hw_99_min_lag2'] == 0),
    ],
    [1, 0],
    default=np.nan
)

# ==============================
# 5. Build table of exact threshold values when HW defs = 1
# ==============================
hw_defs = [
    ("99th 1-day", "hw_99_max_1", "hw_99_min_1"),
    ("99th 2-day", "hw_99_max_2", "hw_99_min_2"),
    ("99th 3-day", "hw_99_max_3", "hw_99_min_3"),
]

rows = []

for label, max_col, min_col in hw_defs:
    # rows where this HW definition is "on" for max or min
    tmp = df.loc[
        (df[max_col] == 1) | (df[min_col] == 1),
        [
            "municipality",
            "date2",
            "tmax_max",
            "tmin_max",
            "hwthr_99_max",
            "hwthr_99_min",
            max_col,
            min_col,
        ]
    ].copy()
    tmp["HW_definition"] = label
    rows.append(tmp)

threshold_event_table = pd.concat(rows, ignore_index=True)

# Optional: reorder columns nicely
threshold_event_table = threshold_event_table[
    [
        "HW_definition",
        "municipality",
        "date2",
        "tmax_max",
        "tmin_max",
        "hwthr_99_max",
        "hwthr_99_min",
        "hw_99_max_1",
        "hw_99_min_1",
        "hw_99_max_2",
        "hw_99_min_2",
        "hw_99_max_3",
        "hw_99_min_3",
    ]
]

print(threshold_event_table.head())
print("Total rows in threshold_event_table:", len(threshold_event_table))

# ==============================
# 6. Save output
# ==============================
out_thr_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/sup1_HW_99_thresholds_all_events_by_row.csv"
threshold_event_table.to_csv(out_thr_path, index=False)
print("✅ Saved threshold event table to:", out_thr_path)
