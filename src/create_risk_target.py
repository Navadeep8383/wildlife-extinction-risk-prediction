"""
Risk Target Creation Script for IUCN Red List Tetrapod Assessment.

Loads:
  - data/processed/clean_dataset.csv

Creates:
  - RiskTarget column mapped from RedlistCategory:
      * LOW_RISK:
          - Least Concern
          - Near Threatened
          - Lower Risk/Least Concern
          - Lower Risk/Near Threatened
          - Lower Risk/Conservation Dependent
      * THREATENED:
          - Vulnerable
          - Endangered
          - Critically Endangered
      * EXTINCT:
          - Extinct
          - Extinct In The Wild

Retains:
  - Original RedlistCategory column and all 19 feature columns.

Saves:
  - data/processed/risk_target.csv

Verification:
  - Asserts no unmapped / null RiskTarget entries.
  - Prints class distribution, counts, and percentages.
"""

from pathlib import Path
import pandas as pd


# Explicit category mapping
RISK_MAPPING = {
    # LOW_RISK
    "Least Concern": "LOW_RISK",
    "Near Threatened": "LOW_RISK",
    "Lower Risk/Least Concern": "LOW_RISK",
    "Lower Risk/Near Threatened": "LOW_RISK",
    "Lower Risk/Conservation Dependent": "LOW_RISK",
    # THREATENED
    "Vulnerable": "THREATENED",
    "Endangered": "THREATENED",
    "Critically Endangered": "THREATENED",
    # EXTINCT
    "Extinct": "EXTINCT",
    "Extinct In The Wild": "EXTINCT",
}


def get_paths():
    """Resolve input and output paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    input_file = data_processed_dir / "clean_dataset.csv"
    output_file = data_processed_dir / "risk_target.csv"
    return input_file, output_file, data_processed_dir


def load_dataset(input_path: Path) -> pd.DataFrame:
    """Load clean dataset without modifying the original file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at: {input_path}")
    print(f"Loading cleaned dataset from: {input_path}...")
    df = pd.read_csv(input_path)
    print(f"  Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def create_risk_target(df: pd.DataFrame) -> pd.DataFrame:
    """Map RedlistCategory to RiskTarget and verify completeness."""
    df_result = df.copy()

    if "RedlistCategory" not in df_result.columns:
        raise KeyError("Column 'RedlistCategory' not found in dataset.")

    # Apply mapping
    df_result["RiskTarget"] = df_result["RedlistCategory"].map(RISK_MAPPING)

    # Verification: check for unmapped or null values
    unmapped_mask = df_result["RiskTarget"].isna()
    unmapped_count = unmapped_mask.sum()

    if unmapped_count > 0:
        unmapped_categories = df_result.loc[unmapped_mask, "RedlistCategory"].unique()
        raise ValueError(
            f"Found {unmapped_count} unmapped RiskTarget values! "
            f"Unmapped categories: {list(unmapped_categories)}"
        )

    print("Verification Passed: 0 unmapped or missing RiskTarget values.")
    return df_result


def print_distribution_report(df: pd.DataFrame):
    """Print class counts, percentages, and verification metrics."""
    total_rows = len(df)
    counts = df["RiskTarget"].value_counts(dropna=False)
    unmapped_count = df["RiskTarget"].isna().sum()

    print("\n" + "=" * 65)
    print("RISK TARGET DISTRIBUTION REPORT")
    print("=" * 65)
    print(f"Total Rows:     {total_rows:,}")
    print(f"Total Columns:  {len(df.columns)} (includes RedlistCategory & RiskTarget)")
    print(f"Unmapped Rows:  {unmapped_count} (0.00% missing)")
    print("-" * 65)
    print(f"{'Class':<15} | {'Count':>10} | {'Percentage':>12} | {'Included IUCN Categories'}")
    print("-" * 65)

    descriptions = {
        "LOW_RISK": "LC, NT, LR/lc, LR/nt, LR/cd",
        "THREATENED": "VU, EN, CR",
        "EXTINCT": "EX, EW",
    }

    # Order by customary risk level: LOW_RISK, THREATENED, EXTINCT
    for class_name in ["LOW_RISK", "THREATENED", "EXTINCT"]:
        cnt = counts.get(class_name, 0)
        pct = (cnt / total_rows) * 100
        desc = descriptions.get(class_name, "")
        print(f"{class_name:<15} | {cnt:>10,d} | {pct:>11.2f}% | {desc}")

    print("-" * 65)
    print(f"{'Total':<15} | {total_rows:>10,d} | {'100.00%':>12} |")
    print("=" * 65 + "\n")


def save_dataset(df: pd.DataFrame, output_path: Path):
    """Save dataset with RiskTarget column to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving risk target dataset to: {output_path}...")
    df.to_csv(output_path, index=False)
    print("Done! File saved successfully.")


def main():
    input_file, output_file, _ = get_paths()
    df = load_dataset(input_file)
    df_with_target = create_risk_target(df)
    print_distribution_report(df_with_target)
    save_dataset(df_with_target, output_file)


if __name__ == "__main__":
    main()
