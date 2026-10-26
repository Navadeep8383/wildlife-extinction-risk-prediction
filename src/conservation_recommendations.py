"""
Evidence-Based Conservation Recommendation Engine for IUCN Tetrapod Species.

Synthesizes:
  - Model Risk Predictions & Class Probabilities
  - Raw Ecological and Anthropogenic Feature Values
  - Local TreeSHAP Feature Attributions
  - Scenario Simulation Outcomes & Intervention Response
  - Multi-dimensional Conservation Priority Scores (CPS)

Core Rule:
  Recommendations are generated strictly and exclusively from DETECTED risk factors:
    1. High Human Footprint        -> Habitat protection, zoning, anti-encroachment
    2. High Invasive Pressure      -> Invasive alien species eradication & biosecurity
    3. Small Geographic Range      -> Micro-reserves, habitat restoration & connectivity
    4. Climate Risk Indicators     -> Climate adaptation, elevation refugia & corridors
    5. High Extinction Probability -> Emergency demographic tracking & captive breeding
"""

from pathlib import Path
import sys
from typing import Dict, Any, List, Optional, Union

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.species_predictor import get_predictor, SpeciesPredictor
from src.conservation_priority import calculate_single_species_priority
from src.scenario_simulator import simulate_scenario


# Threshold definitions for risk factor detection and severity grading
SEVERITY_LEVELS = ["CRITICAL", "HIGH", "MODERATE"]


def _classify_severity(value: float, crit_thresh: float, high_thresh: float, mod_thresh: float, higher_is_worse: bool = True) -> Optional[str]:
    """Classify numerical metric into CRITICAL, HIGH, MODERATE, or None."""
    if higher_is_worse:
        if value >= crit_thresh:
            return "CRITICAL"
        if value >= high_thresh:
            return "HIGH"
        if value >= mod_thresh:
            return "MODERATE"
    else:
        if value <= crit_thresh:
            return "CRITICAL"
        if value <= high_thresh:
            return "HIGH"
        if value <= mod_thresh:
            return "MODERATE"
    return None


class ConservationRecommendationEngine:
    """
    Evaluates ecological threats and derives actionable, transparent conservation
    interventions tailored exclusively to identified vulnerability drivers.
    """

    def __init__(self, predictor: Optional[SpeciesPredictor] = None):
        self.predictor = predictor or get_predictor()

    def generate_recommendations(
        self,
        prediction: Optional[Dict[str, Any]] = None,
        feature_values: Optional[Dict[str, Any]] = None,
        shap_contributions: Optional[List[Dict[str, Any]]] = None,
        scenario_results: Optional[Dict[str, Any]] = None,
        conservation_priority: Optional[Dict[str, Any]] = None,
        scientific_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate evidence-based conservation recommendations.

        Accepts either pre-computed diagnostic dictionaries or a scientific_name
        to evaluate end-to-end.
        """
        # 1. Resolve species context and diagnostics if not fully supplied
        if scientific_name and (prediction is None or feature_values is None or shap_contributions is None):
            pred_res = self.predictor.predict_species(scientific_name, top_k_shap=8)
            prediction = prediction or {
                "predicted_risk_target": pred_res["predicted_risk_target"],
                "prediction_probabilities": pred_res["prediction_probabilities"],
                "original_redlist_category": pred_res["original_redlist_category"],
            }
            feature_values = feature_values or pred_res["raw_features"]
            shap_contributions = shap_contributions or pred_res["top_contributing_features"]

            if conservation_priority is None:
                conservation_priority = calculate_single_species_priority(scientific_name)

            if scenario_results is None:
                scenario_results = simulate_scenario(scientific_name, habitat_loss=0.30, conservation_effort=0.75)

        # Fallback defaults if standalone dicts provided
        sci_name = scientific_name or feature_values.get("ScientificName", "Evaluated Species")
        features = feature_values or {}
        shap_list = shap_contributions or []
        probs = prediction.get("prediction_probabilities", {"LOW_RISK": 0.5, "THREATENED": 0.3, "EXTINCT": 0.2})
        pred_class = prediction.get("predicted_risk_target", "UNKNOWN")
        redlist_status = prediction.get("original_redlist_category", "Unknown")

        # Map active SHAP features for cross-validation
        shap_names = {item.get("feature"): item.get("shap_value", 0.0) for item in shap_list}

        # 2. Detect Risk Factors and Assess Severity
        detected_factors = []

        # ----------------------------------------------------------------------
        # Factor 1: High Human Footprint / Anthropogenic Pressure
        # ----------------------------------------------------------------------
        hfp = float(features.get("HumanFootPrint", 0.0))
        hfp_shap = shap_names.get("HumanFootPrint", 0.0)
        hfp_sev = _classify_severity(hfp, crit_thresh=18000.0, high_thresh=10000.0, mod_thresh=5500.0, higher_is_worse=True)

        if hfp_shap > 0.02 and not hfp_sev:
            hfp_sev = "MODERATE"
        elif hfp_shap > 0.05 and hfp_sev == "MODERATE":
            hfp_sev = "HIGH"

        if hfp_sev:
            detected_factors.append({
                "factor_id": "human_footprint",
                "name": "High Anthropogenic Encroachment & Human Footprint",
                "severity": hfp_sev,
                "metric_name": "HumanFootPrint",
                "metric_value": f"{hfp:,.1f}",
                "shap_impact": round(hfp_shap, 4),
                "trigger_rationale": f"Human footprint score of {hfp:,.1f} indicates intense agricultural, infrastructure, or urban encroachment.",
            })

        # ----------------------------------------------------------------------
        # Factor 2: High Invasive Alien Species Pressure
        # ----------------------------------------------------------------------
        inv = float(features.get("InvasiveSpeciesResidual", 0.0))
        inv_shap = shap_names.get("InvasiveSpeciesResidual", 0.0)
        inv_sev = _classify_severity(inv, crit_thresh=1.50, high_thresh=0.50, mod_thresh=0.05, higher_is_worse=True)

        if inv_shap > 0.02 and not inv_sev:
            inv_sev = "MODERATE"
        elif inv_shap > 0.05 and inv_sev == "MODERATE":
            inv_sev = "HIGH"

        if inv_sev:
            detected_factors.append({
                "factor_id": "invasive_pressure",
                "name": "High Invasive Alien Species Pressure",
                "severity": inv_sev,
                "metric_name": "InvasiveSpeciesResidual",
                "metric_value": f"{inv:+.3f}",
                "shap_impact": round(inv_shap, 4),
                "trigger_rationale": f"Invasive pressure residual of {inv:+.3f} reflects severe exposure to non-native predators or competitors.",
            })

        # ----------------------------------------------------------------------
        # Factor 3: Small Geographic Range / Micro-Endemism
        # ----------------------------------------------------------------------
        rng = float(features.get("Rangesize", 100000.0))
        rng_shap = shap_names.get("Rangesize", 0.0)
        endemic_val = float(features.get("EndemicType", 1.0))
        rng_sev = _classify_severity(rng, crit_thresh=250.0, high_thresh=5000.0, mod_thresh=20000.0, higher_is_worse=False)

        if endemic_val >= 2.0 and not rng_sev:
            rng_sev = "MODERATE"

        if rng_sev:
            detected_factors.append({
                "factor_id": "small_range_size",
                "name": "Restricted Geographic Range & High Endemism",
                "severity": rng_sev,
                "metric_name": "Rangesize",
                "metric_value": f"{rng:,.1f} km2",
                "shap_impact": round(rng_shap, 4),
                "trigger_rationale": f"Extremely restricted range of {rng:,.1f} km2 elevates susceptibility to catastrophic single-event extirpation.",
            })

        # ----------------------------------------------------------------------
        # Factor 4: Climate-Related Risk Indicators
        # ----------------------------------------------------------------------
        temp_seas = float(features.get("TempSeasonality", 300.0))
        annu_temp = float(features.get("AnnuMeanTemp", 20.0))
        prec_seas = float(features.get("PrecipSeasonality", 50.0))

        # Check SHAP flags on climate parameters
        clim_shap_sum = (
            shap_names.get("TempSeasonality", 0.0)
            + shap_names.get("AnnuMeanTemp", 0.0)
            + shap_names.get("AnnuPrecip", 0.0)
            + shap_names.get("PrecipSeasonality", 0.0)
        )

        clim_sev = None
        if clim_shap_sum > 0.03 or temp_seas > 650.0:
            clim_sev = "CRITICAL" if (clim_shap_sum > 0.06 or temp_seas > 800.0) else "HIGH"
        elif clim_shap_sum > 0.01 or temp_seas > 450.0 or prec_seas > 80.0:
            clim_sev = "MODERATE"

        if clim_sev:
            detected_factors.append({
                "factor_id": "climate_risk",
                "name": "High Climatic Seasonality & Thermal Vulnerability",
                "severity": clim_sev,
                "metric_name": "TempSeasonality / Climate SHAP",
                "metric_value": f"TempSeas={temp_seas:.1f}, AnnuTemp={annu_temp:.1f}°C",
                "shap_impact": round(clim_shap_sum, 4),
                "trigger_rationale": "High temperature volatility and model climate sensitivity indicate vulnerability to extreme weather and warming.",
            })

        # ----------------------------------------------------------------------
        # Factor 5: High Extinction Probability / Severe Demographic Decline
        # ----------------------------------------------------------------------
        p_ext = float(probs.get("EXTINCT", 0.0))
        p_thr = float(probs.get("THREATENED", 0.0))
        pop_trend = str(features.get("PopulationTrend", "Unknown"))

        ext_sev = None
        if p_ext >= 0.45 or pred_class == "EXTINCT":
            ext_sev = "CRITICAL"
        elif p_ext >= 0.20 or p_thr >= 0.50 or (p_thr >= 0.40 and pop_trend == "Decreasing"):
            ext_sev = "HIGH"
        elif p_thr >= 0.30 or pop_trend == "Decreasing":
            ext_sev = "MODERATE"

        if ext_sev:
            detected_factors.append({
                "factor_id": "extinction_probability",
                "name": "Imminent Extinction Probability & Population Decline",
                "severity": ext_sev,
                "metric_name": "P(EXTINCT) / P(THREATENED)",
                "metric_value": f"P(EXT)={p_ext:.1%}, P(THR)={p_thr:.1%}, Trend={pop_trend}",
                "shap_impact": round(shap_names.get("PopulationTrend_Decreasing", 0.0), 4),
                "trigger_rationale": f"Predicted extinction probability of {p_ext:.1%} with '{pop_trend}' population trajectory requires emergency intervention.",
            })

        # 3. Generate Actions Exclusively for Detected Risk Factors
        recommendations = []
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}

        # Sort detected factors by severity urgency
        detected_factors.sort(key=lambda item: severity_order.get(item["severity"], 3))

        for factor in detected_factors:
            f_id = factor["factor_id"]
            sev = factor["severity"]

            if f_id == "human_footprint":
                recommendations.append({
                    "risk_factor": "High Human Footprint",
                    "action_category": "Habitat & Anti-Encroachment Protection",
                    "urgency": sev,
                    "headline": "Gazette strict protected reserves and halt agricultural conversion",
                    "action_items": [
                        "Delineate and legally gazette strict core biodiversity zones with a minimum 2 km zero-encroachment buffer.",
                        "Enforce anti-poaching and illegal land-clearing prohibitions via joint community-ranger satellite-monitored patrols.",
                        "Establish community-managed conservancies and conservation easements to prevent ribbon development along access roads.",
                    ],
                })

            elif f_id == "invasive_pressure":
                recommendations.append({
                    "risk_factor": "High Invasive Pressure",
                    "action_category": "Invasive Alien Species Management",
                    "urgency": sev,
                    "headline": "Deploy targeted predator eradication and secure biosecurity perimeters",
                    "action_items": [
                        "Launch targeted baiting, trapping, and eradication campaigns for non-native invasive mammalian predators (feral cats, rats, mongooses).",
                        "Install predator-proof exclusion fencing around remaining primary breeding sanctuaries and critical nesting sites.",
                        "Establish rigorous quarantine inspections and biosecurity screening protocols at transit checkpoints across the species' range.",
                    ],
                })

            elif f_id == "small_range_size":
                recommendations.append({
                    "risk_factor": "Small Geographic Range",
                    "action_category": "Habitat Protection & Ecological Connectivity",
                    "urgency": sev,
                    "headline": "Safeguard 100% of extant habitat and restore fragmented corridors",
                    "action_items": [
                        "Designate Key Biodiversity Areas (KBAs) and micro-reserves encompassing the entire remaining viable distribution.",
                        "Re-establish native vegetation corridors connecting isolated habitat fragments to prevent genetic bottlenecks.",
                        "Identify and survey adjacent potential habitat zones for candidate translocation sites to establish redundant subpopulations.",
                    ],
                })

            elif f_id == "climate_risk":
                recommendations.append({
                    "risk_factor": "Climate Vulnerability",
                    "action_category": "Climate Adaptation & Thermal Refugia",
                    "urgency": sev,
                    "headline": "Protect elevation micro-refugia and enhance landscape thermal buffers",
                    "action_items": [
                        "Map and protect high-elevation, north-facing, and riparian micro-refugia that offer stable microclimatic buffers.",
                        "Restore closed-canopy forest structure and watershed riparian zones to moderate extreme local surface temperatures.",
                        "Initiate feasibility studies for assisted colonization or high-altitude translocations if thermal envelope collapses.",
                    ],
                })

            elif f_id == "extinction_probability":
                recommendations.append({
                    "risk_factor": "High Extinction Probability",
                    "action_category": "Urgent Monitoring & Emergency Demographic Intervention",
                    "urgency": sev,
                    "headline": "Establish emergency telemetry census and insurance captive breeding",
                    "action_items": [
                        "Deploy immediate acoustic and GPS-telemetry census monitoring to establish accurate remnant population numbers.",
                        "Establish an ex-situ insurance colony and genetic biobanking repository under IUCN Species Survival Commission (SSC) protocols.",
                        "Formulate an emergency multi-agency Species Recovery Plan with clear annual survival and recruitment benchmarks.",
                    ],
                })

        # 4. Synthesize Overall Urgency Rating
        if any(f["severity"] == "CRITICAL" for f in detected_factors) or pred_class == "EXTINCT":
            overall_urgency = "CRITICAL / EMERGENCY ACTION REQUIRED"
        elif any(f["severity"] == "HIGH" for f in detected_factors) or pred_class == "THREATENED":
            overall_urgency = "HIGH PRIORITY CONSERVATION ACTION"
        elif detected_factors:
            overall_urgency = "MODERATE TARGETED CONSERVATION INTERVENTION"
        else:
            overall_urgency = "ROUTINE MONITORING / LOW RISK"

        # 5. Integrate Scenario Insights if available
        scenario_insights = None
        if scenario_results:
            scen_trans = scenario_results.get("change_in_risk", {}).get("transition", "Stable")
            scen_delta = scenario_results.get("change_in_risk", {}).get("risk_index_delta", 0.0)
            scenario_insights = {
                "scenario_transition": scen_trans,
                "risk_index_delta": scen_delta,
                "key_finding": (
                    f"Simulation indicates targeted threat mitigation successfully shifts risk: {scen_trans} "
                    f"(Risk Index change: {scen_delta:+.3f})."
                ) if scen_delta < 0 else (
                    f"Unmitigated environmental pressures accelerate extinction trajectory: {scen_trans}."
                ),
            }

        # 6. Priority score integration
        priority_summary = None
        if conservation_priority:
            priority_summary = {
                "conservation_priority_score": conservation_priority.get("conservation_priority_score"),
                "component_breakdown": conservation_priority.get("component_scores"),
            }

        return {
            "scientific_name": sci_name,
            "original_redlist_category": redlist_status,
            "predicted_risk_target": pred_class,
            "class_probabilities": probs,
            "overall_urgency": overall_urgency,
            "detected_risk_factors_count": len(detected_factors),
            "detected_risk_factors": detected_factors,
            "recommendations": recommendations,
            "scenario_insights": scenario_insights,
            "conservation_priority": priority_summary,
        }


# ==============================================================================
# Standalone Convenience Function
# ==============================================================================

_RECOMMENDER_INSTANCE: Optional[ConservationRecommendationEngine] = None


def generate_conservation_recommendations(
    prediction: Optional[Dict[str, Any]] = None,
    feature_values: Optional[Dict[str, Any]] = None,
    shap_contributions: Optional[List[Dict[str, Any]]] = None,
    scenario_results: Optional[Dict[str, Any]] = None,
    conservation_priority: Optional[Dict[str, Any]] = None,
    scientific_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main reusable entry point for generating evidence-based conservation recommendations.
    Accepts pre-computed diagnostic objects or a scientific_name to evaluate on-the-fly.
    """
    global _RECOMMENDER_INSTANCE
    if _RECOMMENDER_INSTANCE is None:
        _RECOMMENDER_INSTANCE = ConservationRecommendationEngine()

    return _RECOMMENDER_INSTANCE.generate_recommendations(
        prediction=prediction,
        feature_values=feature_values,
        shap_contributions=shap_contributions,
        scenario_results=scenario_results,
        conservation_priority=conservation_priority,
        scientific_name=scientific_name,
    )


# ==============================================================================
# Small Test Example & Demonstration
# ==============================================================================

def main():
    print("=" * 95)
    print("IUCN TETRAPOD EVIDENCE-BASED CONSERVATION RECOMMENDATIONS ENGINE")
    print("=" * 95)

    # Test three contrasting species to verify that recommendations are triggered
    # ONLY by detected risk factors
    test_cases = [
        ("Melogale_everetti", "Everett's Ferret-badger (Endangered, high HFP, restricted range)"),
        ("Polyplectron_schleiermacheri", "Bornean Peacock-Pheasant (Endangered, declining, hunting/HFP)"),
        ("Liocichla_steerii", "Taiwan Liocichla (Least Concern, stable habitat)"),
    ]

    for sci_name, description in test_cases:
        print("\n" + "#" * 95)
        print(f"SPECIES: {sci_name}")
        print(f"Profile: {description}")
        print("#" * 95)

        recom_data = generate_conservation_recommendations(scientific_name=sci_name)

        print(f"  * IUCN Status:          {recom_data['original_redlist_category']}")
        print(f"  * Predicted Risk:       {recom_data['predicted_risk_target']}")
        print(f"  * Overall Urgency:      {recom_data['overall_urgency']}")
        print(f"  * Detected Risk Factors: {recom_data['detected_risk_factors_count']}")

        print("\n  DETECTED THREAT DRIVERS:")
        print("  " + "-" * 85)
        for factor in recom_data["detected_risk_factors"]:
            print(f"    [{factor['severity']:<8}] {factor['name']:<46} (Value: {factor['metric_value']})")
            print(f"               --> {factor['trigger_rationale']}")

        print("\n  TAILORED CONSERVATION RECOMMENDATIONS:")
        print("  " + "-" * 85)
        for r_idx, rec in enumerate(recom_data["recommendations"], start=1):
            print(f"    {r_idx}. [{rec['urgency']}] {rec['action_category']} -- for {rec['risk_factor']}")
            print(f"       Headline: {rec['headline']}")
            for action in rec["action_items"]:
                print(f"         - {action}")
            print()

        if recom_data.get("scenario_insights"):
            print(f"  SCENARIO PROJECTION: {recom_data['scenario_insights']['key_finding']}")

    print("=" * 95)
    print("Recommendation engine test completed successfully.")


if __name__ == "__main__":
    main()
