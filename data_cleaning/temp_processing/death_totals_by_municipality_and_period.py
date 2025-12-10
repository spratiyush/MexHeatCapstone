import pandas as pd

# Read the CSV file
df = pd.read_csv('/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/updated_Heatwave_Summary_ByPeriod_Municipality.csv')

# Select columns and rename
df_filtered = df[['hw_95_max_1', 'year_period', 'municipality']].copy()
df_filtered.rename(columns={'hw_95_max_1': 'deaths_total'}, inplace=True)

# Save to new CSV
df_filtered.to_csv('/Users/pratiyush/Desktop/MexicoHeatMortality/heatwave95_total.csv', index=False)

print("CSV file created successfully!")