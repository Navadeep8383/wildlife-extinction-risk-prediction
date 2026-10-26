/**
 * Wildlife Conservation Intelligence - API Client Service
 * Connects directly to FastAPI backend on http://127.0.0.1:8000
 */

const API_BASE_URL = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.startsWith('http'))
  ? (window.location.port === '8000' ? window.location.origin : 'http://127.0.0.1:8000')
  : 'http://127.0.0.1:8000';

export class EcoGuardAPI {
  static async checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`, { method: 'GET' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Backend /health unreachable, using offline mode:", err.message);
      return { status: "offline", service: "Wildlife Conservation Intelligence API (Offline Mock)" };
    }
  }

  static async getSpeciesProfile(scientificName) {
    try {
      const res = await fetch(`${API_BASE_URL}/species/${encodeURIComponent(scientificName)}`);
      if (!res.ok) throw new Error(`Species ${scientificName} not found`);
      return await res.json();
    } catch (err) {
      console.warn("Failed fetching species profile from backend:", err);
      return null;
    }
  }

  static async getSpeciesMarkers(limitPerCategory = 3) {
    try {
      const res = await fetch(`${API_BASE_URL}/species/markers?limit_per_category=${limitPerCategory}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.markers || [];
    } catch (err) {
      console.warn("Failed fetching species markers from backend:", err);
      return [];
    }
  }

  static async autocompleteSpecies(query, limit = 12) {
    try {
      const res = await fetch(`${API_BASE_URL}/species?query=${encodeURIComponent(query)}&limit=${limit}`);
      if (!res.ok) throw new Error(`Autocomplete error`);
      const data = await res.json();
      return data.results || [];
    } catch (err) {
      return [];
    }
  }

  static async predictExtinctionRisk(scientificName, topK = 5) {
    try {
      const res = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scientific_name: scientificName, top_k_shap: topK }),
      });
      if (!res.ok) throw new Error(`Prediction error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error("Prediction API failed:", err);
      return null;
    }
  }

  static async simulateScenario(scientificName, scenarioParams) {
    try {
      const body = {
        scientific_name: scientificName,
        ...scenarioParams,
      };
      const res = await fetch(`${API_BASE_URL}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Simulation error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.error("Simulation API failed:", err);
      return null;
    }
  }

  static async getPriorityScore(scientificName) {
    try {
      const res = await fetch(`${API_BASE_URL}/priority/${encodeURIComponent(scientificName)}`);
      if (!res.ok) throw new Error(`Priority error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      return null;
    }
  }

  static async getRecommendations(scientificName) {
    try {
      const res = await fetch(`${API_BASE_URL}/recommendations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scientific_name: scientificName }),
      });
      if (!res.ok) throw new Error(`Recommendations error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      return null;
    }
  }

  static async getSpeciesTimeline(scientificName) {
    try {
      const res = await fetch(`${API_BASE_URL}/species/${encodeURIComponent(scientificName)}/timeline`);
      if (!res.ok) throw new Error(`Timeline error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Failed fetching species timeline:", err);
      return null;
    }
  }

  static async getSpeciesImage(scientificName, className = null) {
    try {
      const query = className ? `?class_name=${encodeURIComponent(className)}` : '';
      const res = await fetch(`${API_BASE_URL}/species/${encodeURIComponent(scientificName)}/image${query}`);
      if (!res.ok) throw new Error(`Image API error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Failed fetching verified species image:", err);
      return null;
    }
  }

  static async getEmergencyScannerData(limitPerTier = 15, classFilter = null) {
    try {
      const params = new URLSearchParams({ limit_per_tier: limitPerTier });
      if (classFilter) params.append('class_filter', classFilter);
      const res = await fetch(`${API_BASE_URL}/species/scanner?${params.toString()}`);
      if (!res.ok) throw new Error(`Scanner error: HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      console.warn("Failed fetching emergency scanner data:", err);
      return null;
    }
  }
}
