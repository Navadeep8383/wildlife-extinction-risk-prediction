"""
Random Forest Classifier Training & Evaluation Script.

Workflow:
  1. Load SMOTE-balanced training features and labels:
     - data/processed/X_train_smote.csv
     - data/processed/y_train_smote.csv
  2. Load untouched test features and labels:
     - data/processed/X_test.csv
     - data/processed/y_test.csv
  3. Train a RandomForestClassifier:
     - n_estimators=500
     - random_state=42
     - n_jobs=-1
     - max_features="sqrt"
  4. Evaluate on the untouched test set:
     - Accuracy
     - Balanced Accuracy
     - Macro F1
     - Weighted F1
     - Classification Report
     - Confusion Matrix
  5. Save trained model to models/random_forest_smote.joblib.
  6. Print all evaluation results clearly.
  7. Leave existing datasets unmodified.
"""

from pathlib import Path
import time
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


def get_paths():
    """Resolve file and directory paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    models_dir = project_root / "models"

    x_train_path = data_dir / "X_train_smote.csv"
    y_train_path = data_dir / "y_train_smote.csv"
    x_test_path = data_dir / "X_test.csv"
    y_test_path = data_dir / "y_test.csv"
    model_output_path = models_dir / "random_forest_smote.joblib"

    return (
        x_train_path,
        y_train_path,
        x_test_path,
        y_test_path,
        model_output_path,
        models_dir,
    )


def load_datasets(
    x_train_path: Path,
    y_train_path: Path,
    x_test_path: Path,
    y_test_path: Path,
):
    """Load training and test datasets without modifying files."""
    for path in [x_train_path, y_train_path, x_test_path, y_test_path]:
        if not path.exists():
            raise FileNotFoundError(f"Required dataset not found at: {path}")

    print("Loading datasets...")
    X_train = pd.read_csv(x_train_path)
    y_train_df = pd.read_csv(y_train_path)
    y_train = y_train_df["RiskTarget"] if "RiskTarget" in y_train_df.columns else y_train_df.iloc[:, 0]

    X_test = pd.read_csv(x_test_path)
    y_test_df = pd.read_csv(y_test_path)
    y_test = y_test_df["RiskTarget"] if "RiskTarget" in y_test_df.columns else y_test_df.iloc[:, 0]

    print(f"  Training Features (SMOTE): {X_train.shape[0]:,} rows x {X_train.shape[1]} columns")
    print(f"  Training Labels   (SMOTE): {y_train.shape[0]:,} samples")
    print(f"  Test Features (Untouched): {X_test.shape[0]:,} rows x {X_test.shape[1]} columns")
    print(f"  Test Labels   (Untouched): {y_test.shape[0]:,} samples")

    return X_train, y_train, X_test, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """Initialize and train RandomForestClassifier with specified hyperparameters."""
    print("\nInitializing RandomForestClassifier...")
    print("  Hyperparameters: n_estimators=500, random_state=42, n_jobs=-1, max_features='sqrt'")

    rf = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        n_jobs=-1,
        max_features="sqrt",
        verbose=1,
    )

    start_time = time.time()
    print(f"\nTraining model on {len(X_train):,} SMOTE-balanced samples...")
    rf.fit(X_train, y_train)
    elapsed = time.time() - start_time
    print(f"Model training completed in {elapsed:.2f} seconds.")

    return rf


def evaluate_model(model: RandomForestClassifier, X_test: pd.DataFrame, y_test: pd.Series):
    """Evaluate model predictions on untouched test set and compute metrics."""
    print("\nEvaluating model on untouched test set...")
    start_time = time.time()
    y_pred = model.predict(X_test)
    eval_time = time.time() - start_time
    print(f"Inference completed in {eval_time:.2f} seconds.")

    # Target class order
    class_labels = ["LOW_RISK", "THREATENED", "EXTINCT"]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")
    report = classification_report(y_test, y_pred, labels=class_labels, digits=4)
    cm = confusion_matrix(y_test, y_pred, labels=class_labels)

    # Print evaluation report
    print("\n" + "=" * 70)
    print("RANDOM FOREST MODEL EVALUATION REPORT (UNTOUCHED TEST SET)")
    print("=" * 70)
    print(f"Test Set Samples:       {len(y_test):,}")
    print(f"Accuracy:               {acc * 100:.2f}%  ({acc:.4f})")
    print(f"Balanced Accuracy:      {balanced_acc * 100:.2f}%  ({balanced_acc:.4f})")
    print(f"Macro F1 Score:         {macro_f1 * 100:.2f}%  ({macro_f1:.4f})")
    print(f"Weighted F1 Score:      {weighted_f1 * 100:.2f}%  ({weighted_f1:.4f})")
    print("-" * 70)
    print("\nDetailed Classification Report:")
    print(report)
    print("-" * 70)
    print("\nConfusion Matrix (Rows: True, Columns: Predicted):")
    print(f"{'':<14} | {'Pred LOW_RISK':>14} | {'Pred THREATENED':>15} | {'Pred EXTINCT':>12}")
    print("-" * 65)
    for idx, true_label in enumerate(class_labels):
        print(f"True {true_label:<9} | {cm[idx, 0]:>14,d} | {cm[idx, 1]:>15,d} | {cm[idx, 2]:>12,d}")
    print("=" * 70 + "\n")

    return {
        "accuracy": acc,
        "balanced_accuracy": balanced_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "classification_report": report,
        "confusion_matrix": cm,
    }


def save_model(model: RandomForestClassifier, output_path: Path):
    """Save trained model to models directory using joblib."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving trained model to: {output_path}...")
    joblib.dump(model, output_path)
    print(f"Done! Model saved successfully ({output_path.stat().st_size / (1024 * 1024):.2f} MB).")


def main():
    (
        x_train_path,
        y_train_path,
        x_test_path,
        y_test_path,
        model_output_path,
        _,
    ) = get_paths()

    # 1. Load data
    X_train, y_train, X_test, y_test = load_datasets(
        x_train_path, y_train_path, x_test_path, y_test_path
    )

    # 2. Train model
    rf = train_model(X_train, y_train)

    # 3. Evaluate model
    evaluate_model(rf, X_test, y_test)

    # 4. Save model
    save_model(rf, model_output_path)


if __name__ == "__main__":
    main()
