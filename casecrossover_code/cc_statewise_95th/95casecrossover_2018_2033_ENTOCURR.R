# ================================
# Case-Crossover: hw_95_max_1 only
# Stratified by ENT_OCURR & period
# Period: 2018-2022 (chunked by state)
# ================================

# --- 0) Packages ---
suppressPackageStartupMessages({
  library(data.table)
  library(survival)
})

# --- 1) Paths ---
path_deaths  <- "/Users/pratiyush/Desktop/MexicoHeatMortality/combined_sum_death_data/combined_sum_2018_2022.csv"
path_weather <- "/Users/pratiyush/Desktop/MexicoHeatMortality/daymet_temperature_data/updated_dec5_Heatwave_Indicators_Mexico_1998_2022.csv"
path_out     <- "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_18_22_STATE_hw95max1.csv"

# --- 2) Load (minimal columns; stick to data.table) ---
death_dt <- fread(path_deaths)

# Ensure date column
if (!"date" %in% names(death_dt)) {
  if ("date_of_occurrence" %in% names(death_dt)) {
    death_dt[, date := as.IDate(date_of_occurrence)]
  } else stop("No 'date' or 'date_of_occurrence' in death_data.")
} else {
  death_dt[, date := as.IDate(date)]
}

# Ensure municipality id
if (!"municipality" %in% names(death_dt)) {
  stopifnot(all(c("ENT_OCURR","MUN_OCURR") %in% names(death_dt)))
  death_dt[, municipality := paste0("MX",
                                    sprintf("%02d", ENT_OCURR),
                                    sprintf("%03d", MUN_OCURR))]
}

# Sum deaths per day/mun/state
needed_cols <- c("Group_A_SEXO","Group_B_SEXO","Group_C_SEXO")
stopifnot(all(needed_cols %in% names(death_dt)))

death_daily <- death_dt[
  , .(all_deaths = sum(get("Group_A_SEXO") + get("Group_B_SEXO") + get("Group_C_SEXO"), na.rm = TRUE)),
  by = .(ENT_OCURR, municipality, date)
][all_deaths > 0]

# Add stratum helpers & period
death_daily[
  , `:=`(
    wday = as.integer(strftime(date, "%u")),   # 1–7 (Mon–Sun)
    month = as.integer(strftime(date, "%m")),
    year  = as.integer(strftime(date, "%Y")),
    case_date = date,
    ID_grp = .I,                               # unique within this table
    year_period = "2018-2022"
  )
]

# Free original large death data
rm(death_dt); gc()

# Read weather with only the columns we need
# (expects columns: municipality, date, hw_95_max_1; ENT_OCURR optional)
weather_cols <- c("municipality", "date", "hw_95_max_1", "ENT_OCURR")
weather_raw  <- fread(path_weather, select = intersect(weather_cols, names(fread(path_weather, nrows = 0))))

# Date cast and year filter (fast)
if (!inherits(weather_raw$date, "IDate")) weather_raw[, date := as.IDate(date)]
weather_raw  <- weather_raw[date >= "2018-01-01" & date <= "2022-12-31"]

# Ensure state code on weather
if (!"ENT_OCURR" %in% names(weather_raw)) {
  stopifnot("municipality" %in% names(weather_raw))
  weather_raw[, ENT_OCURR := as.integer(substr(municipality, 3, 4))]
}

# Precompute join helpers on weather
weather_raw[
  , `:=`(
    wday  = as.integer(strftime(date, "%u")),
    month = as.integer(strftime(date, "%m")),
    year  = as.integer(strftime(date, "%Y"))
  )
]

# Compute lag-1 by municipality
setorder(weather_raw, municipality, date)
weather_raw[
  , hw_95_max_1_lag1 := shift(hw_95_max_1, n = 1L, type = "lag"),
  by = municipality
]

# Indexing for fast joins
setkey(weather_raw, municipality, year, month, wday)

# --- 3) Helpers ---
run_one_var <- function(DT, varname, label) {
  # Drop NA exposure rows
  X <- DT[!is.na(get(varname))]
  if (nrow(X) == 0L) return(NULL)
  # clogit
  fit <- clogit(case ~ get(varname) + strata(ID_grp), data = X, weights = all_deaths)
  s  <- summary(fit)$coefficients
  # s has rows per term; the first row is our var
  est <- s[1, "coef"]; se <- s[1, "se(coef)"]; z <- s[1, "z"]; p <- s[1, "Pr(>|z|)"]
  data.table(
    variable = varname,
    type = label,
    estimate = est,
    std.error = se,
    statistic = z,
    or = exp(est),
    or_low  = exp(est - 1.96*se),
    or_high = exp(est + 1.96*se),
    p.value = p
  )
}

analyze_state <- function(state_code) {
  # Subset to one state
  d_state <- death_daily[ENT_OCURR == state_code]
  if (nrow(d_state) == 0L) return(NULL)
  
  # Join to weather by (municipality, year, month, wday) — many-to-many
  setkey(d_state, municipality, year, month, wday)
  cc <- weather_raw[d_state, allow.cartesian = TRUE]  # right join onto deaths
  
  # Mark cases (same-date match); keep only case/control tied to case days
  cc[, case := as.integer(date == case_date)]
  cc <- cc[all_deaths > 0L]
  
  # Run two models
  res_same <- run_one_var(cc, "hw_95_max_1",       "Same Day")
  res_lag1 <- run_one_var(cc, "hw_95_max_1_lag1",  "Lag 1 Day")
  
  if (is.null(res_same) && is.null(res_lag1)) return(NULL)
  
  rbindlist(list(res_same, res_lag1), use.names = TRUE, fill = TRUE)[
    , `:=`(ENT_OCURR = state_code, year_period = "2018-2022")
  ]
}

# --- 4) Run per state & append to disk ---
dir.create(dirname(path_out), showWarnings = FALSE, recursive = TRUE)
if (file.exists(path_out)) file.remove(path_out)

states <- sort(unique(death_daily$ENT_OCURR))

for (st in states) {
  cat("Processing state ENT_OCURR =", st, "...\n")
  res <- analyze_state(st)
  if (!is.null(res) && nrow(res)) {
    fwrite(res[
      , .(ENT_OCURR, year_period, variable, type,
          estimate, std.error, statistic, or, or_low, or_high, p.value)
    ], path_out, append = file.exists(path_out))
  }
  # Free memory each iteration
  rm(res); gc()
}

cat("\nSaved stratified results to:\n", path_out, "\n")

# Optional: peek
if (file.exists(path_out)) {
  print(head(fread(path_out)))
}
