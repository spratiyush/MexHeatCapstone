# ====================================================
# Heatmaps by subgroup_type for hw_99_max_1
# X-axis: year_period | Y-axis: subgroup
# One vertically stacked subplot per subgroup_type (aligned)
# ====================================================

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# --- 1) File path ---
path = "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_1998_2022_subgroups_combined.csv"

# --- 2) Load and filter only rows where any column == 'hw_99_max_1' ---
df = pd.read_csv(path)
mask = df.apply(lambda x: x.astype(str).eq("hw_99_max_1"))
filtered_df = df[mask.any(axis=1)].copy()

print(f"✅ Filtered rows with term == 'hw_99_max_1': {len(filtered_df)}")
if filtered_df.empty:
    raise ValueError("No rows found with term == 'hw_99_max_1'.")

# --- 3) Clean column names ---
filtered_df.columns = [c.strip().lower() for c in filtered_df.columns]

# NOTE: after lowercasing, subgroup_type column is now "subgroup_type"
# but its VALUES are things like "EDAD", "ESCOLARIDAD", etc. (unchanged)

# --- 4) Validate required columns ---
required = {"term", "subgroup_type", "subgroup", "year_period", "or"}
missing = required - set(filtered_df.columns)
if missing:
    raise ValueError(f"Missing expected columns: {missing}")

# --- 5) Drop unwanted subgroup entries ---
drop_values = ["Group_C_SEXO", "NACIONALID_NO_ESPEC"]
filtered_df = filtered_df[~filtered_df["subgroup"].isin(drop_values)]
print(f"✅ Dropped unwanted subgroups: {drop_values}")

# --- 6) Replace subgroup codes with descriptive labels ---
label_map = {
    "IS_I": "Circulatory system issues",
    "IS_J": "Respiratory system diseases",
    "IS_F": "Mental, Behavioral and Neurodevelopmental disorders",
    "Group_A_SEXO": "Male",
    "Group_B_SEXO": "Female",
    "Group_A_OCUPACION": "Indoor workers/professions",
    "Group_B_OCUPACION": "Outdoor workers/professions",
    "Group_C_OCUPACION": "Unemployed or ineligible",
    "Group_A_ESCOLARIDA": "No schooling",
    "Group_B_ESCOLARIDA": "Primary or secondary schooling",
    "Group_C_ESCOLARIDA": "High schooling",
    "Group_D_ESCOLARIDA": "Professional schooling",
    "Group_E_ESCOLARIDA": "No information or ineligible",
    "Group_A_EDAD": "Less than 4",
    "Group_B_EDAD": "5–19",
    "Group_C_EDAD": "20–64",
    "Group_D_EDAD": "65–84",
    "Group_E_EDAD": "85–120",
    "Group_F_EDAD": "No specification",
    "CIVIL_SINGLE": "Single",
    "CIVIL_MARRIED": "Married",
    "CIVIL_COHABITING": "Live-in",
    "CIVIL_SEPERATED": "Separated",
    "CIVIL_WIDOWED": "Widowed",
    "CIVIL_NOT_SPEC": "Not specified",
    "NACIONALID_MEXICANA": "Mexican Nationality",
    "NACIONALID_EXTRANJERA": "Foreign Nationality"
}
filtered_df["subgroup"] = filtered_df["subgroup"].replace(label_map)

# --- 7) Time ordering ---
x_order_preferred = ["98_02", "03_07", "08_12", "13_17", "18_22"]
present = [y for y in x_order_preferred if y in filtered_df["year_period"].unique().tolist()]
extras = [y for y in filtered_df["year_period"].unique() if y not in present]
x_periods = present + sorted(extras)  # final x-axis (time) order

# --- 8) Nice orders for each subgroup_type (for Y-axis) ---
# keys here match the *values* of subgroup_type (EDAD, ESCOLARIDAD, etc.)
nice_orders = {
    "EDAD": ["Less than 4", "5–19", "20–64", "65–84", "85–120", "No specification"],
    "SEXO": ["Male", "Female"],
    "OCUPACION": [
        "Indoor workers/professions",
        "Outdoor workers/professions",
        "Unemployed or ineligible",
    ],
    "ESCOLARIDAD": [
        "No schooling",
        "Primary or secondary schooling",
        "High schooling",
        "Professional schooling",
        "No information or ineligible",
    ],
    "CIVIL_STATUS": ["Single", "Married", "Live-in", "Separated", "Widowed", "Not specified"],
    "CAUSE_IS": [
        "Circulatory system issues",
        "Respiratory system diseases",
        "Mental, Behavioral and Neurodevelopmental disorders",
    ],
     "NACIONALIDAD": [
        "Mexican Nationality",
        "Foreign Nationality"
    ],
}

# --- Pretty titles for each subgroup_type, shown ABOVE each panel ---
type_label_map = {
    "EDAD": "Age group",
    "ESCOLARIDAD": "Education level",
    "SEXO": "Sex",
    "CAUSE_IS": "Cause of death",
    "CIVIL_STATUS": "Marital status",
    "OCUPACION": "Occupation",
    "NACIONALIDAD":"Nationality"
}

# --- 9) Plot (stacked vertically, shared x-axis), with equal cell size across subgroup_types ---

types = list(filtered_df["subgroup_type"].dropna().unique())
n = len(types)

# Compute height ratios based on number of subgroups per subgroup_type
height_ratios = []
for t in types:
    sub_n = (
        filtered_df.loc[filtered_df["subgroup_type"] == t, "subgroup"]
        .dropna()
        .nunique()
    )
    height_ratios.append(max(sub_n, 1))  # avoid zero

# Scale figure height with total rows to keep cell size ~constant
fig_height = 0.6 * sum(height_ratios)  # tweak 0.6 to make cells taller/shorter

fig, axes = plt.subplots(
    n,
    1,
    figsize=(11, fig_height),
    sharex=True,
    constrained_layout=True,
    gridspec_kw={"height_ratios": height_ratios},
)

if n == 1:
    axes = [axes]

last_im = None

for ax, t in zip(axes, types):
    dft = filtered_df[filtered_df["subgroup_type"] == t].copy()

    # Determine Y-axis order based on nice_orders (per subgroup_type)
    key = t.strip()
    y_order = list(dft["subgroup"].dropna().unique())
    if key in nice_orders:
        wanted = nice_orders[key]
        y_order = [y for y in wanted if y in y_order] + [y for y in y_order if y not in wanted]

    # Pivot so rows=subgroup (Y), columns=year_period (X)
    piv = dft.pivot_table(index="subgroup", columns="year_period", values="or", aggfunc="mean")
    piv = piv.reindex(index=y_order)
    piv = piv.reindex(columns=x_periods)

    data = np.array(piv.values, dtype=float)

    # Handle all-NaN cases
    if np.isnan(data).all():
        title = type_label_map.get(key, key)
        ax.set_title(f"{title} (no data)", fontsize=12, pad=6)
        ax.axis("off")
        continue

    # TwoSlopeNorm centered at 1
    vmin, vmax = np.nanmin(data), np.nanmax(data)
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        vmin, vmax = 0.9, 1.1
    if vmin >= 1:
        vmin = 0.9
    if vmax <= 1:
        vmax = 1.1
    if vmin == vmax:
        vmin, vmax = 0.9, 1.1

    norm = TwoSlopeNorm(vmin=vmin, vcenter=1.0, vmax=vmax)
    cmap = mpl.colormaps.get("RdYlBu_r")

    # aspect='auto' so matrix fills axes; height_ratios handle cell size consistency
    last_im = ax.imshow(data, aspect="auto", cmap=cmap, norm=norm)

    # Y ticks = subgroups
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=10)

    # Put the pretty label ABOVE the panel
    pretty_title = type_label_map.get(key, key)
    ax.set_title(pretty_title, fontsize=13, pad=6)

    # no big y-axis label like "EDAD" etc.
    ax.set_ylabel("")

# Shared X-axis ticks/labels on the bottom subplot
axes[-1].set_xticks(range(len(x_periods)))
axes[-1].set_xticklabels(x_periods, rotation=0, ha="center", fontsize=10)
axes[-1].set_xlabel("Year period", fontsize=11)

# --- Shared colorbar ---
if last_im is not None:
    cbar = fig.colorbar(last_im, ax=axes, orientation="horizontal", fraction=0.05, pad=0.06)
    cbar.set_label("Odds Ratio (OR)", rotation=0, labelpad=8)
    ticks = cbar.get_ticks()
    if 1 not in np.round(ticks, 6):
        ticks = np.unique(np.append(ticks, 1.0))
        ticks.sort()
        cbar.set_ticks(ticks)

fig.suptitle(
    "Heatwave (hw_99_max_1): OR by subgroup (Y) and year period (X)",
    fontsize=15,
    y=1.02,
)

out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/fig4_try3_heatwave_hw_99_max_1_by_subgroup_Yx_Xtime.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight")
print(f"✅ Saved figure to: {out_path}")
plt.show()
