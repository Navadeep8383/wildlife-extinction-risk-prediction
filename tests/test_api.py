"""
Automated Endpoint Tests for EcoGuard AI FastAPI Backend.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from starlette.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_health():
    print("Testing GET /health ...")
    res = client.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["status"] == "healthy"
    assert data["catalog_species_count"] > 30000
    print("  -> Passed! Catalog species:", data["catalog_species_count"])


def test_get_species():
    print("Testing GET /species/Polyplectron_schleiermacheri ...")
    res = client.get("/species/Polyplectron_schleiermacheri")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["scientific_name"] == "Polyplectron_schleiermacheri"
    assert data["original_redlist_category"] == "Endangered"
    assert "rangesize_km2" in data["geographical_traits"]
    print("  -> Passed! Red List Category:", data["original_redlist_category"])

    print("Testing GET /species/Unknown_fake_species (404 test) ...")
    res_404 = client.get("/species/Unknown_fake_species")
    assert res_404.status_code == 404
    print("  -> Passed! Correctly returned 404.")


def test_predict():
    print("Testing POST /predict with catalog species ...")
    res = client.post("/predict", json={"scientific_name": "Polyplectron_schleiermacheri", "top_k_shap": 3})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["predicted_risk_target"] in ["LOW_RISK", "THREATENED", "EXTINCT"]
    assert "prediction_probabilities" in data
    assert len(data["top_contributing_features"]) == 3
    print("  -> Passed! Prediction:", data["predicted_risk_target"], data["prediction_probabilities"])

    print("Testing POST /predict with custom features ...")
    custom_body = {
        "features": {
            "BodyMass": 1500.0,
            "Rangesize": 25.0,
            "HumanFootPrint": 18000.0,
            "InvasiveSpeciesResidual": 2.1,
            "PopulationTrend": "Decreasing",
            "ClassName": "Aves",
            "OrderName": "Columbiformes",
            "FamilyName": "Columbidae",
            "EndemicType": 1.0,
        },
        "scientific_name": "Hypothetical Island Dove",
    }
    res_c = client.post("/predict", json=custom_body)
    assert res_c.status_code == 200
    print("  -> Passed! Custom prediction:", res_c.json()["predicted_risk_target"])

    print("Testing POST /predict invalid body (400 test) ...")
    res_400 = client.post("/predict", json={})
    assert res_400.status_code == 400
    print("  -> Passed! Correctly returned 400.")


def test_simulate():
    print("Testing POST /simulate ...")
    sim_body = {
        "scientific_name": "Liocichla_steerii",
        "habitat_loss": 0.50,
        "human_pressure": 0.40,
        "climate_pressure": 1.00,
        "invasive_pressure": 0.20,
        "conservation_effort": 0.80,
    }
    res = client.post("/simulate", json=sim_body)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "baseline_risk" in data
    assert "scenario_risk" in data
    assert "change_in_risk" in data
    assert "applied_adjustments" in data
    print("  -> Passed! Scenario transition:", data["change_in_risk"]["transition"])


def test_priority():
    print("Testing GET /priority/Melogale_everetti ...")
    res = client.get("/priority/Melogale_everetti")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "conservation_priority_score" in data
    assert "component_scores" in data
    cps = data["conservation_priority_score"]
    assert 0.0 <= cps <= 1.0
    print("  -> Passed! Priority CPS:", cps)

    print("Testing GET /priority/Unknown_fake_species (404 test) ...")
    res_404 = client.get("/priority/Unknown_fake_species")
    assert res_404.status_code == 404
    print("  -> Passed! Correctly returned 404.")


def test_recommendations():
    print("Testing POST /recommendations ...")
    res = client.post("/recommendations", json={"scientific_name": "Melogale_everetti"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "detected_risk_factors" in data
    assert len(data["detected_risk_factors"]) > 0
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    print("  -> Passed! Overall Urgency:", data["overall_urgency"], "Recommendations:", len(data["recommendations"]))


def test_species_image():
    print("Testing GET /species/Polyplectron_schleiermacheri/image ...")
    res = client.get("/species/Polyplectron_schleiermacheri/image?class_name=Aves")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["scientific_name"] == "Polyplectron_schleiermacheri"
    assert data["has_image"] is True
    assert "image_url" in data
    assert "attribution" in data
    print("  -> Passed! Image source:", data.get("source"), "Attribution:", data.get("attribution"))

    print("Testing GET /species/Pennatomys_nivalis/image (silhouette fallback) ...")
    res_sil = client.get("/species/Pennatomys_nivalis/image?class_name=Mammalia")
    assert res_sil.status_code == 200, f"Expected 200, got {res_sil.status_code}: {res_sil.text}"
    data_sil = res_sil.json()
    assert data_sil["has_image"] is False
    assert data_sil["silhouette_class"] == "Mammalia"
    print("  -> Passed! Silhouette class:", data_sil.get("silhouette_class"))


def run_all_tests():
    print("=" * 80)
    print("RUNNING ECOGUARD AI FASTAPI ENDPOINT VERIFICATION")
    print("=" * 80)
    test_health()
    test_get_species()
    test_predict()
    test_simulate()
    test_priority()
    test_recommendations()
    test_species_image()
    print("=" * 80)
    print("ALL ENDPOINT TESTS PASSED SUCCESSFULLY (100% PASS RATE)!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

