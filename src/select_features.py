"""
Feature Selection Script for IUCN Red List Tetrapod Assessment.

Loads:
  - data/processed/merged_dataset.csv

Filters:
  - 19 Feature Columns:
      BodyMass, Verticality, TrophicLevel, Nocturnality, MajorHabitatSum,
      Latitude, AnnuMeanTemp, AnnuPrecip, TempSeasonality, PrecipSeasonality,
      Elevation, Rangesize, HumanFootPrint, InvasiveSpeciesResidual,
      ClassName, OrderName, FamilyName, EndemicType, PopulationTrend
  - 1 Target Column:
      RedlistCategory

Drops:
  - All other columns

Saves:
  - data/processed/feature_selected.csv

Prints:
  - Resulting shape
  - Selected columns list
  - Missing-value counts and percentages
"""

from pathlib import Path
import pandas as pd


# Exact columns to retain
FEATURE_COLUMNS = [
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
    "ClassName",
    "OrderName",
    "FamilyName",
    "EndemicType",
    "PopulationTrend",
]

TARGET_COLUMN = "RedlistCategory"
ALL_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN]


def get_paths():
    """Resolve file paths relative to the project root directory."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    input_file = data_processed_dir / "merged_dataset.csv"
    output_file = data_processed_dir / "feature_selected.csv"
    return input_file, output_file, data_processed_dir


def load_dataset(input_path: Path) -> pd.DataFrame:
    """Load merged dataset without modifying original file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at: {input_path}")
    print(f"Loading merged dataset from: {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def select_features(df: pd.DataFrame) -> pd.DataFrame:
    """Select feature columns and target column, dropping all others."""
    # Verify all expected columns are present
    missing_cols = [col for col in ALL_COLUMNS if col not in df.columns]
    if missing_cols:
        raise KeyError(f"The following required columns were not found in dataset: {missing_cols}")

    df_selected = df[ALL_COLUMNS].copy()
    return df_selected


def print_report(df: pd.DataFrame):
    """Print shape, columns, and missing-value counts."""
    print("\n" + "=" * 65)
    print("FEATURE SELECTION REPORT")
    print("=" * 65)
    print(f"Resulting Shape: {df.shape[0]:,} rows x {df.shape[1]} columns\n")

    print("Columns (20 total):")
    print(f"  Features ({len(FEATURE_COLUMNS)}):")
    for idx, col in enumerate(FEATURE_COLUMNS, 1):
        print(f"    {idx:2d}. {col}")
    print(f"  Target (1):")
    print(f"    20. {TARGET_COLUMN}\n")

    print("Missing-Value Counts:")
    print(f"  {'Column':<26} | {'Missing Count':>13} | {'Missing %':>9}")
    print("  " + "-" * 54)
    missing_series = df.isna().sum()
    for col in ALL_COLUMNS:
        cnt = missing_series[col]
        pct = (cnt / len(df)) * 100
        print(f"  {col:<26} | {cnt:>13,d} | {pct:>8.2f}%")
    print("=" * 65 + "\n")


def save_dataset(df: pd.DataFrame, output_path: Path):
    """Save the filtered dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving feature-selected dataset to: {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done! File saved successfully.")


def main():
    input_file, output_file, _ = get_paths()
    df = load_dataset(input_file)
    df_selected = select_features(df)
    print_report(df_selected)
    save_dataset(df_selected, output_file)


if __name__ == "__main__":
    main()
