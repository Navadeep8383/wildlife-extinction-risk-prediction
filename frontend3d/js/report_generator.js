/**
 * Wildlife Conservation Intelligence - Species Intelligence Report Generator
 * Generates an executive, printable scientific report document from empirical model inference.
 */

export class ReportGenerator {
  /**
   * Compiles species data into a self-contained HTML report and triggers browser download.
   */
  static generateReport(data) {
    const {
      speciesName,
      taxonomy,
      profile,
      prediction,
      priority,
      recommendations,
      timeline,
      scenarioResult,
      scenarioParams,
      imageData,
    } = data;

    const formattedName = speciesName ? speciesName.replace(/_/g, ' ') : 'Unknown Species';
    const timestamp = new Date().toUTCString();
    const target = prediction?.predicted_risk_target || 'UNKNOWN';
    const targetColor = target === 'EXTINCT' ? '#ef4444' : target === 'THREATENED' ? '#f59e0b' : '#10b981';

    const probs = prediction?.prediction_probabilities || { LOW_RISK: 0, THREATENED: 0, EXTINCT: 0 };
    const pLow = ((probs.LOW_RISK ?? 0) * 100).toFixed(1);
    const pThr = ((probs.THREATENED ?? 0) * 100).toFixed(1);
    const pExt = ((probs.EXTINCT ?? 0) * 100).toFixed(1);

    const shapRows = (prediction?.top_contributing_features || [])
      .map((f, i) => {
        const val = typeof f.shap_value === 'number' ? f.shap_value.toFixed(4) : f.shap_value;
        const dir = f.direction === 'increases_risk' ? '▲ Escalates Risk' : '▼ Mitigates Risk';
        const dirColor = f.direction === 'increases_risk' ? '#ef4444' : '#10b981';
        return `
          <tr>
            <td><strong>#${i + 1}</strong> ${f.feature.replace(/_/g, ' ')}</td>
            <td style="font-family: monospace; text-align: right; color: ${val >= 0 ? '#38bdf8' : '#34d399'};">${val > 0 ? '+' : ''}${val}</td>
            <td style="color: ${dirColor}; font-weight: 600;">${dir}</td>
          </tr>
        `;
      })
      .join('');

    const recCards = (recommendations?.recommendations || [])
      .map(r => `
        <div style="background: #f8fafc; border-left: 4px solid #06b6d4; padding: 12px 16px; margin-bottom: 10px; border-radius: 4px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <strong style="color: #0f172a; font-size: 13px;">${r.action_category}</strong>
            <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: #e0f2fe; color: #0284c7; font-weight: 600;">${r.urgency} Urgency</span>
          </div>
          <div style="font-size: 12.5px; color: #334155; line-height: 1.45;">${r.headline}</div>
        </div>
      `)
      .join('');

    const timelineRows = (timeline || [])
      .map(t => {
        const extP = ((t.scenario_probabilities?.EXTINCT ?? 0) * 100).toFixed(1);
        const rColor = t.scenario_risk === 'EXTINCT' ? '#ef4444' : t.scenario_risk === 'THREATENED' ? '#f59e0b' : '#10b981';
        return `
          <tr>
            <td><strong>${t.year}</strong> (${t.label})</td>
            <td>${t.scenario_name}</td>
            <td style="color: ${rColor}; font-weight: 700;">${t.scenario_risk}</td>
            <td style="font-family: monospace; text-align: right;">${extP}%</td>
          </tr>
        `;
      })
      .join('');

    const cpsScore = priority?.conservation_priority_score
      ? (priority.conservation_priority_score * 100).toFixed(1)
      : 'N/A';

    const reportHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${formattedName} — Conservation Intelligence Dossier</title>
  <style>
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .no-print { display: none !important; }
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 32px 40px;
      color: #0f172a;
      background: #ffffff;
      line-height: 1.5;
    }
    .header {
      border-bottom: 2px solid #0f172a;
      padding-bottom: 20px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .brand-title {
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #0284c7;
      font-weight: 800;
    }
    h1 {
      font-size: 26px;
      font-weight: 800;
      margin: 4px 0 6px 0;
      color: #0f172a;
    }
    .taxonomy-sub {
      font-size: 13px;
      color: #64748b;
    }
    .risk-badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 6px;
      font-weight: 800;
      font-size: 14px;
      letter-spacing: 0.04em;
      color: #ffffff;
      background: ${targetColor};
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }
    .card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px 20px;
    }
    .card h2 {
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #475569;
      margin: 0 0 12px 0;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 6px;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      font-size: 12.5px;
      margin-bottom: 8px;
    }
    .metric-row span:last-child {
      font-weight: 600;
      font-family: monospace;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    th, td {
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
    }
    th {
      background: #f1f5f9;
      font-weight: 700;
      color: #475569;
    }
    .disclaimer-box {
      margin-top: 30px;
      padding: 12px 16px;
      background: #f1f5f9;
      border-radius: 6px;
      font-size: 11px;
      color: #64748b;
      line-height: 1.5;
    }
    .print-btn {
      position: fixed;
      top: 20px;
      right: 20px;
      background: #0284c7;
      color: #fff;
      border: none;
      padding: 10px 18px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
    }
  </style>
</head>
<body>
  <button class="print-btn no-print" onclick="window.print()">Print / Save as PDF</button>

  <div class="header">
    <div>
      <div class="brand-title">Wildlife Conservation Intelligence • Official Analytical Dossier</div>
      <h1>${formattedName}</h1>
      <div class="taxonomy-sub">
        Class: <strong>${taxonomy?.class || 'Tetrapoda'}</strong> &bull;
        Order: <strong>${taxonomy?.order || 'N/A'}</strong> &bull;
        Family: <strong>${taxonomy?.family || 'N/A'}</strong> &bull;
        IUCN Status: <strong>${profile?.original_redlist_category || 'Evaluated'}</strong>
      </div>
    </div>
    <div style="text-align: right;">
      <div class="risk-badge">${target}</div>
      <div style="font-size: 10.5px; color: #94a3b8; margin-top: 6px;">Generated: ${timestamp}</div>
    </div>
  </div>

  <div class="grid">
    <!-- Risk Probability Distribution -->
    <div class="card">
      <h2>Random Forest Model Probabilities (500-Tree Forest)</h2>
      <div class="metric-row">
        <span>Low Extinction Risk</span>
        <span style="color: #10b981;">${pLow}%</span>
      </div>
      <div class="metric-row">
        <span>Threatened (Vulnerable / Endangered)</span>
        <span style="color: #f59e0b;">${pThr}%</span>
      </div>
      <div class="metric-row">
        <span>High Extinction Likelihood</span>
        <span style="color: #ef4444;">${pExt}%</span>
      </div>
      <div style="margin-top: 14px; padding-top: 10px; border-top: 1px dashed #cbd5e1;">
        <div class="metric-row">
          <span>Conservation Priority Score (CPS)</span>
          <span style="color: #0284c7; font-size: 14px;">${cpsScore} / 100</span>
        </div>
      </div>
    </div>

    <!-- Geographic & Anthropogenic Traits -->
    <div class="card">
      <h2>Geographic & Environmental Traits (Dataset Centroid)</h2>
      <div class="metric-row">
        <span>Dataset Centroid Latitude</span>
        <span>${profile?.geographical_traits?.latitude !== undefined ? profile.geographical_traits.latitude.toFixed(2) + '°' : 'N/A'}</span>
      </div>
      <div class="metric-row">
        <span>Observed Range Size</span>
        <span>${profile?.geographical_traits?.rangesize_km2 ? Math.round(profile.geographical_traits.rangesize_km2).toLocaleString() + ' km²' : 'N/A'}</span>
      </div>
      <div class="metric-row">
        <span>Elevation Centroid</span>
        <span>${profile?.geographical_traits?.elevation_m ? Math.round(profile.geographical_traits.elevation_m) + ' m' : 'N/A'}</span>
      </div>
      <div class="metric-row">
        <span>Human Footprint Exposure</span>
        <span>${profile?.anthropogenic_pressures?.human_footprint_score !== undefined ? profile.anthropogenic_pressures.human_footprint_score.toFixed(2) : 'N/A'}</span>
      </div>
      <div class="metric-row">
        <span>Invasive Alien Species Residual</span>
        <span>${profile?.anthropogenic_pressures?.invasive_species_residual !== undefined ? profile.anthropogenic_pressures.invasive_species_residual.toFixed(2) : 'N/A'}</span>
      </div>
    </div>
  </div>

  <!-- Local TreeSHAP Feature Attributions -->
  <div class="card" style="margin-bottom: 24px;">
    <h2>Top TreeSHAP Local Feature Explainability (Empirical Driver Attribution)</h2>
    <table>
      <thead>
        <tr>
          <th>Trait / Environmental Feature</th>
          <th style="text-align: right;">SHAP Contribution Value</th>
          <th>Biological Risk Vector</th>
        </tr>
      </thead>
      <tbody>
        ${shapRows || '<tr><td colspan="3">No SHAP attribution records available.</td></tr>'}
      </tbody>
    </table>
  </div>

  ${timeline && timeline.length > 0 ? `
  <!-- Multi-Year Future Risk Timeline -->
  <div class="card" style="margin-bottom: 24px;">
    <h2>Simulated Multi-Year Horizon Trajectory (2026 – 2070)</h2>
    <table>
      <thead>
        <tr>
          <th>Target Year</th>
          <th>Scenario Benchmark</th>
          <th>Predicted Risk Target</th>
          <th style="text-align: right;">Extinction Probability</th>
        </tr>
      </thead>
      <tbody>
        ${timelineRows}
      </tbody>
    </table>
  </div>
  ` : ''}

  ${scenarioResult ? `
  <!-- Specific Interactive What-If Simulation -->
  <div class="card" style="margin-bottom: 24px;">
    <h2>Evaluated What-If Environmental Stress Simulation</h2>
    <div class="metric-row">
      <span>Habitat Loss Lever</span>
      <span>${Math.round((scenarioParams?.habitat_loss ?? 0) * 100)}%</span>
    </div>
    <div class="metric-row">
      <span>Human Pressure Lever</span>
      <span>${Math.round((scenarioParams?.human_pressure ?? 0) * 100)}%</span>
    </div>
    <div class="metric-row">
      <span>Climate Warming Lever</span>
      <span>+${(scenarioParams?.climate_pressure ?? 0).toFixed(1)}°C</span>
    </div>
    <div class="metric-row">
      <span>Mitigation Effort</span>
      <span>${Math.round((scenarioParams?.conservation_effort ?? 0) * 100)}%</span>
    </div>
    <div class="metric-row" style="margin-top: 10px; font-weight: 700; color: #0284c7;">
      <span>Resulting Scenario Classification</span>
      <span>${scenarioResult.scenario_risk}</span>
    </div>
  </div>
  ` : ''}

  <!-- Targeted Action Recommendations -->
  <div class="card" style="margin-bottom: 24px;">
    <h2>Evidence-Based Conservation Recommendations</h2>
    ${recCards || '<div style="font-size: 12px; color: #64748b;">No action recommendations recorded.</div>'}
  </div>

  <div class="disclaimer-box">
    <strong>Methodological Notice & Scientific Transparency:</strong>
    Predictions, probability distributions, and TreeSHAP attributions are generated by a 500-Tree Tuned Random Forest Classifier trained on 30,711 verified terrestrial tetrapods. Centroid latitudes represent empirical dataset coordinates; longitudinal distributions on visual engines are for analytical visualization only. Scenario simulations reflect empirical what-if stress perturbations rather than deterministic longitudinal forecasts.
  </div>
</body>
</html>`;

    // Trigger instant download as clean HTML file
    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${speciesName}_Conservation_Intelligence_Report.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}
