# Wildlife Extinction Risk Prediction Using Machine Learning

An AI-powered wildlife conservation platform that predicts species extinction risk, explains model predictions, and helps explore conservation priorities through interactive 3D visualization.

## Overview

Wildlife extinction is influenced by habitat loss, human activities, climate change, invasive species, and other ecological factors. This project uses machine learning to classify wildlife extinction risk and provide interpretable insights to support conservation decision-making.

The system combines a Random Forest classifier, SHAP-based Explainable AI, conservation priority scoring, hypothetical scenario simulation, and an interactive 3D Earth interface.

## Key Features

- **Extinction Risk Prediction:** Classifies species into `LOW_RISK`, `THREATENED`, and `EXTINCT`.
- **Explainable AI:** Uses SHAP to help interpret factors influencing predictions.
- **Interactive 3D Visualization:** Explores wildlife information through a 3D Earth interface.
- **Scenario Simulation:** Investigates hypothetical changes in environmental pressures and conservation efforts.
- **Conservation Prioritization:** Assigns priority scores to support conservation planning.
- **Recommendations:** Provides rule-based conservation suggestions.
- **Species Profiles:** Presents species-level risk information and model outputs.

## Dataset

The project uses data covering approximately 30,711 terrestrial vertebrate species.

Dataset reference: *Global patterns and drivers of extinction risk in island endemic terrestrial vertebrates.*

DOI: https://doi.org/10.5061/dryad.kprr4xhkf

## Technology Stack

- **Language:** Python, JavaScript
- **Machine Learning:** Scikit-learn, Random Forest
- **Data Processing:** Pandas, NumPy
- **Class Imbalance:** SMOTE
- **Explainable AI:** SHAP
- **Backend:** FastAPI
- **Frontend:** HTML, CSS, Three.js
- **Model Storage:** Joblib

## Project Structure

```text
wildlife-extinction-risk-prediction/
├── app/
│   └── api.py
├── data/
│   └── processed/
├── frontend3d/
│   ├── index.html
│   ├── css/
│   └── js/
├── models/
├── src/
├── tests/
└── requirements.txt
```

## Installation and Usage

### 1. Clone the repository

```bash
git clone https://github.com/Navadeep8383/wildlife-extinction-risk-prediction.git
cd wildlife-extinction-risk-prediction
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the backend

From the project root, run:

```bash
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

### 4. Open the application

Visit:

- Application: http://127.0.0.1:8000/
- API documentation: http://127.0.0.1:8000/docs

**Note:** The backend entry point, model paths, and dependencies must match the repository structure and available files. If the application does not start, check the API configuration before deployment.

## Project Objective

To develop an interactive machine learning-based conservation decision-support system that helps users understand wildlife extinction risk, examine contributing factors, and explore potential conservation priorities.

## Limitations

Scenario simulations explore hypothetical changes to model inputs and should not be interpreted as validated ecological forecasts. Predictions depend on the quality, coverage, and limitations of the available dataset.

## Future Enhancements

- Integration of verified geographic and biodiversity observations.
- Expanded independent model validation.
- Improved ecological scenario modelling.
- Additional conservation datasets and research-based recommendations.

## Author

**Navadeep8383**

GitHub Repository: https://github.com/Navadeep8383/wildlife-extinction-risk-prediction
## Project Screenshots

### Main Dashboard
![Main Dashboard](screenshots/main-dashboard.png)

### Conservation Emergency Scanner
![Conservation Scanner](screenshots/conservation-scanner.png)

### Species Profile and Risk Explanation
![Species Profile](screenshots/species-profile.png)

### Scenario Simulation
![Scenario Simulation](screenshots/scenario-simulation.png)

### Species Comparison
![Species Comparison](screenshots/species-comparison.png)
