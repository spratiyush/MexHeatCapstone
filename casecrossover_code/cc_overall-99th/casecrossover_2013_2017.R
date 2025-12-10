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

# --- 6) Export (fix the path!) ---
out_path <- "~/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_13_17.csv"
dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)
write.csv(results_all, out_path, row.names = FALSE)

# Quick view
results_all %>% arrange(type, variable)
