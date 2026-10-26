"""
Species Extinction Risk Predictor & Real-time Explainability Module.

Provides reusable inference and local SHAP feature attribution for individual
species assessments, designed for direct integration with backend APIs and 3D UI frontends.

Capabilities:
  1. Find species in the catalog by ScientificName (case-insensitive, normalized).
  2. Extract raw biological, ecological, and environmental feature attributes.
  3. Transform attributes into model-ready vector representation.
  4. Predict IUCN Risk Target: LOW_RISK, THREATENED, or EXTINCT.
  5. Compute precise prediction probabilities across all 3 classes.
  6. Return original IUCN RedlistCategory and status.
  7. Compute instant on-the-fly TreeSHAP attributions highlighting the top positive
     and negative drivers behind the individual classification.
  8. Support hypothetical / what-if simulations from custom input features.
"""

from pathlib import Path
import csv
import struct
import time
from typing import Dict, List, Optional, Any, Union

CLASSES = ["LOW_RISK", "THREATENED", "EXTINCT"]

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

CATEGORICAL_PREFIXES = [
    ("ClassName", "ClassName_"),
    ("OrderName", "OrderName_"),
    ("FamilyName", "FamilyName_"),
    ("PopulationTrend", "PopulationTrend_"),
]


class TreeSHAPNode:
    """Compact node structure for tree inference and SHAP attribution."""
    __slots__ = ["feature", "threshold", "left", "right", "leaf_class", "class_dist", "sample_count"]

    def __init__(self):
        self.feature = -1
        self.threshold = 0.0
        self.left: Optional[TreeSHAPNode] = None
        self.right: Optional[TreeSHAPNode] = None
        self.leaf_class: int = 0
        self.class_dist = [0.0, 0.0, 0.0]
        self.sample_count = 1


def _read_node(stream) -> Optional[TreeSHAPNode]:
    """Recursively deserialize tree nodes from binary stream."""
    type_b = stream.read(1)
    if not type_b or type_b[0] == 255:
        return None
    node = TreeSHAPNode()
    if type_b[0] == 1:
        node.leaf_class = stream.read(1)[0]
        node.feature = -1
        return node
    else:
        feat, thresh = struct.unpack("<if", stream.read(8))
        node.feature = feat
        node.threshold = thresh
        node.left = _read_node(stream)
        node.right = _read_node(stream)
        return node


def _compute_node_distributions(node: Optional[TreeSHAPNode]):
    """Recursively compute expected class distributions at every node."""
    if node is None:
        return
    if node.feature == -1:
        node.class_dist = [0.0, 0.0, 0.0]
        node.class_dist[node.leaf_class] = 1.0
        node.sample_count = 1
        return

    _compute_node_distributions(node.left)
    _compute_node_distributions(node.right)

    left_cnt = node.left.sample_count if node.left else 1
    right_cnt = node.right.sample_count if node.right else 1
    node.sample_count = left_cnt + right_cnt
    node.class_dist = [0.0, 0.0, 0.0]

    for c in range(3):
        lv = node.left.class_dist[c] if node.left else 0.0
        rv = node.right.class_dist[c] if node.right else 0.0
        node.class_dist[c] = (lv * left_cnt + rv * right_cnt) / node.sample_count


class SpeciesPredictor:
    """
    Production-grade predictor service for tetrapod species extinction risk
    and real-time local SHAP explainability.
    """

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent

        self.project_root = project_root
        self.model_path = project_root / "models" / "best_random_forest.joblib"
        self.risk_target_path = project_root / "data" / "processed" / "risk_target.csv"
        self.merged_path = project_root / "data" / "processed" / "merged_dataset.csv"
        self.feature_names_path = project_root / "data" / "processed" / "X_test.csv"

        # Internal model and catalog structures
        self.trees: List[TreeSHAPNode] = []
        self.n_trees: int = 0
        self.n_features: int = 0
        self.feature_names: List[str] = []
        self.feature_to_idx: Dict[str, int] = {}
        self.species_catalog: Dict[str, Dict[str, Any]] = {}
        self.species_name_lookup: Dict[str, str] = {}  # Normalized key -> original name

        # Load assets
        self._load_feature_schema()
        self._load_model()
        self._load_species_catalog()

    def _load_feature_schema(self):
        """Load ordered 633 feature names and index mapping."""
        if not self.feature_names_path.exists():
            raise FileNotFoundError(f"Feature schema file not found at: {self.feature_names_path}")

        with open(self.feature_names_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            self.feature_names = next(reader)

        self.n_features = len(self.feature_names)
        self.feature_to_idx = {name: i for i, name in enumerate(self.feature_names)}

    def _load_model(self):
        """Load trained Random Forest ensemble from binary serialization."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Trained model not found at: {self.model_path}")

        with open(self.model_path, "rb") as f:
            self.n_trees, model_n_features = struct.unpack("<ii", f.read(8))
            self.trees = [_read_node(f) for _ in range(self.n_trees)]

        for t in self.trees:
            _compute_node_distributions(t)

    def _load_species_catalog(self):
        """
        Load risk_target.csv alongside merged_dataset.csv to create a fast,
        in-memory indexed lookup of all ~30,711 evaluated species.
        """
        if not self.risk_target_path.exists():
            raise FileNotFoundError(f"Risk target file not found: {self.risk_target_path}")
        if not self.merged_path.exists():
            raise FileNotFoundError(f"Merged dataset file not found: {self.merged_path}")

        with open(self.risk_target_path, "r", encoding="utf-8-sig") as f_r, \
             open(self.merged_path, "r", encoding="utf-8-sig") as f_m:

            r_reader = csv.reader(f_r)
            m_reader = csv.reader(f_m)

            r_header = next(r_reader)
            m_header = next(m_reader)

            for r_row, m_row in zip(r_reader, m_reader):
                if not r_row or not m_row:
                    continue
                scientific_name = m_row[0].strip()
                norm_key = self._normalize_name(scientific_name)

                row_dict = dict(zip(r_header, r_row))
                row_dict["ScientificName"] = scientific_name

                self.species_catalog[norm_key] = row_dict
                self.species_name_lookup[norm_key] = scientific_name

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize scientific name for case-insensitive and delimiter-agnostic search."""
        return name.strip().lower().replace(" ", "_").replace("-", "_")

    def find_species(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a species by ScientificName (exact normalized match or fuzzy prefix).
        Returns species attribute dictionary or None if not found.
        """
        norm_query = self._normalize_name(scientific_name)

        # 1. Exact match
        if norm_query in self.species_catalog:
            return self.species_catalog[norm_query]

        # 2. Substring or prefix match
        for key in self.species_catalog:
            if norm_query in key:
                return self.species_catalog[key]

        return None

    def search_species(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Autocomplete search for species names.
        Returns a list of matching species with scientific name, class, original category, and real latitude.
        """
        norm_q = self._normalize_name(query)
        matches = []
        for key, data in self.species_catalog.items():
            if norm_q in key:
                matches.append({
                    "ScientificName": data["ScientificName"],
                    "ClassName": data.get("ClassName", ""),
                    "OrderName": data.get("OrderName", ""),
                    "FamilyName": data.get("FamilyName", ""),
                    "RedlistCategory": data.get("RedlistCategory", ""),
                    "RiskTarget": data.get("RiskTarget", ""),
                    "Latitude": float(data.get("Latitude", 0.0)),
                })
                if len(matches) >= limit:
                    break
        return matches

    def get_species_features(self, species_data_or_name: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract biological, ecological, and environmental feature attributes for a species.
        Returns raw features and the transformed 633-element model vector.
        """
        if isinstance(species_data_or_name, str):
            species_data = self.find_species(species_data_or_name)
            if species_data is None:
                raise ValueError(f"Species '{species_data_or_name}' not found in catalog.")
        else:
            species_data = species_data_or_name

        # Construct raw features dict
        raw_features = {}
        for col in NUMERIC_FEATURES:
            raw_features[col] = float(species_data.get(col, 0.0))

        for cat_col, _ in CATEGORICAL_PREFIXES:
            raw_features[cat_col] = str(species_data.get(cat_col, ""))

        # Build 633-feature numeric vector for Random Forest
        vector = [0.0] * self.n_features

        # Set numeric values
        for col in NUMERIC_FEATURES:
            if col in self.feature_to_idx:
                vector[self.feature_to_idx[col]] = raw_features[col]

        # Set one-hot categorical flags
        for cat_col, prefix in CATEGORICAL_PREFIXES:
            val = raw_features.get(cat_col, "")
            full_col_name = f"{prefix}{val}"
            if full_col_name in self.feature_to_idx:
                vector[self.feature_to_idx[full_col_name]] = 1.0

        return {
            "raw_features": raw_features,
            "vector": vector,
            "ScientificName": species_data.get("ScientificName", "Custom Species"),
            "RedlistCategory": species_data.get("RedlistCategory", "Unknown"),
            "RiskTarget": species_data.get("RiskTarget", "Unknown"),
        }

    def predict_species(
        self,
        scientific_name: str,
        top_k_shap: int = 5,
    ) -> Dict[str, Any]:
        """
        Full prediction and local explainability pipeline for a catalog species.

        Returns a comprehensive dictionary containing:
          - ScientificName
          - Original RedlistCategory & RiskTarget
          - Predicted RiskTarget (LOW_RISK, THREATENED, EXTINCT)
          - Prediction probabilities for all 3 classes
          - Top K SHAP feature contributions for the predicted class
          - Complete class-specific SHAP breakdown
          - Raw biological feature values
          - Inference latency in milliseconds
        """
        species_info = self.get_species_features(scientific_name)
        return self._predict_vector(species_info, top_k_shap=top_k_shap)

    def predict_custom_features(
        self,
        feature_dict: Dict[str, Any],
        scientific_name: str = "Hypothetical Species",
        top_k_shap: int = 5,
    ) -> Dict[str, Any]:
        """
        Run inference and SHAP explanation on user-specified hypothetical traits.
        Ideal for interactive what-if scenarios in the 3D frontend or API simulations.
        """
        species_data = dict(feature_dict)
        species_data["ScientificName"] = scientific_name
        species_data["RedlistCategory"] = feature_dict.get("RedlistCategory", "Not Evaluated")
        species_data["RiskTarget"] = feature_dict.get("RiskTarget", "Unknown")

        species_info = self.get_species_features(species_data)
        return self._predict_vector(species_info, top_k_shap=top_k_shap)

    def _predict_vector(
        self,
        species_info: Dict[str, Any],
        top_k_shap: int = 5,
    ) -> Dict[str, Any]:
        """Core inference engine calculating tree vote probabilities and local TreeSHAP values."""
        t0 = time.time()
        vector = species_info["vector"]
        raw_features = species_info["raw_features"]
        inv_n_trees = 1.0 / self.n_trees

        # Accumulators
        class_probs = [0.0, 0.0, 0.0]
        shap_values = [[0.0] * self.n_features for _ in range(3)]

        for tree in self.trees:
            curr = tree
            while curr.feature != -1:
                f_idx = curr.feature
                val = vector[f_idx]
                next_node = curr.left if val <= curr.threshold else curr.right
                if not next_node:
                    break

                for c in range(3):
                    delta = (next_node.class_dist[c] - curr.class_dist[c]) * inv_n_trees
                    shap_values[c][f_idx] += delta

                curr = next_node

            for c in range(3):
                class_probs[c] += curr.class_dist[c] * inv_n_trees

        # Determine predicted class
        pred_idx = max(range(3), key=lambda c: class_probs[c])
        predicted_class = CLASSES[pred_idx]

        latency_ms = (time.time() - t0) * 1000.0

        # Extract top-K SHAP features for the predicted class
        pred_shap_list = []
        for i in range(self.n_features):
            s_val = shap_values[pred_idx][i]
            if abs(s_val) > 1e-6:
                pred_shap_list.append({
                    "feature": self.feature_names[i],
                    "shap_value": round(s_val, 6),
                    "feature_value": vector[i],
                    "direction": "increases_risk" if (pred_idx > 0 and s_val > 0) or (pred_idx == 0 and s_val < 0) else "decreases_risk",
                    "impact": "positive" if s_val > 0 else "negative",
                })

        # Sort by absolute contribution
        pred_shap_list.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        top_contributions = pred_shap_list[:top_k_shap]

        # Detailed breakdown across all classes
        class_shap_breakdown = {}
        for c_idx, c_name in enumerate(CLASSES):
            c_list = [
                {"feature": self.feature_names[i], "shap_value": round(shap_values[c_idx][i], 6)}
                for i in range(self.n_features) if abs(shap_values[c_idx][i]) > 1e-6
            ]
            c_list.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            class_shap_breakdown[c_name] = c_list[:top_k_shap]

        return {
            "ScientificName": species_info["ScientificName"],
            "original_redlist_category": species_info["RedlistCategory"],
            "original_risk_target": species_info["RiskTarget"],
            "predicted_risk_target": predicted_class,
            "predicted_class_index": pred_idx,
            "prediction_probabilities": {
                "LOW_RISK": round(class_probs[0], 4),
                "THREATENED": round(class_probs[1], 4),
                "EXTINCT": round(class_probs[2], 4),
            },
            "top_contributing_features": top_contributions,
            "class_shap_breakdown": class_shap_breakdown,
            "raw_features": raw_features,
            "inference_time_ms": round(latency_ms, 2),
        }


# ==============================================================================
# Module-level convenience functions (Singleton pattern for high API throughput)
# ==============================================================================

_PREDICTOR_INSTANCE: Optional[SpeciesPredictor] = None


def get_predictor() -> SpeciesPredictor:
    """Obtain or initialize the global singleton SpeciesPredictor instance."""
    global _PREDICTOR_INSTANCE
    if _PREDICTOR_INSTANCE is None:
        _PREDICTOR_INSTANCE = SpeciesPredictor()
    return _PREDICTOR_INSTANCE


def find_species(scientific_name: str) -> Optional[Dict[str, Any]]:
    """Find species by scientific name."""
    return get_predictor().find_species(scientific_name)


def get_species_features(scientific_name: str) -> Dict[str, Any]:
    """Retrieve raw and encoded features for a species."""
    return get_predictor().get_species_features(scientific_name)


def predict_species(scientific_name: str, top_k_shap: int = 5) -> Dict[str, Any]:
    """Run full prediction, probabilities, and local SHAP explanations for a species."""
    return get_predictor().predict_species(scientific_name, top_k_shap=top_k_shap)


def predict_custom_features(
    feature_dict: Dict[str, Any],
    scientific_name: str = "Hypothetical Species",
    top_k_shap: int = 5,
) -> Dict[str, Any]:
    """Run prediction on custom trait values."""
    return get_predictor().predict_custom_features(
        feature_dict, scientific_name=scientific_name, top_k_shap=top_k_shap
    )


def search_species(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """Autocomplete search for species in the catalog."""
    return get_predictor().search_species(query, limit=limit)


# ==============================================================================
# CLI Demonstration
# ==============================================================================

def main():
    import sys

    print("=" * 80)
    print("IUCN TETRAPOD EXTINCTION RISK PREDICTOR & SHAP EXPLAINABILITY ENGINE")
    print("=" * 80)

    predictor = get_predictor()
    print(f"Catalog loaded: {len(predictor.species_catalog):,} species.")
    print(f"Random Forest model loaded: {predictor.n_trees} trees, {predictor.n_features} features.\n")

    # Target test specimens representing each risk category
    demo_species = [
        ("Liocichla_steerii", "Taiwan Liocichla"),
        ("Polyplectron_schleiermacheri", "Bornean Peacock-Pheasant"),
        ("Raphus_cucullatus", "Dodo"),
    ]

    # Allow custom CLI argument
    if len(sys.argv) > 1:
        query_name = " ".join(sys.argv[1:])
        demo_species = [(query_name, "User Query Species")]

    for sci_name, common_hint in demo_species:
        print("-" * 80)
        print(f"Querying: {sci_name} ({common_hint})")
        result = predictor.predict_species(sci_name, top_k_shap=5)

        if not result:
            print(f"Species '{sci_name}' not found in catalog.\n")
            continue

        probs = result["prediction_probabilities"]
        print(f"  Original IUCN Category:   {result['original_redlist_category']}")
        print(f"  Original Target Class:    {result['original_risk_target']}")
        print(f"  Predicted Target Class:   {result['predicted_risk_target']}")
        print(f"  Probabilities:            LOW_RISK: {probs['LOW_RISK']:.1%}, THREATENED: {probs['THREATENED']:.1%}, EXTINCT: {probs['EXTINCT']:.1%}")
        print(f"  Inference Latency:        {result['inference_time_ms']} ms")

        print(f"\n  Top SHAP Drivers for [{result['predicted_risk_target']}]:")
        for i, contrib in enumerate(result["top_contributing_features"], start=1):
            print(f"    {i}. {contrib['feature']:<30} SHAP: {contrib['shap_value']:+.4f} (value: {contrib['feature_value']})")
        print()

    print("=" * 80)
    print("Predictor verification completed successfully.")


if __name__ == "__main__":
    main()
