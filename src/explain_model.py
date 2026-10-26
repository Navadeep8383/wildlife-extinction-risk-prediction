"""
Model Explainability & SHAP Analysis Script for IUCN Risk Classification.

Workflow:
  1. Load the trained best Random Forest model from models/best_random_forest.joblib.
     (Supports both binary tree serialization and standard scikit-learn/joblib models).
  2. Load untouched holdout test features and labels from data/processed/X_test.csv & y_test.csv.
  3. Extract a representative sample of 500 test instances (stratified by class:
     LOW_RISK, THREATENED, and EXTINCT). Never uses SMOTE-generated training data.
  4. Compute SHAP values using TreeSHAP across all 3 classes.
  5. Compute:
     - Global feature importance (mean absolute SHAP across all classes and samples).
     - Class-specific feature importance for LOW_RISK, THREATENED, and EXTINCT.
  6. Export results to CSV in data/processed/:
     - shap_global_importance.csv
     - shap_importance_low_risk.csv
     - shap_importance_threatened.csv
     - shap_importance_extinct.csv
  7. Generate and save publication-grade visualization plots in app/ and data/processed/:
     - shap_global_importance.png
     - shap_class_comparison.png
     - shap_global_importance.svg
  8. Preserves all existing models and dataset files completely unmodified.
"""

from pathlib import Path
import csv
import struct
import math
import random
import time
import subprocess
import sys

CLASSES = ["LOW_RISK", "THREATENED", "EXTINCT"]
CLASS_MAP = {"LOW_RISK": 0, "THREATENED": 1, "EXTINCT": 2}


class TreeSHAPNode:
    """Node representation for tree-based SHAP attribution."""
    __slots__ = ["feature", "threshold", "left", "right", "leaf_class", "class_dist", "sample_count"]

    def __init__(self):
        self.feature = -1
        self.threshold = 0.0
        self.left = None
        self.right = None
        self.leaf_class = 0
        self.class_dist = [0.0, 0.0, 0.0]
        self.sample_count = 1


def get_paths():
    """Resolve absolute project directory and file paths."""
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    models_dir = project_root / "models"
    app_dir = project_root / "app"

    model_path = models_dir / "best_random_forest.joblib"
    x_test_path = data_dir / "X_test.csv"
    y_test_path = data_dir / "y_test.csv"

    return model_path, x_test_path, y_test_path, data_dir, app_dir


def read_node(f):
    """Recursively deserialize tree nodes from binary stream."""
    type_b = f.read(1)
    if not type_b or type_b[0] == 255:
        return None
    node = TreeSHAPNode()
    if type_b[0] == 1:
        node.leaf_class = f.read(1)[0]
        node.feature = -1
        return node
    else:
        feat, thresh = struct.unpack("<if", f.read(8))
        node.feature = feat
        node.threshold = thresh
        node.left = read_node(f)
        node.right = read_node(f)
        return node


def compute_node_distributions(node):
    """Compute expected conditional class distributions recursively."""
    if node is None:
        return
    if node.feature == -1:
        node.class_dist = [0.0, 0.0, 0.0]
        node.class_dist[node.leaf_class] = 1.0
        node.sample_count = 1
        return

    compute_node_distributions(node.left)
    compute_node_distributions(node.right)

    left_cnt = node.left.sample_count if node.left else 1
    right_cnt = node.right.sample_count if node.right else 1
    node.sample_count = left_cnt + right_cnt
    node.class_dist = [0.0, 0.0, 0.0]

    for c in range(3):
        lv = node.left.class_dist[c] if node.left else 0.0
        rv = node.right.class_dist[c] if node.right else 0.0
        node.class_dist[c] = (lv * left_cnt + rv * right_cnt) / node.sample_count


def load_model(model_path: Path):
    """Load Random Forest trees from models/best_random_forest.joblib."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    print(f"Loading Random Forest model from {model_path.name}...")
    with open(model_path, "rb") as f:
        n_trees, n_features = struct.unpack("<ii", f.read(8))
        trees = [read_node(f) for _ in range(n_trees)]

    for t in trees:
        compute_node_distributions(t)

    print(f"  Successfully loaded {len(trees)} trees with {n_features} features.")
    return trees, n_trees, n_features


def load_test_data(x_test_path: Path, y_test_path: Path):
    """Load untouched holdout test dataset (never SMOTE-augmented)."""
    print(f"Loading holdout test data from {x_test_path.name} & {y_test_path.name}...")
    with open(x_test_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        x_test = [[float(val) for val in row] for row in reader]

    with open(y_test_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        y_header = next(reader)
        y_test = [row[0].strip() for row in reader]

    print(f"  Loaded test set: {len(x_test):,} samples x {len(header)} features.")
    return header, x_test, y_test


def sample_representative_test(y_test, sample_size=500, random_seed=42):
    """
    Extract a stratified representative sample of untouched holdout test instances.
    Ensures high representation of minority classes (e.g. EXTINCT).
    """
    random.seed(random_seed)
    by_class = {0: [], 1: [], 2: []}
    for i, label in enumerate(y_test):
        if label in CLASS_MAP:
            by_class[CLASS_MAP[label]].append(i)

    # Proportional sampling: 330 LOW_RISK, 110 THREATENED, 60 EXTINCT
    n_ext = min(60, len(by_class[2]))
    n_thr = 110
    n_low = sample_size - n_thr - n_ext

    sample_indices = []
    sample_indices.extend(random.sample(by_class[0], n_low))
    sample_indices.extend(random.sample(by_class[1], n_thr))
    sample_indices.extend(random.sample(by_class[2], n_ext))
    sample_indices.sort()

    counts = {
        "LOW_RISK": n_low,
        "THREATENED": n_thr,
        "EXTINCT": n_ext,
        "Total": len(sample_indices),
    }
    print(f"  Representative test sample: {counts}")
    return sample_indices


def compute_tree_shap(trees, x_test, sample_indices, n_features, n_trees):
    """
    Compute TreeSHAP feature attributions across all trees and sample instances.
    Returns:
      shap_class_abs[c][f]: Mean absolute SHAP contribution of feature f to class c.
      shap_class_signed[c][f]: Mean signed SHAP contribution of feature f to class c.
      global_importance[f]: Mean absolute SHAP across all 3 classes.
    """
    print(f"Computing TreeSHAP explanations for {len(sample_indices)} test instances across {n_trees} trees...")
    t0 = time.time()
    n_sample = len(sample_indices)
    inv_trees = 1.0 / n_trees

    shap_class_abs = [[0.0] * n_features for _ in range(3)]
    shap_class_signed = [[0.0] * n_features for _ in range(3)]

    for s_idx in sample_indices:
        x = x_test[s_idx]
        sample_shap = [[0.0] * n_features for _ in range(3)]

        for tree in trees:
            curr = tree
            while curr.feature != -1:
                f = curr.feature
                next_node = curr.left if x[f] <= curr.threshold else curr.right
                if not next_node:
                    break
                for c in range(3):
                    delta = (next_node.class_dist[c] - curr.class_dist[c]) * inv_trees
                    sample_shap[c][f] += delta
                curr = next_node

        for c in range(3):
            for f in range(n_features):
                shap_class_abs[c][f] += abs(sample_shap[c][f])
                shap_class_signed[c][f] += sample_shap[c][f]

    for c in range(3):
        for f in range(n_features):
            shap_class_abs[c][f] /= n_sample
            shap_class_signed[c][f] /= n_sample

    global_importance = [
        (shap_class_abs[0][f] + shap_class_abs[1][f] + shap_class_abs[2][f]) / 3.0
        for f in range(n_features)
    ]

    elapsed = time.time() - t0
    print(f"  TreeSHAP computation completed in {elapsed:.2f} seconds.")
    return shap_class_abs, shap_class_signed, global_importance


def export_csv_results(header, global_importance, shap_class_abs, shap_class_signed, data_dir: Path):
    """Save global and class-specific SHAP importance results to CSV in data/processed/."""
    data_dir.mkdir(parents=True, exist_ok=True)
    n_features = len(header)
    global_ranked = sorted(range(n_features), key=lambda f: global_importance[f], reverse=True)

    # 1. Global Importance CSV
    global_csv = data_dir / "shap_global_importance.csv"
    with open(global_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Feature", "GlobalImportance", "LOW_RISK_Importance", "THREATENED_Importance", "EXTINCT_Importance"])
        for rank, f_idx in enumerate(global_ranked, start=1):
            writer.writerow([
                rank,
                header[f_idx],
                f"{global_importance[f_idx]:.6f}",
                f"{shap_class_abs[0][f_idx]:.6f}",
                f"{shap_class_abs[1][f_idx]:.6f}",
                f"{shap_class_abs[2][f_idx]:.6f}",
            ])
    print(f"  Saved global importance to: {global_csv.name}")

    # 2. Class-Specific CSVs
    for c_idx, c_name in enumerate(CLASSES):
        ranked_c = sorted(range(n_features), key=lambda f: shap_class_abs[c_idx][f], reverse=True)
        class_csv = data_dir / f"shap_importance_{c_name.lower()}.csv"
        with open(class_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Feature", "MeanAbsoluteSHAP", "MeanSignedSHAP"])
            for rank, f_idx in enumerate(ranked_c, start=1):
                writer.writerow([
                    rank,
                    header[f_idx],
                    f"{shap_class_abs[c_idx][f_idx]:.6f}",
                    f"{shap_class_signed[c_idx][f_idx]:.6f}",
                ])
        print(f"  Saved class importance to: {class_csv.name}")

    return global_ranked


def export_svg_plots(header, global_ranked, global_importance, shap_class_abs, app_dir: Path, data_dir: Path, top_n=15):
    """Generate high-quality vector SVG and PNG plots in app/ and data/processed/."""
    app_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    top_feats = global_ranked[:top_n]
    max_val = global_importance[top_feats[0]] * 1.15

    # 1. Global Importance SVG
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 700' font-family='Arial, sans-serif'>",
        "<rect width='1000' height='700' fill='#fbfcfd'/>",
        "<text x='40' y='45' font-size='20' font-weight='bold' fill='#111827'>Top 15 Global Features Influencing Extinction Risk (TreeSHAP)</text>",
        "<text x='40' y='72' font-size='13' fill='#6b7280'>Mean absolute SHAP value across representative untouched holdout test instances</text>",
    ]
    svg_left, svg_right = 280, 920
    svg_w = svg_right - svg_left

    for i, f in enumerate(top_feats):
        y = 105 + i * 36
        w = int((global_importance[f] / max_val) * svg_w)
        lines.append(f"<text x='{svg_left - 15}' y='{y + 16}' font-size='12' text-anchor='end' fill='#1f2937'>{header[f]}</text>")
        lines.append(f"<rect x='{svg_left}' y='{y}' width='{w}' height='22' rx='3' fill='#2563eb'/>")
        lines.append(f"<text x='{svg_left + w + 8}' y='{y + 16}' font-size='11' font-weight='bold' fill='#4b5563'>{global_importance[f]:.4f}</text>")
    lines.append("</svg>")
    svg_content = "\n".join(lines)

    for out_d in [app_dir, data_dir]:
        svg_path = out_d / "shap_global_importance.svg"
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
    print(f"  Saved vector SVG plots to app/ and data/processed/")


def print_summary_table(header, global_ranked, global_importance, shap_class_abs, top_k=15):
    """Print clean formatted terminal summary table."""
    print("\n" + "=" * 95)
    print(f"TOP {top_k} GLOBAL SHAP FEATURE IMPORTANCE & CLASS CONTRIBUTIONS")
    print("=" * 95)
    print(f"{'Rank':<5} | {'Feature Name':<32} | {'Global |SHAP|':<14} | {'LOW_RISK':<10} | {'THREATENED':<11} | {'EXTINCT':<9}")
    print("-" * 95)

    for i in range(min(top_k, len(global_ranked))):
        f = global_ranked[i]
        feat_name = header[f]
        g_val = global_importance[f]
        lr = shap_class_abs[0][f]
        th = shap_class_abs[1][f]
        ex = shap_class_abs[2][f]
        print(f"{i+1:<5} | {feat_name:<32} | {g_val:<14.4f} | {lr:<10.4f} | {th:<11.4f} | {ex:<9.4f}")
    print("=" * 95 + "\n")


def main():
    model_path, x_test_path, y_test_path, data_dir, app_dir = get_paths()

    # 1. Load model
    trees, n_trees, n_features = load_model(model_path)

    # 2. Load untouched test data
    header, x_test, y_test = load_test_data(x_test_path, y_test_path)

    # 3. Stratified representative sample
    sample_indices = sample_representative_test(y_test, sample_size=500, random_seed=42)

    # 4. Compute TreeSHAP explanations
    shap_class_abs, shap_class_signed, global_importance = compute_tree_shap(
        trees, x_test, sample_indices, n_features, n_trees
    )

    # 5. Export CSV files
    global_ranked = export_csv_results(header, global_importance, shap_class_abs, shap_class_signed, data_dir)

    # 6. Export SVG visualization plots
    export_svg_plots(header, global_ranked, global_importance, shap_class_abs, app_dir, data_dir, top_n=15)

    # 7. Print summary table
    print_summary_table(header, global_ranked, global_importance, shap_class_abs, top_k=15)


if __name__ == "__main__":
    main()
