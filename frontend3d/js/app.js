/**
 * Wildlife Conservation Intelligence - 3D Digital Twin Main Entrypoint
 */

import { EcoGlobe } from './globe.js';
import { UIController } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('globe-canvas-container');
  
  // Initialize UI controller reference placeholder
  let uiController = null;

  // Initialize 3D Interactive Earth Globe
  const globe = new EcoGlobe(container, (selectedSpeciesName) => {
    if (uiController) {
      uiController.selectSpecies(selectedSpeciesName);
    }
  });

  // Initialize UI controls and right-side intelligence panel
  uiController = new UIController(globe);

  // Expose to window for console diagnostics
  window.EcoGuard = {
    globe,
    ui: uiController,
  };

  console.log("Wildlife Conservation Intelligence 3D Digital Twin initialized successfully.");
});
