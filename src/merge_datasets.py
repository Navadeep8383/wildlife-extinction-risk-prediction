import os
from pathlib import Path
import pandas as pd


def get_paths():
    """Resolve file paths relative to the project root directory."""
    project_root = Path(__file__).resolve().parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"

    s2_file = data_raw_dir / "Data_S2._Summary_of_non-DD_Terrestrial_vertebrate_species.xlsx"
    s3_file = data_raw_dir / "Data_S3._Raw_data_for_the_30_711_analyzed_tetrapod_species_before_any_imputation.xlsx"
    output_file = data_processed_dir / "merged_dataset.csv"

    return s2_file, s3_file, output_file, data_processed_dir


def load_s2_data(s2_file: Path) -> pd.DataFrame:
    """Load S2 Excel file containing IUCN Red List categories and taxonomic metadata."""
    print(f"Loading S2: {s2_file.name}...")
    df_s2 = pd.read_excel(s2_file, sheet_name="Sheet 1", engine="openpyxl")
    print(f"  Loaded {len(df_s2):,} rows and {len(df_s2.columns)} columns from S2.")
    return df_s2


def load_s3_data(s3_file: Path) -> pd.DataFrame:
    """Load S3 Excel file across all 4 tetrapod classes (AVES, MAMMALIA, REPTILIA, AMPHIBIA)."""
    print(f"Loading S3: {s3_file.name}...")
    class_sheets = ["AVES", "MAMMALIA", "REPTILIA", "AMPHIBIA"]
    dfs = []

    for sheet in class_sheets:
        print(f"  Reading sheet: '{sheet}'...")
        df_sheet = pd.read_excel(s3_file, sheet_name=sheet, engine="openpyxl")
        print(f"    - {sheet}: {len(df_sheet):,} rows, {len(df_sheet.columns)} columns")
        dfs.append(df_sheet)

    # Combine all 4 taxonomic classes into a single DataFrame
    df_s3 = pd.concat(dfs, ignore_index=True)
    print(f"  Combined S3 dataset: {len(df_s3):,} rows, {len(df_s3.columns)} columns.")
    return df_s3


def main():
    s2_file, s3_file, output_file, data_processed_dir = get_paths()

    # Verify input files exist (read-only access, files are never modified)
    if not s2_file.exists():
        raise FileNotFoundError(f"Missing S2 file at: {s2_file}")
    if not s3_file.exists():
        raise FileNotFoundError(f"Missing S3 file at: {s3_file}")

    # 1. Load Excel datasets using pandas and openpyxl
    df_s2 = load_s2_data(s2_file)
    df_s3 = load_s3_data(s3_file)

    # 2. Compute matched and unmatched species counts before merge
    s3_species = set(df_s3["ScientificName"].dropna().unique())
    s2_species = set(df_s2["ScientificName"].dropna().unique())

    matched_species = s3_species.intersection(s2_species)
    unmatched_s3 = s3_species - s2_species
    unmatched_s2 = s2_species - s3_species

    # 3. Merge datasets on ScientificName
    # df_s3 has trait/environmental features
    # df_s2 contributes RedlistCategory and taxonomic metadata
    print("\nMerging S3 features and S2 IUCN categories on 'ScientificName'...")
    df_merged = pd.merge(df_s3, df_s2, on="ScientificName", how="inner")

    # 4. Print metrics
    print("\n" + "=" * 55)
    print("DATASET MERGE REPORT")
    print("=" * 55)
    print(f"Merged Rows:              {len(df_merged):,}")
    print(f"Merged Columns:           {len(df_merged.columns):,}")
    print("-" * 55)
    print(f"Unique Species in S3:     {len(s3_species):,}")
    print(f"Unique Species in S2:     {len(s2_species):,}")
    print(f"Matched Species:          {len(matched_species):,}")
    print(f"S3 Unmatched Species:     {len(unmatched_s3):,}")
    print(f"S2 Unmatched Species:     {len(unmatched_s2):,}")
    print("-" * 55)
    print("RedlistCategory Value Counts:")
    category_counts = df_merged["RedlistCategory"].value_counts(dropna=False)
    for category, count in category_counts.items():
        print(f"  {str(category):<32} {count:>7,}")
    print(f"  {'-' * 40}")
    print(f"  {'Total Labeled':<32} {category_counts.sum():>7,}")
    print("=" * 55 + "\n")

    # 5. Save the merged dataset to data/processed/merged_dataset.csv
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving merged dataset to: {output_file}...")
    df_merged.to_csv(output_file, index=False)
    print("Done! File saved successfully.")


if __name__ == "__main__":
    main()
