"""
Conservation Priority Ranking Module for IUCN Tetrapod Species.

Calculates a multi-dimensional Conservation Priority Score (CPS) combining:
  1. Predicted Extinction Risk (from Random Forest model probabilities)
  2. Geographic Range Vulnerability (log-transformed inverted Rangesize)
  3. Anthropogenic Encroachment (normalized HumanFootPrint)
  4. Invasive Alien Species Stress (normalized InvasiveSpeciesResidual)

Designed for conservation planners, backend REST APIs, and 3D geospatial dashboards.
"""

from pathlib import Path
import csv
import math
import struct
import sys
import time
from typing import Dict, Any, List, Optional, Union

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.species_predictor import get_predictor, SpeciesPredictor

# Default normalized component weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "risk": 0.40,       # Intrinsic extinction vulnerability from ML predictions
    "range": 0.25,      # Micro-endemism & geographic restriction vulnerability
    "human": 0.20,      # Anthropogenic infrastructure and land-use footprint
    "invasive": 0.15,   # Invasive predator and competitor residual pressure
}

# Empirical normalization bounds from tetrapod assessment
BOUNDS = {
    "hfp_min": 0.0,
    "hfp_max": 41485.2,
    "inv_min": -3.62,
    "inv_max": 3.22,
    "log_rng_min": math.log10(1.0),
    "log_rng_max": math.log10(3261276.0),
}


class ConservationPriorityCalculator:
    """
    Computes transparent conservation priority indices and rankings across
    the untouched holdout test dataset or individual species.
    """

    def __init__(self, predictor: Optional[SpeciesPredictor] = None):
        self.predictor = predictor or get_predictor()
        self.project_root = self.predictor.project_root
        self.x_test_path = self.project_root / "data" / "processed" / "X_test.csv"
        self.y_test_path = self.project_root / "data" / "processed" / "y_test.csv"
        self.risk_target_path = self.project_root / "data" / "processed" / "risk_target.csv"
        self.merged_path = self.project_root / "data" / "processed" / "merged_dataset.csv"

        # Cached species metadata lookup
        self.species_lookup: Dict[tuple, List[tuple]] = {}
        self._load_species_lookup()

    def _load_species_lookup(self):
        """Construct deterministic feature tuple -> metadata lookup from processed files."""
        with open(self.risk_target_path, "r", encoding="utf-8-sig") as f_r, \
             open(self.merged_path, "r", encoding="utf-8-sig") as f_m:

            r_reader = csv.reader(f_r)
            m_reader = csv.reader(f_m)
            next(r_reader)
            next(m_reader)

            for r_row, m_row in zip(r_reader, m_reader):
                if not r_row or not m_row:
                    continue
                # Key: (BodyMass, Rangesize, Latitude) rounded
                key = (round(float(r_row[0]), 2), round(float(r_row[11]), 1), round(float(r_row[5]), 4))
                if key not in self.species_lookup:
                    self.species_lookup[key] = []
                self.species_lookup[key].append((m_row[0].strip(), r_row[-2].strip(), r_row[-1].strip()))

    def compute_component_scores(
        self,
        rangesize: float,
        human_footprint: float,
        invasive_residual: float,
        prob_threatened: float,
        prob_extinct: float,
    ) -> Dict[str, float]:
        """
        Compute transparent, normalized individual component scores in [0.0, 1.0].

        Formulas:
          1. Extinction Risk Score:
             S_risk = P(EXTINCT) * 1.0 + P(THREATENED) * 0.5
          2. Range Vulnerability Score (IUCN Criterion B proxy):
             S_range = 1.0 - (log10(Rangesize) - min) / (max - min)
             (Smaller geographic range -> higher vulnerability score)
          3. Human Pressure Score:
             S_human = (HumanFootPrint - min) / (max - min)
          4. Invasive Pressure Score:
             S_invasive = (InvasiveSpeciesResidual - min) / (max - min)
        """
        # 1. Extinction risk component
        s_risk = min(1.0, max(0.0, prob_extinct * 1.0 + prob_threatened * 0.5))

        # 2. Geographic range vulnerability component (inverted log-scale)
        rng = max(1.0, float(rangesize))
        log_rng = math.log10(rng)
        s_range = 1.0 - (log_rng - BOUNDS["log_rng_min"]) / (BOUNDS["log_rng_max"] - BOUNDS["log_rng_min"])
        s_range = min(1.0, max(0.0, s_range))

        # 3. Human footprint component
        hfp = float(human_footprint)
        s_human = (hfp - BOUNDS["hfp_min"]) / (BOUNDS["hfp_max"] - BOUNDS["hfp_min"])
        s_human = min(1.0, max(0.0, s_human))

        # 4. Invasive pressure component
        inv = float(invasive_residual)
        s_invasive = (inv - BOUNDS["inv_min"]) / (BOUNDS["inv_max"] - BOUNDS["inv_min"])
        s_invasive = min(1.0, max(0.0, s_invasive))

        return {
            "extinction_risk_score": round(s_risk, 4),
            "range_vulnerability_score": round(s_range, 4),
            "human_pressure_score": round(s_human, 4),
            "invasive_pressure_score": round(s_invasive, 4),
        }

    def compute_priority_score(
        self,
        component_scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate weighted conservation priority score (CPS) in [0.0, 1.0].
        """
        w = weights or DEFAULT_WEIGHTS
        cps = (
            w.get("risk", 0.40) * component_scores["extinction_risk_score"]
            + w.get("range", 0.25) * component_scores["range_vulnerability_score"]
            + w.get("human", 0.20) * component_scores["human_pressure_score"]
            + w.get("invasive", 0.15) * component_scores["invasive_pressure_score"]
        )
        return round(min(1.0, max(0.0, cps)), 4)

    def calculate_single_species_priority(
        self,
        species_identifier_or_features: Union[str, Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Calculate priority score and component breakdown for an individual species."""
        if isinstance(species_identifier_or_features, str):
            pred_res = self.predictor.predict_species(species_identifier_or_features)
            raw = pred_res["raw_features"]
            sci_name = pred_res["ScientificName"]
            redlist = pred_res["original_redlist_category"]
        else:
            pred_res = self.predictor.predict_custom_features(species_identifier_or_features)
            raw = pred_res["raw_features"]
            sci_name = pred_res["ScientificName"]
            redlist = pred_res["original_redlist_category"]

        probs = pred_res["prediction_probabilities"]
        components = self.compute_component_scores(
            rangesize=raw.get("Rangesize", 1000.0),
            human_footprint=raw.get("HumanFootPrint", 4000.0),
            invasive_residual=raw.get("InvasiveSpeciesResidual", 0.0),
            prob_threatened=probs["THREATENED"],
            prob_extinct=probs["EXTINCT"],
        )
        cps = self.compute_priority_score(components, weights=weights)

        return {
            "scientific_name": sci_name,
            "original_redlist_category": redlist,
            "predicted_risk": pred_res["predicted_risk_target"],
            "class_probabilities": probs,
            "component_scores": components,
            "conservation_priority_score": cps,
            "raw_values": {
                "Rangesize": raw.get("Rangesize"),
                "HumanFootPrint": raw.get("HumanFootPrint"),
                "InvasiveSpeciesResidual": raw.get("InvasiveSpeciesResidual"),
            },
        }

    def rank_test_dataset(
        self,
        top_n: Optional[int] = None,
        weights: Optional[Dict[str, float]] = None,
        filter_predicted_class: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate and rank all 6,144 holdout test observations from highest to lowest
        conservation priority score.

        Parameters:
          top_n:
            Limit the returned ranking to top N species (returns all if None).
          weights:
            Custom component weighting dictionary.
          filter_predicted_class:
            Optional filter (e.g. 'EXTINCT', 'THREATENED', or None).

        Returns:
          List of species ranking dictionaries ordered from highest to lowest CPS.
        """
        if not self.x_test_path.exists():
            raise FileNotFoundError(f"Test dataset not found at: {self.x_test_path}")

        # Read X_test
        with open(self.x_test_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            x_header = next(reader)
            x_rows = list(reader)

        n_samples = len(x_rows)
        inv_trees = 1.0 / self.predictor.n_trees

        ranked_list = []

        for i, row in enumerate(x_rows):
            vec = [float(val) for val in row]

            # Fast tree traversal for probabilities
            probs = [0.0, 0.0, 0.0]
            for tree in self.predictor.trees:
                curr = tree
                while curr.feature != -1:
                    curr = curr.left if vec[curr.feature] <= curr.threshold else curr.right
                for c in range(3):
                    probs[c] += curr.class_dist[c] * inv_trees

            pred_idx = max(range(3), key=lambda c: probs[c])
            pred_class = ["LOW_RISK", "THREATENED", "EXTINCT"][pred_idx]

            if filter_predicted_class and pred_class != filter_predicted_class:
                continue

            # Resolve species metadata from unique tuple key
            key = (round(vec[0], 2), round(vec[11], 1), round(vec[5], 4))
            meta_entries = self.species_lookup.get(key, [])
            sci_name = meta_entries[0][0] if meta_entries else f"Test_Sample_{i+1}"
            redlist = meta_entries[0][1] if meta_entries else "Unknown"

            # Raw values for components
            rng = vec[11]      # Rangesize
            hfp = vec[12]      # HumanFootPrint
            inv = vec[13]      # InvasiveSpeciesResidual

            components = self.compute_component_scores(
                rangesize=rng,
                human_footprint=hfp,
                invasive_residual=inv,
                prob_threatened=probs[1],
                prob_extinct=probs[2],
            )
            cps = self.compute_priority_score(components, weights=weights)

            ranked_list.append({
                "scientific_name": sci_name,
                "original_redlist_category": redlist,
                "predicted_risk": pred_class,
                "class_probabilities": {
                    "LOW_RISK": round(probs[0], 4),
                    "THREATENED": round(probs[1], 4),
                    "EXTINCT": round(probs[2], 4),
                },
                "component_scores": components,
                "raw_values": {
                    "Rangesize": round(rng, 1),
                    "HumanFootPrint": round(hfp, 1),
                    "InvasiveSpeciesResidual": round(inv, 3),
                },
                "conservation_priority_score": cps,
            })

        # Sort descending by conservation priority score
        ranked_list.sort(key=lambda item: item["conservation_priority_score"], reverse=True)

        # Assign 1-indexed rank
        for rank, item in enumerate(ranked_list, start=1):
            item["rank"] = rank

        if top_n is not None:
            return ranked_list[:top_n]
        return ranked_list


# ==============================================================================
# Standalone Convenience Functions
# ==============================================================================

_CALCULATOR_INSTANCE: Optional[ConservationPriorityCalculator] = None


def get_calculator() -> ConservationPriorityCalculator:
    """Retrieve or initialize global singleton priority calculator."""
    global _CALCULATOR_INSTANCE
    if _CALCULATOR_INSTANCE is None:
        _CALCULATOR_INSTANCE = ConservationPriorityCalculator()
    return _CALCULATOR_INSTANCE


def calculate_conservation_priority(
    top_n: Optional[int] = 20,
    weights: Optional[Dict[str, float]] = None,
    filter_predicted_class: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Main reusable function: Calculate conservation priority scores for the
    untouched holdout test dataset, ranking species from highest to lowest urgency.
    """
    return get_calculator().rank_test_dataset(
        top_n=top_n, weights=weights, filter_predicted_class=filter_predicted_class
    )


def calculate_single_species_priority(
    species_identifier_or_features: Union[str, Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate conservation priority score and component breakdown for a single species."""
    return get_calculator().calculate_single_species_priority(
        species_identifier_or_features, weights=weights
    )


# ==============================================================================
# CLI Demonstration & Test Example
# ==============================================================================

def main():
    print("=" * 105)
    print("IUCN TETRAPOD CONSERVATION PRIORITY RANKING & ACTION INDEX")
    print("=" * 105)

    calculator = get_calculator()
    print(f"Model loaded: {calculator.predictor.n_trees} trees, {calculator.predictor.n_features} features.")
    print("Weights Configuration:")
    for k, v in DEFAULT_WEIGHTS.items():
        print(f"  - {k:<10}: {v:.0%}")
    print()

    print("Evaluating untouched holdout test dataset (6,144 observations)...")
    t0 = time.time()
    top_species = calculator.rank_test_dataset(top_n=15)
    elapsed = time.time() - t0
    print(f"Computed rankings in {elapsed:.2f} seconds.\n")

    # Formatted priority table
    header_fmt = "{:<4} | {:<28} | {:<16} | {:<11} | {:<7} | {:<7} | {:<7} | {:<7} | {:<8}"
    row_fmt    = "{:<4} | {:<28} | {:<16} | {:<11} | {:<7.3f} | {:<7.3f} | {:<7.3f} | {:<7.3f} | {:<8.4f}"

    print("-" * 105)
    print(header_fmt.format(
        "Rank", "Scientific Name", "Red List Status", "Pred Risk",
        "S_Risk", "S_Range", "S_Human", "S_Invas", "CPS Score"
    ))
    print("-" * 105)

    for sp in top_species:
        c = sp["component_scores"]
        print(row_fmt.format(
            sp["rank"],
            sp["scientific_name"][:28],
            sp["original_redlist_category"][:16],
            sp["predicted_risk"],
            c["extinction_risk_score"],
            c["range_vulnerability_score"],
            c["human_pressure_score"],
            c["invasive_pressure_score"],
            sp["conservation_priority_score"],
        ))

    print("-" * 105)
    print("Component Legend:")
    print("  * S_Risk:  Extinction Risk Probability [40% weight]")
    print("  * S_Range: Geographic Range Vulnerability (inverted log-scale) [25% weight]")
    print("  * S_Human: Anthropogenic Encroachment Footprint [20% weight]")
    print("  * S_Invas: Invasive Alien Species Residual Pressure [15% weight]")
    print("=" * 105)

    # Test single-species calculation
    test_focal = "Polyplectron_schleiermacheri"
    print(f"\nSingle Species Priority Drilldown: {test_focal}")
    focal_res = calculate_single_species_priority(test_focal)
    print(f"  Predicted Risk:      {focal_res['predicted_risk']}")
    print(f"  Class Probabilities: {focal_res['class_probabilities']}")
    print(f"  Component Scores:    {focal_res['component_scores']}")
    print(f"  Final Priority Score: {focal_res['conservation_priority_score']:.4f}")
    print()


if __name__ == "__main__":
    main()
