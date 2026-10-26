/**
 * Wildlife Conservation Intelligence - UI Controller & DOM State Manager
 * Integrates 30,711 species search, TreeSHAP, Future Risk Timeline (2026-2070),
 * Scenario Simulation with Action Impact Breakdown, Species Comparison Mode,
 * Global Risk Explorer Layer, Downloadable Dossier Reports, and Demo Investigation Tour.
 */

import { EcoGuardAPI } from './api.js';
import { ReportGenerator } from './report_generator.js';

export class UIController {
  constructor(ecoGlobeInstance) {
    this.globe = ecoGlobeInstance;
    this.currentSpecies = "Polyplectron_schleiermacheri"; // Initial focal species
    this.currentTimeline = [];
    this.activeYear = 2026;

    // Retained intelligence cache for export and comparisons
    this.currentProfile = null;
    this.currentPrediction = null;
    this.currentPriority = null;
    this.currentRecommendations = null;
    this.currentImageData = null;
    this.currentScenarioResult = null;
    this.currentScenarioParams = null;

    // Demo Investigation Tour state
    this.demoSpeciesList = [
      { name: "Liocichla_steerii", class_name: "Aves", status: "Least Concern (LOW_RISK)", desc: "Empirical baseline with robust range resilience across montane broadleaf canopy." },
      { name: "Polyplectron_schleiermacheri", class_name: "Aves", status: "Endangered (THREATENED)", desc: "Bornean peacock-pheasant facing lowland Dipterocarp forest conversion." },
      { name: "Melogale_everetti", class_name: "Mammalia", status: "Endangered (THREATENED)", desc: "High-elevation montane endemic with restricted geographical range." },
      { name: "Raphus_cucullatus", class_name: "Aves", status: "Extinct (EXTINCT)", desc: "Historical flightless columbid endemic to Mauritius, lost to anthropogenic pressure." },
      { name: "Atelopus_chiriquiensis", class_name: "Amphibia", status: "Extinct (EXTINCT)", desc: "Panamanian harlequin toad severely impacted by chytridiomycosis epidemic." },
      { name: "Chelonoidis_niger", class_name: "Reptilia", status: "Extinct (EXTINCT)", desc: "Galápagos giant tortoise subspecies driven to extinction by historic overharvesting." }
    ];
    this.demoIndex = 0;
    this.isDemoPlaying = false;
    this.demoInterval = null;

    // Comparison Mode state
    this.compareSpeciesA = "Polyplectron_schleiermacheri";
    this.compareSpeciesB = "Raphus_cucullatus";
    this.compareDataA = null;
    this.compareDataB = null;

    this.initElements();
    this.bindEvents();
    this.loadInitialSpecies(this.currentSpecies);
    this.checkApiHealth();
  }

  initElements() {
    // Search elements
    this.searchInput = document.getElementById('species-search-input');
    this.searchDropdown = document.getElementById('search-dropdown');

    // Navigation action toolbar
    this.btnEmergencyScanner = document.getElementById('btn-emergency-scanner');
    this.btnOpenCompare = document.getElementById('btn-open-compare');
    this.btnToggleExplorer = document.getElementById('btn-toggle-explorer');
    this.textExplorerToggle = document.getElementById('text-explorer-toggle');
    this.btnDemoTour = document.getElementById('btn-demo-tour');
    this.btnExportReport = document.getElementById('btn-export-report');

    // AI Risk Fingerprint
    this.fingerprintInterpretationText = document.getElementById('fingerprint-interpretation-text');

    // Loading & Error elements
    this.loadingOverlay = document.getElementById('panel-loading-overlay');
    this.errorBanner = document.getElementById('panel-error-banner');
    this.errorMsg = document.getElementById('panel-error-msg');
    this.errorRetryBtn = document.getElementById('panel-error-retry');

    // Right panel elements
    this.sciNameEl = document.getElementById('panel-sci-name');
    this.commonTagEl = document.getElementById('panel-common-tag');
    this.coordsTextEl = document.getElementById('panel-coords-text');
    this.iucnBadgeEl = document.getElementById('panel-iucn-badge');
    this.predBadgeEl = document.getElementById('panel-pred-badge');
    this.panelTimelineBadge = document.getElementById('panel-timeline-badge');

    // Species verified image & silhouette card elements
    this.imageCard = document.getElementById('species-image-card');
    this.imageSkeleton = document.getElementById('species-image-skeleton');
    this.imageContainer = document.getElementById('species-image-container');
    this.speciesPhoto = document.getElementById('species-photo');
    this.imageSourceBadge = document.getElementById('image-source-badge');
    this.imageAuthorText = document.getElementById('image-author-text');
    this.imageLicenseLink = document.getElementById('image-license-link');
    this.silhouetteContainer = document.getElementById('species-silhouette-container');
    this.silhouetteIcon = document.getElementById('species-silhouette-icon');
    this.silhouetteClassName = document.getElementById('silhouette-class-name');
    this.silhouetteDesc = document.getElementById('silhouette-desc');

    // Probability meter
    this.probBarLow = document.getElementById('prob-bar-low');
    this.probBarThr = document.getElementById('prob-bar-thr');
    this.probBarExt = document.getElementById('prob-bar-ext');
    this.probValLow = document.getElementById('prob-val-low');
    this.probValThr = document.getElementById('prob-val-thr');
    this.probValExt = document.getElementById('prob-val-ext');

    // SHAP List
    this.shapContainer = document.getElementById('shap-list-container');

    // Priority & Recommendations
    this.cpsValueEl = document.getElementById('cps-score-value');
    this.cpsBarFill = document.getElementById('cps-bar-fill');
    this.recommendationsContainer = document.getElementById('recommendations-container');

    // Future Risk Timeline elements
    this.timelineWidget = document.getElementById('globe-timeline-widget');
    this.timelineButtonsContainer = document.getElementById('timeline-buttons-container');
    this.timelineDescEl = document.getElementById('timeline-scenario-desc');
    this.timelineSvgPath = document.getElementById('timeline-svg-path');
    this.timelineSvgDots = document.getElementById('timeline-svg-dots');

    // Bottom scenario controls & Action Impact Breakdown
    this.sliderHabitat = document.getElementById('slider-habitat');
    this.sliderHuman = document.getElementById('slider-human');
    this.sliderClimate = document.getElementById('slider-climate');
    this.sliderConservation = document.getElementById('slider-conservation');

    this.valHabitat = document.getElementById('val-habitat');
    this.valHuman = document.getElementById('val-human');
    this.valClimate = document.getElementById('val-climate');
    this.valConservation = document.getElementById('val-conservation');

    this.btnSimulate = document.getElementById('btn-run-simulation');
    this.apiStatusText = document.getElementById('api-status-text');
    this.apiStatusDot = document.getElementById('api-status-dot');

    this.impactTransitionBadge = document.getElementById('impact-transition-badge');
    this.pillHabitat = document.getElementById('pill-habitat');
    this.deltaHabitat = document.getElementById('delta-habitat');
    this.dirHabitat = document.getElementById('dir-habitat');
    this.pillHuman = document.getElementById('pill-human');
    this.deltaHuman = document.getElementById('delta-human');
    this.dirHuman = document.getElementById('dir-human');
    this.pillClimate = document.getElementById('pill-climate');
    this.deltaClimate = document.getElementById('delta-climate');
    this.dirClimate = document.getElementById('dir-climate');
    this.pillConservation = document.getElementById('pill-conservation');
    this.deltaConservation = document.getElementById('delta-conservation');
    this.dirConservation = document.getElementById('dir-conservation');

    // Collapsible Scenario Intelligence Drawer
    this.scenarioDrawerOverlay = document.getElementById('scenario-drawer-overlay');
    this.btnToggleScenarioDrawer = document.getElementById('btn-toggle-scenario-drawer');
    this.btnCloseScenarioDrawer = document.getElementById('btn-close-scenario-drawer');
    this.drawerToggleIcon = document.getElementById('drawer-toggle-icon');
    this.drawerToggleText = document.getElementById('drawer-toggle-text');
    this.drawerToggleBadge = document.getElementById('drawer-toggle-badge');

    // Global Risk Explorer HUD Legend
    this.explorerHudLegend = document.getElementById('explorer-hud-legend');
    this.btnCloseExplorerLegend = document.getElementById('btn-close-explorer-legend');

    // Demo Investigation Tour Widget
    this.demoTourWidget = document.getElementById('demo-tour-widget');
    this.demoTourStep = document.getElementById('demo-tour-step');
    this.demoTourSpeciesName = document.getElementById('demo-tour-species-name');
    this.demoTourDesc = document.getElementById('demo-tour-desc');
    this.btnDemoPrev = document.getElementById('btn-demo-prev');
    this.btnDemoPlay = document.getElementById('btn-demo-play');
    this.btnDemoNext = document.getElementById('btn-demo-next');
    this.btnCloseDemo = document.getElementById('btn-close-demo');

    // Comparison Mode Modal
    this.compareModal = document.getElementById('compare-modal');
    this.compareModalBackdrop = document.getElementById('compare-modal-backdrop');
    this.btnCloseCompare = document.getElementById('btn-close-compare');
    this.compareSearchA = document.getElementById('compare-search-a');
    this.compareDropdownA = document.getElementById('compare-dropdown-a');
    this.compareSearchB = document.getElementById('compare-search-b');
    this.compareDropdownB = document.getElementById('compare-dropdown-b');
    this.compareBody = document.getElementById('compare-body');

    // Conservation What-If Battle elements
    this.battleBaselineTarget = document.getElementById('battle-baseline-target');
    this.battleBaselineExtProb = document.getElementById('battle-baseline-ext-prob');
    this.battleBaseBarLow = document.getElementById('battle-base-bar-low');
    this.battleBaseBarThr = document.getElementById('battle-base-bar-thr');
    this.battleBaseBarExt = document.getElementById('battle-base-bar-ext');
    this.battleBaseLblLow = document.getElementById('battle-base-lbl-low');
    this.battleBaseLblThr = document.getElementById('battle-base-lbl-thr');
    this.battleBaseLblExt = document.getElementById('battle-base-lbl-ext');
    this.battleScenarioTag = document.getElementById('battle-scenario-tag');
    this.battleScenarioTarget = document.getElementById('battle-scenario-target');
    this.battleScenarioExtProb = document.getElementById('battle-scenario-ext-prob');
    this.battleScenBarLow = document.getElementById('battle-scen-bar-low');
    this.battleScenBarThr = document.getElementById('battle-scen-bar-thr');
    this.battleScenBarExt = document.getElementById('battle-scen-bar-ext');
    this.battleScenLblLow = document.getElementById('battle-scen-lbl-low');
    this.battleScenLblThr = document.getElementById('battle-scen-lbl-thr');
    this.battleScenLblExt = document.getElementById('battle-scen-lbl-ext');
    this.battleNetRiskShift = document.getElementById('battle-net-risk-shift');

    // Emergency Scanner Modal elements
    this.scannerModal = document.getElementById('emergency-scanner-modal');
    this.scannerModalBackdrop = document.getElementById('scanner-modal-backdrop');
    this.btnCloseScanner = document.getElementById('btn-close-scanner');
    this.tabScannerCritical = document.getElementById('tab-scanner-critical');
    this.tabScannerHigh = document.getElementById('tab-scanner-high');
    this.tabScannerStable = document.getElementById('tab-scanner-stable');
    this.badgeCountCritical = document.getElementById('badge-count-critical');
    this.badgeCountHigh = document.getElementById('badge-count-high');
    this.badgeCountStable = document.getElementById('badge-count-stable');
    this.scannerClassFilter = document.getElementById('scanner-class-filter');
    this.scannerSpeciesList = document.getElementById('scanner-species-list');

    // Strictly ensure Scenario Analysis drawer starts collapsed on initial load
    this.closeScenarioDrawer();
  }

  bindEvents() {
    // 1. Search Autocomplete with debounce across all 30,711 species
    let debounceTimer;
    this.searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();
      if (query.length < 2) {
        this.searchDropdown.classList.remove('active');
        return;
      }
      debounceTimer = setTimeout(async () => {
        const results = await EcoGuardAPI.autocompleteSpecies(query, 12);
        this.renderSearchResults(results);
      }, 200);
    });

    // Handle Enter keypress for exact search against 30,711 catalog
    this.searchInput.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.searchDropdown.classList.remove('active');
        await this.handleSearchSubmit(this.searchInput.value);
      }
    });

    // Close search dropdown on click outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-box')) {
        this.searchDropdown.classList.remove('active');
      }
    });

    // 2. Navigation Actions
    if (this.btnOpenCompare) {
      this.btnOpenCompare.addEventListener('click', () => {
        this.openComparisonModal();
      });
    }

    if (this.btnToggleExplorer) {
      this.btnToggleExplorer.addEventListener('click', () => {
        this.toggleGlobalRiskExplorer();
      });
    }

    if (this.btnCloseExplorerLegend) {
      this.btnCloseExplorerLegend.addEventListener('click', () => {
        if (this.explorerHudLegend) this.explorerHudLegend.classList.add('hidden');
      });
    }

    if (this.btnDemoTour) {
      this.btnDemoTour.addEventListener('click', () => {
        this.startDemoTour();
      });
    }

    if (this.btnCloseDemo) {
      this.btnCloseDemo.addEventListener('click', () => {
        this.stopDemoTour();
      });
    }

    if (this.btnDemoPrev) {
      this.btnDemoPrev.addEventListener('click', () => {
        this.prevDemoSpecies();
      });
    }

    if (this.btnDemoNext) {
      this.btnDemoNext.addEventListener('click', () => {
        this.nextDemoSpecies();
      });
    }

    if (this.btnDemoPlay) {
      this.btnDemoPlay.addEventListener('click', () => {
        this.toggleDemoPlay();
      });
    }

    // 3. Export Intelligence Report
    if (this.btnExportReport) {
      this.btnExportReport.addEventListener('click', () => {
        this.exportIntelligenceReport();
      });
    }

    // 4. Comparison Modal controls
    if (this.btnCloseCompare) {
      this.btnCloseCompare.addEventListener('click', () => {
        this.closeComparisonModal();
      });
    }
    if (this.compareModalBackdrop) {
      this.compareModalBackdrop.addEventListener('click', () => {
        this.closeComparisonModal();
      });
    }
    this.setupComparisonSearch();
    this.setupEmergencyScanner();

    // 5. Error retry button
    if (this.errorRetryBtn) {
      this.errorRetryBtn.addEventListener('click', () => {
        if (this.currentSpecies) {
          this.loadInitialSpecies(this.currentSpecies);
        } else if (this.searchInput.value.trim()) {
          this.handleSearchSubmit(this.searchInput.value.trim());
        } else {
          this.loadInitialSpecies("Polyplectron_schleiermacheri");
        }
      });
    }

    // 6. Future Risk Timeline Year Click Event Delegation
    if (this.timelineButtonsContainer) {
      this.timelineButtonsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.timeline-btn');
        if (btn && btn.dataset.year) {
          const year = parseInt(btn.dataset.year, 10);
          this.applyTimelineYear(year, true);
        }
      });
    }

    // 7. Bottom slider value displays and real-time Action Impact Breakdown
    this.sliderHabitat.addEventListener('input', (e) => {
      this.valHabitat.textContent = `${Math.round(e.target.value * 100)}%`;
      this.updateActionImpactBreakdown();
    });
    this.sliderHuman.addEventListener('input', (e) => {
      const v = Math.round(e.target.value * 100);
      this.valHuman.textContent = `${v >= 0 ? '+' : ''}${v}%`;
      this.updateActionImpactBreakdown();
    });
    this.sliderClimate.addEventListener('input', (e) => {
      this.valClimate.textContent = `+${parseFloat(e.target.value).toFixed(1)}°C`;
      this.updateActionImpactBreakdown();
    });
    this.sliderConservation.addEventListener('input', (e) => {
      this.valConservation.textContent = `${Math.round(e.target.value * 100)}%`;
      this.updateActionImpactBreakdown();
    });

    // Run Simulation Button
    this.btnSimulate.addEventListener('click', () => {
      this.runSimulation();
    });

    // Toggle Scenario Drawer (Collapsible overlay)
    if (this.btnToggleScenarioDrawer) {
      this.btnToggleScenarioDrawer.addEventListener('click', () => {
        this.toggleScenarioDrawer();
      });
    }
    if (this.btnCloseScenarioDrawer) {
      this.btnCloseScenarioDrawer.addEventListener('click', () => {
        this.closeScenarioDrawer();
      });
    }
  }

  toggleScenarioDrawer(forceState = null) {
    if (!this.scenarioDrawerOverlay) return;
    const isCurrentlyClosed = this.scenarioDrawerOverlay.classList.contains('collapsed') || this.scenarioDrawerOverlay.classList.contains('hidden');
    const shouldOpen = forceState !== null ? forceState : isCurrentlyClosed;

    if (shouldOpen) {
      this.scenarioDrawerOverlay.classList.remove('collapsed', 'hidden');
      if (this.btnToggleScenarioDrawer) this.btnToggleScenarioDrawer.classList.add('active');
      if (this.drawerToggleIcon) this.drawerToggleIcon.textContent = '▼';
    } else {
      this.scenarioDrawerOverlay.classList.add('collapsed', 'hidden');
      if (this.btnToggleScenarioDrawer) this.btnToggleScenarioDrawer.classList.remove('active');
      if (this.drawerToggleIcon) this.drawerToggleIcon.textContent = '▲';
    }
  }

  openScenarioDrawer() {
    this.toggleScenarioDrawer(true);
  }

  closeScenarioDrawer() {
    this.toggleScenarioDrawer(false);
  }

  async checkApiHealth() {
    const health = await EcoGuardAPI.checkHealth();
    if (health && health.status === "healthy") {
      this.apiStatusText.textContent = "API ONLINE (127.0.0.1:8000)";
      this.apiStatusDot.style.background = "#10b981";
      this.apiStatusDot.style.boxShadow = "0 0 10px #10b981";
    } else {
      this.apiStatusText.textContent = "STANDALONE READY";
      this.apiStatusDot.style.background = "#06b6d4";
    }
  }

  renderSearchResults(results) {
    if (!results || results.length === 0) {
      this.searchDropdown.innerHTML = '<div style="padding: 12px 16px; font-size: 12px; color: #64748b;">No matching species in the 30,711 catalog</div>';
      this.searchDropdown.classList.add('active');
      return;
    }

    this.searchDropdown.innerHTML = '';
    results.forEach((sp) => {
      const item = document.createElement('div');
      item.className = 'search-item';

      const badgeColor = sp.RiskTarget === 'EXTINCT' ? '#ef4444' : sp.RiskTarget === 'THREATENED' ? '#f59e0b' : '#10b981';
      const latText = typeof sp.Latitude === 'number' ? `Lat: ${sp.Latitude >= 0 ? '+' : ''}${sp.Latitude.toFixed(1)}°` : '';

      item.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 2px;">
          <span class="search-item-name">${sp.ScientificName.replace(/_/g, ' ')}</span>
          <span style="font-size: 10px; color: #64748b;">${sp.ClassName || ''} &bull; ${sp.RedlistCategory || ''} ${latText ? '&bull; ' + latText : ''}</span>
        </div>
        <span class="search-item-class" style="background: ${badgeColor}22; color: ${badgeColor}; border: 1px solid ${badgeColor}44;">${sp.RiskTarget || sp.ClassName}</span>
      `;

      item.addEventListener('click', () => {
        this.searchInput.value = sp.ScientificName.replace(/_/g, ' ');
        this.searchDropdown.classList.remove('active');
        this.selectSpecies(sp.ScientificName);
      });

      this.searchDropdown.appendChild(item);
    });

    this.searchDropdown.classList.add('active');
  }

  async handleSearchSubmit(query) {
    const trimmed = query.trim();
    if (!trimmed) return;

    if (this.loadingOverlay) this.loadingOverlay.classList.remove('hidden');
    if (this.errorBanner) this.errorBanner.classList.add('hidden');

    try {
      const results = await EcoGuardAPI.autocompleteSpecies(trimmed, 10);
      const normQuery = trimmed.toLowerCase().replace(/[\s\-]+/g, '_');

      let match = null;
      if (results && results.length > 0) {
        match = results.find(r => r.ScientificName.toLowerCase() === normQuery);
        if (!match) {
          match = results.find(r => r.ScientificName.toLowerCase().replace(/_/g, ' ') === trimmed.toLowerCase());
        }
        if (!match) {
          match = results[0];
        }
      }

      if (!match) {
        const directProfile = await EcoGuardAPI.getSpeciesProfile(trimmed);
        if (directProfile && directProfile.scientific_name) {
          match = { ScientificName: directProfile.scientific_name };
        }
      }

      if (match && match.ScientificName) {
        this.searchInput.value = match.ScientificName.replace(/_/g, ' ');
        await this.selectSpecies(match.ScientificName);
      } else {
        this.handleSpeciesNotFound(trimmed);
      }
    } catch (err) {
      this.handleSpeciesNotFound(trimmed);
    } finally {
      if (this.loadingOverlay) this.loadingOverlay.classList.add('hidden');
    }
  }

  resetSpeciesState(query = "") {
    this.currentSpecies = null;
    this.currentProfile = null;
    this.currentPrediction = null;
    this.currentPriority = null;
    this.currentRecommendations = null;
    this.currentTimeline = [];

    // 1. Clear 3D Globe active markers and latitude rings
    if (this.globe && typeof this.globe.clearActiveSpecies === 'function') {
      this.globe.clearActiveSpecies();
    }

    // 2. Reset species hero headers
    if (this.sciNameEl) {
      this.sciNameEl.textContent = query ? query.replace(/_/g, ' ') : "No Species Selected";
    }
    if (this.commonTagEl) {
      this.commonTagEl.textContent = query
        ? `Not present in 30,711-species catalog`
        : `Search the 30,711 tetrapod species catalog`;
    }
    if (this.coordsTextEl) {
      this.coordsTextEl.textContent = "Lat: --";
    }

    // 3. Reset badges
    if (this.iucnBadgeEl) {
      this.iucnBadgeEl.textContent = "UNCATALOGED";
      this.iucnBadgeEl.style.background = "rgba(100, 116, 139, 0.2)";
      this.iucnBadgeEl.style.color = "#94a3b8";
      this.iucnBadgeEl.style.borderColor = "rgba(100, 116, 139, 0.4)";
    }
    if (this.predBadgeEl) {
      this.predBadgeEl.textContent = "PRED: NONE";
      this.predBadgeEl.style.background = "rgba(100, 116, 139, 0.2)";
      this.predBadgeEl.style.color = "#94a3b8";
      this.predBadgeEl.style.borderColor = "rgba(100, 116, 139, 0.4)";
    }
    if (this.panelTimelineBadge) {
      this.panelTimelineBadge.textContent = "NO DATA";
      this.panelTimelineBadge.style.background = "rgba(100, 116, 139, 0.18)";
      this.panelTimelineBadge.style.color = "#94a3b8";
      this.panelTimelineBadge.style.borderColor = "rgba(100, 116, 139, 0.4)";
    }

    // 4. Reset Extinction Probability distribution
    if (this.probBarLow) this.probBarLow.style.width = "0%";
    if (this.probBarThr) this.probBarThr.style.width = "0%";
    if (this.probBarExt) this.probBarExt.style.width = "0%";
    if (this.probValLow) this.probValLow.textContent = "--";
    if (this.probValThr) this.probValThr.textContent = "--";
    if (this.probValExt) this.probValExt.textContent = "--";

    // 5. Reset TreeSHAP feature list and AI Risk Fingerprint
    if (this.shapContainer) {
      this.shapContainer.innerHTML = '<div style="color: #64748b; font-size: 11px; padding: 6px 0;">No SHAP explanation available (species not in catalog).</div>';
    }
    if (this.fingerprintInterpretationText) {
      this.fingerprintInterpretationText.textContent = "Select a species from the 30,711 catalog to evaluate model risk drivers.";
    }

    // 6. Reset Conservation Priority Score (CPS)
    if (this.cpsValueEl) this.cpsValueEl.textContent = "-- / 100";
    if (this.cpsBarFill) this.cpsBarFill.style.width = "0%";

    // 7. Reset Targeted Recommendations
    if (this.recommendationsContainer) {
      this.recommendationsContainer.innerHTML = '<div style="color: #64748b; font-size: 11px; padding: 6px 0;">Select a verified species from the catalog to view recommendations.</div>';
    }

    // 8. Reset Species Image and Silhouette
    if (this.imageSkeleton) this.imageSkeleton.classList.add('hidden');
    if (this.imageContainer) this.imageContainer.classList.add('hidden');
    if (this.speciesPhoto) this.speciesPhoto.src = "";
    if (this.silhouetteContainer) this.silhouetteContainer.classList.add('hidden');

    // 9. Reset Floating Timeline Chart & Description
    if (this.timelineSvgPath) this.timelineSvgPath.setAttribute('d', '');
    if (this.timelineSvgDots) this.timelineSvgDots.innerHTML = '';
    if (this.timelineDescEl) {
      this.timelineDescEl.textContent = "No active trajectory • Select a catalog species";
    }
    const buttons = this.timelineButtonsContainer?.querySelectorAll('.timeline-btn') || [];
    buttons.forEach(btn => btn.classList.remove('active'));

    // 10. Reset Sliders to 0 and Action Impact Breakdown
    if (this.sliderHabitat) this.sliderHabitat.value = 0;
    if (this.sliderHuman) this.sliderHuman.value = 0;
    if (this.sliderClimate) this.sliderClimate.value = 0;
    if (this.sliderConservation) this.sliderConservation.value = 0;
    if (this.valHabitat) this.valHabitat.textContent = "0%";
    if (this.valHuman) this.valHuman.textContent = "0%";
    if (this.valClimate) this.valClimate.textContent = "+0.0°C";
    if (this.valConservation) this.valConservation.textContent = "0%";

    this.updateActionImpactBreakdown();
    this.updateWhatIfBattle();

    // 11. Hide loading overlay
    if (this.loadingOverlay) this.loadingOverlay.classList.add('hidden');
  }

  handleSpeciesNotFound(query) {
    this.resetSpeciesState(query);

    if (this.errorBanner && this.errorMsg) {
      const displayQuery = query ? query.replace(/_/g, ' ') : "Specified species";
      this.errorMsg.textContent = `Species "${displayQuery}" is not present in the 30,711-species catalog.`;
      this.errorBanner.classList.remove('hidden');
    }
  }

  async selectSpecies(scientificName) {
    this.searchInput.value = scientificName.replace(/_/g, ' ');
    await this.loadInitialSpecies(scientificName);
  }

  async loadInitialSpecies(scientificName) {
    if (!scientificName) {
      this.resetSpeciesState();
      return;
    }

    if (this.errorBanner) this.errorBanner.classList.add('hidden');
    if (this.loadingOverlay) this.loadingOverlay.classList.remove('hidden');

    try {
      const profile = await EcoGuardAPI.getSpeciesProfile(scientificName);
      if (!profile || !profile.scientific_name) {
        this.handleSpeciesNotFound(scientificName);
        return;
      }

      this.currentSpecies = profile.scientific_name;
      this.currentProfile = profile;
      this.sciNameEl.textContent = profile.scientific_name.replace(/_/g, ' ');
      this.commonTagEl.textContent = "Querying 500-Tree Forest, TreeSHAP & Multi-Year Timeline...";

      this.loadSpeciesImage(profile.scientific_name, profile.taxonomy?.class);

      const [prediction, priority, recs, timelineData] = await Promise.all([
        EcoGuardAPI.predictExtinctionRisk(profile.scientific_name, 5),
        EcoGuardAPI.getPriorityScore(profile.scientific_name),
        EcoGuardAPI.getRecommendations(profile.scientific_name),
        EcoGuardAPI.getSpeciesTimeline(profile.scientific_name),
      ]);

      if (!prediction) {
        throw new Error(`ML model inference unavailable for catalog species "${profile.scientific_name.replace(/_/g, ' ')}".`);
      }

      this.currentPrediction = prediction;
      this.currentPriority = priority;
      this.currentRecommendations = recs;
      this.currentTimeline = timelineData?.timeline || [];

      // 1. Update Taxonomy Hero
      const taxonomy = profile.taxonomy;
      const commonDesc = taxonomy?.class ? `${taxonomy.class} • ${taxonomy.order || ''} • ${taxonomy.family || ''}` : "Tetrapod Vertebrate";
      this.commonTagEl.textContent = commonDesc;

      // 2. Update Real Latitude Tag
      const realLat = profile.geographical_traits?.latitude ?? 0.0;
      if (this.coordsTextEl) {
        const sign = realLat >= 0 ? '+' : '';
        this.coordsTextEl.textContent = `Lat: ${sign}${realLat.toFixed(2)}° (Dataset Centroid)`;
      }

      // 3. Update IUCN Red List Badge
      const redlist = prediction.original_redlist_category || profile.original_redlist_category || "Evaluated";
      this.iucnBadgeEl.textContent = redlist;
      this.updateStatusBadge(this.iucnBadgeEl, redlist);

      // 4. Update Conservation Priority Score
      const cps = priority ? priority.conservation_priority_score : 0.0;
      const cpsPct = (cps * 100).toFixed(1);
      this.cpsValueEl.textContent = `${cpsPct} / 100`;
      if (this.cpsBarFill) {
        this.cpsBarFill.style.width = `${Math.min(100, Math.max(0, cps * 100)).toFixed(1)}%`;
      }

      // 5. Update Tailored Recommendations
      this.renderRecommendations(recs);

      // 6. Synchronize with 3D Globe: Active beacon marker & glowing latitude parallel ring
      if (this.globe && typeof realLat === 'number') {
        this.globe.setActiveSpecies({
          scientific_name: profile.scientific_name,
          latitude: realLat,
          class_name: taxonomy?.class || "Tetrapod",
          redlist_category: redlist,
          risk_target: prediction.predicted_risk_target,
          rangesize: profile.geographical_traits?.rangesize_km2 || 0,
        });
      }

      // 7. Render Future Risk Timeline Trajectory & Apply 2026 Baseline
      if (this.currentTimeline.length > 0) {
        this.renderTimelineChart(this.currentTimeline);
        this.applyTimelineYear(2026, false);
      } else {
        const predTarget = prediction.predicted_risk_target || "LOW_RISK";
        this.predBadgeEl.textContent = `PRED: ${predTarget}`;
        this.updateStatusBadge(this.predBadgeEl, predTarget);

        const probs = prediction.prediction_probabilities || { LOW_RISK: 0, THREATENED: 0, EXTINCT: 0 };
        const pLow = ((probs.LOW_RISK ?? 0) * 100).toFixed(1);
        const pThr = ((probs.THREATENED ?? 0) * 100).toFixed(1);
        const pExt = ((probs.EXTINCT ?? 0) * 100).toFixed(1);

        this.probBarLow.style.width = `${pLow}%`;
        this.probBarThr.style.width = `${pThr}%`;
        this.probBarExt.style.width = `${pExt}%`;

        this.probValLow.textContent = `${pLow}%`;
        this.probValThr.textContent = `${pThr}%`;
        this.probValExt.textContent = `${pExt}%`;

        if (prediction.top_contributing_features) {
          this.renderShapContributors(prediction.top_contributing_features);
        }
      }

      this.updateActionImpactBreakdown();

    } catch (err) {
      console.error("Failed to load species profile:", err);
      this.resetSpeciesState(scientificName);
      if (this.errorBanner && this.errorMsg) {
        let msg = err.message || "Failed to load conservation intelligence.";
        msg = msg.replace(/EcoGuard\s*(AI)?/gi, "Wildlife Conservation Intelligence");
        this.errorMsg.textContent = msg;
        this.errorBanner.classList.remove('hidden');
      }
    } finally {
      if (this.loadingOverlay) {
        this.loadingOverlay.classList.add('hidden');
      }
    }
  }

  // =========================================================================
  // Action Impact Breakdown (Scenario Simulator)
  // =========================================================================

  updateActionImpactBreakdown(simResult = null) {
    const habitatVal = parseFloat(this.sliderHabitat?.value || 0);
    const humanVal = parseFloat(this.sliderHuman?.value || 0);
    const climateVal = parseFloat(this.sliderClimate?.value || 0);
    const conservationVal = parseFloat(this.sliderConservation?.value || 0);

    const isModified = (habitatVal !== 0 || humanVal !== 0 || climateVal !== 0 || conservationVal !== 0);
    const hasRunResult = !!(simResult && simResult.scenario_probabilities);

    // Habitat Loss Pill
    if (this.deltaHabitat) {
      this.deltaHabitat.textContent = `${Math.round(habitatVal * 100)}%`;
    }
    if (this.dirHabitat) {
      if (habitatVal > 0) {
        this.dirHabitat.textContent = hasRunResult ? "▲ Threat Escalation" : "▲ Pending: Escalation";
        this.pillHabitat?.classList.add(hasRunResult ? 'escalate' : 'pending-escalate');
        this.pillHabitat?.classList.remove('mitigate', 'pending-mitigate');
      } else {
        this.dirHabitat.textContent = "0% Baseline";
        this.pillHabitat?.classList.remove('escalate', 'mitigate', 'pending-escalate', 'pending-mitigate');
      }
    }

    // Human Pressure Pill
    if (this.deltaHuman) {
      this.deltaHuman.textContent = `${humanVal >= 0 ? '+' : ''}${Math.round(humanVal * 100)}%`;
    }
    if (this.dirHuman) {
      if (humanVal > 0) {
        this.dirHuman.textContent = hasRunResult ? "▲ Encroachment" : "▲ Pending: Encroachment";
        this.pillHuman?.classList.add(hasRunResult ? 'escalate' : 'pending-escalate');
        this.pillHuman?.classList.remove('mitigate', 'pending-mitigate');
      } else if (humanVal < 0) {
        this.dirHuman.textContent = hasRunResult ? "▼ De-escalation" : "▼ Pending: De-escalation";
        this.pillHuman?.classList.add(hasRunResult ? 'mitigate' : 'pending-mitigate');
        this.pillHuman?.classList.remove('escalate', 'pending-escalate');
      } else {
        this.dirHuman.textContent = "0% Baseline";
        this.pillHuman?.classList.remove('escalate', 'mitigate', 'pending-escalate', 'pending-mitigate');
      }
    }

    // Climate Warming Pill
    if (this.deltaClimate) {
      this.deltaClimate.textContent = `+${climateVal.toFixed(1)}°C`;
    }
    if (this.dirClimate) {
      if (climateVal > 0) {
        this.dirClimate.textContent = hasRunResult ? "▲ Thermal Stress" : "▲ Pending: Thermal Stress";
        this.pillClimate?.classList.add(hasRunResult ? 'escalate' : 'pending-escalate');
        this.pillClimate?.classList.remove('mitigate', 'pending-mitigate');
      } else {
        this.dirClimate.textContent = "0.0°C Baseline";
        this.pillClimate?.classList.remove('escalate', 'mitigate', 'pending-escalate', 'pending-mitigate');
      }
    }

    // Conservation Effort Pill
    if (this.deltaConservation) {
      this.deltaConservation.textContent = `${Math.round(conservationVal * 100)}%`;
    }
    if (this.dirConservation) {
      if (conservationVal > 0) {
        this.dirConservation.textContent = hasRunResult ? "▼ Active Mitigation" : "▼ Pending: Mitigation";
        this.pillConservation?.classList.add(hasRunResult ? 'mitigate' : 'pending-mitigate');
        this.pillConservation?.classList.remove('escalate', 'pending-escalate');
      } else {
        this.dirConservation.textContent = "0% Baseline";
        this.pillConservation?.classList.remove('escalate', 'mitigate', 'pending-escalate', 'pending-mitigate');
      }
    }

    // Transition summary badge
    if (this.impactTransitionBadge) {
      const baselineTarget = this.currentPrediction?.predicted_risk_target || 'N/A';
      const baselineExt = this.currentPrediction?.prediction_probabilities?.EXTINCT;
      const baseExtPct = baselineExt !== undefined ? `${(baselineExt * 100).toFixed(1)}%` : '--';

      if (hasRunResult) {
        this.impactTransitionBadge.classList.remove('pending');
        const scenarioTarget = simResult.scenario_risk;
        const scenExt = simResult.scenario_probabilities.EXTINCT;
        const scenExtPct = `${(scenExt * 100).toFixed(1)}%`;
        const diff = baselineExt !== undefined ? ((scenExt - baselineExt) * 100).toFixed(1) : 0;
        const diffSign = diff >= 0 ? `+${diff}%` : `${diff}%`;

        this.impactTransitionBadge.textContent = `Baseline: ${baselineTarget} (${baseExtPct}) ➔ Scenario: ${scenarioTarget} (${scenExtPct}) [Δ: ${diffSign}]`;
      } else if (isModified) {
        this.impactTransitionBadge.classList.add('pending');
        this.impactTransitionBadge.textContent = `[Pending Scenario — Click "Run Scenario" to simulate changes]`;
      } else {
        this.impactTransitionBadge.classList.remove('pending');
        this.impactTransitionBadge.textContent = `Baseline: ${baselineTarget} (${baseExtPct}) ➔ Adjust levers & click Run Scenario`;
      }
    }

    // Synchronize drawer toggle badge
    if (this.drawerToggleBadge) {
      if (hasRunResult) {
        this.drawerToggleBadge.classList.remove('hidden');
        this.drawerToggleBadge.textContent = 'ACTIVE';
        this.drawerToggleBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        this.drawerToggleBadge.style.color = '#34d399';
        this.drawerToggleBadge.style.background = 'rgba(16, 185, 129, 0.2)';
      } else if (isModified) {
        this.drawerToggleBadge.classList.remove('hidden');
        this.drawerToggleBadge.textContent = 'PENDING';
        this.drawerToggleBadge.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        this.drawerToggleBadge.style.color = '#fbbf24';
        this.drawerToggleBadge.style.background = 'rgba(245, 158, 11, 0.2)';
      } else {
        this.drawerToggleBadge.classList.add('hidden');
      }
    }

    // Synchronize Conservation What-If Battle view
    this.updateWhatIfBattle(simResult);
  }

  // =========================================================================
  // Conservation What-If Battle (Side-by-Side Trajectory Comparison)
  // =========================================================================

  updateWhatIfBattle(simResult = null) {
    if (!this.battleBaselineTarget) return;

    const basePred = this.currentPrediction?.predicted_risk_target || 'THREATENED';
    const baseProbs = this.currentPrediction?.prediction_probabilities || { LOW_RISK: 0.38, THREATENED: 0.544, EXTINCT: 0.076 };
    const baseExt = (baseProbs.EXTINCT * 100).toFixed(1);
    const baseThr = (baseProbs.THREATENED * 100).toFixed(1);
    const baseLow = (baseProbs.LOW_RISK * 100).toFixed(1);

    this.battleBaselineTarget.textContent = basePred;
    this.updateStatusBadge(this.battleBaselineTarget, basePred);
    if (this.battleBaselineExtProb) this.battleBaselineExtProb.textContent = `${baseExt}%`;
    if (this.battleBaseBarLow) this.battleBaseBarLow.style.width = `${baseLow}%`;
    if (this.battleBaseBarThr) this.battleBaseBarThr.style.width = `${baseThr}%`;
    if (this.battleBaseBarExt) this.battleBaseBarExt.style.width = `${baseExt}%`;
    if (this.battleBaseLblLow) this.battleBaseLblLow.textContent = `Low: ${baseLow}%`;
    if (this.battleBaseLblThr) this.battleBaseLblThr.textContent = `Thr: ${baseThr}%`;
    if (this.battleBaseLblExt) this.battleBaseLblExt.textContent = `Ext: ${baseExt}%`;

    if (simResult && simResult.scenario_probabilities) {
      const sp = simResult.scenario_probabilities;
      const scenExt = (sp.EXTINCT * 100).toFixed(1);
      const scenThr = (sp.THREATENED * 100).toFixed(1);
      const scenLow = (sp.LOW_RISK * 100).toFixed(1);

      if (this.battleScenarioTag) {
        this.battleScenarioTag.textContent = 'SIMULATED SCENARIO';
      }
      if (this.battleScenarioTarget) {
        this.battleScenarioTarget.textContent = simResult.scenario_risk;
        this.updateStatusBadge(this.battleScenarioTarget, simResult.scenario_risk);
      }
      if (this.battleScenarioExtProb) this.battleScenarioExtProb.textContent = `${scenExt}%`;
      if (this.battleScenBarLow) this.battleScenBarLow.style.width = `${scenLow}%`;
      if (this.battleScenBarThr) this.battleScenBarThr.style.width = `${scenThr}%`;
      if (this.battleScenBarExt) this.battleScenBarExt.style.width = `${scenExt}%`;
      if (this.battleScenLblLow) this.battleScenLblLow.textContent = `Low: ${scenLow}%`;
      if (this.battleScenLblThr) this.battleScenLblThr.textContent = `Thr: ${scenThr}%`;
      if (this.battleScenLblExt) this.battleScenLblExt.textContent = `Ext: ${scenExt}%`;

      if (this.battleNetRiskShift) {
        const shift = (parseFloat(scenExt) - parseFloat(baseExt)).toFixed(1);
        if (parseFloat(shift) < 0) {
          this.battleNetRiskShift.textContent = `${shift}% Risk Reduction`;
          this.battleNetRiskShift.className = 'battle-shift-tag mitigate';
        } else if (parseFloat(shift) > 0) {
          this.battleNetRiskShift.textContent = `+${shift}% Risk Escalation`;
          this.battleNetRiskShift.className = 'battle-shift-tag escalate';
        } else {
          this.battleNetRiskShift.textContent = `No Net Shift`;
          this.battleNetRiskShift.className = 'battle-shift-tag neutral';
        }
      }
    } else {
      if (this.battleScenarioTarget) {
        this.battleScenarioTarget.textContent = 'AWAITING RUN';
        this.battleScenarioTarget.style.color = '#94a3b8';
      }
      if (this.battleScenarioExtProb) this.battleScenarioExtProb.textContent = '--';
      if (this.battleScenBarLow) this.battleScenBarLow.style.width = '0%';
      if (this.battleScenBarThr) this.battleScenBarThr.style.width = '0%';
      if (this.battleScenBarExt) this.battleScenBarExt.style.width = '0%';
      if (this.battleScenLblLow) this.battleScenLblLow.textContent = 'Low: --';
      if (this.battleScenLblThr) this.battleScenLblThr.textContent = 'Thr: --';
      if (this.battleScenLblExt) this.battleScenLblExt.textContent = 'Ext: --';
      if (this.battleNetRiskShift) {
        this.battleNetRiskShift.textContent = 'Awaiting Run';
        this.battleNetRiskShift.className = 'battle-shift-tag neutral';
      }
    }
  }

  // =========================================================================
  // AI Risk Fingerprint: Intervention-Oriented Feature Interpretation
  // =========================================================================

  renderFingerprintInterpretation(features) {
    if (!this.fingerprintInterpretationText) return;

    if (!features || features.length === 0) {
      this.fingerprintInterpretationText.textContent = "No local SHAP attributions available for this specimen.";
      return;
    }

    // Find top positive risk contributor (direction === 'increases_risk' or shap_value > 0)
    const riskDrivers = features.filter(f => (f.direction === 'increases_risk' || f.shap_value > 0));
    const topDriver = riskDrivers.length > 0 ? riskDrivers[0] : features[0];
    const featName = topDriver.feature || '';
    const shapVal = Math.abs(topDriver.shap_value || 0).toFixed(3);

    let interpretation = "";
    if (featName.includes("Human") || featName.includes("FootPrint")) {
      interpretation = `Primary model vulnerability association is elevated anthropogenic infrastructure pressure (+${shapVal} SHAP). Intervention focus: Strengthen protected area buffer enforcement, restrict linear road encroachment, and develop community co-management zones.`;
    } else if (featName.includes("Range") || featName.includes("size")) {
      interpretation = `Primary model vulnerability association is geographical range restriction (+${shapVal} SHAP). Intervention focus: Prioritize micro-reserve establishment, legal land acquisition, and biological movement corridors to safeguard localized populations.`;
    } else if (featName.includes("Invasive")) {
      interpretation = `Primary model vulnerability association is invasive competitor and predator stress (+${shapVal} SHAP). Intervention focus: Implement systematic island/reserve biosecurity quarantines and targeted invasive alien species eradication.`;
    } else if (featName.includes("Temp") || featName.includes("Precip") || featName.includes("Climate")) {
      interpretation = `Primary model vulnerability association is bioclimatic envelope sensitivity (+${shapVal} SHAP). Intervention focus: Identify and protect microclimate thermal refugia, retain old-growth canopy cover, and enable altitudinal migration paths.`;
    } else if (featName.includes("MajorHabitat") || featName.includes("Habitat")) {
      interpretation = `Primary model vulnerability association is ecological habitat specialization (+${shapVal} SHAP). Intervention focus: Preserve intact ecotones across habitat mosaics and prevent contiguous forest canopy fragmentation.`;
    } else if (featName.includes("BodyMass")) {
      interpretation = `Primary model vulnerability association is large body mass (+${shapVal} SHAP), indicating trophic sensitivity. Intervention focus: Enforce anti-poaching field patrols, maintain wide contiguous foraging ranges, and reduce human-wildlife conflict.`;
    } else {
      interpretation = `Primary model vulnerability association is linked to ${featName.replace(/_/g, ' ')} (+${shapVal} SHAP). Intervention focus: Targeted ecological monitoring, habitat integrity protection, and population census validation.`;
    }

    this.fingerprintInterpretationText.textContent = interpretation;
  }

  // =========================================================================
  // Conservation Emergency Scanner Manager
  // =========================================================================

  setupEmergencyScanner() {
    this.currentScannerTier = 'critical';
    this.currentScannerClass = null;

    if (this.btnEmergencyScanner) {
      this.btnEmergencyScanner.addEventListener('click', () => {
        this.openEmergencyScanner();
      });
    }

    if (this.btnCloseScanner) {
      this.btnCloseScanner.addEventListener('click', () => {
        this.closeEmergencyScanner();
      });
    }

    if (this.scannerModalBackdrop) {
      this.scannerModalBackdrop.addEventListener('click', () => {
        this.closeEmergencyScanner();
      });
    }

    const tabs = [
      { btn: this.tabScannerCritical, tier: 'critical' },
      { btn: this.tabScannerHigh, tier: 'high_priority' },
      { btn: this.tabScannerStable, tier: 'stable' },
    ];

    tabs.forEach(({ btn, tier }) => {
      if (btn) {
        btn.addEventListener('click', () => {
          tabs.forEach(t => t.btn?.classList.remove('active'));
          btn.classList.add('active');
          this.currentScannerTier = tier;
          this.renderScannerList();
        });
      }
    });

    if (this.scannerClassFilter) {
      this.scannerClassFilter.addEventListener('change', (e) => {
        this.currentScannerClass = e.target.value || null;
        this.fetchEmergencyScannerData();
      });
    }
  }

  async openEmergencyScanner() {
    if (this.scannerModal) {
      this.scannerModal.classList.remove('hidden');
    }
    await this.fetchEmergencyScannerData();
  }

  closeEmergencyScanner() {
    if (this.scannerModal) {
      this.scannerModal.classList.add('hidden');
    }
  }

  async fetchEmergencyScannerData() {
    if (this.scannerSpeciesList) {
      this.scannerSpeciesList.innerHTML = `
        <div class="scanner-loading-state">
          <div class="scanner-spinner"></div>
          <span>Scanning global catalog across priority tiers...</span>
        </div>
      `;
    }

    const data = await EcoGuardAPI.getEmergencyScannerData(20, this.currentScannerClass);
    if (!data || !data.tiers) {
      if (this.scannerSpeciesList) {
        this.scannerSpeciesList.innerHTML = `<div style="color: #f87171; text-align: center; padding: 24px;">Failed to scan catalog species.</div>`;
      }
      return;
    }

    this.scannerData = data.tiers;

    if (this.badgeCountCritical) {
      this.badgeCountCritical.textContent = (data.tiers.critical || []).length;
    }
    if (this.badgeCountHigh) {
      this.badgeCountHigh.textContent = (data.tiers.high_priority || []).length;
    }
    if (this.badgeCountStable) {
      this.badgeCountStable.textContent = (data.tiers.stable || []).length;
    }

    this.renderScannerList();
  }

  renderScannerList() {
    if (!this.scannerSpeciesList || !this.scannerData) return;

    const list = this.scannerData[this.currentScannerTier] || [];
    if (list.length === 0) {
      this.scannerSpeciesList.innerHTML = `<div style="color: #94a3b8; text-align: center; padding: 24px;">No species found matching the current filter.</div>`;
      return;
    }

    this.scannerSpeciesList.innerHTML = '';
    list.forEach((sp) => {
      const row = document.createElement('div');
      row.className = 'scanner-row';

      const sciName = sp.scientific_name.replace(/_/g, ' ');
      const redlist = sp.redlist_category || 'Evaluated';
      const className = sp.class_name || 'Tetrapod';
      const lat = typeof sp.latitude === 'number' ? `${sp.latitude >= 0 ? '+' : ''}${sp.latitude.toFixed(2)}°` : '0.0°';
      const cpsScore = sp.conservation_priority_score ? (sp.conservation_priority_score * 100).toFixed(1) : 'N/A';

      const tierClass = this.currentScannerTier === 'critical' ? 'critical' :
                        this.currentScannerTier === 'high_priority' ? 'high' : 'stable';

      row.innerHTML = `
        <div class="scanner-row-left">
          <div class="scanner-row-name">${sciName}</div>
          <div class="scanner-row-sub">${className} &bull; ${redlist} &bull; Lat: ${lat}</div>
        </div>
        <div class="scanner-row-right">
          <span class="scanner-cps-pill ${tierClass}">CPS: ${cpsScore}</span>
          <button class="scanner-inspect-btn">Inspect &rarr;</button>
        </div>
      `;

      row.addEventListener('click', () => {
        this.closeEmergencyScanner();
        this.selectSpecies(sp.scientific_name);
      });

      this.scannerSpeciesList.appendChild(row);
    });
  }

  // =========================================================================
  // Global Risk Explorer Layer
  // =========================================================================

  toggleGlobalRiskExplorer() {
    if (!this.globe) return;
    const currentState = this.globe.isGlobalRiskExplorerActive;
    const newState = !currentState;
    this.globe.setGlobalRiskExplorerVisible(newState);

    if (this.btnToggleExplorer) {
      if (newState) {
        this.btnToggleExplorer.classList.add('active');
        if (this.textExplorerToggle) this.textExplorerToggle.textContent = 'Hide Explorer';
      } else {
        this.btnToggleExplorer.classList.remove('active');
        if (this.textExplorerToggle) this.textExplorerToggle.textContent = 'Risk Explorer';
      }
    }

    if (this.explorerHudLegend) {
      if (newState) {
        this.explorerHudLegend.classList.remove('hidden');
      } else {
        this.explorerHudLegend.classList.add('hidden');
      }
    }
  }

  // =========================================================================
  // Demo Investigation Tour
  // =========================================================================

  startDemoTour() {
    this.demoIndex = 0;
    this.isDemoPlaying = true;
    if (this.demoTourWidget) this.demoTourWidget.classList.remove('hidden');
    if (this.btnDemoTour) this.btnDemoTour.classList.add('active');
    this.loadDemoSpecies(this.demoIndex);

    // Auto advance every 8 seconds
    if (this.demoInterval) clearInterval(this.demoInterval);
    this.demoInterval = setInterval(() => {
      if (this.isDemoPlaying) {
        this.nextDemoSpecies();
      }
    }, 8000);
  }

  stopDemoTour() {
    this.isDemoPlaying = false;
    if (this.demoInterval) {
      clearInterval(this.demoInterval);
      this.demoInterval = null;
    }
    if (this.demoTourWidget) this.demoTourWidget.classList.add('hidden');
    if (this.btnDemoTour) this.btnDemoTour.classList.remove('active');
  }

  toggleDemoPlay() {
    this.isDemoPlaying = !this.isDemoPlaying;
    if (this.btnDemoPlay) {
      this.btnDemoPlay.textContent = this.isDemoPlaying ? '⏸ Pause' : '▶ Resume';
    }
  }

  nextDemoSpecies() {
    this.demoIndex = (this.demoIndex + 1) % this.demoSpeciesList.length;
    this.loadDemoSpecies(this.demoIndex);
  }

  prevDemoSpecies() {
    this.demoIndex = (this.demoIndex - 1 + this.demoSpeciesList.length) % this.demoSpeciesList.length;
    this.loadDemoSpecies(this.demoIndex);
  }

  loadDemoSpecies(index) {
    const item = this.demoSpeciesList[index];
    if (!item) return;

    if (this.demoTourStep) {
      this.demoTourStep.textContent = `Species ${index + 1} of ${this.demoSpeciesList.length}`;
    }
    if (this.demoTourSpeciesName) {
      this.demoTourSpeciesName.textContent = item.name.replace(/_/g, ' ');
    }
    if (this.demoTourDesc) {
      this.demoTourDesc.textContent = `${item.class_name} • ${item.status}`;
    }

    this.selectSpecies(item.name);
  }

  // =========================================================================
  // Downloadable Species Intelligence Report
  // =========================================================================

  exportIntelligenceReport() {
    if (!this.currentSpecies || !this.currentProfile) {
      alert("Please select a verified species from the catalog before generating a report.");
      return;
    }

    ReportGenerator.generateReport({
      speciesName: this.currentSpecies,
      taxonomy: this.currentProfile.taxonomy,
      profile: this.currentProfile,
      prediction: this.currentPrediction,
      priority: this.currentPriority,
      recommendations: this.currentRecommendations,
      timeline: this.currentTimeline,
      scenarioResult: this.currentScenarioResult,
      scenarioParams: this.currentScenarioParams,
      imageData: this.currentImageData,
    });
  }

  // =========================================================================
  // Species Comparison Mode
  // =========================================================================

  openComparisonModal() {
    if (this.compareModal) {
      this.compareModal.classList.remove('hidden');
    }
    if (this.currentSpecies) {
      this.compareSpeciesA = this.currentSpecies;
      if (this.compareSearchA) {
        this.compareSearchA.value = this.currentSpecies.replace(/_/g, ' ');
      }
    }
    if (!this.compareSpeciesB) {
      this.compareSpeciesB = "Raphus_cucullatus";
    }
    if (this.compareSearchB) {
      this.compareSearchB.value = this.compareSpeciesB.replace(/_/g, ' ');
    }

    this.executeComparison();
  }

  closeComparisonModal() {
    if (this.compareModal) {
      this.compareModal.classList.add('hidden');
    }
  }

  setupComparisonSearch() {
    // Autocomplete for Species A
    let timerA;
    if (this.compareSearchA) {
      this.compareSearchA.addEventListener('input', (e) => {
        clearTimeout(timerA);
        const query = e.target.value.trim();
        if (query.length < 2) {
          if (this.compareDropdownA) this.compareDropdownA.classList.remove('active');
          return;
        }
        timerA = setTimeout(async () => {
          const results = await EcoGuardAPI.autocompleteSpecies(query, 8);
          this.renderCompareDropdown(results, this.compareDropdownA, (selected) => {
            this.compareSpeciesA = selected;
            this.compareSearchA.value = selected.replace(/_/g, ' ');
            this.executeComparison();
          });
        }, 200);
      });
    }

    // Autocomplete for Species B
    let timerB;
    if (this.compareSearchB) {
      this.compareSearchB.addEventListener('input', (e) => {
        clearTimeout(timerB);
        const query = e.target.value.trim();
        if (query.length < 2) {
          if (this.compareDropdownB) this.compareDropdownB.classList.remove('active');
          return;
        }
        timerB = setTimeout(async () => {
          const results = await EcoGuardAPI.autocompleteSpecies(query, 8);
          this.renderCompareDropdown(results, this.compareDropdownB, (selected) => {
            this.compareSpeciesB = selected;
            this.compareSearchB.value = selected.replace(/_/g, ' ');
            this.executeComparison();
          });
        }, 200);
      });
    }
  }

  renderCompareDropdown(results, dropdownEl, onSelect) {
    if (!dropdownEl) return;
    if (!results || results.length === 0) {
      dropdownEl.innerHTML = '<div style="padding: 10px 14px; font-size: 11.5px; color: #64748b;">No matching species in catalog</div>';
      dropdownEl.classList.add('active');
      return;
    }

    dropdownEl.innerHTML = '';
    results.forEach((sp) => {
      const item = document.createElement('div');
      item.className = 'search-item';
      item.innerHTML = `
        <span class="search-item-name">${sp.ScientificName.replace(/_/g, ' ')}</span>
        <span style="font-size: 10px; color: #64748b;">${sp.ClassName || ''} &bull; ${sp.RedlistCategory || ''}</span>
      `;
      item.addEventListener('click', () => {
        dropdownEl.classList.remove('active');
        onSelect(sp.ScientificName);
      });
      dropdownEl.appendChild(item);
    });
    dropdownEl.classList.add('active');
  }

  async executeComparison() {
    if (!this.compareSpeciesA || !this.compareSpeciesB || !this.compareBody) return;

    this.compareBody.innerHTML = '<div style="text-align: center; padding: 40px; color: #38bdf8;">Retrieving empirical features, 500-Tree inferences &amp; SHAP profiles from catalog...</div>';

    try {
      const [profA, predA, prioA, profB, predB, prioB] = await Promise.all([
        EcoGuardAPI.getSpeciesProfile(this.compareSpeciesA),
        EcoGuardAPI.predictExtinctionRisk(this.compareSpeciesA, 5),
        EcoGuardAPI.getPriorityScore(this.compareSpeciesA),
        EcoGuardAPI.getSpeciesProfile(this.compareSpeciesB),
        EcoGuardAPI.predictExtinctionRisk(this.compareSpeciesB, 5),
        EcoGuardAPI.getPriorityScore(this.compareSpeciesB),
      ]);

      if (!profA || !profB || !predA || !predB) {
        this.compareBody.innerHTML = '<div style="text-align: center; padding: 30px; color: #f87171;">Failed to load empirical data for one or both comparative taxa. Ensure both species exist in the 30,711 catalog.</div>';
        return;
      }

      this.renderComparisonView(profA, predA, prioA, profB, predB, prioB);
    } catch (err) {
      this.compareBody.innerHTML = `<div style="text-align: center; padding: 30px; color: #f87171;">Comparison error: ${err.message}</div>`;
    }
  }

  renderComparisonView(profA, predA, prioA, profB, predB, prioB) {
    const targetA = predA.predicted_risk_target;
    const targetB = predB.predicted_risk_target;
    const colorA = targetA === 'EXTINCT' ? '#ef4444' : targetA === 'THREATENED' ? '#f59e0b' : '#10b981';
    const colorB = targetB === 'EXTINCT' ? '#ef4444' : targetB === 'THREATENED' ? '#f59e0b' : '#10b981';

    const probsA = predA.prediction_probabilities;
    const probsB = predB.prediction_probabilities;

    const latA = profA.geographical_traits?.latitude ?? 0;
    const latB = profB.geographical_traits?.latitude ?? 0;
    const rangeA = profA.geographical_traits?.rangesize_km2 ?? 0;
    const rangeB = profB.geographical_traits?.rangesize_km2 ?? 0;
    const footA = profA.anthropogenic_pressures?.human_footprint_score ?? 0;
    const footB = profB.anthropogenic_pressures?.human_footprint_score ?? 0;
    const massA = profA.ecological_traits?.body_mass_g ?? 0;
    const massB = profB.ecological_traits?.body_mass_g ?? 0;
    const elevA = profA.geographical_traits?.elevation_m ?? 0;
    const elevB = profB.geographical_traits?.elevation_m ?? 0;

    const cpsA = prioA?.conservation_priority_score ? (prioA.conservation_priority_score * 100).toFixed(1) : 'N/A';
    const cpsB = prioB?.conservation_priority_score ? (prioB.conservation_priority_score * 100).toFixed(1) : 'N/A';

    this.compareBody.innerHTML = `
      <div class="compare-grid-cards">
        <!-- Species A Card -->
        <div class="compare-card">
          <div class="compare-card-title">
            <div>
              <div class="compare-sci-name">${profA.scientific_name.replace(/_/g, ' ')}</div>
              <div class="compare-tax-sub">${profA.taxonomy?.class || 'Tetrapod'} &bull; ${profA.taxonomy?.order || ''} &bull; ${profA.taxonomy?.family || ''}</div>
            </div>
            <span style="background: ${colorA}22; color: ${colorA}; border: 1px solid ${colorA}55; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px;">${targetA}</span>
          </div>
          <div>
            <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Extinction Probabilities:</div>
            <div class="prob-meter">
              <div class="prob-bars">
                <div style="width: ${(probsA.LOW_RISK * 100).toFixed(1)}%; background: #10b981; height: 100%;"></div>
                <div style="width: ${(probsA.THREATENED * 100).toFixed(1)}%; background: #f59e0b; height: 100%;"></div>
                <div style="width: ${(probsA.EXTINCT * 100).toFixed(1)}%; background: #ef4444; height: 100%;"></div>
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; font-family: var(--font-mono); margin-top: 4px;">
              <span style="color: #10b981;">Low: ${(probsA.LOW_RISK * 100).toFixed(1)}%</span>
              <span style="color: #f59e0b;">Thr: ${(probsA.THREATENED * 100).toFixed(1)}%</span>
              <span style="color: #ef4444;">Ext: ${(probsA.EXTINCT * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <!-- Species B Card -->
        <div class="compare-card">
          <div class="compare-card-title">
            <div>
              <div class="compare-sci-name">${profB.scientific_name.replace(/_/g, ' ')}</div>
              <div class="compare-tax-sub">${profB.taxonomy?.class || 'Tetrapod'} &bull; ${profB.taxonomy?.order || ''} &bull; ${profB.taxonomy?.family || ''}</div>
            </div>
            <span style="background: ${colorB}22; color: ${colorB}; border: 1px solid ${colorB}55; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 11px;">${targetB}</span>
          </div>
          <div>
            <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Extinction Probabilities:</div>
            <div class="prob-meter">
              <div class="prob-bars">
                <div style="width: ${(probsB.LOW_RISK * 100).toFixed(1)}%; background: #10b981; height: 100%;"></div>
                <div style="width: ${(probsB.THREATENED * 100).toFixed(1)}%; background: #f59e0b; height: 100%;"></div>
                <div style="width: ${(probsB.EXTINCT * 100).toFixed(1)}%; background: #ef4444; height: 100%;"></div>
              </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 10px; font-family: var(--font-mono); margin-top: 4px;">
              <span style="color: #10b981;">Low: ${(probsB.LOW_RISK * 100).toFixed(1)}%</span>
              <span style="color: #f59e0b;">Thr: ${(probsB.THREATENED * 100).toFixed(1)}%</span>
              <span style="color: #ef4444;">Ext: ${(probsB.EXTINCT * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Trait Matrix Comparison Table with empirical deltas -->
      <div style="background: rgba(16, 25, 40, 0.7); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden;">
        <table class="compare-trait-table">
          <thead>
            <tr>
              <th>Biological &amp; Geographical Trait</th>
              <th>${profA.scientific_name.replace(/_/g, ' ')}</th>
              <th>${profB.scientific_name.replace(/_/g, ' ')}</th>
              <th>Empirical Differential</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Centroid Latitude</td>
              <td>${latA.toFixed(2)}°</td>
              <td>${latB.toFixed(2)}°</td>
              <td><span class="diff-tag ${Math.abs(latA) > Math.abs(latB) ? 'higher' : 'lower'}">Δ ${Math.abs(latA - latB).toFixed(2)}°</span></td>
            </tr>
            <tr>
              <td>Geographical Range Size</td>
              <td>${Math.round(rangeA).toLocaleString()} km²</td>
              <td>${Math.round(rangeB).toLocaleString()} km²</td>
              <td><span class="diff-tag ${rangeA > rangeB ? 'lower' : 'higher'}">${rangeA > rangeB ? 'A has larger range' : 'B has larger range'}</span></td>
            </tr>
            <tr>
              <td>Human Footprint Index</td>
              <td>${footA.toFixed(2)}</td>
              <td>${footB.toFixed(2)}</td>
              <td><span class="diff-tag ${footA > footB ? 'higher' : 'lower'}">${footA > footB ? 'A has higher exposure' : 'B has higher exposure'}</span></td>
            </tr>
            <tr>
              <td>Conservation Priority Score (CPS)</td>
              <td><strong>${cpsA} / 100</strong></td>
              <td><strong>${cpsB} / 100</strong></td>
              <td><span class="diff-tag ${parseFloat(cpsA) > parseFloat(cpsB) ? 'higher' : 'lower'}">Δ ${Math.abs(parseFloat(cpsA || 0) - parseFloat(cpsB || 0)).toFixed(1)} pts</span></td>
            </tr>
            <tr>
              <td>Body Mass</td>
              <td>${massA ? massA.toFixed(1) + ' g' : 'N/A'}</td>
              <td>${massB ? massB.toFixed(1) + ' g' : 'N/A'}</td>
              <td><span class="diff-tag same">${massA > massB ? 'A heavier' : 'B heavier'}</span></td>
            </tr>
            <tr>
              <td>Centroid Elevation</td>
              <td>${Math.round(elevA)} m</td>
              <td>${Math.round(elevB)} m</td>
              <td><span class="diff-tag same">Δ ${Math.abs(Math.round(elevA) - Math.round(elevB))} m</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- TreeSHAP Local Contributors Comparison -->
      <div class="compare-grid-cards">
        <div class="compare-card">
          <div style="font-size: 12px; font-weight: 700; color: #38bdf8;">Top TreeSHAP Drivers: Species A</div>
          <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px;">
            ${(predA.top_contributing_features || []).map(f => `
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.04); padding-bottom: 4px;">
                <span>${f.feature.replace(/_/g, ' ')}</span>
                <span style="font-family: var(--font-mono); color: ${f.direction === 'increases_risk' ? '#ef4444' : '#10b981'}; font-weight: 600;">${f.shap_value > 0 ? '+' : ''}${f.shap_value.toFixed(4)}</span>
              </div>
            `).join('')}
          </div>
        </div>
        <div class="compare-card">
          <div style="font-size: 12px; font-weight: 700; color: #38bdf8;">Top TreeSHAP Drivers: Species B</div>
          <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px;">
            ${(predB.top_contributing_features || []).map(f => `
              <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.04); padding-bottom: 4px;">
                <span>${f.feature.replace(/_/g, ' ')}</span>
                <span style="font-family: var(--font-mono); color: ${f.direction === 'increases_risk' ? '#ef4444' : '#10b981'}; font-weight: 600;">${f.shap_value > 0 ? '+' : ''}${f.shap_value.toFixed(4)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // Core UI Renders
  // =========================================================================

  renderTimelineChart(timeline) {
    if (!timeline || timeline.length === 0 || !this.timelineSvgPath) return;

    const xMin = 26;
    const xMax = 314;
    const yMin = 34;
    const yMax = 8;

    const probs = timeline.map(p => p.scenario_probabilities?.EXTINCT ?? 0.05);
    const minP = Math.min(...probs);
    const maxP = Math.max(...probs, minP + 0.04);

    const points = timeline.map((p, i) => {
      const x = xMin + (i / (timeline.length - 1)) * (xMax - xMin);
      const prob = p.scenario_probabilities?.EXTINCT ?? 0.05;
      const norm = (prob - minP) / (maxP - minP || 0.01);
      const y = yMin - norm * (yMin - yMax);
      return { x, y, prob, year: p.year, risk: p.scenario_risk };
    });

    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpX1 = prev.x + (curr.x - prev.x) * 0.45;
      const cpY1 = prev.y;
      const cpX2 = prev.x + (curr.x - prev.x) * 0.55;
      const cpY2 = curr.y;
      d += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${curr.x} ${curr.y}`;
    }

    this.timelineSvgPath.setAttribute('d', d);

    if (this.timelineSvgDots) {
      this.timelineSvgDots.innerHTML = '';
      points.forEach((pt) => {
        const color = pt.risk === 'EXTINCT' ? '#ef4444' : pt.risk === 'THREATENED' ? '#f59e0b' : '#10b981';
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.style.cursor = 'pointer';
        g.addEventListener('click', () => {
          this.applyTimelineYear(pt.year, true);
        });

        g.innerHTML = `
          <circle cx="${pt.x}" cy="${pt.y}" r="4" fill="${color}" stroke="#03060a" stroke-width="1.5"/>
          <circle cx="${pt.x}" cy="${pt.y}" r="7" fill="none" stroke="${color}" stroke-width="1" opacity="0.4"/>
        `;
        this.timelineSvgDots.appendChild(g);
      });
    }
  }

  applyTimelineYear(year, updateSliders = true) {
    this.activeYear = year;

    const buttons = this.timelineButtonsContainer?.querySelectorAll('.timeline-btn') || [];
    buttons.forEach((btn) => {
      if (parseInt(btn.dataset.year, 10) === year) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    const milestone = this.currentTimeline.find(p => p.year === year);
    if (!milestone) return;

    if (this.timelineDescEl) {
      this.timelineDescEl.textContent = `${milestone.label} • ${milestone.scenario_name} (${milestone.description})`;
    }

    if (this.panelTimelineBadge) {
      if (year === 2026) {
        this.panelTimelineBadge.textContent = '2026 BASELINE';
        this.panelTimelineBadge.style.background = 'rgba(6, 182, 212, 0.18)';
        this.panelTimelineBadge.style.color = '#38bdf8';
        this.panelTimelineBadge.style.borderColor = 'rgba(6, 182, 212, 0.4)';
      } else {
        this.panelTimelineBadge.textContent = `SIM ${year}: ${milestone.scenario_risk}`;
        const color = milestone.scenario_risk === 'EXTINCT' ? '#f87171' : milestone.scenario_risk === 'THREATENED' ? '#fbbf24' : '#34d399';
        this.panelTimelineBadge.style.background = `${color}22`;
        this.panelTimelineBadge.style.color = color;
        this.panelTimelineBadge.style.borderColor = `${color}55`;
      }
    }

    const predLabel = year === 2026 ? `PRED: ${milestone.scenario_risk}` : `SIM: ${milestone.scenario_risk}`;
    this.predBadgeEl.textContent = predLabel;
    this.updateStatusBadge(this.predBadgeEl, milestone.scenario_risk);

    const probs = milestone.scenario_probabilities;
    const pLow = (probs.LOW_RISK * 100).toFixed(1);
    const pThr = (probs.THREATENED * 100).toFixed(1);
    const pExt = (probs.EXTINCT * 100).toFixed(1);

    this.probBarLow.style.width = `${pLow}%`;
    this.probBarThr.style.width = `${pThr}%`;
    this.probBarExt.style.width = `${pExt}%`;

    this.probValLow.textContent = `${pLow}%`;
    this.probValThr.textContent = `${pThr}%`;
    this.probValExt.textContent = `${pExt}%`;

    if (milestone.top_contributing_features) {
      this.renderShapContributors(milestone.top_contributing_features);
    }

    if (updateSliders && milestone.params) {
      const p = milestone.params;
      this.sliderHabitat.value = p.habitat_loss;
      this.valHabitat.textContent = `${Math.round(p.habitat_loss * 100)}%`;
      this.sliderHuman.value = p.human_pressure;
      const hv = Math.round(p.human_pressure * 100);
      this.valHuman.textContent = `${hv >= 0 ? '+' : ''}${hv}%`;
      this.sliderClimate.value = p.climate_pressure;
      this.valClimate.textContent = `+${parseFloat(p.climate_pressure).toFixed(1)}°C`;
      this.sliderConservation.value = p.conservation_effort;
      this.valConservation.textContent = `${Math.round(p.conservation_effort * 100)}%`;
      this.updateActionImpactBreakdown();
    }
  }

  updateStatusBadge(badgeEl, category) {
    if (!badgeEl) return;
    const cat = (category || "").toUpperCase();
    if (cat.includes("EXTINCT") || cat.includes("CRITICALLY")) {
      badgeEl.style.background = "rgba(239, 68, 68, 0.22)";
      badgeEl.style.color = "#f87171";
      badgeEl.style.border = "1px solid rgba(239, 68, 68, 0.45)";
    } else if (cat.includes("THREATENED") || cat.includes("ENDANGERED") || cat.includes("VULNERABLE")) {
      badgeEl.style.background = "rgba(245, 158, 11, 0.22)";
      badgeEl.style.color = "#fbbf24";
      badgeEl.style.border = "1px solid rgba(245, 158, 11, 0.45)";
    } else {
      badgeEl.style.background = "rgba(16, 185, 129, 0.22)";
      badgeEl.style.color = "#34d399";
      badgeEl.style.border = "1px solid rgba(16, 185, 129, 0.45)";
    }
  }

  renderShapContributors(features) {
    if (!features || features.length === 0) {
      this.shapContainer.innerHTML = '<div style="color: #64748b; font-size: 11px;">No local SHAP attribution available</div>';
      if (this.fingerprintInterpretationText) {
        this.fingerprintInterpretationText.textContent = "No local SHAP attribution available for this specimen.";
      }
      return;
    }

    this.renderFingerprintInterpretation(features);

    this.shapContainer.innerHTML = '';
    const maxVal = Math.max(...features.map(f => Math.abs(f.shap_value || 0)), 0.01);

    features.forEach((feat) => {
      const val = feat.shap_value || 0;
      const pct = Math.min(100, Math.max(6, (Math.abs(val) / maxVal) * 100)).toFixed(0);
      const isRiskIncreaser = feat.direction === 'increases_risk' || val > 0;
      const color = isRiskIncreaser ? '#ef4444' : '#10b981';

      const row = document.createElement('div');
      row.className = 'shap-row';
      row.innerHTML = `
        <div class="shap-info">
          <span class="shap-name" title="${feat.feature}">${feat.feature.replace(/_/g, ' ')}</span>
          <span class="shap-val" style="color: ${color}">${val > 0 ? '+' : ''}${val.toFixed(4)}</span>
        </div>
        <div class="shap-bar-bg">
          <div class="shap-bar-fill" style="width: ${pct}%; background: ${color};"></div>
        </div>
      `;
      this.shapContainer.appendChild(row);
    });
  }

  renderRecommendations(recs) {
    if (!recs || !recs.recommendations || recs.recommendations.length === 0) {
      this.recommendationsContainer.innerHTML = `
        <div style="font-size: 11.5px; color: #10b981; padding: 6px 0;">
          &bull; Routine empirical monitoring &amp; baseline habitat protection.
        </div>
      `;
      return;
    }

    this.recommendationsContainer.innerHTML = '';
    recs.recommendations.slice(0, 3).forEach((rec) => {
      const div = document.createElement('div');
      div.className = 'rec-item';
      const urgencyColor = rec.urgency === 'High' ? '#f87171' : rec.urgency === 'Medium' ? '#fbbf24' : '#34d399';
      div.innerHTML = `
        <div class="rec-item-header">
          <span class="rec-category">${rec.action_category}</span>
          <span class="rec-urgency" style="background: ${urgencyColor}22; color: ${urgencyColor}; border: 1px solid ${urgencyColor}44;">${rec.urgency}</span>
        </div>
        <div class="rec-headline">${rec.headline}</div>
      `;
      this.recommendationsContainer.appendChild(div);
    });
  }

  async runSimulation() {
    if (!this.currentSpecies) {
      if (this.errorBanner && this.errorMsg) {
        this.errorMsg.textContent = "Please select a species from the 30,711 catalog before running a scenario simulation.";
        this.errorBanner.classList.remove('hidden');
      }
      return;
    }

    this.btnSimulate.textContent = "Simulating...";
    this.btnSimulate.style.opacity = "0.7";

    const params = {
      habitat_loss: parseFloat(this.sliderHabitat.value),
      human_pressure: parseFloat(this.sliderHuman.value),
      climate_pressure: parseFloat(this.sliderClimate.value),
      conservation_effort: parseFloat(this.sliderConservation.value),
    };

    this.currentScenarioParams = params;

    const simResult = await EcoGuardAPI.simulateScenario(this.currentSpecies, params);
    this.btnSimulate.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg> Run Scenario`;
    this.btnSimulate.style.opacity = "1";

    if (simResult && simResult.scenario_probabilities) {
      this.currentScenarioResult = simResult;
      this.openScenarioDrawer();
      const sp = simResult.scenario_probabilities;
      const pLow = (sp.LOW_RISK * 100).toFixed(1);
      const pThr = (sp.THREATENED * 100).toFixed(1);
      const pExt = (sp.EXTINCT * 100).toFixed(1);

      this.probBarLow.style.width = `${pLow}%`;
      this.probBarThr.style.width = `${pThr}%`;
      this.probBarExt.style.width = `${pExt}%`;

      this.probValLow.textContent = `${pLow}%`;
      this.probValThr.textContent = `${pThr}%`;
      this.probValExt.textContent = `${pExt}%`;

      this.predBadgeEl.textContent = `SIM: ${simResult.scenario_risk}`;
      this.updateStatusBadge(this.predBadgeEl, simResult.scenario_risk);

      if (simResult.top_contributing_features_scenario) {
        this.renderShapContributors(simResult.top_contributing_features_scenario);
      }

      if (this.globe) {
        this.globe.updateActiveSpeciesRisk(simResult.scenario_risk);
      }

      this.updateActionImpactBreakdown(simResult);
    }
  }

  async loadSpeciesImage(scientificName, className = null) {
    if (!scientificName) return;

    if (this.imageSkeleton) this.imageSkeleton.classList.remove('hidden');
    if (this.imageContainer) this.imageContainer.classList.add('hidden');
    if (this.silhouetteContainer) this.silhouetteContainer.classList.add('hidden');

    try {
      const imgData = await EcoGuardAPI.getSpeciesImage(scientificName, className);
      if (this.currentSpecies !== scientificName) return;

      this.currentImageData = imgData;

      if (imgData && imgData.has_image && imgData.image_url) {
        const preloader = new Image();
        preloader.onload = () => {
          if (this.currentSpecies !== scientificName) return;
          if (this.speciesPhoto) {
            this.speciesPhoto.src = imgData.image_url;
            this.speciesPhoto.alt = `${scientificName.replace(/_/g, ' ')} - Verified Biodiversity Photograph`;
          }
          if (this.imageSourceBadge) {
            this.imageSourceBadge.textContent = imgData.source || "Biodiversity Archive";
          }
          if (this.imageAuthorText) {
            const author = (imgData.attribution || "Public Domain").replace(/EcoGuard\s*AI/gi, "Wildlife Conservation Intelligence");
            this.imageAuthorText.textContent = author;
            this.imageAuthorText.title = author;
          }
          if (this.imageLicenseLink) {
            this.imageLicenseLink.textContent = imgData.license || "Open Access";
            this.imageLicenseLink.href = imgData.external_url || "#";
          }

          if (this.imageSkeleton) this.imageSkeleton.classList.add('hidden');
          if (this.imageContainer) this.imageContainer.classList.remove('hidden');
          if (this.silhouetteContainer) this.silhouetteContainer.classList.add('hidden');
        };

        preloader.onerror = () => {
          this.renderTaxonomicSilhouette(className || imgData?.silhouette_class, "Verified media offline • Archival silhouette");
        };

        preloader.src = imgData.image_url;
      } else {
        const rawDesc = imgData?.description || "Historical/Subfossil taxon • No verified photographic media";
        const desc = rawDesc.replace(/EcoGuard\s*AI/gi, "Wildlife Conservation Intelligence");
        this.renderTaxonomicSilhouette(className || imgData?.silhouette_class, desc);
      }
    } catch (err) {
      console.warn("Failed fetching species image:", err);
      this.renderTaxonomicSilhouette(className, "Biodiversity archival silhouette");
    }
  }

  renderTaxonomicSilhouette(className, description) {
    const cls = (className || "Tetrapod").toLowerCase();
    let svgIcon = "";

    if (cls.includes("av") || cls.includes("bird")) {
      svgIcon = `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 40 C16 32, 28 22, 44 14 C48 12, 54 10, 56 12 C58 14, 54 20, 50 24 C42 32, 34 38, 22 46 Z" fill="rgba(56, 189, 248, 0.15)"/>
        <path d="M28 28 C34 18, 44 8, 52 6 C48 16, 42 26, 36 34" stroke="#38bdf8"/>
        <path d="M12 40 C18 44, 26 48, 32 50 C28 54, 22 58, 16 56 C12 54, 10 46, 12 40 Z" fill="rgba(16, 185, 129, 0.2)"/>
        <circle cx="50" cy="15" r="1.5" fill="#fff"/>
      </svg>`;
    } else if (cls.includes("mammal")) {
      svgIcon = `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 38 C12 30, 18 26, 26 26 C32 26, 38 28, 46 24 C50 22, 54 18, 56 20 C58 22, 56 28, 52 30 C48 32, 46 36, 44 46 L40 46 L40 38 L24 38 L24 46 L20 46 L18 36 C14 36, 12 44, 8 46" fill="rgba(56, 189, 248, 0.15)"/>
        <path d="M48 20 C50 16, 54 16, 54 20" stroke="#38bdf8"/>
        <circle cx="51" cy="23" r="1.2" fill="#fff"/>
      </svg>`;
    } else if (cls.includes("reptil")) {
      svgIcon = `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M54 18 C50 14, 44 14, 38 18 C32 22, 28 26, 22 28 C16 30, 10 36, 8 44 C7 48, 9 52, 14 50 C18 48, 22 42, 26 38 C32 32, 38 30, 46 28 L54 18 Z" fill="rgba(56, 189, 248, 0.15)"/>
        <path d="M38 24 L44 32 M26 30 L20 38 M44 18 L48 10 M32 36 L30 46" stroke="#10b981"/>
        <circle cx="48" cy="17" r="1.2" fill="#fff"/>
      </svg>`;
    } else if (cls.includes("amphib")) {
      svgIcon = `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M32 16 C22 16, 16 26, 16 36 C16 46, 24 52, 32 52 C40 52, 48 46, 48 36 C48 26, 42 16, 32 16 Z" fill="rgba(16, 185, 129, 0.15)"/>
        <circle cx="24" cy="20" r="4" stroke="#38bdf8" fill="rgba(6, 182, 212, 0.2)"/>
        <circle cx="40" cy="20" r="4" stroke="#38bdf8" fill="rgba(6, 182, 212, 0.2)"/>
        <circle cx="24" cy="20" r="1.5" fill="#fff"/>
        <circle cx="40" cy="20" r="1.5" fill="#fff"/>
        <path d="M16 38 C10 42, 8 48, 12 50 C16 52, 20 46, 22 44" stroke="#34d399"/>
        <path d="M48 38 C54 42, 56 48, 52 50 C48 52, 44 46, 42 44" stroke="#34d399"/>
      </svg>`;
    } else {
      svgIcon = `<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="32" cy="32" r="20" stroke="#06b6d4" fill="rgba(6, 182, 212, 0.1)"/>
        <path d="M22 32 C22 26, 42 26, 42 32 C42 38, 22 38, 22 32 Z" stroke="#34d399"/>
        <circle cx="32" cy="32" r="3" fill="#38bdf8"/>
      </svg>`;
    }

    if (this.silhouetteIcon) this.silhouetteIcon.innerHTML = svgIcon;
    if (this.silhouetteClassName) this.silhouetteClassName.textContent = className || "Tetrapod";
    if (this.silhouetteDesc) this.silhouetteDesc.innerHTML = description || "Historical/subfossil taxon with no verified public-domain photography.";

    if (this.imageSkeleton) this.imageSkeleton.classList.add('hidden');
    if (this.imageContainer) this.imageContainer.classList.add('hidden');
    if (this.silhouetteContainer) this.silhouetteContainer.classList.remove('hidden');
  }
}
