import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib import colors as mcolors

# --------------------------------------------------------
# Paths & basic settings
# --------------------------------------------------------
CSV_PATH   = "/Users/pratiyush/Desktop/MexicoHeatMortality/descriptive_summary_1998_2022__COMBINED.csv"
OUT_MAIN   = "/Users/pratiyush/Desktop/MexicoHeatMortality/stacked_by_year_all_categories_shades.png"
OUT_LEGEND = "/Users/pratiyush/Desktop/MexicoHeatMortality/stacked_by_year_all_categories_shades_legend.png"

plt.rcParams["font.family"] = "IBM Plex Sans"

year_cols = ["1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022"]

categories = [
    "AGE GROUP",
    "SEX",
    "SCHOOLING",
    "CAUSE OF DEATH",
    "NATIONALITY",
    "CIVIL STATUS",
    "OCCUPATION",
]

# Base color for each category (feel free to tweak)
base_colors = {
    "AGE GROUP"      : "#1f77b4",  # blue
    "SEX"            : "#d62728",  # red
    "SCHOOLING"      : "#2ca02c",  # green
    "CAUSE OF DEATH" : "#9467bd",  # purple
    "NATIONALITY"    : "#ff7f0e",  # orange
    "CIVIL STATUS"   : "#8c564b",  # brown
    "OCCUPATION"     : "#17becf",  # teal
}

df = pd.read_csv(CSV_PATH)

# --------------------------------------------------------
# Helpers
# --------------------------------------------------------
def get_section(df, category):
    """Slice rows belonging to a section like '— AGE GROUP —'."""
    section_label = f"— {category} —"
    idx_list = df.index[df["Subgroup"] == section_label].tolist()
    if not idx_list:
        raise ValueError(f"Section {category} not found")
    start_idx = idx_list[0]

    sub_rows = []
    for i in range(start_idx + 1, len(df)):
        val = df.loc[i, "Subgroup"]
        # stop at next section header line
        if isinstance(val, str) and val.strip().startswith("—"):
            break
        if pd.isna(val):
            df.loc[i, "Subgroup"] = "Unspecified"
        sub_rows.append(i)

    sub_df = df.loc[sub_rows, ["Subgroup"] + year_cols].copy()
    sub_df["Subgroup"] = sub_df["Subgroup"].fillna("Unspecified")
    sub_df[year_cols] = sub_df[year_cols].apply(pd.to_numeric, errors="coerce")
    return sub_df

def make_shades(base_color, n):
    """
    From a base hex color, create n darker/lighter shades
    using HSV value scaling.
    """
    rgb = np.array(mcolors.to_rgb(base_color))
    hsv = mcolors.rgb_to_hsv(rgb.reshape(1, 1, 3))[0, 0]

    # vary value (brightness) from 0.4 to 1.0
    vals = np.linspace(0.4, 1.0, n)
    shades = []
    for v in vals:
        h, s, _ = hsv
        new_hsv = np.array([h, s, v])
        new_rgb = mcolors.hsv_to_rgb(new_hsv.reshape(1, 1, 3))[0, 0]
        shades.append(new_rgb)
    return shades

# --------------------------------------------------------
# Prepare section data
# --------------------------------------------------------
sections = {}
for cat in categories:
    sections[cat] = get_section(df, cat)

n_years = len(year_cols)
n_cat = len(categories)

# --------------------------------------------------------
# MAIN FIGURE
# --------------------------------------------------------
plt.style.use("default")
fig, ax = plt.subplots(figsize=(14, 7))

fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x_years    = np.arange(n_years)
group_width = 0.8
bar_width   = group_width / n_cat

handles = []
labels  = []

for c_idx, cat in enumerate(categories):
    sub_df    = sections[cat]
    subgroups = sub_df["Subgroup"].tolist()
    values    = sub_df[year_cols].to_numpy()  # (n_subgroups, n_years)

    totals    = values.sum(axis=0)
    props_pct = values / totals * 100

    # positions for this category’s bar within each year cluster
    offset = (c_idx - (n_cat - 1) / 2) * bar_width
    x_cat  = x_years + offset

    bottom = np.zeros(n_years)

    # color shades for subgroups of this category
    base = base_colors.get(cat, "#333333")
    shades = make_shades(base, len(subgroups))

    for s_idx, subgroup in enumerate(subgroups):
        vals = values[s_idx]
        color = shades[s_idx]

        bars = ax.bar(
            x_cat,
            vals,
            bar_width,
            bottom=bottom,
            color=color,
            edgecolor="white",
        )

        # (optional) % labels inside stacks – commented to keep things clean
        # pct_vals = props_pct[s_idx]
        # for bar, pct in zip(bars, pct_vals):
        #     if pct > 8:
        #         ax.text(
        #             bar.get_x() + bar.get_width() / 2,
        #             bar.get_y() + bar.get_height() / 2,
        #             f"{pct:.0f}%",
        #             ha="center",
        #             va="center",
        #             fontsize=6,
        #             color="white",
        #         )

        bottom += vals

        # legend entry for this subgroup
        legend_label = f"{cat}: {subgroup}"
        handle = Patch(facecolor=color, edgecolor="white")
        handles.append(handle)
        labels.append(legend_label)

# axes styling
ax.set_xticks(x_years)
ax.set_xticklabels(year_cols, fontsize=11)
ax.set_ylabel("Total deaths", fontsize=12)
ax.set_xlabel("Year period", fontsize=12)
ax.set_title(
    "Heat-Related Mortality in Mexico\n"
    "Subgroup Composition by Year Period and Variable Group",
    fontsize=14,
)

# no legend here – saved separately
plt.tight_layout()
plt.savefig(OUT_MAIN, dpi=300, facecolor="white")
plt.show()

# --------------------------------------------------------
# LEGEND FIGURE (separate image)
# --------------------------------------------------------
fig_leg, ax_leg = plt.subplots(figsize=(8, 10))
fig_leg.patch.set_facecolor("white")
ax_leg.axis("off")

legend = ax_leg.legend(
    handles,
    labels,
    loc="center",
    frameon=False,
    ncol=2,
    fontsize=8,
    title="Subgroups by Variable Group",
)

plt.tight_layout()
plt.savefig(OUT_LEGEND, dpi=300, facecolor="white")
plt.show()
