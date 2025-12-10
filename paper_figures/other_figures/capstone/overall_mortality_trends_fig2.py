import matplotlib.pyplot as plt
from matplotlib import font_manager

# Use IBM Plex Sans (must be installed on system)
plt.rcParams['font.family'] = 'IBM Plex Sans'

# Data
years = ["1998–2002", "2003–2007", "2008–2012", "2013–2017", "2018–2022"]
deaths = [2214743, 2442976, 2883684, 3290952, 4470363]

# Styling
plt.style.use("default")
fig, ax = plt.subplots(figsize=(10,6))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")

# Plot (updated color)
ax.plot(years, deaths, color="#C95136", marker="o", markersize=8, linewidth=3)

# Labels
ax.set_title("Heat-Related Mortality Trends in Mexico", fontsize=18, color="white")
ax.set_ylabel("Total Deaths", fontsize=14, color="white")
ax.set_xlabel("Year Period", fontsize=14, color="white")

# Tick styling
ax.tick_params(colors="white", labelsize=12)

# Grid
ax.grid(color="gray", alpha=0.3)

# Save
plt.savefig("heat_mortality_mexico_trend.png", dpi=300, facecolor="black")

plt.show()
