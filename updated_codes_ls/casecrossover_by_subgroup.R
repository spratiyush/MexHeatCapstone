# -------------------------------------------------------------
# --- 0) Packages ---
# -------------------------------------------------------------
library(data.table)
library(dplyr)
library(lubridate)
library(survival)
library(broom)

# -------------------------------------------------------------
# --- 1) Paths ---
# -------------------------------------------------------------
BASE_DIR <- "/Users/larasch/Documents/UCB_postdoc/Research/Mexico_heat_vulnerability/data"

death_dir   <- file.path(BASE_DIR, "death_data/summaries")
weather_dir <- file.path(BASE_DIR, "updated_temp_data")
output_dir  <- file.path(BASE_DIR, "casecrossover_data")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

output_file <- file.path(
  output_dir,
  "heatwave_case_crossover_all_periods_subgroups.csv"
)

# -------------------------------------------------------------
# --- 2) Periods & heatwave variables ---
# -------------------------------------------------------------
periods <- list(
  "1998_2002" = 1998:2002,
  "2003_2007" = 2003:2007,
  "2008_2012" = 2008:2012,
  "2013_2017" = 2013:2017,
  "2018_2022" = 2018:2022
)

hw_vars <- c(
  "hw_99_max_1",
  "hw_95_max_1",
  "hw_90_max_1",
  "hw_abs_30",
  "hw_abs_35"
)

# -------------------------------------------------------------
# --- 3) Load weather once ---
# -------------------------------------------------------------
weather_file <- file.path(
  weather_dir,
  "Heatwave_Indicators_Mexico_1998_2022.csv"
)

weather_data <- fread(weather_file)
weather_data[, date := as.IDate(date)]

weather_data[, `:=`(
  wday  = as.integer(strftime(date, "%u")),
  month = as.integer(strftime(date, "%m")),
  year  = as.integer(strftime(date, "%Y"))
)]

setkey(weather_data, municipality, year, month, wday)

# -------------------------------------------------------------
# --- 4) Helper functions ---
# -------------------------------------------------------------

# ---- 4a) Weighted conditional logistic regression ----
run_models <- function(DT, vars, label, weight_col) {
  
  res <- lapply(vars, function(var) {
    
    dat <- DT[
      !is.na(DT[[var]]) &
        !is.na(DT[[weight_col]]) &
        DT[[weight_col]] > 0
    ]
    
    if (nrow(dat) == 0) return(NULL)
    
    fit <- clogit(
      as.formula(paste0("case ~ ", var, " + strata(ID_grp)")),
      data   = dat,
      weight = dat[[weight_col]],
      method = "approximate"
    )
    
    tidy(fit) |>
      filter(term == var) |>
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

# ---- 4b) Create case-crossover dataset ----
make_cc_subgroup <- function(death_data, subgroup_var, period_years) {
  
  if (is.null(subgroup_var)) {
    # Overall population: sum across SEXO
    sexo_vars <- c("Group_A_SEXO","Group_B_SEXO","Group_C_SEXO")
    
    daily <- death_data[
      year(date_of_occurrence) %in% period_years,
      .(
        ENT_OCURR = ENT_OCURR,
        municipality = paste0(
          "MX",
          sprintf("%02d", ENT_OCURR),
          sprintf("%03d", MUN_OCURR)
        ),
        date = as.IDate(date_of_occurrence),
        weight = rowSums(.SD, na.rm = TRUE)
      ),
      .SDcols = sexo_vars
    ]
    
  } else {
    # Subgroup: use the column directly
    daily <- death_data[
      year(date_of_occurrence) %in% period_years,
      .(
        ENT_OCURR = ENT_OCURR,
        municipality = paste0(
          "MX",
          sprintf("%02d", ENT_OCURR),
          sprintf("%03d", MUN_OCURR)
        ),
        date = as.IDate(date_of_occurrence),
        weight = get(subgroup_var)
      )
    ]
  }
  
  # Keep only days with deaths
  daily <- daily[weight > 0]
  
  daily[, `:=`(
    wday      = as.integer(strftime(date, "%u")),
    month     = as.integer(strftime(date, "%m")),
    year      = as.integer(strftime(date, "%Y")),
    case_date = date,
    ID_grp    = .I
  )]
  
  setkey(daily, municipality, year, month, wday)
  cc <- weather_data[daily, allow.cartesian = TRUE]
  
  cc[, case := as.integer(date == case_date)]
  
  cc[]
}

# ---- 4c) Run all subgroups within a family ----
analyze_subgroup_set <- function(death_data, period_years, group_cols, subgroup_type_label) {
  
  res_list <- lapply(group_cols, function(gvar) {
    
    message("  ▶ Subgroup: ", gvar)
    
    cc_df <- make_cc_subgroup(
      death_data,
      subgroup_var = gvar,
      period_years = period_years
    )
    
    run_models(
      cc_df,
      hw_vars,
      label      = "Same Day",
      weight_col = "weight"
    ) |>
      mutate(
        subgroup_type = subgroup_type_label,
        subgroup      = gvar,
        year_period   = paste0(min(period_years), "_", max(period_years))
      )
  })
  
  bind_rows(res_list)
}

# -------------------------------------------------------------
# --- 5) Subgroup families ---
# -------------------------------------------------------------
subgroup_list <- list(
  EDAD = paste0("Group_", LETTERS[1:6], "_EDAD"),
  ESCOLARIDAD = paste0("Group_", LETTERS[1:5], "_ESCOLARIDA"),
  SEXO = paste0("Group_", LETTERS[1:3], "_SEXO"),
  CAUSE_IS = c("IS_I", "IS_J", "IS_F", "IS_TX"),
  NACIONALIDAD = c(
    "NACIONALID_MEXICANA",
    "NACIONALID_EXTRANJERA",
    "NACIONALID_NO_ESPEC"
  ),
  CIVIL_STATUS = c(
    "CIVIL_SINGLE",
    "CIVIL_MARRIED",
    "CIVIL_COHABITING",
    "CIVIL_DIVORCED_SEPERATED",
    "CIVIL_WIDOWED",
    "CIVIL_NOT_SPEC"
  ),
  OCUPACION = c(
    "Group_A_OCUPACION",
    "Group_B_OCUPACION",
    "Group_C_OCUPACION"
  )
)

# -------------------------------------------------------------
# --- 6) MAIN LOOP ---
# -------------------------------------------------------------
all_results <- list()

for (period_name in names(periods)) {
  
  message("==== Processing period: ", period_name, " ====")
  period_years <- periods[[period_name]]
  
  death_file <- file.path(
    death_dir,
    paste0("combined_sum_", period_name, ".csv")
  )
  
  death_data <- fread(death_file)
  death_data[, date_of_occurrence := as.IDate(date_of_occurrence)]
  
  # ---- Overall population ----
  cc_overall <- make_cc_subgroup(
    death_data,
    subgroup_var = NULL,
    period_years = period_years
  )
  
  res_overall <- run_models(
    cc_overall,
    hw_vars,
    label      = "Same Day",
    weight_col = "weight"
  ) |>
    mutate(
      subgroup_type = "All",
      subgroup      = "All",
      year_period   = period_name
    )
  
  # ---- Subgroups ----
  res_subgroups <- lapply(names(subgroup_list), function(subgrp) {
    analyze_subgroup_set(
      death_data,
      period_years,
      subgroup_list[[subgrp]],
      subgroup_type_label = subgrp
    )
  }) |> bind_rows()
  
  all_results[[period_name]] <- bind_rows(
    res_overall,
    res_subgroups
  )
}

# -------------------------------------------------------------
# --- 7) Save results ---
# -------------------------------------------------------------
final_results <- bind_rows(all_results)
fwrite(final_results, output_file)

message("Saved results to: ", output_file)
