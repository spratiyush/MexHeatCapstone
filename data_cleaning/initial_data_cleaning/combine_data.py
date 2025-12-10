import pandas as pd
import glob
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

##### COMBINE YEARLY DATASETS #####

# Folder path
folder_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/yearly_death_data"

# Find all CSVs that match the pattern
file_pattern = os.path.join(folder_path, "*data.csv")
csv_files = glob.glob(file_pattern)

print("Found files:", csv_files)

# Load and combine all CSVs
df_list = []
for file in csv_files:
    try:
        temp_df = pd.read_csv(file)
        df_list.append(temp_df)
        print(f"Loaded {os.path.basename(file)} with {len(temp_df)} rows")
    except Exception as e:
        print(f"Error loading {file}: {e}")

# Concatenate all dataframes
if df_list:
    combined_df = pd.concat(df_list, ignore_index=True)
    print(f"\n✅ Combined dataset has {len(combined_df)} rows and {len(combined_df.columns)} columns.")

    # Save the combined dataset
    output_path = os.path.join(folder_path, "combined_all_years.csv")
    combined_df.to_csv(output_path, index=False)
    print(f"✅ Saved combined file to: {output_path}")
else:
    print("⚠️ No CSV files were found or loaded.")

##### SPLIT INTO YEAR RANGES #####

# ---- CONFIG ----
input_path = Path("/Users/pratiyush/Desktop/MexicoHeatMortality/yearly_death_data/combined_all_years.csv")
output_dir = input_path.parent

# Candidate date column names
DATE_CANDIDATES = ["date_of_occurrence"]

# Year bins (inclusive)
YEAR_BUCKETS = [
    ((1998, 2002), "1998_2002"),
    ((2003, 2007), "2003_2007"),
    ((2008, 2012), "2008_2012"),
    ((2013, 2017), "2013_2017"),
    ((2018, 2022), "2018_2022"),
]

def normalize(name: str) -> str:
    """Lowercase and remove non-alphanumerics to compare column names robustly."""
    return "".join(ch for ch in name.lower() if ch.isalnum())

def find_date_column(cols) -> Optional[str]:
    norm_map = {normalize(c): c for c in cols}
    for cand in DATE_CANDIDATES:
        if normalize(cand) in norm_map:
            return norm_map[normalize(cand)]
    return None

def parse_dates_safe(series: pd.Series) -> pd.Series:
    """Parse dates with multiple common formats; coerce invalid to NaT."""
    dt = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
    if dt.notna().any():
        return dt
    fmts = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]
    for fmt in fmts:
        dt = pd.to_datetime(series, errors="coerce", format=fmt)
        if dt.notna().any():
            return dt
    return pd.to_datetime(series, errors="coerce")

def main():
    df = pd.read_csv(input_path)

    # Find date or year column
    date_col = find_date_column(df.columns)
    year_col = None
    for c in df.columns:
        if normalize(c) in {"year", "anio", "ano"}:
            year_col = c
            break

    # Create __YEAR__ column
    if year_col is not None:
        df["__YEAR__"] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    elif date_col is not None:
        dt = parse_dates_safe(df[date_col])
        if dt.isna().all():
            raise ValueError(f"Could not parse any dates from column '{date_col}'.")
        df["__YEAR__"] = dt.dt.year.astype("Int64")
    else:
        raise ValueError("No valid date or year column found.")

    # Split and save
    for (start, end), tag in YEAR_BUCKETS:
        mask = (df["__YEAR__"] >= start) & (df["__YEAR__"] <= end)
        bucket_df = df.loc[mask].drop(columns=["__YEAR__"])
        out_path = output_dir / f"combined_{tag}.csv"
        bucket_df.to_csv(out_path, index=False)
        print(f"Saved {len(bucket_df):>7} rows to: {out_path}")

    print("Done.")

if __name__ == "__main__":
    main()
