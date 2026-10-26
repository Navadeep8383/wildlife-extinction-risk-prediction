"""
Random Forest Hyperparameter Tuning & Comparison Script.

Configurations Evaluated:
  1. n_estimators=500, max_features="sqrt", min_samples_leaf=1
  2. n_estimators=500, max_features="sqrt", min_samples_leaf=2
  3. n_estimators=500, max_features="sqrt", min_samples_leaf=4
  4. n_estimators=500, max_features="log2", min_samples_leaf=2

Evaluation Metrics:
  - Accuracy
  - Balanced Accuracy
  - Macro F1
  - Weighted F1
  - EXTINCT Precision, Recall, and F1

Selection Criteria:
  - Primarily Macro F1 and Balanced Accuracy, with consideration for EXTINCT recall.
  - Best model saved to models/best_random_forest.joblib.
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
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix,
)


CONFIGURATIONS = [
    {
        "name": "Config 1 (sqrt, leaf=1)",
        "n_estimators": 500,
        "max_features": "sqrt",
        "min_samples_leaf": 1,
    },
    {
        "name": "Config 2 (sqrt, leaf=2)",
        "n_estimators": 500,
        "max_features": "sqrt",
        "min_samples_leaf": 2,
    },
    {
        "name": "Config 3 (sqrt, leaf=4)",
        "n_estimators": 500,
        "max_features": "sqrt",
        "min_samples_leaf": 4,
    },
    {
        "name": "Config 4 (log2, leaf=2)",
        "n_estimators": 500,
        "max_features": "log2",
        "min_samples_leaf": 2,
    },
]


def get_paths():
    """Resolve file paths relative to project root."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    models_dir = project_root / "models"

    x_train_path = data_dir / "X_train_smote.csv"
    y_train_path = data_dir / "y_train_smote.csv"
    x_test_path = data_dir / "X_test.csv"
    y_test_path = data_dir / "y_test.csv"
    best_model_path = models_dir / "best_random_forest.joblib"

    return (
        x_train_path,
        y_train_path,
        x_test_path,
        y_test_path,
        best_model_path,
        models_dir,
    )


def load_datasets(x_train_path, y_train_path, x_test_path, y_test_path):
    """Load train and test data."""
    print("Loading datasets...")
    X_train = pd.read_csv(x_train_path)
    y_train_df = pd.read_csv(y_train_path)
    y_train = y_train_df["RiskTarget"] if "RiskTarget" in y_train_df.columns else y_train_df.iloc[:, 0]

    X_test = pd.read_csv(x_test_path)
    y_test_df = pd.read_csv(y_test_path)
    y_test = y_test_df["RiskTarget"] if "RiskTarget" in y_test_df.columns else y_test_df.iloc[:, 0]

    print(f"  Training set: {X_train.shape[0]:,} samples x {X_train.shape[1]} features")
    print(f"  Test set:     {X_test.shape[0]:,} samples x {X_test.shape[1]} features")
    return X_train, y_train, X_test, y_test


def evaluate_config(config, X_train, y_train, X_test, y_test):
    """Train and evaluate a single Random Forest configuration."""
    print(f"\nTraining {config['name']}...")
    print(f"  Params: n_estimators={config['n_estimators']}, max_features='{config['max_features']}', min_samples_leaf={config['min_samples_leaf']}")

    model = RandomForestClassifier(
        n_estimators=config["n_estimators"],
        max_features=config["max_features"],
        min_samples_leaf=config["min_samples_leaf"],
        random_state=42,
        n_jobs=-1,
    )

    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    y_pred = model.predict(X_test)

    # Compute metrics
    acc = accuracy_score(y_test, y_pred)
    b_acc = balanced_accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    # Extinct metrics (target class 'EXTINCT')
    extinct_p = precision_score(y_test, y_pred, labels=["EXTINCT"], average=None, zero_division=0)[0]
    extinct_r = recall_score(y_test, y_pred, labels=["EXTINCT"], average=None, zero_division=0)[0]
    extinct_f1 = f1_score(y_test, y_pred, labels=["EXTINCT"], average=None, zero_division=0)[0]

    print(f"  Completed in {train_time:.1f}s | Acc: {acc:.4f} | BalAcc: {b_acc:.4f} | MacroF1: {macro_f1:.4f} | EXTINCT Recall: {extinct_r:.4f}")

    return {
        "config": config,
        "model": model,
        "accuracy": acc,
        "balanced_accuracy": b_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "extinct_precision": extinct_p,
        "extinct_recall": extinct_r,
        "extinct_f1": extinct_f1,
        "train_time": train_time,
        "y_pred": y_pred,
    }


def print_comparison_table(results):
    """Print comparative table of all configurations."""
    print("\n" + "=" * 105)
    print("RANDOM FOREST HYPERPARAMETER TUNING COMPARISON")
    print("=" * 105)
    header_fmt = "{:<25} | {:<7} | {:<7} | {:<8} | {:<8} | {:<9} | {:<8} | {:<8}"
    row_fmt    = "{:<25} | {:<7.4f} | {:<7.4f} | {:<8.4f} | {:<8.4f} | {:<9.4f} | {:<8.4f} | {:<8.4f}"

    print(header_fmt.format(
        "Configuration", "Acc", "BalAcc", "MacroF1", "W-F1", "EXT-Prec", "EXT-Rec", "EXT-F1"
    ))
    print("-" * 105)

    for r in results:
        print(row_fmt.format(
            r["config"]["name"],
            r["accuracy"],
            r["balanced_accuracy"],
            r["macro_f1"],
            r["weighted_f1"],
            r["extinct_precision"],
            r["extinct_recall"],
            r["extinct_f1"],
        ))
    print("=" * 105 + "\n")


def select_best_model(results):
    """
    Select best model primarily by Macro F1 and Balanced Accuracy,
    while considering EXTINCT recall.
    Composite score = 0.5 * MacroF1 + 0.3 * BalancedAcc + 0.2 * ExtinctRecall.
    """
    best = None
    best_score = -1.0

    for r in results:
        # Weighted composite score balancing general class fairness with critical extinction detection
        score = (
            0.50 * r["macro_f1"]
            + 0.30 * r["balanced_accuracy"]
            + 0.20 * r["extinct_recall"]
        )
        if score > best_score:
            best_score = score
            best = r

    print(f"Selected Best Model: {best['config']['name']}")
    print(f"  Macro F1:          {best['macro_f1']:.4f}")
    print(f"  Balanced Accuracy: {best['balanced_accuracy']:.4f}")
    print(f"  EXTINCT Recall:    {best['extinct_recall']:.4f}")
    print(f"  Overall Accuracy:  {best['accuracy']:.4f}")
    return best


def save_best_model(best_result, output_path):
    """Save best model to models/best_random_forest.joblib."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving best model to {output_path}...")
    joblib.dump(best_result["model"], output_path)
    print(f"Done! Model saved successfully ({output_path.stat().st_size / (1024 * 1024):.2f} MB).")


def main():
    (
        x_train_path,
        y_train_path,
        x_test_path,
        y_test_path,
        best_model_path,
        _,
    ) = get_paths()

    # 1. Load data
    X_train, y_train, X_test, y_test = load_datasets(
        x_train_path, y_train_path, x_test_path, y_test_path
    )

    # 2. Evaluate all configurations
    results = []
    for cfg in CONFIGURATIONS:
        res = evaluate_config(cfg, X_train, y_train, X_test, y_test)
        results.append(res)

    # 3. Print comparison table
    print_comparison_table(results)

    # 4. Select and save best model
    best = select_best_model(results)
    save_best_model(best, best_model_path)


if __name__ == "__main__":
    main()
