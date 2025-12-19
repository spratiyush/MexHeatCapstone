import pandas as pd
import numpy as np

# ---- 0. Load data ----
in_path = "/Users/larasch/Documents/UCB_postdoc/Research/Mexico_heat_vulnerability/data/updated_temp_data/final_estimates/Mexico_daymet_municipalities_1998_2022_v3.csv"
df = pd.read_csv(in_path)

# ---- Parse date and extract year/month ----
dt = pd.to_datetime(df['date'].astype(str).str[:10], errors='coerce')
df['date2'] = dt.dt.date
df['year']  = dt.dt.year
df['month'] = dt.dt.month

# ---- Rename columns for consistency ----
df = df.rename(columns={
    'ADM2_PCODE': 'municipality',
    'tmax': 'tmax_max',
    'tmin': 'tmin_max'
})

# ---- Filter valid years ----
df = df[(df['year'] >= 1998) & (df['year'] <= 2022)].copy()

# Ensure proper order for lag calculations
df = df.sort_values(['municipality', 'date2']).reset_index(drop=True)

# ---- 1. Relative heatwave thresholds ----
df['hwthr_99_max'] = df.groupby('municipality')['tmax_max'].transform(lambda s: s.quantile(0.99, interpolation='linear'))
df['hwthr_99_min'] = df.groupby('municipality')['tmin_max'].transform(lambda s: s.quantile(0.99, interpolation='linear'))

df['hwthr_95_max'] = df.groupby('municipality')['tmax_max'].transform(lambda s: s.quantile(0.95, interpolation='linear'))
df['hwthr_95_min'] = df.groupby('municipality')['tmin_max'].transform(lambda s: s.quantile(0.95, interpolation='linear'))

df['hwthr_90_max'] = df.groupby('municipality')['tmax_max'].transform(lambda s: s.quantile(0.90, interpolation='linear'))
df['hwthr_90_min'] = df.groupby('municipality')['tmin_max'].transform(lambda s: s.quantile(0.90, interpolation='linear'))
# ---- 1-day indicators ----
df['hw_99_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_99_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_99_max'].isna(), np.nan, 0)
)
df['hw_99_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_99_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_99_min'].isna(), np.nan, 0)
)
df['hw_95_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_95_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_95_max'].isna(), np.nan, 0)
)
df['hw_95_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_95_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_95_min'].isna(), np.nan, 0)
)
df['hw_90_max_1'] = np.where(
    df['tmax_max'] >= df['hwthr_90_max'], 1,
    np.where(df['tmax_max'].isna() | df['hwthr_90_max'].isna(), np.nan, 0)
)
df['hw_90_min_1'] = np.where(
    df['tmin_max'] >= df['hwthr_90_min'], 1,
    np.where(df['tmin_max'].isna() | df['hwthr_90_min'].isna(), np.nan, 0)
)


# ---- 2. Absolute thresholds ----
df['hw_abs_30'] = np.where(df['tmax_max'] >= 30, 1, np.where(df['tmax_max'].isna(), np.nan, 0))
df['hw_abs_35'] = np.where(df['tmax_max'] >= 35, 1, np.where(df['tmax_max'].isna(), np.nan, 0))

# ---- 3. Compute all lags ----
df['hw_99_max_lag1'] = df.groupby('municipality')['hw_99_max_1'].shift(1)
df['hw_99_min_lag1'] = df.groupby('municipality')['hw_99_min_1'].shift(1)
df['hw_99_max_lag2'] = df.groupby('municipality')['hw_99_max_1'].shift(2)
df['hw_99_min_lag2'] = df.groupby('municipality')['hw_99_min_1'].shift(2)
df['hw_99_max_lag3'] = df.groupby('municipality')['hw_99_max_1'].shift(3)
df['hw_99_min_lag3'] = df.groupby('municipality')['hw_99_min_1'].shift(3)

# Absolute threshold lags
df['hw_abs_30_lag1'] = df.groupby('municipality')['hw_abs_30'].shift(1)
df['hw_abs_35_lag1'] = df.groupby('municipality')['hw_abs_35'].shift(1)

# ---- 4. 2-day and 3-day relative indicators ----
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

# ---- 5. Final export (no threshold cols, includes all lags) ----
df['date'] = df['date2']

cols_to_export = [
    'municipality', 'date', 'tmin_max', 'tmax_max',
    'date2', 'year', 'month',
    'hw_99_max_1', 'hw_99_min_1',
    'hw_abs_30', 'hw_abs_35',
    'hw_abs_30_lag1', 'hw_abs_35_lag1',
    'hw_99_max_lag1', 'hw_99_min_lag1',
    'hw_99_max_2', 'hw_99_min_2',
    'hw_99_max_lag2', 'hw_99_min_lag2',
    'hw_99_max_lag3', 'hw_99_min_lag3',
    'hw_99_max_3', 'hw_99_min_3','hw_95_min_1','hw_95_max_1','hw_90_min_1','hw_90_max_1'
]

df_final = df[cols_to_export].copy()

#out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/updated_dec5_Heatwave_Indicators_Mexico_1998_2022.csv"
out_path = "/Users/larasch/Documents/UCB_postdoc/Research/Mexico_heat_vulnerability/data/updated_temp_data/Heatwave_Indicators_Mexico_1998_2022.csv"

df_final.to_csv(out_path, index=False)

print("✅ Saved:", out_path)
print("🧾 Columns in final file:", len(df_final.columns))
print(df_final.columns.tolist())

