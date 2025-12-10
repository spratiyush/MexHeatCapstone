# --- Combine Case-Crossover Results (STATE_hw99max1) ---

library(data.table)

# File paths
files <- c(
  "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_98_02_STATE_hw99max1.csv",
  "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_03_07_STATE_hw99max1.csv",
  "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_08_12_STATE_hw99max1.csv",
  "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_13_17_STATE_hw99max1.csv",
  "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/heatwave_case_crossover_results_18_22_STATE_hw99max1.csv"
)

# Read and combine
combined <- rbindlist(lapply(files, fread), fill = TRUE)

# Output path
out_path <- "/Users/pratiyush/Desktop/MexicoHeatMortality/casecrossover_data/combined_heatwave_case_crossover_results_STATE_hw99max1.csv"

# Write combined file
fwrite(combined, out_path)

cat("✅ Combined file saved to:", out_path, "\n")

n_rows <- nrow(fread(out_path))
cat("✅ Number of rows in combined file:", n_rows, "\n")

