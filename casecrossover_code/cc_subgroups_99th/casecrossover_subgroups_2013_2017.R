# --- 0) Packages ---
library(dplyr)
library(lubridate)
library(survival)
library(broom)
library(data.table)

# --- 1) Load ---
death_data <- fread("/Users/pratiyush/Desktop/MexicoHeatMortality/combined_sum_death_data/combined_sum_2013_2017.csv")
death_data$date <- as.Date(death_data$date_of_occurrence)

death_data$municipality <- paste0("MX",
                                  sprintf("%02d", death_data$ENT_OCURR),
                                  sprintf("%03d", death_data$MUN_OCURR))

weather_data <- fread("/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/Heatwave_Indicators_Mexico_1998_2022.csv")

# make sure 'date' is Date in weather
if (!inherits(weather_data$date, "Date")) weather_data$date <- as.Date(weather_data$date)

weather_data <- weather_data %>% filter(year(date) >= 2013, year(date) <= 2017)

# -------------------------------
# 2. Aggregate Mortality Dataset
# -------------------------------

death_data <- death_data %>%
  mutate(date = as.Date(date_of_occurrence))

daily_deaths <- death_data %>%
  group_by(municipality, date) %>%
  summarise(all_deaths = sum(Group_A_SEXO + Group_B_SEXO + Group_C_SEXO, na.rm = TRUE), .groups = "drop") %>%
  mutate(
    wday  = lubridate::wday(date),
    month = lubridate::month(date),
    year  = lubridate::year(date),
    case_date = date,
    ID_grp = dplyr::row_number()
  )

# --- 3) Weather lags (per municipality) ---
weather_data <- weather_data %>%
  arrange(municipality, date) %>%
  group_by(municipality) %>%
  mutate(
    hw_99_max_1_lag1 = lag(hw_99_max_1),
    hw_99_min_1_lag1 = lag(hw_99_min_1),
    hw_99_max_2_lag1 = lag(hw_99_max_2),
    hw_99_min_2_lag1 = lag(hw_99_min_2),
    hw_99_max_3_lag1 = lag(hw_99_max_3),
    hw_99_min_3_lag1 = lag(hw_99_min_3),
    hw_abs_30_lag1   = lag(hw_abs_30),
    hw_abs_35_lag1   = lag(hw_abs_35),
    wday  = lubridate::wday(date),
    month = lubridate::month(date),
    year  = lubridate::year(date)
  ) %>%
  ungroup()

# --- 4) Time-stratified expansion (case + matched controls) ---
# KEEP dates as Date; join on (municipality, year, month, wday) by design.
data_cc <- daily_deaths %>%
  left_join(
    weather_data,
    by = c("municipality","year","month","wday"),
    relationship = "many-to-many"  # <-- acknowledge expected m2m
  ) %>%
  mutate(
    # case if the weather row corresponds to the actual case day
    case = as.integer(date.y == case_date)
  ) %>%
  # keep only strata with at least one event (weights > 0 already guaranteed by construction)
  filter(all_deaths > 0)

# Optional sanity checks:
# how many controls per case?
# data_cc %>% count(municipality, case_date, name = "n_controls") %>% summary(n_controls)
# how many events?
# sum(data_cc$case)

# --- 5) Models ---
hw_vars <- c("hw_99_max_1", "hw_99_min_1", "hw_99_max_2", "hw_99_min_2",
             "hw_99_max_3", "hw_99_min_3", "hw_abs_30", "hw_abs_35")
hw_vars_lag1 <- paste0(hw_vars, "_lag1")

run_models <- function(vars, data, label = "Same Day") {
  res <- lapply(vars, function(var) {
    dat <- data %>% filter(!is.na(.data[[var]]))
    if (nrow(dat) == 0) return(NULL)
    
    fit <- clogit(as.formula(paste0("case ~ ", var, " + strata(ID_grp)")),
                  data = dat, weights = all_deaths)
    
    broom::tidy(fit) %>%
      dplyr::filter(term == var) %>%
      mutate(
        variable = var,
        or      = exp(estimate),
        or_low  = exp(estimate - 1.96*std.error),
        or_high = exp(estimate + 1.96*std.error),
        type    = label
      )
  })
  bind_rows(res)
}

results_same_day <- run_models(hw_vars, data_cc, "Same Day")
results_lag1    <- run_models(hw_vars_lag1, data_cc, "Lag 1 Day")
results_all     <- bind_rows(results_same_day, results_lag1) %>%
  dplyr::mutate(year_period = "2013-2017") %>%
  select(variable, type, estimate, std.error, statistic, or, or_low, or_high, p.value, year_period)

# ===============================
# 6. Subgroup analyses (add-on)
# ===============================

# -- Helper to build a case-crossover dataset for a given subgroup weight column
make_cc_for_subgroup <- function(weight_col) {
  # Aggregate subgroup-specific deaths per municipality-day
  daily_sub <- death_data %>%
    mutate(date = as.Date(date_of_occurrence)) %>%
    group_by(municipality = paste0("MX", sprintf("%02d", ENT_OCURR), sprintf("%03d", MUN_OCURR)),
             date) %>%
    summarise(all_deaths = sum(.data[[weight_col]], na.rm = TRUE), .groups = "drop") %>%
    mutate(
      wday = wday(date),
      month = month(date),
      year = year(date),
      week = week(date),
      day = format(date, "%d"),
      case_date = date,
      ID_grp = row_number()
    )
  
  # Match your current join keys & case flag
  daily_sub %>%
    mutate(date = as.character(date)) %>%
    left_join(
      weather_data %>% mutate(date = as.character(date)),
      by = c("municipality", "year", "month", "wday")
    ) %>%
    mutate(case = if_else(as.character(date.x) == as.character(date.y), 1, 0)) %>%
    filter(all_deaths > 0)
}

# -- Vectors of subgroup columns (adjust names here if needed)
edad_groups        <- paste0("Group_", LETTERS[1:6], "_EDAD")        # A..F
escolarida_groups  <- paste0("Group_", LETTERS[1:5], "_ESCOLARIDA")  # A..E
sexo_groups        <- paste0("Group_", LETTERS[1:3], "_SEXO")        # A..C
is_groups          <- c("IS_I", "IS_J", "IS_F", "IS_TX")

# NEW subgroup families
nationality_groups <- c("NACIONALID_MEXICANA",
                        "NACIONALID_EXTRANJERA",
                        "NACIONALID_NO_ESPEC")

civil_groups <- c("CIVIL_SINGLE",
                  "CIVIL_MARRIED",
                  "CIVIL_COHABITING",
                  "CIVIL_DIVORCED_SEPERATED",
                  "CIVIL_WIDOWED",
                  "CIVIL_NOT_SPEC")

ocupacion_groups <- c("Group_A_OCUPACION",
                      "Group_B_OCUPACION",
                      "Group_C_OCUPACION")

# -- Wrapper to run models for a list of subgroup columns
analyze_subgroup_set <- function(group_cols, subgroup_type_label) {
  results_list <- lapply(seq_along(group_cols), function(i) {
    gc <- group_cols[i]
    message(paste0("▶ Starting subgroup ", i, "/", length(group_cols),
                   " [", subgroup_type_label, " → ", gc, "] ..."))
    
    cc_df <- make_cc_for_subgroup(gc)
    res_same  <- run_models(hw_vars,      cc_df, "Same Day")
    res_lag1  <- run_models(hw_vars_lag1, cc_df, "Lag 1 Day")
    
    result <- bind_rows(res_same, res_lag1) %>%
      mutate(subgroup_type = subgroup_type_label,
             subgroup      = gc,
             year_period = "2013-2017")
    
    message(paste0("✅ Completed: ", subgroup_type_label, " → ", gc))
    return(result)
  })
  
  bind_rows(results_list)
}

# -- Run all subgroup families
results_edad         <- analyze_subgroup_set(edad_groups,        "EDAD")
results_escolarida   <- analyze_subgroup_set(escolarida_groups,  "ESCOLARIDAD")
results_sexo         <- analyze_subgroup_set(sexo_groups,        "SEXO")
results_is           <- analyze_subgroup_set(is_groups,          "CAUSE_IS")
results_nationality  <- analyze_subgroup_set(nationality_groups, "NACIONALIDAD")
results_civil        <- analyze_subgroup_set(civil_groups,       "CIVIL_STATUS")
results_ocupacion    <- analyze_subgroup_set(ocupacion_groups,   "OCUPACION")

# -- Combine with your overall results if you want a single file
results_subgroups_all <- bind_rows(
  results_edad,
  results_escolarida,
  results_sexo,
  results_is,
  results_nationality,
  results_civil,
  results_ocupacion
)

# -- Save & view a comparison table
write.csv(results_subgroups_all,
          "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_13_17_subgroups.csv",
          row.names = FALSE)

results_subgroups_all %>%
  select(subgroup_type, subgroup, variable, type, or, or_low, or_high, p.value) %>%
  arrange(subgroup_type, subgroup, type, variable)


