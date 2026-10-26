"""
Training Data Preparation Script for IUCN Red List Tetrapod Assessment.

Pipeline:
  1. Load data/processed/risk_target.csv.
  2. Separate predictors (19 feature columns) from target (RiskTarget).
     (Excludes original RedlistCategory from predictors).
  3. Perform stratified 80/20 train/test split with random_state=42.
  4. One-hot encode categorical features consistently (fit on train, transform train and test).
  5. Apply SMOTE exclusively to the training data (never test data) to balance classes.
  6. Save train/test datasets and SMOTE-balanced datasets to data/processed/.
  7. Print shapes and class distributions before and after SMOTE.
  8. Leave risk_target.csv unmodified.
"""

from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from imblearn.over_sampling import SMOTE


# 19 Feature predictors
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

CATEGORICAL_FEATURES = [
    "ClassName",
    "OrderName",
    "FamilyName",
    "PopulationTrend",
]

NUMERIC_FEATURES = [
    col for col in FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES
]

TARGET_COLUMN = "RiskTarget"


def get_paths():
    """Resolve input and output paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    input_file = data_processed_dir / "risk_target.csv"
    return input_file, data_processed_dir


def load_data(input_file: Path) -> pd.DataFrame:
    """Load risk_target.csv without modifying the file."""
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found at: {input_file}")
    print(f"Loading data from: {input_file}...")
    df = pd.read_csv(input_file)
    print(f"  Loaded {len(df):,} rows and {len(df.columns)} columns.")
    return df


def split_data(df: pd.DataFrame):
    """Split into 80% train and 20% test with stratification on RiskTarget."""
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    print("\nPerforming Stratified 80/20 Split (random_state=42)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"  Train set: {len(X_train):,} samples (80.0%)")
    print(f"  Test set:  {len(X_test):,} samples (20.0%)")
    return X_train, X_test, y_train, y_test


def encode_features(X_train: pd.DataFrame, X_test: pd.DataFrame):
    """
    Fit OneHotEncoder on train categorical features and transform both train and test.
    Keeps numeric features unchanged and concatenates encoded columns.
    """
    print("\nOne-Hot Encoding Categorical Features...")
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    
    # Fit on training set only to prevent data leakage
    encoder.fit(X_train[CATEGORICAL_FEATURES])

    encoded_cat_train = encoder.transform(X_train[CATEGORICAL_FEATURES])
    encoded_cat_test = encoder.transform(X_test[CATEGORICAL_FEATURES])

    encoded_cat_cols = list(encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    print(f"  Encoded {len(CATEGORICAL_FEATURES)} categorical features into {len(encoded_cat_cols)} one-hot columns.")

    # Convert back to DataFrames with preserved indices
    df_cat_train = pd.DataFrame(encoded_cat_train, columns=encoded_cat_cols, index=X_train.index)
    df_cat_test = pd.DataFrame(encoded_cat_test, columns=encoded_cat_cols, index=X_test.index)

    # Combine numeric and one-hot encoded categorical features
    X_train_encoded = pd.concat([X_train[NUMERIC_FEATURES], df_cat_train], axis=1)
    X_test_encoded = pd.concat([X_test[NUMERIC_FEATURES], df_cat_test], axis=1)

    print(f"  Total encoded feature count: {X_train_encoded.shape[1]}")
    return X_train_encoded, X_test_encoded, encoder


def apply_smote(X_train_encoded: pd.DataFrame, y_train: pd.Series):
    """Apply SMOTE only to training data to balance minority classes."""
    print("\nApplying SMOTE to training data (random_state=42)...")
    smote = SMOTE(random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train_encoded, y_train)

    # Wrap back into DataFrame and Series with correct column names
    X_train_smote = pd.DataFrame(X_train_smote, columns=X_train_encoded.columns)
    y_train_smote = pd.Series(y_train_smote, name=TARGET_COLUMN)

    return X_train_smote, y_train_smote


def print_distributions(y_train: pd.Series, y_test: pd.Series, y_train_smote: pd.Series):
    """Print class counts and percentages before and after SMOTE."""
    order = ["LOW_RISK", "THREATENED", "EXTINCT"]

    print("\n" + "=" * 70)
    print("CLASS DISTRIBUTIONS & SHAPES BEFORE AND AFTER SMOTE")
    print("=" * 70)

    print("\n1. Train Set (Original 80% Split, Before SMOTE):")
    train_counts = y_train.value_counts()
    for cls in order:
        cnt = train_counts.get(cls, 0)
        pct = (cnt / len(y_train)) * 100
        print(f"   {cls:<15} : {cnt:>6,d} ({pct:6.2f}%)")
    print(f"   {'TOTAL':<15} : {len(y_train):>6,d} (100.00%)")

    print("\n2. Test Set (Original 20% Split, Unmodified):")
    test_counts = y_test.value_counts()
    for cls in order:
        cnt = test_counts.get(cls, 0)
        pct = (cnt / len(y_test)) * 100
        print(f"   {cls:<15} : {cnt:>6,d} ({pct:6.2f}%)")
    print(f"   {'TOTAL':<15} : {len(y_test):>6,d} (100.00%)")

    print("\n3. Train Set (After SMOTE Oversampling):")
    smote_counts = y_train_smote.value_counts()
    for cls in order:
        cnt = smote_counts.get(cls, 0)
        pct = (cnt / len(y_train_smote)) * 100
        print(f"   {cls:<15} : {cnt:>6,d} ({pct:6.2f}%)")
    print(f"   {'TOTAL':<15} : {len(y_train_smote):>6,d} (100.00%)")
    print("=" * 70 + "\n")


def save_datasets(
    output_dir: Path,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    X_train_smote: pd.DataFrame,
    y_train_smote: pd.Series,
):
    """Save split and balanced training/test datasets to data/processed."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Saving datasets to {output_dir}...")

    # 1. Feature and target files for original split
    X_train.to_csv(output_dir / "X_train.csv", index=False)
    y_train.to_csv(output_dir / "y_train.csv", index=False)
    X_test.to_csv(output_dir / "X_test.csv", index=False)
    y_test.to_csv(output_dir / "y_test.csv", index=False)
    print("  Saved X_train.csv, y_train.csv, X_test.csv, y_test.csv")

    # 2. SMOTE-balanced training files
    X_train_smote.to_csv(output_dir / "X_train_smote.csv", index=False)
    y_train_smote.to_csv(output_dir / "y_train_smote.csv", index=False)
    print("  Saved X_train_smote.csv, y_train_smote.csv")

    # 3. Combined full datasets for convenience
    train_combined = pd.concat([X_train, y_train.reset_index(drop=True)], axis=1)
    test_combined = pd.concat([X_test, y_test.reset_index(drop=True)], axis=1)
    train_smote_combined = pd.concat([X_train_smote, y_train_smote.reset_index(drop=True)], axis=1)

    train_combined.to_csv(output_dir / "train_data.csv", index=False)
    test_combined.to_csv(output_dir / "test_data.csv", index=False)
    train_smote_combined.to_csv(output_dir / "train_data_smote.csv", index=False)
    print("  Saved combined datasets: train_data.csv, test_data.csv, train_data_smote.csv")
    print("All datasets saved successfully.")


def main():
    input_file, output_dir = get_paths()
    df = load_data(input_file)

    # 1. Split data
    X_train, X_test, y_train, y_test = split_data(df)

    # 2. One-hot encode
    X_train_encoded, X_test_encoded, _ = encode_features(X_train, X_test)

    # 3. Apply SMOTE on train only
    X_train_smote, y_train_smote = apply_smote(X_train_encoded, y_train)

    # 4. Print distributions
    print_distributions(y_train, y_test, y_train_smote)

    # 5. Save all datasets
    save_datasets(
        output_dir,
        X_train_encoded,
        y_train,
        X_test_encoded,
        y_test,
        X_train_smote,
        y_train_smote,
    )


if __name__ == "__main__":
    main()
