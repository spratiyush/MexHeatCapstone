library(dplyr)
library(lubridate)
library(readr)

# --- Load death dataset ---
death_data <- read_csv("/Users/pratiyush/Desktop/MexicoHeatMortality/combined_sum_death_data/00_combined_sum_1998_2022.csv")

# --- Load weather dataset ---
weather_data <- read_csv("/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Heatwave_Indicators_Mexico_1998_2022.csv")

# --- Create unified municipality ID for death data ---
death_data <- death_data %>%
  mutate(
    municipality = paste0(
      "MX",
      sprintf("%02d", ENT_OCURR),
      sprintf("%03d", MUN_OCURR)
    ),
    date = as.Date(date_of_occurrence)
  )

# Make sure columns align
names(death_data)
names(weather_data)

# Check overlap in municipality IDs and dates
length(intersect(death_data$municipality, weather_data$municipality))

# Perform left join to retain all mortality observations
merged_data <- death_data %>%
  left_join(weather_data, by = c("municipality", "date"))

# Inspect merged dataset
glimpse(merged_data)

# Count of municipalities and dates
merged_data %>%
  summarise(
    n_municipalities = n_distinct(municipality),
    date_range = paste(min(date), max(date))
  )

write_csv(
  merged_data,
  "/Users/pratiyush/Desktop/MexicoHeatMortality/merged_mortality_weather_1998_2022.csv"
)

