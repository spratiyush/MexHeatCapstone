import pandas as pd
from pathlib import Path

# ---------- paths ----------
xlsx_path = Path("/Users/pratiyush/Desktop/MexicoHeatMortality/descriptive_summary_1998_2022.xlsx")
out_csv  = xlsx_path.with_name("descriptive_summary_1998_2022__COMBINED.csv")
out_xlsx = xlsx_path.with_name("descriptive_summary_1998_2022__COMBINED.xlsx")

# ---------- 1) Read ALL sheets ----------
# Each sheet should be a table where rows are subgroups and columns are periods (e.g., 1998-2002,..., Total)
sheets = pd.read_excel(xlsx_path, sheet_name=None)  # dict: {sheet_name: DataFrame}

# ---- Build TOTAL category from SEX sheet ----
sex_df = sheets.get("Sex")

if sex_df is not None:

    # Ensure subgroup column exists
    if sex_df.columns[0] != "Subgroup":
        sex_df = sex_df.rename(columns={sex_df.columns[0]: "Subgroup"})

    # Identify period columns
    period_cols = [c for c in sex_df.columns if c != "Subgroup"]

    # Convert to numeric
    sex_df[period_cols] = sex_df[period_cols].apply(pd.to_numeric, errors="coerce")

    # Build TOTAL row
    total_row = {"Subgroup": "TOTAL"}
    total_row.update({col: sex_df[col].sum() for col in period_cols})

    # Build TOTAL block (divider + row)
    total_divider = {col: "" for col in sex_df.columns}
    total_divider["Subgroup"] = "— TOTAL —"

    total_block = [
        pd.DataFrame([total_divider]),
        pd.DataFrame([total_row])
    ]
else:
    total_block = []   # no Sex sheet → skip


# Define the order you want the sections to appear (match your saved sheet names)
order = [
    "Age group",
    "Sex",
    "Schooling",
    "Cause of death",
    "Nationality",
    "Civil status",
    "Occupation",
]

# ---------- 2) Normalize each sheet ----------
blocks = []
for name in order:
    if name not in sheets:
        print(f"⚠️ Sheet not found (skipped): {name}")
        continue

    df = sheets[name].copy()

    # If the first column is the subgroup label but unnamed, name it:
    if df.columns[0] != "Subgroup":
        df = df.rename(columns={df.columns[0]: "Subgroup"})
    # Ensure Subgroup is string
    df["Subgroup"] = df["Subgroup"].astype(str)

    # Create a divider/header row
    divider = {col: "" for col in df.columns}
    divider["Subgroup"] = f"— {name.upper()} —"
    div_df = pd.DataFrame([divider])

    # Append divider + the section table
    blocks.append(div_df)
    blocks.append(df)

# ---------- 3) Concatenate to one long table ----------
combined = pd.concat(total_block + blocks, ignore_index=True)


# Optional: enforce column order if you want periods in a specific order:
desired_cols = ["Subgroup", "1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022", "Total"]
existing = [c for c in desired_cols if c in combined.columns]
others   = [c for c in combined.columns if c not in existing]
combined = combined[existing + others]  # keep any extra cols at end

# ---------- 4) Save CSV (plain) ----------
combined.to_csv(out_csv, index=False)
print(f"✅ Combined table (CSV): {out_csv}")

# ---------- 5) Save styled Excel with divider formatting ----------
with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
    combined.to_excel(writer, index=False, sheet_name="Combined")
    wb  = writer.book
    ws  = writer.sheets["Combined"]

    # Formats
    header_fmt  = wb.add_format({"bold": True, "text_wrap": False, "border": 0})
    divider_fmt = wb.add_format({"bold": True, "italic": False, "bg_color": "#EFEFEF"})
    num_fmt     = wb.add_format({"num_format": "#,##0"})

    # Format header row
    ws.set_row(0, None, header_fmt)

    # Autosize columns & apply number format to numeric columns
    for col_idx, col in enumerate(combined.columns):
        # Autosize by max length in column
        series = combined[col].astype(str)
        max_len = max([len(col)] + series.str.len().tolist())
        ws.set_column(col_idx, col_idx, min(max_len + 2, 40))

        # Numeric formatting (skip Subgroup column)
        if col != "Subgroup":
            # Apply number format to all rows below header
            ws.set_column(col_idx, col_idx, None, num_fmt)

    # Apply divider formatting to rows where Subgroup starts with "— "
    for row_idx in range(1, len(combined) + 1):  # 1-based in Excel (row 0 is header)
        cell_val = combined.loc[row_idx - 1, "Subgroup"]
        if isinstance(cell_val, str) and cell_val.startswith("— "):
            ws.set_row(row_idx, None, divider_fmt)

print(f"✅ Combined table (styled Excel): {out_xlsx}")

# ---------- 6) (Optional) Quick figure example ----------
# If you want a quick bar of totals across major sections (sum of section rows):
# This treats divider rows as section markers and sums until the next divider.
make_quick_figure = False
if make_quick_figure:
    import matplotlib.pyplot as plt

    # Identify divider rows
    is_div = combined["Subgroup"].astype(str).str.startswith("— ")
    sections = []
    section_sums = []

    current_name = None
    current_block = []

    for i, row in combined.iterrows():
        if is_div.iloc[i]:
            # flush old block
            if current_name is not None and current_block:
                block_df = pd.DataFrame(current_block)
                num_cols = [c for c in block_df.columns if c not in ["Subgroup"]]
                sections.append(current_name)
                section_sums.append(block_df[num_cols].apply(pd.to_numeric, errors="coerce").sum(numeric_only=True))
            # start new block
            current_name = row["Subgroup"].strip("— ").strip(" ").title()
            current_block = []
        else:
            current_block.append(row)

    # flush the last block
    if current_name is not None and current_block:
        block_df = pd.DataFrame(current_block)
        num_cols = [c for c in block_df.columns if c not in ["Subgroup"]]
        sections.append(current_name)
        section_sums.append(block_df[num_cols].apply(pd.to_numeric, errors="coerce").sum(numeric_only=True))

    # Build a summary DataFrame (e.g., use "Total" column if present)
    sec_df = pd.DataFrame(section_sums, index=sections)
    col_for_plot = "Total" if "Total" in sec_df.columns else sec_df.columns[-1]

    plt.figure(figsize=(8, 5))
    plt.bar(sec_df.index, sec_df[col_for_plot])
    plt.title(f"Totals by Section ({col_for_plot})")
    plt.xlabel("Section")
    plt.ylabel("Total")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()
