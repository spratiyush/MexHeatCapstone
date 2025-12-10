import pandas as pd

# File paths
input_files = [
    "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_death_data/combined_1998_2002.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_death_data/combined_2003_2007.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_death_data/combined_2008_2012.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_death_data/combined_2013_2017.csv",
    "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_death_data/combined_2018_2022.csv"
]

# Columns to drop if present
cols_to_drop = ['TLOC_OCURR', 'DIA_REGIS', 'AREA_UR']

# Process each file
for file in input_files:
    print(f"\nProcessing: {file}")

    # Load data
    combined_data = pd.read_csv(file)

    # Drop unnecessary columns if they exist
    existing_to_drop = [col for col in cols_to_drop if col in combined_data.columns]
    if existing_to_drop:
        combined_data = combined_data.drop(columns=existing_to_drop)
        print(f"Dropped columns: {existing_to_drop}")
    else:
        print("No columns to drop found.")

    # Filter invalid municipalities
    combined_data = combined_data[combined_data['MUN_OCURR'] != 999]
    print(f"Rows after filtering: {len(combined_data)}")

    # Group and sum numeric columns
    summed_data = combined_data.groupby(
        ['date_of_occurrence', 'ENT_OCURR', 'MUN_OCURR'], as_index=False
    ).sum(numeric_only=True)

    # Print quick info
    print(f"Summed dataset shape: {summed_data.shape}")
    print(f"Columns: {summed_data.columns.tolist()}")

    # Define output path
    output_file = file.replace("combined_", "combined_sum_")
    summed_data.to_csv(output_file, index=False)

    print(f"✅ Saved summed file to: {output_file}")
