"""
Scenario Simulation Engine for IUCN Tetrapod Extinction Risk Assessment.

Enables what-if policy and environmental simulation around models/best_random_forest.joblib.
Evaluates the impact of:
  - Habitat loss
  - Human footprint / infrastructure pressure
  - Climate pressure (warming & volatility)
  - Invasive alien species pressure
  - Conservation effort & protected area interventions

Core Principle:
  Conservation effort acts exclusively as an ecological threat mitigation modifier
  reducing on-the-ground pressure inputs (habitat degradation, human encroachment,
  invasive pressure, and demographic destabilization) rather than directly altering
  model predictions or targets.
"""

from pathlib import Path
import sys
from typing import Dict, Any, Optional, Union, List

# Ensure parent directory is accessible for local imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.species_predictor import get_predictor, SpeciesPredictor

# Standard risk weight mapping for scalar risk index:
# LOW_RISK = 0.0, THREATENED = 1.0, EXTINCT = 2.0
RISK_WEIGHTS = {"LOW_RISK": 0.0, "THREATENED": 1.0, "EXTINCT": 2.0}


def _compute_risk_index(probs: Dict[str, float]) -> float:
    """Calculate expected scalar risk score between 0.0 (safe) and 2.0 (extinct)."""
    return round(
        0.0 * probs.get("LOW_RISK", 0.0)
        + 1.0 * probs.get("THREATENED", 0.0)
        + 2.0 * probs.get("EXTINCT", 0.0),
        4,
    )


class ScenarioSimulator:
    """
    Simulates environmental scenarios, climate shifts, and conservation interventions
    on tetrapod species using the trained Random Forest model.
    """

    def __init__(self, predictor: Optional[SpeciesPredictor] = None):
        self.predictor = predictor or get_predictor()

    def simulate_scenario(
        self,
        species_identifier_or_features: Union[str, Dict[str, Any]],
        habitat_loss: float = 0.0,
        human_pressure: float = 0.0,
        climate_pressure: float = 0.0,
        invasive_pressure: float = 0.0,
        conservation_effort: float = 0.0,
        scientific_name: Optional[str] = None,
        top_k_shap: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute an environmental scenario simulation for a species.

        Parameters:
          species_identifier_or_features:
            Either a string (ScientificName) or a dictionary of baseline trait values.
          habitat_loss:
            Fractional habitat reduction in [0.0, 1.0] (e.g. 0.30 = 30% habitat lost).
          human_pressure:
            Relative change in human footprint in [-1.0, 2.0] (e.g. +0.40 = +40% pressure).
          climate_pressure:
            Climate warming & volatility index in [-1.0, 3.0] (e.g. 1.0 = +2°C warming).
          invasive_pressure:
            Relative change in invasive alien species pressure in [-2.0, 2.0].
          conservation_effort:
            Conservation & threat abatement intensity in [0.0, 1.0].
            Mitigates pressure inputs before model inference.
          scientific_name:
            Optional label when providing custom feature dictionaries.
          top_k_shap:
            Number of top SHAP explanation drivers to return.

        Returns:
          Comprehensive simulation audit dictionary containing baseline risk, scenario risk,
          class probabilities, risk delta, applied adjustments, and feature changes.
        """
        # 1. Resolve baseline features and metadata
        if isinstance(species_identifier_or_features, str):
            sci_name = species_identifier_or_features
            species_entry = self.predictor.find_species(sci_name)
            if species_entry is None:
                raise ValueError(f"Species '{sci_name}' not found in catalog.")
            baseline_features = dict(species_entry)
            display_name = species_entry.get("ScientificName", sci_name)
            original_category = species_entry.get("RedlistCategory", "Unknown")
        else:
            baseline_features = dict(species_identifier_or_features)
            display_name = scientific_name or baseline_features.get("ScientificName", "Custom Specimen")
            original_category = baseline_features.get("RedlistCategory", "Not Evaluated")

        # 2. Compute baseline prediction
        baseline_pred = self.predictor.predict_custom_features(
            baseline_features, scientific_name=display_name, top_k_shap=top_k_shap
        )

        # 3. Apply transparent scenario rules (mitigated by conservation effort)
        modified_features, applied_adjustments = self._apply_scenario_rules(
            baseline_features=baseline_features,
            habitat_loss=habitat_loss,
            human_pressure=human_pressure,
            climate_pressure=climate_pressure,
            invasive_pressure=invasive_pressure,
            conservation_effort=conservation_effort,
        )

        # 4. Compute scenario prediction on modified features
        scenario_pred = self.predictor.predict_custom_features(
            modified_features, scientific_name=f"{display_name} (Scenario)", top_k_shap=top_k_shap
        )

        # 5. Calculate change in risk
        base_probs = baseline_pred["prediction_probabilities"]
        scen_probs = scenario_pred["prediction_probabilities"]

        base_index = _compute_risk_index(base_probs)
        scen_index = _compute_risk_index(scen_probs)
        index_delta = round(scen_index - base_index, 4)

        base_risk = baseline_pred["predicted_risk_target"]
        scen_risk = scenario_pred["predicted_risk_target"]

        if base_risk != scen_risk:
            risk_shift = "increased" if index_delta > 0 else "decreased"
            transition = f"{base_risk} -> {scen_risk}"
        else:
            if abs(index_delta) >= 0.05:
                risk_shift = "increased_probability" if index_delta > 0 else "decreased_probability"
            else:
                risk_shift = "stable"
            transition = f"{base_risk} (No Category Change)"

        prob_deltas = {
            cls: round(scen_probs[cls] - base_probs[cls], 4)
            for cls in ["LOW_RISK", "THREATENED", "EXTINCT"]
        }

        # 6. Audit feature modifications
        feature_changes = self._diff_features(baseline_features, modified_features)

        return {
            "scientific_name": display_name,
            "original_redlist_category": original_category,
            "baseline_risk": base_risk,
            "scenario_risk": scen_risk,
            "baseline_probabilities": base_probs,
            "scenario_probabilities": scen_probs,
            "change_in_risk": {
                "risk_shift": risk_shift,
                "transition": transition,
                "risk_index_baseline": base_index,
                "risk_index_scenario": scen_index,
                "risk_index_delta": index_delta,
                "probability_deltas": prob_deltas,
            },
            "applied_adjustments": applied_adjustments,
            "feature_changes": feature_changes,
            "top_contributing_features_scenario": scenario_pred["top_contributing_features"],
            "inference_time_ms": scenario_pred["inference_time_ms"],
        }

    def _apply_scenario_rules(
        self,
        baseline_features: Dict[str, Any],
        habitat_loss: float,
        human_pressure: float,
        climate_pressure: float,
        invasive_pressure: float,
        conservation_effort: float,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Convert scenario levers into biological feature updates using transparent rules.

        Rules:
          1. Conservation Mitigation:
             Conservation effort in [0, 1] attenuates negative pressures:
             - Habitat loss mitigated by up to 75%: eff_loss = loss * (1 - 0.75 * conservation)
             - Human pressure reduced: eff_human = human - (0.50 * conservation)
             - Invasive pressure reduced: eff_inv = invasive - (0.80 * conservation)
             - Climate sensitivity buffered: eff_climate = climate * (1 - 0.35 * conservation)
          2. Rangesize:
             Contracts proportionally: Rangesize * (1 - eff_loss) (clamped >= 1.0 km²)
          3. MajorHabitatSum:
             If effective habitat loss exceeds 45%, habitat diversity degrades.
          4. HumanFootPrint:
             Scales with effective human pressure: HFP * (1 + eff_human) (clamped in [0, 45000])
          5. InvasiveSpeciesResidual:
             Increases with net invasive pressure: Invasive + eff_inv * 1.5 (clamped in [-3.6, 3.5])
          6. Climate Features:
             - AnnuMeanTemp shifts by +2.0°C per unit climate pressure
             - TempSeasonality increases by +15% per unit
             - AnnuPrecip decreases by -10% per unit
             - PrecipSeasonality increases by +10% per unit
          7. PopulationTrend:
             - High conservation (>=0.70) with low net threat shifts Decreasing -> Stable or Stable -> Increasing
             - Severe cumulative threat (>0.40) with low conservation (<0.30) shifts Stable -> Decreasing
        """
        features = dict(baseline_features)

        # Clamp conservation effort in [0.0, 1.0]
        ce = max(0.0, min(1.0, float(conservation_effort)))

        # 1. Compute effective pressures after conservation mitigation
        eff_habitat_loss = max(0.0, min(1.0, float(habitat_loss) * (1.0 - 0.75 * ce)))
        eff_human_pressure = float(human_pressure) - (0.50 * ce)
        eff_invasive_pressure = float(invasive_pressure) - (0.80 * ce)
        eff_climate_pressure = float(climate_pressure) * (1.0 - 0.35 * ce)

        applied_adjustments = {
            "inputs": {
                "habitat_loss": habitat_loss,
                "human_pressure": human_pressure,
                "climate_pressure": climate_pressure,
                "invasive_pressure": invasive_pressure,
                "conservation_effort": conservation_effort,
            },
            "effective_pressures": {
                "effective_habitat_loss": round(eff_habitat_loss, 4),
                "effective_human_pressure": round(eff_human_pressure, 4),
                "effective_climate_pressure": round(eff_climate_pressure, 4),
                "effective_invasive_pressure": round(eff_invasive_pressure, 4),
                "mitigation_factor": round(ce, 4),
            },
        }

        # 2. Rangesize modification
        base_range = float(features.get("Rangesize", 1000.0))
        new_range = max(1.0, base_range * (1.0 - eff_habitat_loss))
        features["Rangesize"] = round(new_range, 2)

        # 3. MajorHabitatSum modification
        base_hab_sum = int(float(features.get("MajorHabitatSum", 1)))
        if eff_habitat_loss >= 0.45 and base_hab_sum > 1:
            loss_hab = 1 if eff_habitat_loss < 0.75 else 2
            features["MajorHabitatSum"] = max(1, base_hab_sum - loss_hab)

        # 4. HumanFootPrint modification
        base_hfp = float(features.get("HumanFootPrint", 4000.0))
        new_hfp = max(0.0, min(45000.0, base_hfp * (1.0 + eff_human_pressure)))
        features["HumanFootPrint"] = round(new_hfp, 2)

        # 5. InvasiveSpeciesResidual modification
        base_inv = float(features.get("InvasiveSpeciesResidual", 0.0))
        new_inv = max(-3.6, min(3.5, base_inv + eff_invasive_pressure * 1.5))
        features["InvasiveSpeciesResidual"] = round(new_inv, 4)

        # 6. Climate parameters modification
        base_temp = float(features.get("AnnuMeanTemp", 20.0))
        features["AnnuMeanTemp"] = round(base_temp + eff_climate_pressure * 2.0, 2)

        base_temp_seas = float(features.get("TempSeasonality", 300.0))
        features["TempSeasonality"] = round(max(10.0, base_temp_seas * (1.0 + 0.15 * eff_climate_pressure)), 2)

        base_precip = float(features.get("AnnuPrecip", 1200.0))
        features["AnnuPrecip"] = round(max(10.0, base_precip * (1.0 - 0.10 * eff_climate_pressure)), 2)

        base_prec_seas = float(features.get("PrecipSeasonality", 50.0))
        features["PrecipSeasonality"] = round(max(5.0, base_prec_seas * (1.0 + 0.10 * eff_climate_pressure)), 2)

        # 7. PopulationTrend trajectory update
        base_trend = str(features.get("PopulationTrend", "Stable"))
        cumulative_stress = (eff_habitat_loss * 0.40) + max(0.0, eff_human_pressure * 0.30) + max(0.0, eff_invasive_pressure * 0.30)

        if ce >= 0.70 and cumulative_stress <= 0.15:
            # Threat abatement allows recovery
            if base_trend == "Decreasing":
                features["PopulationTrend"] = "Stable"
            elif base_trend == "Stable":
                features["PopulationTrend"] = "Increasing"
        elif cumulative_stress >= 0.35 and ce <= 0.25:
            # Intense unmitigated pressure triggers population decline
            if base_trend in ["Stable", "Increasing", "Unknown"]:
                features["PopulationTrend"] = "Decreasing"

        return features, applied_adjustments

    @staticmethod
    def _diff_features(baseline: Dict[str, Any], modified: Dict[str, Any]) -> Dict[str, Any]:
        """Produce an explicit audit diff of all features that changed during the scenario."""
        diff = {}
        all_keys = set(baseline.keys()).union(set(modified.keys()))

        for key in sorted(all_keys):
            v_base = baseline.get(key)
            v_mod = modified.get(key)

            if v_base != v_mod:
                try:
                    f_base = float(v_base)
                    f_mod = float(v_mod)
                    delta = round(f_mod - f_base, 4)
                    pct_change = round((delta / f_base) * 100.0, 2) if abs(f_base) > 1e-6 else 0.0
                    diff[key] = {
                        "baseline": f_base,
                        "scenario": f_mod,
                        "delta": delta,
                        "percent_change": pct_change,
                    }
                except (ValueError, TypeError):
                    diff[key] = {
                        "baseline": str(v_base),
                        "scenario": str(v_mod),
                        "delta": "categorical_shift",
                    }
        return diff


# ==============================================================================
# Standalone Simulation Function
# ==============================================================================

_SIMULATOR_INSTANCE: Optional[ScenarioSimulator] = None


def simulate_scenario(
    species_identifier_or_features: Union[str, Dict[str, Any]],
    habitat_loss: float = 0.0,
    human_pressure: float = 0.0,
    climate_pressure: float = 0.0,
    invasive_pressure: float = 0.0,
    conservation_effort: float = 0.0,
    scientific_name: Optional[str] = None,
    top_k_shap: int = 5,
) -> Dict[str, Any]:
    """
    Main reusable entry point for scenario simulation.

    Accepts species baseline traits and scenario adjustments.
    Returns baseline risk, scenario risk, class probabilities, and change in risk.
    """
    global _SIMULATOR_INSTANCE
    if _SIMULATOR_INSTANCE is None:
        _SIMULATOR_INSTANCE = ScenarioSimulator()

    return _SIMULATOR_INSTANCE.simulate_scenario(
        species_identifier_or_features=species_identifier_or_features,
        habitat_loss=habitat_loss,
        human_pressure=human_pressure,
        climate_pressure=climate_pressure,
        invasive_pressure=invasive_pressure,
        conservation_effort=conservation_effort,
        scientific_name=scientific_name,
        top_k_shap=top_k_shap,
    )


# ==============================================================================
# Small Test Example & Demonstration
# ==============================================================================

def main():
    print("=" * 85)
    print("IUCN TETRAPOD EXTINCTION RISK -- ENVIRONMENTAL SCENARIO SIMULATOR")
    print("=" * 85)

    test_species = "Liocichla_steerii"  # Taiwan Liocichla (Baseline: LOW_RISK)

    print(f"\nTarget Specimen: {test_species}")
    print("Testing 3 Policy & Environmental Scenarios:\n")

    scenarios = [
        {
            "name": "Scenario 1: High Habitat Loss & Encroachment (No Conservation)",
            "params": {
                "habitat_loss": 0.65,
                "human_pressure": 0.60,
                "climate_pressure": 1.00,
                "invasive_pressure": 0.50,
                "conservation_effort": 0.00,
            },
        },
        {
            "name": "Scenario 2: Same Pressures + Maximum Conservation Intervention",
            "params": {
                "habitat_loss": 0.65,
                "human_pressure": 0.60,
                "climate_pressure": 1.00,
                "invasive_pressure": 0.50,
                "conservation_effort": 0.90,  # Protected area + threat abatement
            },
        },
        {
            "name": "Scenario 3: Proactive Restoration & Invasive Eradication",
            "params": {
                "habitat_loss": 0.00,
                "human_pressure": -0.40,      # Reduced human encroachment
                "climate_pressure": 0.20,
                "invasive_pressure": -0.80,   # Active predator eradication
                "conservation_effort": 0.85,
            },
        },
    ]

    for idx, scen in enumerate(scenarios, start=1):
        print("-" * 85)
        print(f"[{idx}] {scen['name']}")
        p = scen["params"]
        print(f"    Inputs: HabitatLoss={p['habitat_loss']:.0%}, HumanPressure={p['human_pressure']:+.0%}, "
              f"Climate={p['climate_pressure']:+.1f}, Invasive={p['invasive_pressure']:+.1f}, "
              f"ConservationEffort={p['conservation_effort']:.0%}")

        result = simulate_scenario(
            species_identifier_or_features=test_species,
            **p,
            top_k_shap=3,
        )

        b_probs = result["baseline_probabilities"]
        s_probs = result["scenario_probabilities"]
        chg = result["change_in_risk"]

        print(f"    Baseline Risk:      {result['baseline_risk']:<12} (LR: {b_probs['LOW_RISK']:.1%}, TH: {b_probs['THREATENED']:.1%}, EX: {b_probs['EXTINCT']:.1%})")
        print(f"    Scenario Risk:      {result['scenario_risk']:<12} (LR: {s_probs['LOW_RISK']:.1%}, TH: {s_probs['THREATENED']:.1%}, EX: {s_probs['EXTINCT']:.1%})")
        print(f"    Risk Transition:    {chg['transition']} (Risk Index Delta: {chg['risk_index_delta']:+.4f})")

        print("    Key Modified Features:")
        for feat, diff in list(result["feature_changes"].items())[:4]:
            if isinstance(diff.get("delta"), (int, float)):
                print(f"      - {feat:<24}: {diff['baseline']:>8.1f} -> {diff['scenario']:>8.1f} ({diff['percent_change']:+6.1f}%)")
            else:
                print(f"      - {feat:<24}: {diff['baseline']} -> {diff['scenario']}")

        print(f"    Top SHAP Drivers under Scenario:")
        for s_feat in result["top_contributing_features_scenario"][:3]:
            print(f"      * {s_feat['feature']:<28} SHAP: {s_feat['shap_value']:+.4f}")
        print()

    print("=" * 85)
    print("Scenario simulation test completed successfully.")


if __name__ == "__main__":
    main()
