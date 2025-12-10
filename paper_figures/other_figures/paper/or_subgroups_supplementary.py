import pandas as pd

# Path to your file
path = "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_1998_2022_subgroups_combined.csv"

# Load data
df = pd.read_csv(path)

# Filter for term == "hw_99_max_1" AND type == "Same Day"
df_filtered = df[(df["term"] == "hw_99_max_1") & (df["type"] == "Same Day")]

# ---------------------------------------------------------------------
# Label map for subgroup (detailed categories)
# ---------------------------------------------------------------------
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
}

# ---------------------------------------------------------------------
# Label map for subgroup_type (higher-level categories)
# ---------------------------------------------------------------------
subgroup_type_map = {
    "EDAD": "Age group",
    "ESCOLARIDAD": "Education level",
    "SEXO": "Sex",
    "CAUSE_IS": "Cause of death",
    "CIVIL_STATUS": "Marital status",
    "OCUPACION": "Occupation",
}

# Apply mapping to "subgroup"
df_filtered["subgroup"] = df_filtered["subgroup"].map(label_map).fillna(df_filtered["subgroup"])

# Apply mapping to "subgroup_type"
df_filtered["subgroup_type"] = df_filtered["subgroup_type"].map(subgroup_type_map).fillna(df_filtered["subgroup_type"])

# Select columns (dropping type)
cols = ["or", "or_low", "or_high", "subgroup_type", "subgroup", "year_period"]
df_selected = df_filtered[cols]

# View results
print(df_selected)

# Save
df_selected.to_csv("sup_fig1_filtered_hw99max1_sameday.csv", index=False)
