import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1) Path to your filtered Same Day file ---
path = "/Users/pratiyush/Desktop/MexicoHeatMortality/sup_fig1_filtered_hw99max1_sameday.csv"

# --- 2) Load and filter for Sex (Male/Female only) ---
df = pd.read_csv(path)

sex_df = df[
    (df["subgroup_type"] == "Sex") &
    (df["subgroup"].isin(["Male", "Female"]))
].copy()

# Ensure numeric
for col in ["or", "or_low", "or_high"]:
    sex_df[col] = pd.to_numeric(sex_df[col], errors="coerce")

# --- 3) Define time order for x-axis ---
year_order = ["1998-2002", "2003-2007", "2008-2012", "2013-2017", "2018-2022"]
x_base = np.arange(len(year_order))

fig, ax = plt.subplots(figsize=(8, 5))

# --- 4) Black background styling ---
fig.patch.set_facecolor("black")
ax.set_facecolor("black")

for spine in ax.spines.values():
    spine.set_color("white")

ax.tick_params(colors="white")
ax.yaxis.label.set_color("white")
ax.xaxis.label.set_color("white")
ax.title.set_color("white")

# --- 5) Colors (point vs CI) ---
# Male: brighter point, deeper CI
male_point_color = "#ffeb3b"   # bright yellow
male_ci_color    = "#fbc02d"   # darker/deeper yellow

# Women = pink theme
female_point_color = "#ff80ab"  # bright pink
female_ci_color    = "#d81b60" 

# X-offset so groups don't overlap
offset = 0.12
subgroups = [("Male", -offset, male_point_color, male_ci_color),
             ("Female", +offset, female_point_color, female_ci_color)]

# --- 6) Faint horizontal reference band around OR ~ 1.0–1.02 ---
ax.axhspan(1.0, 1.02, color="grey", alpha=0.15, zorder=0)

# --- 7) Plot CI bars + points with halo for each sex group ---
for subgroup, x_off, pt_color, ci_color in subgroups:
    d = sex_df[sex_df["subgroup"] == subgroup].set_index("year_period")
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
        color="white",
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
ax.set_xticklabels(year_order, rotation=0, color="white")
ax.set_xlabel("Year period")
ax.set_ylabel("Odds ratio (OR)")

# horizontal line at OR = 1
ax.axhline(1, linestyle="--", linewidth=1, color="white", alpha=0.6, zorder=1)

ax.set_title("Heatwave (hw_99_max_1, Same Day): OR for heat-related mortality by sex")

# Legend
handles, labels = ax.get_legend_handles_labels()
# remove duplicates (since we added label twice)
unique = dict(zip(labels, handles))
legend = ax.legend(
    unique.values(),
    unique.keys(),
    title="Sex",
    facecolor="black",
    edgecolor="white",
)
plt.setp(legend.get_texts(), color="white")
plt.setp(legend.get_title(), color="white")

fig.tight_layout()

out_path = "/Users/pratiyush/Desktop/MexicoHeatMortality/sex_or_line_with_ci.png"
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"✅ Saved figure to: {out_path}")

plt.show()


