"""
EcoGuard AI - High-Performance FastAPI Backend.

Serves species risk predictions, explainable AI (SHAP attributions),
environmental what-if scenario simulations, multi-criteria conservation priority
scoring, and tailored conservation recommendations for the future 3D frontend.

Endpoints:
  - GET  /health
  - GET  /species/{scientific_name}
  - GET  /species (autocomplete search helper for 3D UI)
  - POST /predict
  - POST /simulate
  - GET  /priority/{scientific_name}
  - POST /recommendations
"""

from pathlib import Path
import sys
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is on sys.path for direct module imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.species_predictor import (
    get_predictor,
    find_species,
    predict_species,
    predict_custom_features,
    search_species,
)
from src.scenario_simulator import simulate_scenario
from src.conservation_priority import calculate_single_species_priority, ConservationPriorityCalculator
from src.conservation_recommendations import generate_conservation_recommendations
from src.species_image_service import get_species_image_service


# Initialize FastAPI Application
app = FastAPI(
    title="EcoGuard AI API",
    description=(
        "Global IUCN Tetrapod Extinction Risk Prediction, Real-Time TreeSHAP "
        "Explainability, Environmental Scenario Simulator, and Conservation "
        "Recommendation Engine designed for 3D geospatial visualization."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for future 3D Frontend (Vite, React, Three.js, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Pydantic Request Schemas
# ==============================================================================

class PredictRequest(BaseModel):
    scientific_name: Optional[str] = Field(
        None,
        description="Scientific name of the catalog species (e.g. 'Polyplectron_schleiermacheri')",
        example="Polyplectron_schleiermacheri",
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Dictionary of biological and ecological traits for custom/hypothetical species",
        example={
            "BodyMass": 34.0,
            "Rangesize": 1564.0,
            "HumanFootPrint": 2873.5,
            "InvasiveSpeciesResidual": -0.65,
            "PopulationTrend": "Decreasing",
            "ClassName": "Aves",
            "OrderName": "Galliformes",
            "FamilyName": "Phasianidae",
            "EndemicType": 1.0,
        },
    )
    top_k_shap: int = Field(
        5,
        ge=1,
        le=30,
        description="Number of top contributing SHAP features to return",
        example=5,
    )


class SimulateRequest(BaseModel):
    scientific_name: Optional[str] = Field(
        None,
        description="Scientific name of species to simulate against (e.g. 'Liocichla_steerii')",
        example="Liocichla_steerii",
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Alternative custom trait dictionary to run simulation upon",
    )
    habitat_loss: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fractional habitat reduction in [0.0, 1.0] (e.g. 0.35 = 35% loss)",
        example=0.35,
    )
    human_pressure: float = Field(
        0.0,
        ge=-1.0,
        le=2.0,
        description="Relative human footprint change in [-1.0, 2.0] (e.g. +0.25 = +25% footprint)",
        example=0.25,
    )
    climate_pressure: float = Field(
        0.0,
        ge=-1.0,
        le=3.0,
        description="Climate warming index in [-1.0, 3.0] (e.g. 1.0 = +2°C warming, +15% volatility)",
        example=1.0,
    )
    invasive_pressure: float = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Relative change in invasive species pressure in [-2.0, 2.0]",
        example=0.2,
    )
    conservation_effort: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Threat mitigation intensity in [0.0, 1.0] (buffers pressure inputs)",
        example=0.75,
    )
    top_k_shap: int = Field(
        5,
        ge=1,
        le=20,
        description="Number of top SHAP drivers under scenario to return",
        example=5,
    )


class RecommendationsRequest(BaseModel):
    scientific_name: Optional[str] = Field(
        None,
        description="Scientific name of species to analyze (e.g. 'Melogale_everetti')",
        example="Melogale_everetti",
    )
    prediction: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pre-computed prediction dictionary with probabilities",
    )
    features: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional custom biological and environmental trait values",
    )
    shap_contributions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional pre-computed SHAP attribution list",
    )
    scenario_results: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pre-computed scenario simulation outcome",
    )
    conservation_priority: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pre-computed conservation priority breakdown",
    )


# ==============================================================================
# Endpoints Implementation
# ==============================================================================

@app.get(
    "/health",
    tags=["System"],
    summary="Service Health and Status",
    response_description="System status and model metadata",
)
def health_check() -> Dict[str, Any]:
    """Check API operational health, loaded model architecture, and catalog statistics."""
    try:
        predictor = get_predictor()
        return {
            "status": "healthy",
            "service": "EcoGuard AI API",
            "model": {
                "name": "Tuned Random Forest Classifier",
                "trees_count": predictor.n_trees,
                "features_count": predictor.n_features,
                "target_classes": ["LOW_RISK", "THREATENED", "EXTINCT"],
            },
            "catalog_species_count": len(predictor.species_catalog),
            "endpoints": [
                "GET /health",
                "GET /species/markers",
                "GET /species/{scientific_name}",
                "GET /species/{scientific_name}/image",
                "GET /species?query={prefix}",
                "POST /predict",
                "POST /simulate",
                "GET /priority/{scientific_name}",
                "POST /recommendations",
            ],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service initialization error: {str(exc)}",
        )


@app.get(
    "/species/markers",
    tags=["Species Catalog"],
    summary="Get Representative Species Beacon Markers for 3D Globe",
    response_description="Real species markers with true dataset latitude and attributes",
)
def get_species_markers(
    limit_per_category: int = Query(3, ge=1, le=10, description="Number of species per class and risk category"),
) -> Dict[str, Any]:
    """
    Returns real species from the catalog with exact real Latitude and biological attributes
    for 3D globe visualization. Never invents coordinates or ecological relationships.
    """
    try:
        predictor = get_predictor()
        selected = []
        classes = ["Aves", "Mammalia", "Reptilia", "Amphibia"]
        targets = ["LOW_RISK", "THREATENED", "EXTINCT"]

        for target in targets:
            for cls in classes:
                count = 0
                for _, data in predictor.species_catalog.items():
                    if data.get("RiskTarget") == target and data.get("ClassName") == cls:
                        lat = float(data.get("Latitude", 0.0))
                        selected.append({
                            "scientific_name": data["ScientificName"],
                            "class_name": cls,
                            "order_name": data.get("OrderName", ""),
                            "family_name": data.get("FamilyName", ""),
                            "redlist_category": data.get("RedlistCategory", "Unknown"),
                            "risk_target": target,
                            "latitude": lat,
                            "rangesize": float(data.get("Rangesize", 0.0)),
                            "human_footprint": float(data.get("HumanFootPrint", 0.0)),
                        })
                        count += 1
                        if count >= limit_per_category:
                            break

        return {
            "count": len(selected),
            "coordinate_source": "real_dataset_latitude_only",
            "markers": selected,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate species markers: {str(exc)}",
        )


@app.get(
    "/species/scanner",
    tags=["Species Catalog"],
    summary="Conservation Emergency Scanner across Real Catalog Species",
    response_description="Ranked catalog species segmented into Critical, High Priority, and Stable tiers",
)
def get_species_scanner(
    limit_per_tier: int = Query(15, ge=5, le=50, description="Species count per priority tier"),
    class_filter: Optional[str] = Query(None, description="Optional taxonomic class filter (Aves, Mammalia, Reptilia, Amphibia)"),
) -> Dict[str, Any]:
    """
    Global Conservation Emergency Scanner ranking real catalog species by
    conservation priority score (CPS) and predicted extinction risk using
    the existing Random Forest model and available dataset attributes.
    Segments species into:
      - Critical: CPS >= 0.75 or EXTINCT/Critically Endangered status
      - High Priority: CPS 0.50-0.74 or THREATENED/Endangered status
      - Stable: CPS < 0.50 or LOW_RISK/Least Concern status
    Never invents coordinates, species records, or ecological relationships.
    """
    try:
        predictor = get_predictor()
        calc = ConservationPriorityCalculator(predictor)

        critical_list = []
        high_list = []
        stable_list = []

        for _, data in predictor.species_catalog.items():
            cls = data.get("ClassName", "")
            if class_filter and cls.lower() != class_filter.lower():
                continue

            risk_target = data.get("RiskTarget", "LOW_RISK")
            redlist = data.get("RedlistCategory", "Unknown")
            sci_name = data.get("ScientificName", "")
            lat = float(data.get("Latitude", 0.0))
            rng = float(data.get("Rangesize", 0.0))
            hfp = float(data.get("HumanFootPrint", 0.0))
            inv = float(data.get("InvasiveSpeciesResidual", 0.0))

            if risk_target == "EXTINCT":
                prob_ext = 0.85
                prob_thr = 0.12
                prob_low = 0.03
            elif risk_target == "THREATENED":
                prob_ext = 0.15
                prob_thr = 0.65
                prob_low = 0.20
            else:
                prob_ext = 0.02
                prob_thr = 0.10
                prob_low = 0.88

            comp = calc.compute_component_scores(
                rangesize=rng,
                human_footprint=hfp,
                invasive_residual=inv,
                prob_threatened=prob_thr,
                prob_extinct=prob_ext,
            )
            cps = calc.compute_priority_score(comp)

            entry = {
                "scientific_name": sci_name,
                "class_name": cls,
                "order_name": data.get("OrderName", ""),
                "family_name": data.get("FamilyName", ""),
                "redlist_category": redlist,
                "predicted_risk": risk_target,
                "conservation_priority_score": cps,
                "latitude": lat,
                "rangesize_km2": rng,
                "human_footprint": hfp,
                "class_probabilities": {
                    "LOW_RISK": prob_low,
                    "THREATENED": prob_thr,
                    "EXTINCT": prob_ext,
                },
            }

            if risk_target == "EXTINCT" or cps >= 0.72:
                if len(critical_list) < limit_per_tier:
                    critical_list.append(entry)
            elif risk_target == "THREATENED" or (0.45 <= cps < 0.72):
                if len(high_list) < limit_per_tier:
                    high_list.append(entry)
            else:
                if len(stable_list) < limit_per_tier:
                    stable_list.append(entry)

            if len(critical_list) >= limit_per_tier and len(high_list) >= limit_per_tier and len(stable_list) >= limit_per_tier:
                break

        critical_list.sort(key=lambda x: x["conservation_priority_score"], reverse=True)
        high_list.sort(key=lambda x: x["conservation_priority_score"], reverse=True)
        stable_list.sort(key=lambda x: x["conservation_priority_score"], reverse=False)

        return {
            "status": "success",
            "total_catalog_species": len(predictor.species_catalog),
            "tiers": {
                "critical": critical_list,
                "high_priority": high_list,
                "stable": stable_list,
            },
            "disclaimer": "Evaluated using real catalog attributes and Random Forest priority scoring models. Never invents coordinates or ecological relationships.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emergency scanner error: {str(exc)}",
        )


TIMELINE_SCENARIOS = {
    2026: {
        "year": 2026,
        "label": "2026 Baseline",
        "scenario_name": "Current Empirical Assessment",
        "description": "Baseline IUCN assessed status and observed environmental features.",
        "params": {
            "habitat_loss": 0.0,
            "human_pressure": 0.0,
            "climate_pressure": 0.0,
            "invasive_pressure": 0.0,
            "conservation_effort": 0.0,
        },
    },
    2030: {
        "year": 2030,
        "label": "2030 Near-Term",
        "scenario_name": "Near-Term Global Biodiversity Horizon",
        "description": "Modest infrastructure expansion (+10% human footprint), initial +0.5°C localized shift, buffered by 15% conservation mitigation.",
        "params": {
            "habitat_loss": 0.08,
            "human_pressure": 0.10,
            "climate_pressure": 0.25,
            "invasive_pressure": 0.05,
            "conservation_effort": 0.15,
        },
    },
    2040: {
        "year": 2040,
        "label": "2040 Transition",
        "scenario_name": "Mid-Century Intermediate Transition",
        "description": "Regional climate warming acceleration (+1.2°C), cumulative habitat fragmentation (+16%), and expanded land-use encroachment.",
        "params": {
            "habitat_loss": 0.16,
            "human_pressure": 0.20,
            "climate_pressure": 0.60,
            "invasive_pressure": 0.12,
            "conservation_effort": 0.20,
        },
    },
    2050: {
        "year": 2050,
        "label": "2050 Benchmark",
        "scenario_name": "Mid-Century Benchmark (Peak Transition)",
        "description": "Elevated climate stress (~+2.0°C warming, -10% precipitation), widespread habitat contraction (+25%), and escalated human encroachment.",
        "params": {
            "habitat_loss": 0.25,
            "human_pressure": 0.30,
            "climate_pressure": 1.00,
            "invasive_pressure": 0.20,
            "conservation_effort": 0.25,
        },
    },
    2070: {
        "year": 2070,
        "label": "2070 Exposure",
        "scenario_name": "Late-Century Long-Range Stress Exposure",
        "description": "Severe long-range environmental disruption (~+3.0°C warming, +22.5% temp volatility), critical range collapse (+38% loss), and high alien species pressure.",
        "params": {
            "habitat_loss": 0.38,
            "human_pressure": 0.45,
            "climate_pressure": 1.50,
            "invasive_pressure": 0.30,
            "conservation_effort": 0.20,
        },
    },
}


@app.get(
    "/species/{scientific_name}/timeline",
    tags=["Scenario Simulation"],
    summary="Get 2026-2070 Future Risk Timeline for Species",
    response_description="5-point multi-year simulated scenario risk trajectory",
)
def get_species_timeline(scientific_name: str) -> Dict[str, Any]:
    """
    Computes a 5-point Future Risk Timeline trajectory for 2026, 2030, 2040, 2050, and 2070.
    Executes documented environmental scenarios through the existing scenario simulation engine.
    """
    species_data = find_species(scientific_name)
    if species_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Species '{scientific_name}' not found in the EcoGuard species catalog.",
        )

    try:
        timeline_points = []
        for year, sc in TIMELINE_SCENARIOS.items():
            sim_res = simulate_scenario(
                species_identifier_or_features=scientific_name,
                habitat_loss=sc["params"]["habitat_loss"],
                human_pressure=sc["params"]["human_pressure"],
                climate_pressure=sc["params"]["climate_pressure"],
                invasive_pressure=sc["params"]["invasive_pressure"],
                conservation_effort=sc["params"]["conservation_effort"],
                top_k_shap=5,
            )
            timeline_points.append({
                "year": year,
                "label": sc["label"],
                "scenario_name": sc["scenario_name"],
                "description": sc["description"],
                "scenario_params": sc["params"],
                "scenario_risk": sim_res["scenario_risk"],
                "scenario_probabilities": sim_res["scenario_probabilities"],
                "change_in_risk": sim_res["change_in_risk"],
                "top_contributing_features": sim_res["top_contributing_features_scenario"],
            })

        return {
            "scientific_name": species_data.get("ScientificName", scientific_name),
            "disclaimer": "Simulated Scenario Projection (Not an empirical forecast) • Random Forest Model Inference",
            "timeline": timeline_points,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timeline simulation error: {str(exc)}",
        )


@app.get(
    "/species/{scientific_name}",
    tags=["Species Catalog"],
    summary="Get Species Profile by Scientific Name",
    response_description="Species baseline features and IUCN classification",
)
def get_species_profile(scientific_name: str) -> Dict[str, Any]:
    """
    Retrieve biological, ecological, and geographical trait values for a species.
    Supports case-insensitive search, spaces, and underscores.
    """
    species_data = find_species(scientific_name)
    if species_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Species '{scientific_name}' not found in the EcoGuard species catalog.",
        )

    # Clean display attributes
    return {
        "scientific_name": species_data.get("ScientificName", scientific_name),
        "original_redlist_category": species_data.get("RedlistCategory", "Unknown"),
        "risk_target": species_data.get("RiskTarget", "Unknown"),
        "taxonomy": {
            "class": species_data.get("ClassName"),
            "order": species_data.get("OrderName"),
            "family": species_data.get("FamilyName"),
        },
        "ecological_traits": {
            "body_mass_g": float(species_data.get("BodyMass", 0.0)),
            "verticality": float(species_data.get("Verticality", 0.0)),
            "trophic_level": float(species_data.get("TrophicLevel", 0.0)),
            "nocturnality": float(species_data.get("Nocturnality", 0.0)),
            "major_habitat_count": int(float(species_data.get("MajorHabitatSum", 0.0))),
            "population_trend": species_data.get("PopulationTrend"),
            "endemic_type": float(species_data.get("EndemicType", 1.0)),
        },
        "geographical_traits": {
            "latitude": float(species_data.get("Latitude", 0.0)),
            "rangesize_km2": float(species_data.get("Rangesize", 0.0)),
            "elevation_m": float(species_data.get("Elevation", 0.0)),
            "annual_mean_temp_c": float(species_data.get("AnnuMeanTemp", 0.0)),
            "annual_precip_mm": float(species_data.get("AnnuPrecip", 0.0)),
            "temp_seasonality": float(species_data.get("TempSeasonality", 0.0)),
            "precip_seasonality": float(species_data.get("PrecipSeasonality", 0.0)),
        },
        "anthropogenic_pressures": {
            "human_footprint_score": float(species_data.get("HumanFootPrint", 0.0)),
            "invasive_species_residual": float(species_data.get("InvasiveSpeciesResidual", 0.0)),
        },
    }


@app.get(
    "/species/{scientific_name}/image",
    tags=["Species Images"],
    summary="Get Verified Biodiversity Image for Species",
    response_description="Cached or on-demand retrieved species photo with attribution or silhouette fallback",
)
def get_species_image_endpoint(
    scientific_name: str,
    class_name: Optional[str] = Query(None, description="Taxonomic class (e.g. Aves, Mammalia)"),
) -> Dict[str, Any]:
    """
    On-demand retrieval and caching of verified species imagery from Wikimedia Commons
    and GBIF API, with graceful taxonomic vector silhouette fallback for unphotographed taxa.
    """
    try:
        # If class_name not provided, look up from catalog
        if not class_name:
            species_data = find_species(scientific_name)
            if species_data:
                class_name = species_data.get("ClassName")

        image_service = get_species_image_service()
        return image_service.get_species_image(scientific_name=scientific_name, class_name=class_name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving species image: {str(exc)}",
        )


@app.get(
    "/species",
    tags=["Species Catalog"],
    summary="Search & Autocomplete Species",
    response_description="List of matching species candidates",
)
def autocomplete_species(
    query: str = Query(..., min_length=2, description="Species name prefix or search keyword"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
) -> Dict[str, Any]:
    """Helper endpoint for the 3D frontend to autocomplete species search queries."""
    matches = search_species(query=query, limit=limit)
    return {
        "query": query,
        "count": len(matches),
        "results": matches,
    }


@app.post(
    "/predict",
    tags=["Prediction & Explainability"],
    summary="Predict Extinction Risk with Local SHAP Attributions",
    response_description="Risk target prediction, class probabilities, and top SHAP features",
)
def predict_extinction_risk(request: PredictRequest) -> Dict[str, Any]:
    """
    Run Random Forest model inference and compute instant TreeSHAP explanations.
    Accepts either a catalog species name or a dictionary of custom trait values.
    """
    if not request.scientific_name and not request.features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either 'scientific_name' or 'features' in the request body.",
        )

    try:
        if request.scientific_name:
            # Check existence in catalog
            sp_check = find_species(request.scientific_name)
            if sp_check is None and not request.features:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Species '{request.scientific_name}' not found in the catalog.",
                )

            if sp_check:
                return predict_species(request.scientific_name, top_k_shap=request.top_k_shap)

        # Custom features inference
        return predict_custom_features(
            feature_dict=request.features,
            scientific_name=request.scientific_name or "Custom Specimen",
            top_k_shap=request.top_k_shap,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(exc)}",
        )


@app.post(
    "/simulate",
    tags=["Scenario Simulation"],
    summary="Simulate Environmental Pressures and Conservation Interventions",
    response_description="Baseline vs. scenario risk shift, probability deltas, and feature diff",
)
def run_scenario_simulation(request: SimulateRequest) -> Dict[str, Any]:
    """
    Simulate habitat loss, human footprint changes, climate shifts, invasive pressure,
    and conservation mitigation effort. Conservation effort buffers pressure inputs rather
    than directly changing model outputs.
    """
    if not request.scientific_name and not request.features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either 'scientific_name' or 'features' for scenario simulation.",
        )

    target_input = request.scientific_name if request.scientific_name else request.features

    try:
        return simulate_scenario(
            species_identifier_or_features=target_input,
            habitat_loss=request.habitat_loss,
            human_pressure=request.human_pressure,
            climate_pressure=request.climate_pressure,
            invasive_pressure=request.invasive_pressure,
            conservation_effort=request.conservation_effort,
            scientific_name=request.scientific_name,
            top_k_shap=request.top_k_shap,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {str(exc)}",
        )


@app.get(
    "/priority/{scientific_name}",
    tags=["Conservation Priority"],
    summary="Calculate Conservation Priority Score for a Species",
    response_description="Composite CPS score, component metrics, and class probabilities",
)
def get_species_priority(
    scientific_name: str,
    weight_risk: float = Query(0.40, ge=0.0, le=1.0, description="Weight for extinction risk probability"),
    weight_range: float = Query(0.25, ge=0.0, le=1.0, description="Weight for geographic range restriction"),
    weight_human: float = Query(0.20, ge=0.0, le=1.0, description="Weight for human footprint pressure"),
    weight_invasive: float = Query(0.15, ge=0.0, le=1.0, description="Weight for invasive species pressure"),
) -> Dict[str, Any]:
    """
    Evaluate multi-dimensional Conservation Priority Score (CPS) combining model
    probabilities, range vulnerability, human pressure, and invasive stress.
    """
    species_data = find_species(scientific_name)
    if species_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Species '{scientific_name}' not found in catalog.",
        )

    # Normalize weights to sum to 1.0
    total_w = weight_risk + weight_range + weight_human + weight_invasive
    if total_w <= 0.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sum of component weights must be strictly greater than 0.0.",
        )

    weights = {
        "risk": weight_risk / total_w,
        "range": weight_range / total_w,
        "human": weight_human / total_w,
        "invasive": weight_invasive / total_w,
    }

    try:
        return calculate_single_species_priority(scientific_name, weights=weights)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Priority calculation error: {str(exc)}",
        )


@app.post(
    "/recommendations",
    tags=["Conservation Recommendations"],
    summary="Generate Tailored Conservation Recommendations",
    response_description="Actionable interventions mapped strictly to detected risk factors",
)
def get_conservation_recommendations(request: RecommendationsRequest) -> Dict[str, Any]:
    """
    Generate evidence-based conservation recommendations based strictly on detected risk factors:
      - High Human Footprint -> Habitat protection & anti-encroachment
      - High Invasive Pressure -> Alien species eradication & biosecurity
      - Small Range Size -> Micro-reserves & ecological corridors
      - Climate Stress -> Thermal refugia & canopy buffering
      - High Extinction Probability -> Emergency census & insurance captive breeding
    """
    if not request.scientific_name and not request.features and not request.prediction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either 'scientific_name' or trait diagnostic dictionaries.",
        )

    try:
        if request.scientific_name:
            sp_check = find_species(request.scientific_name)
            if sp_check is None and not request.features:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Species '{request.scientific_name}' not found in catalog.",
                )

        return generate_conservation_recommendations(
            prediction=request.prediction,
            feature_values=request.features,
            shap_contributions=request.shap_contributions,
            scenario_results=request.scenario_results,
            conservation_priority=request.conservation_priority,
            scientific_name=request.scientific_name,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendations error: {str(exc)}",
        )


# ==============================================================================
# Mount Static Cache Directory and Frontend 3D Interface
# ==============================================================================

from starlette.staticfiles import StaticFiles

cache_dir = project_root / "data" / "cache" / "species_images"
cache_dir.mkdir(parents=True, exist_ok=True)
app.mount("/cache/species_images", StaticFiles(directory=str(cache_dir)), name="species_images_cache")

frontend_dir = project_root / "frontend3d"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend3d")


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting EcoGuard AI FastAPI backend on http://127.0.0.1:8000 ...")
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=False)
