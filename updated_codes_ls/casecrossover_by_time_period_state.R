# --- 0) Packages ---
library(dplyr)
library(lubridate)
library(survival)
library(broom)
library(data.table)

# --- 1) Paths ---
BASE_DIR <- "/Users/larasch/Documents/UCB_postdoc/Research/Mexico_heat_vulnerability/data"

death_dir   <- file.path(BASE_DIR, "death_data/summaries")
weather_dir <- file.path(BASE_DIR, "updated_temp_data")
output_dir  <- file.path(BASE_DIR, "casecrossover_data")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

output_file <- file.path(output_dir, "heatwave_case_crossover_all_periods.csv")

# --- 2) Periods & heatwave variables ---
periods <- list(
  "1998_2002" = 1998:2002,
  "2003_2007" = 2003:2007,
  "2008_2012" = 2008:2012,
  "2013_2017" = 2013:2017,
  "2018_2022" = 2018:2022
)

hw_vars <- c("hw_99_max_1","hw_95_max_1")  # add more if needed
hw_vars_lag1 <- paste0(hw_vars, "_lag1")

# --- 3) Helper function to run models ---
run_models <- function(DT, vars, label) {
  res <- lapply(vars, function(var) {
    dat <- DT[!is.na(DT[[var]]), ]
    if (nrow(dat) == 0) return(NULL)
    
    fit <- clogit(
      as.formula(paste0("case ~ ", var, " + strata(ID_grp)")),
      data = dat,
      weights = all_deaths,
      method="approximate"
    )
    
    tidy(fit) %>%
      filter(term == var) %>%
      mutate(
        variable = var,
        or       = exp(estimate),
        or_low   = exp(estimate - 1.96 * std.error),
        or_high  = exp(estimate + 1.96 * std.error),
        type     = label
      )
  })
  bind_rows(res)
}

# --- 4) Loop through periods ---
all_results <- list()

for (period_name in names(periods)) {
  
  years_subset <- periods[[period_name]]
  message("Processing period: ", period_name)
  
  # ----- Load death data -----
  death_file <- file.path(death_dir, paste0("combined_sum_", period_name, ".csv"))
  death_data <- fread(death_file)
  
  death_data[, date := as.IDate(date_of_occurrence)]
  death_data[, municipality := paste0("MX",
                                      sprintf("%02d", ENT_OCURR),
                                      sprintf("%03d", MUN_OCURR))]
  
  # Sum deaths per day
  daily_deaths <- death_data[, .(
    all_deaths = sum(Group_A_SEXO + Group_B_SEXO + Group_C_SEXO, na.rm = TRUE)
  ), by = .(ENT_OCURR, municipality, date)][all_deaths > 0]
  
  # Add case-crossover helpers
  daily_deaths[, `:=`(
    wday = as.integer(strftime(date, "%u")),
    month = as.integer(strftime(date, "%m")),
    year = as.integer(strftime(date, "%Y")),
    case_date = date,
    ID_grp = .I,
    year_period = period_name
  )]
  
  # ----- Load weather data -----
  weather_file <- file.path(weather_dir, "Heatwave_Indicators_Mexico_1998_2022.csv")
  weather_data <- fread(weather_file)
  weather_data[, date := as.IDate(date)]
  weather_data <- weather_data[year(date) %in% years_subset]
  
  # Add lag1
  #setorder(weather_data, municipality, date)
  #for (var in hw_vars) {
   # weather_data[, paste0(var, "_lag1") := shift(.SD[[var]], 1L, type = "lag"), by = municipality]
 # }
  
  # Add join helpers
  weather_data[, `:=`(
    wday = as.integer(strftime(date, "%u")),
    month = as.integer(strftime(date, "%m")),
    year = as.integer(strftime(date, "%Y"))
  )]
  
  # ----- Merge daily deaths with weather -----
  setkey(daily_deaths, municipality, year, month, wday)
  setkey(weather_data, municipality, year, month, wday)
  cc_all <- weather_data[daily_deaths, allow.cartesian = TRUE]
  cc_all[, case := as.integer(date == case_date)]
  
  # ----- 4a) Overall models -----
  results_overall <- run_models(cc_all, hw_vars, "Same Day")
  #results_overall <- bind_rows(results_overall,
                              # run_models(cc_all, hw_vars_lag1, "Lag 1 Day"))
  results_overall <- results_overall %>% mutate(ENT_OCURR = "All", year_period = period_name)
  
  # ----- 4b) State-specific models -----
  #states <- sort(unique(daily_deaths$ENT_OCURR))
  states <- as.character(sort(unique(daily_deaths$ENT_OCURR)))
  results_states <- lapply(states, function(st) {
    dt_st <- cc_all[ENT_OCURR == st]
    if (nrow(dt_st) == 0) return(NULL)
    res <- run_models(dt_st, hw_vars, "Same Day")
    res <- bind_rows(res, run_models(dt_st, hw_vars_lag1, "Lag 1 Day"))
    if (nrow(res) == 0) return(NULL)
    res$ENT_OCURR <- st
    res$year_period <- period_name
    res
  })
  results_states <- bind_rows(results_states)
  
  # ----- Combine and store -----
  all_results[[period_name]] <- bind_rows(results_overall, results_states)
  
}

# ----- 5) Final dataset -----
final_results <- bind_rows(all_results)

# Save
fwrite(final_results, output_file)
message("Saved all results to: ", output_file)
