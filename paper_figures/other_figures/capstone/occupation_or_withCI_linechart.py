import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1) Path to your filtered Same Day file ---
path = "/Users/pratiyush/Desktop/MexicoHeatMortality/sup_fig1_filtered_hw99max1_sameday.csv"

# --- 2) Load and filter for Occupation subgroups ---
df = pd.read_csv(path)

occupation_df = df[
    (df["subgroup_type"] == "Occupation") &
    (df["subgroup"].isin([
        "Indoor workers/professions",
        "Outdoor workers/professions",
        "Unemployed or ineligible",
    ]))
].copy()

# Ensure numeric
for col in ["or", "or_low", "or_high"]:
    occupation_df[col] = pd.to_numeric(occupation_df[col], errors="coerce")

# --- 3) Define time order for x-axis ---
year_order = ["1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022"]
x_base = np.arange(len(year_order))

fig, ax = plt.subplots(figsize=(8, 5))

# --- 4) Black background styling ---
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

for spine in ax.spines.values():
    spine.set_color("black")

ax.tick_params(colors="black")
ax.yaxis.label.set_color("black")
ax.xaxis.label.set_color("black")
ax.title.set_color("black")

# --- 5) Colors (point vs CI) ---
# Indoor = green theme
indoor_point_color = "#81c784"   # light green
indoor_ci_color    = "#388e3c"   # darker green

# Outdoor = blue theme
outdoor_point_color = "#64b5f6"  # light blue
outdoor_ci_color    = "#1976d2"  # darker blue

# Unemployed/ineligible = yellow theme
unemp_point_color = "#fff59d"    # light yellow
unemp_ci_color    = "#fbc02d"    # darker yellow

# X-offset so groups don't overlap (3 groups)
offset = 0.18
subgroups = [
    ("Indoor workers/professions",   -offset, indoor_point_color, indoor_ci_color),
    ("Outdoor workers/professions",   0.0,    outdoor_point_color, outdoor_ci_color),
    ("Unemployed or ineligible",     +offset, unemp_point_color,   unemp_ci_color),
]

# --- 6) Faint horizontal reference band around OR ~ 1.0–1.02 ---
ax.axhspan(1.0, 1.02, color="grey", alpha=0.15, zorder=0)

# --- 7) Plot CI bars + points with halo for each occupation group ---
for subgroup, x_off, pt_color, ci_color in subgroups:
    d = occupation_df[occupation_df["subgroup"] == subgroup].set_index("year_period")
    d = d.reindex(year_order)

    y_or = d["or"].values
    y_low = d["or_low"].values
    y_high = d["or_high"].values

    x_pos = x_base + x_off

    # --- CI as thick vertical bar with caps ---
    for x, y0, y1 in zip(x_pos, y_low, y_high):
        if np.isnan(y0) or np.isnan(y1):
            continue

        # vertical "range" bar
        ax.vlines(
            x,
            y0,
            y1,
            color=ci_color,
            linewidth=5,      # thick
            alpha=0.6,
            zorder=1,
        )

        # small caps at top and bottom
        cap_width = 0.06
        ax.hlines(
            [y0, y1],
            x - cap_width,
            x + cap_width,
            color=ci_color,
            linewidth=3,
            alpha=0.8,
            zorder=2,
        )

    # --- Connect OR means across time with a line (behind points) ---
    ax.plot(
        x_pos,
        y_or,
        color=ci_color,
        linewidth=1.5,
        alpha=0.9,
        zorder=2,
    )

    # --- Point with white "halo" then filled color ---
    # halo
    ax.scatter(
        x_pos,
        y_or,
        s=70,
        color="black",
        zorder=3,
    )
    # colored point on top
    ax.scatter(
        x_pos,
        y_or,
        s=45,
        color=pt_color,
        edgecolor="none",
        alpha=1.0,
        zorder=4,
        label=subgroup,
    )

# --- 8) Axis labels, ticks, ref line, legend ---
ax.set_xticks(x_base)
ax.set_xticklabels(year_order, rotation=0, color="black")
ax.set_xlabel("Year period")
ax.set_ylabel("Odds ratio (OR)")

# horizontal line at OR = 1
ax.axhline(1, linestyle="--", linewidth=1, color="black", alpha=0.6, zorder=1)

ax.set_title("Heatwave (hw_99_max_1, Same Day): OR for heat-related mortality by occupation")

# Legend
handles, labels = ax.get_legend_handles_labels()
# remove duplicates (since we added label multiple times)
unique = dict(zip(labels, handles))
legend = ax.legend(
    unique.values(),
    unique.keys(),
    title="Occupation",
    facecolor="white",
    edgecolor="white",
)
plt.setp(legend.get_texts(), color="black")
plt.setp(legend.get_title(), color="black")

fig.tight_layout()

out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/slide45.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"✅ Saved figure to: {out_path}")

plt.show()