"""
Data Cleaning & Missing Value Imputation Script.

Pipeline:
  1. Load data/processed/feature_selected.csv.
  2. For numeric feature columns:
     - Convert values to numeric (coercing any invalid/citation text to NaN).
     - Fill missing values using the median of each column.
  3. For categorical feature columns:
     - Fill missing values using the mode (most frequent value).
  4. Keep RedlistCategory unchanged as the target.
  5. Save the cleaned dataset to data/processed/clean_dataset.csv.
  6. Print the shape and total number of missing values after cleaning.
  7. Do not modify feature_selected.csv.
"""

from pathlib import Path
import pandas as pd


# Schema definition
NUMERIC_FEATURES = [
    "BodyMass",
    "Verticality",
    "TrophicLevel",
    "Nocturnality",
    "MajorHabitatSum",
    "Latitude",
    "AnnuMeanTemp",
    "AnnuPrecip",
    "TempSeasonality",
    "PrecipSeasonality",
    "Elevation",
    "Rangesize",
    "HumanFootPrint",
    "InvasiveSpeciesResidual",
    "EndemicType",
]

CATEGORICAL_FEATURES = [
    "ClassName",
    "OrderName",
    "FamilyName",
    "PopulationTrend",
]

TARGET_COLUMN = "RedlistCategory"


def get_paths():
    """Resolve file paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    input_file = data_processed_dir / "feature_selected.csv"
    output_file = data_processed_dir / "clean_dataset.csv"
    return input_file, output_file, data_processed_dir


def load_dataset(input_path: Path) -> pd.DataFrame:
    """Load feature-selected dataset without modifying the original file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at: {input_path}")
    print(f"Loading dataset from: {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def clean_data(df: pd.DataFrame):
    """
    Imputes missing values:
      - Numeric features: converted via pd.to_numeric(..., errors='coerce') and filled with median.
      - Categorical features: filled with mode.
      - Target: kept unchanged.
    """
    df_clean = df.copy()

    imputation_summary = []

    print("\n--- Imputing Numeric Features (Median) ---")
    for col in NUMERIC_FEATURES:
        if col not in df_clean.columns:
            continue
        # Convert to numeric, coercing any malformed or non-numeric entries to NaN
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
        missing_count = int(df_clean[col].isna().sum())
        median_val = float(df_clean[col].median())
        df_clean[col] = df_clean[col].fillna(median_val)
        imputation_summary.append({
            "column": col,
            "type": "Numeric",
            "missing_imputed": missing_count,
            "fill_value": f"{median_val:.4g}" if isinstance(median_val, float) else str(median_val)
        })
        print(f"  {col:<25} | Missing: {missing_count:>6,d} | Imputed Median: {median_val}")

    print("\n--- Imputing Categorical Features (Mode) ---")
    for col in CATEGORICAL_FEATURES:
        if col not in df_clean.columns:
            continue
        missing_count = int(df_clean[col].isna().sum())
        mode_series = df_clean[col].mode(dropna=True)
        mode_val = mode_series.iloc[0] if not mode_series.empty else "Unknown"
        df_clean[col] = df_clean[col].fillna(mode_val)
        imputation_summary.append({
            "column": col,
            "type": "Categorical",
            "missing_imputed": missing_count,
            "fill_value": str(mode_val)
        })
        print(f"  {col:<25} | Missing: {missing_count:>6,d} | Imputed Mode: {mode_val}")

    print("\n--- Target Column ---")
    target_missing = int(df_clean[TARGET_COLUMN].isna().sum())
    print(f"  {TARGET_COLUMN:<25} | Unchanged | Missing: {target_missing}")

    return df_clean, imputation_summary


def print_clean_report(df_before: pd.DataFrame, df_clean: pd.DataFrame, summary: list):
    """Print cleaning report, shape, and total missing values."""
    print("\n" + "=" * 65)
    print("CLEANING & IMPUTATION REPORT")
    print("=" * 65)
    print(f"Dataset Shape: {df_clean.shape[0]:,} rows x {df_clean.shape[1]} columns")
    
    total_missing_before = df_before.isna().sum().sum()
    total_missing_after = df_clean.isna().sum().sum()

    print(f"Total Missing Values Before Cleaning: {total_missing_before:,}")
    print(f"Total Missing Values After Cleaning:  {total_missing_after:,}")
    print("-" * 65)

    print(f"{'Column':<25} | {'Type':<11} | {'Imputed':<8} | {'Fill Value'}")
    print("-" * 65)
    for item in summary:
        print(f"{item['column']:<25} | {item['type']:<11} | {item['missing_imputed']:<8} | {item['fill_value']}")
    print("=" * 65 + "\n")


def save_dataset(df: pd.DataFrame, output_path: Path):
    """Save cleaned dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving cleaned dataset to: {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done! Cleaned dataset saved successfully.")


def main():
    input_file, output_file, _ = get_paths()
    df_raw = load_dataset(input_file)
    df_clean, summary = clean_data(df_raw)
    print_clean_report(df_raw, df_clean, summary)
    save_dataset(df_clean, output_file)


if __name__ == "__main__":
    main()
