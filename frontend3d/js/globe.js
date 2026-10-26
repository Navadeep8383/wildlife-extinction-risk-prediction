/**
 * Wildlife Conservation Intelligence - Interactive 3D Conservation Globe Engine
 * Built with Three.js (ES Module setup)
 * Features realistic Earth shading, specular oceans, organic clouds, atmospheric Rayleigh scattering,
 * restrained celestial cosmos, scientific geospatial needle beacons, and Global Risk Explorer layer.
 */

import * as THREE from 'https://esm.sh/three@0.160.0';
import { OrbitControls } from 'https://esm.sh/three@0.160.0/addons/controls/OrbitControls.js';
import { EcoGuardAPI } from './api.js';

export class EcoGlobe {
  constructor(containerElement, onSelectSpeciesCallback) {
    this.container = containerElement;
    this.onSelectSpecies = onSelectSpeciesCallback;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    this.globeGroup = null;
    this.earthMesh = null;
    this.cloudMesh = null;
    this.cloudMeshOuter = null;
    this.atmosphereMesh = null;
    this.outerGlowMesh = null;
    this.pinGroup = null;
    this.activePinGroup = null;
    this.activeLatitudeRing = null;
    this.globalRiskExplorerGroup = null;
    this.isGlobalRiskExplorerActive = false;
    this.tooltip = null;

    this.isAutoRotating = true;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    this.init();
  }

  init() {
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;

    // 1. Scene setup
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x03060a);
    this.scene.fog = new THREE.FogExp2(0x03060a, 0.0015);

    // 2. Camera setup - Comfortable default framing showing the complete Earth without clipping
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    this.camera.position.set(0, 35, 245);

    // 3. Renderer setup with high-precision color management and tone mapping
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.container.appendChild(this.renderer.domElement);

    // 4. Orbit Controls with realistic inertia damping
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.045; // Silky inertia
    this.controls.rotateSpeed = 0.75;
    this.controls.zoomSpeed = 1.1;
    this.controls.minDistance = 110;
    this.controls.maxDistance = 500;
    this.controls.enablePan = false;

    // Pause auto-rotation on user drag, gently resume on idle
    let resumeTimeout = null;
    this.controls.addEventListener('start', () => {
      this.isAutoRotating = false;
      if (resumeTimeout) clearTimeout(resumeTimeout);
    });
    this.controls.addEventListener('end', () => {
      resumeTimeout = setTimeout(() => {
        this.isAutoRotating = true;
      }, 3500);
    });

    // 5. Dynamic Lighting & Realistic Day/Night Terminator
    this.setupLighting();

    // 6. Globe & Atmospheric layers
    this.globeGroup = new THREE.Group();
    this.scene.add(this.globeGroup);

    this.createEarth();
    this.createAtmosphereGlow();
    this.createCloudLayers();
    this.createStarfield();
    this.createSpeciesPins();
    this.createGlobalRiskExplorerLayer();

    // 7. Event listeners
    window.addEventListener('resize', this.onWindowResize.bind(this));
    this.renderer.domElement.addEventListener('click', this.onCanvasClick.bind(this));
    this.renderer.domElement.addEventListener('pointermove', this.onCanvasPointerMove.bind(this));
    this.renderer.domElement.addEventListener('pointerleave', () => {
      if (this.tooltip) this.tooltip.classList.remove('visible');
    });

    // Initialize tooltip reference
    this.tooltip = document.getElementById('globe-tooltip');

    // 8. Start render loop
    this.animate();
  }

  setupLighting() {
    // Balanced ambient fill for natural space shadow contrast
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.38);
    this.scene.add(ambientLight);

    // Primary Sun Directional Light (realistic solar illumination with warm day/night terminator falloff)
    const sunLight = new THREE.DirectionalLight(0xfff7ed, 2.5);
    sunLight.position.set(160, 50, 160);
    this.scene.add(sunLight);

    // Cyan-Blue atmospheric limb bounce fill for dark-side scatter
    const darkRimLight = new THREE.DirectionalLight(0x38bdf8, 0.45);
    darkRimLight.position.set(-160, -30, -140);
    this.scene.add(darkRimLight);
  }

  createEarthTextures() {
    // Generate high-resolution procedural Earth texture with detailed continents, coastal shelves, and biomes
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    // 1. Natural Ocean Depth Gradient (Deep sapphire abyssal depths to rich cerulean equatorial waters)
    const oceanGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    oceanGrad.addColorStop(0, '#061a2e');
    oceanGrad.addColorStop(0.18, '#0b2a4a');
    oceanGrad.addColorStop(0.5, '#0e3a63');
    oceanGrad.addColorStop(0.82, '#0b2a4a');
    oceanGrad.addColorStop(1, '#061a2e');
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Fine coordinate graticule grid lines (15-degree parallels and meridians)
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.08)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= canvas.width; x += canvas.width / 24) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += canvas.height / 12) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Highlight Tropics (23.5° N/S) and Equator
    ctx.strokeStyle = 'rgba(52, 211, 153, 0.22)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height * 0.369); // Tropic of Cancer
    ctx.lineTo(canvas.width, canvas.height * 0.369);
    ctx.moveTo(0, canvas.height * 0.631); // Tropic of Capricorn
    ctx.lineTo(canvas.width, canvas.height * 0.631);
    ctx.stroke();

    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height / 2); // Equator
    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();

    // 3. Detailed Global Continents & Islands Poly Coordinates
    const continents = [
      // Africa
      { poly: [[0.47, 0.36], [0.52, 0.35], [0.57, 0.36], [0.60, 0.42], [0.63, 0.49], [0.61, 0.58], [0.56, 0.70], [0.52, 0.75], [0.49, 0.68], [0.46, 0.56], [0.44, 0.46], [0.45, 0.40], [0.47, 0.36]], type: 'africa' },
      // Madagascar
      { poly: [[0.61, 0.62], [0.63, 0.64], [0.62, 0.71], [0.60, 0.69], [0.61, 0.62]], type: 'island' },
      // Eurasia Main Landmass
      { poly: [[0.46, 0.32], [0.51, 0.26], [0.58, 0.22], [0.68, 0.20], [0.80, 0.19], [0.90, 0.22], [0.87, 0.34], [0.82, 0.42], [0.77, 0.48], [0.72, 0.46], [0.68, 0.44], [0.60, 0.42], [0.54, 0.38], [0.47, 0.35], [0.46, 0.32]], type: 'eurasia' },
      // Scandinavia & UK
      { poly: [[0.48, 0.22], [0.52, 0.18], [0.54, 0.24], [0.50, 0.28], [0.48, 0.22]], type: 'boreal' },
      { poly: [[0.44, 0.24], [0.46, 0.23], [0.46, 0.28], [0.43, 0.27], [0.44, 0.24]], type: 'temperate' },
      // Japan & Sakhalin
      { poly: [[0.83, 0.34], [0.86, 0.36], [0.85, 0.42], [0.82, 0.40], [0.83, 0.34]], type: 'island' },
      // Indian Subcontinent
      { poly: [[0.67, 0.42], [0.72, 0.43], [0.71, 0.54], [0.67, 0.50], [0.67, 0.42]], type: 'tropical' },
      // SE Asia & Sundaland Archipelago
      { poly: [[0.74, 0.46], [0.78, 0.48], [0.77, 0.58], [0.73, 0.54], [0.74, 0.46]], type: 'tropical' },
      { poly: [[0.76, 0.59], [0.82, 0.60], [0.80, 0.65], [0.75, 0.62], [0.76, 0.59]], type: 'tropical' }, // Indonesia/Java
      { poly: [[0.83, 0.56], [0.87, 0.58], [0.86, 0.64], [0.82, 0.61], [0.83, 0.56]], type: 'tropical' }, // New Guinea
      // North America
      { poly: [[0.12, 0.22], [0.20, 0.18], [0.28, 0.20], [0.33, 0.26], [0.31, 0.38], [0.28, 0.46], [0.22, 0.50], [0.18, 0.42], [0.14, 0.34], [0.10, 0.28], [0.12, 0.22]], type: 'north_america' },
      // Central America & Caribbean
      { poly: [[0.21, 0.48], [0.25, 0.52], [0.26, 0.56], [0.23, 0.54], [0.21, 0.48]], type: 'tropical' },
      // South America
      { poly: [[0.27, 0.52], [0.33, 0.52], [0.37, 0.58], [0.35, 0.72], [0.32, 0.84], [0.29, 0.78], [0.27, 0.68], [0.25, 0.58], [0.27, 0.52]], type: 'south_america' },
      // Australia
      { poly: [[0.77, 0.64], [0.87, 0.63], [0.88, 0.74], [0.84, 0.79], [0.76, 0.76], [0.74, 0.69], [0.77, 0.64]], type: 'australia' },
      // New Zealand
      { poly: [[0.89, 0.77], [0.91, 0.79], [0.90, 0.85], [0.88, 0.82], [0.89, 0.77]], type: 'island' },
      // Greenland Ice Sheet
      { poly: [[0.34, 0.12], [0.42, 0.11], [0.40, 0.20], [0.33, 0.21], [0.34, 0.12]], type: 'polar' },
      // Antarctica Ice Cap
      { poly: [[0.05, 0.90], [0.95, 0.90], [0.95, 0.99], [0.05, 0.99], [0.05, 0.90]], type: 'polar' }
    ];

    // Pass 1: Turquoise Continental Shelf Shallow-Water Halo
    ctx.save();
    ctx.strokeStyle = 'rgba(14, 165, 233, 0.45)';
    ctx.lineWidth = 9;
    ctx.shadowColor = 'rgba(6, 182, 212, 0.70)';
    ctx.shadowBlur = 14;
    continents.forEach(({ poly }) => {
      ctx.beginPath();
      poly.forEach(([px, py], i) => {
        const x = px * canvas.width;
        const y = py * canvas.height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.stroke();
    });
    ctx.restore();

    // Pass 2: Natural Earth Biomes & Topographic Shading
    continents.forEach(({ poly, type }) => {
      ctx.beginPath();
      poly.forEach(([px, py], i) => {
        const x = px * canvas.width;
        const y = py * canvas.height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();

      // Differentiate natural earthy biomes
      if (type === 'polar') {
        ctx.fillStyle = '#e2e8f0'; // Arctic ice/snow
        ctx.strokeStyle = '#cbd5e1';
      } else if (type === 'tropical') {
        ctx.fillStyle = '#1e4b37'; // Lush canopy forest
        ctx.strokeStyle = '#2d6a4f';
      } else if (type === 'australia') {
        ctx.fillStyle = '#8c5225'; // Red sandstone & arid scrub
        ctx.strokeStyle = '#a6602e';
      } else if (type === 'boreal') {
        ctx.fillStyle = '#1f3f2d'; // Coniferous taiga
        ctx.strokeStyle = '#2d5a44';
      } else if (type === 'south_america') {
        ctx.fillStyle = '#23533c'; // Amazonian rainforest + Andes spine
        ctx.strokeStyle = '#2f6d50';
      } else {
        ctx.fillStyle = '#275239'; // Temperate woodlands and plains
        ctx.strokeStyle = '#386f50';
      }

      ctx.fill();
      ctx.lineWidth = 1.8;
      ctx.stroke();
    });

    // Pass 3: Subtle Warm Coastal Settlements & Human Infrastructure
    ctx.fillStyle = 'rgba(254, 215, 170, 0.85)';
    const urbanPoints = [
      [0.48, 0.37], [0.55, 0.38], [0.71, 0.50], [0.77, 0.53], [0.83, 0.38],
      [0.24, 0.44], [0.28, 0.38], [0.32, 0.62], [0.85, 0.74], [0.51, 0.28]
    ];
    urbanPoints.forEach(([ux, uy]) => {
      ctx.beginPath();
      ctx.arc(ux * canvas.width, uy * canvas.height, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });

    const diffuseTexture = new THREE.CanvasTexture(canvas);
    diffuseTexture.wrapS = THREE.RepeatWrapping;
    diffuseTexture.wrapT = THREE.ClampToEdgeWrapping;

    // 4. Generate Ocean Specular / Roughness Map (Oceans = reflective, Land = matte)
    const roughCanvas = document.createElement('canvas');
    roughCanvas.width = 1024;
    roughCanvas.height = 512;
    const rCtx = roughCanvas.getContext('2d');

    // Oceans are smooth and glossy
    rCtx.fillStyle = '#1e293b';
    rCtx.fillRect(0, 0, roughCanvas.width, roughCanvas.height);

    // Continents are rough and diffuse
    rCtx.fillStyle = '#f1f5f9';
    continents.forEach(({ poly }) => {
      rCtx.beginPath();
      poly.forEach(([px, py], i) => {
        const x = px * roughCanvas.width;
        const y = py * roughCanvas.height;
        if (i === 0) rCtx.moveTo(x, y);
        else rCtx.lineTo(x, y);
      });
      rCtx.closePath();
      rCtx.fill();
    });

    const roughnessTexture = new THREE.CanvasTexture(roughCanvas);
    roughnessTexture.wrapS = THREE.RepeatWrapping;
    roughnessTexture.wrapT = THREE.ClampToEdgeWrapping;

    return { diffuseTexture, roughnessTexture };
  }

  createEarth() {
    const geometry = new THREE.SphereGeometry(70, 64, 64);
    const { diffuseTexture, roughnessTexture } = this.createEarthTextures();

    // Standard PBR material with realistic ocean reflections and gradual terminator falloff
    const material = new THREE.MeshStandardMaterial({
      map: diffuseTexture,
      roughnessMap: roughnessTexture,
      roughness: 0.50,
      metalness: 0.12,
      emissive: new THREE.Color(0x02182b),
      emissiveIntensity: 0.18,
    });

    this.earthMesh = new THREE.Mesh(geometry, material);
    this.globeGroup.add(this.earthMesh);

    // Asynchronously upgrade with high-res dark satellite texture if network allows
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(
      'https://unpkg.com/three-globe/example/img/earth-dark.jpg',
      (tex) => {
        if (this.earthMesh && this.earthMesh.material) {
          this.earthMesh.material.map = tex;
          this.earthMesh.material.needsUpdate = true;
        }
      },
      undefined,
      () => { /* gracefully retain high-detail procedural biomes */ }
    );
  }

  createAtmosphereGlow() {
    // Custom Rayleigh/Mie atmospheric scattering shader with limb falloff
    const vertexShader = `
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vNormal = normalize(normalMatrix * normal);
        vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

    const fragmentShader = `
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vec3 viewDir = normalize(-vPosition);
        float fresnel = 1.0 - max(0.0, dot(vNormal, viewDir));
        float intensity = pow(fresnel, 2.6) * 0.95;
        vec3 cyanColor = vec3(0.03, 0.72, 0.92);
        vec3 emeraldColor = vec3(0.06, 0.75, 0.52);
        vec3 glowColor = mix(emeraldColor, cyanColor, fresnel);
        gl_FragColor = vec4(glowColor, intensity);
      }
    `;

    const atmosphereGeo = new THREE.SphereGeometry(74.8, 64, 64);
    const atmosphereMat = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    });

    this.atmosphereMesh = new THREE.Mesh(atmosphereGeo, atmosphereMat);
    this.globeGroup.add(this.atmosphereMesh);

    // Soft outer planetary glow shell
    const outerGlowGeo = new THREE.SphereGeometry(76.2, 32, 32);
    const outerGlowMat = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader: `
        varying vec3 vNormal;
        varying vec3 vPosition;
        void main() {
          vec3 viewDir = normalize(-vPosition);
          float fresnel = 1.0 - max(0.0, dot(vNormal, viewDir));
          float intensity = pow(fresnel, 4.0) * 0.40;
          gl_FragColor = vec4(0.02, 0.65, 0.85, intensity);
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
    });
    this.outerGlowMesh = new THREE.Mesh(outerGlowGeo, outerGlowMat);
    this.globeGroup.add(this.outerGlowMesh);
  }

  createCloudLayers() {
    // 1. Inner mid-altitude cumulus cloud layer with organic puffs
    const cloudGeo = new THREE.SphereGeometry(71.25, 64, 64);
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Generate organic cloud clusters with soft radial falloff
    for (let i = 0; i < 75; i++) {
      const cx = Math.random() * canvas.width;
      const cy = Math.random() * canvas.height;
      const radius = 22 + Math.random() * 55;
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
      grad.addColorStop(0, 'rgba(255, 255, 255, 0.26)');
      grad.addColorStop(0.5, 'rgba(255, 255, 255, 0.12)');
      grad.addColorStop(1, 'rgba(255, 255, 255, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fill();
    }

    const cloudTexture = new THREE.CanvasTexture(canvas);
    const cloudMat = new THREE.MeshStandardMaterial({
      map: cloudTexture,
      transparent: true,
      opacity: 0.46,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    this.globeGroup.add(this.cloudMesh);

    // 2. Outer high-altitude cirrus filaments for 3D parallax depth
    const cloudGeoOuter = new THREE.SphereGeometry(71.85, 64, 64);
    const canvasOuter = document.createElement('canvas');
    canvasOuter.width = 1024;
    canvasOuter.height = 512;
    const ctxOuter = canvasOuter.getContext('2d');
    ctxOuter.clearRect(0, 0, canvasOuter.width, canvasOuter.height);

    for (let i = 0; i < 45; i++) {
      const cx = Math.random() * canvasOuter.width;
      const cy = Math.random() * canvasOuter.height;
      const radius = 30 + Math.random() * 65;
      const grad = ctxOuter.createRadialGradient(cx, cy, 0, cx, cy, radius);
      grad.addColorStop(0, 'rgba(240, 249, 255, 0.18)');
      grad.addColorStop(0.6, 'rgba(240, 249, 255, 0.06)');
      grad.addColorStop(1, 'rgba(240, 249, 255, 0)');
      ctxOuter.fillStyle = grad;
      ctxOuter.beginPath();
      ctxOuter.arc(cx, cy, radius, 0, Math.PI * 2);
      ctxOuter.fill();
    }

    const cloudTextureOuter = new THREE.CanvasTexture(canvasOuter);
    const cloudMatOuter = new THREE.MeshStandardMaterial({
      map: cloudTextureOuter,
      transparent: true,
      opacity: 0.32,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });

    this.cloudMeshOuter = new THREE.Mesh(cloudGeoOuter, cloudMatOuter);
    this.globeGroup.add(this.cloudMeshOuter);
  }

  createStarfield() {
    // Restrained, realistic celestial cosmos with multi-spectral stellar color temperatures
    // Total stars: ~950 (restrained density to avoid particle demo clutter)
    
    // Tier 1: Distant soft white/silver stars (650 particles)
    const starsGeo1 = new THREE.BufferGeometry();
    const count1 = 650;
    const pos1 = new Float32Array(count1 * 3);
    for (let i = 0; i < count1 * 3; i += 3) {
      const r = 420 + Math.random() * 550;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      pos1[i] = r * Math.sin(phi) * Math.cos(theta);
      pos1[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos1[i + 2] = r * Math.cos(phi);
    }
    starsGeo1.setAttribute('position', new THREE.BufferAttribute(pos1, 3));
    const starsMat1 = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.85,
      transparent: true,
      opacity: 0.50,
    });
    this.scene.add(new THREE.Points(starsGeo1, starsMat1));

    // Tier 2: Navigational warm-white stellar bodies (220 particles)
    const starsGeo2 = new THREE.BufferGeometry();
    const count2 = 220;
    const pos2 = new Float32Array(count2 * 3);
    for (let i = 0; i < count2 * 3; i += 3) {
      const r = 380 + Math.random() * 500;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      pos2[i] = r * Math.sin(phi) * Math.cos(theta);
      pos2[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos2[i + 2] = r * Math.cos(phi);
    }
    starsGeo2.setAttribute('position', new THREE.BufferAttribute(pos2, 3));
    const starsMat2 = new THREE.PointsMaterial({
      color: 0xfffbeb,
      size: 1.4,
      transparent: true,
      opacity: 0.75,
    });
    this.scene.add(new THREE.Points(starsGeo2, starsMat2));

    // Tier 3: Rare celestial bright blue-white beacons (75 particles)
    const starsGeo3 = new THREE.BufferGeometry();
    const count3 = 75;
    const pos3 = new Float32Array(count3 * 3);
    for (let i = 0; i < count3 * 3; i += 3) {
      const r = 340 + Math.random() * 450;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      pos3[i] = r * Math.sin(phi) * Math.cos(theta);
      pos3[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos3[i + 2] = r * Math.cos(phi);
    }
    starsGeo3.setAttribute('position', new THREE.BufferAttribute(pos3, 3));
    const starsMat3 = new THREE.PointsMaterial({
      color: 0xbae6fd,
      size: 2.0,
      transparent: true,
      opacity: 0.90,
    });
    this.scene.add(new THREE.Points(starsGeo3, starsMat3));
  }

  latLonToVector3(lat, lon, radius = 70.5) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = (radius * Math.sin(phi) * Math.sin(theta));
    const y = (radius * Math.cos(phi));
    return new THREE.Vector3(x, y, z);
  }

  createScientificBeaconMesh(sp, displayLon, isProminent = false) {
    const riskColor = sp.risk_target === 'EXTINCT' ? 0xef4444 :
                      sp.risk_target === 'THREATENED' ? 0xf59e0b : 0x10b981;
    const baseRadius = 70.4;
    const needleHeight = isProminent ? 6.0 : 4.2;
    const surfacePos = this.latLonToVector3(sp.latitude, displayLon, baseRadius);
    const tipPos = this.latLonToVector3(sp.latitude, displayLon, baseRadius + needleHeight);

    const group = new THREE.Group();

    // 1. Vertical holographic coordinate laser needle anchored to true latitude
    const needleGeo = new THREE.BufferGeometry().setFromPoints([surfacePos, tipPos]);
    const needleMat = new THREE.LineBasicMaterial({
      color: riskColor,
      transparent: true,
      opacity: isProminent ? 0.95 : 0.70,
      linewidth: 2,
    });
    const needleLine = new THREE.Line(needleGeo, needleMat);
    group.add(needleLine);

    // 2. Diamond / Octahedral scientific beacon head emitter at the tip
    const diamondGeo = new THREE.OctahedronGeometry(isProminent ? 2.2 : 1.4, 0);
    const diamondMat = new THREE.MeshBasicMaterial({
      color: riskColor,
      wireframe: false,
    });
    const diamondMesh = new THREE.Mesh(diamondGeo, diamondMat);
    diamondMesh.position.copy(tipPos);
    group.add(diamondMesh);

    // 3. Inner pulsing sonar ring at needle base
    const ringGeo = new THREE.RingGeometry(isProminent ? 2.2 : 1.4, isProminent ? 3.4 : 2.2, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: riskColor,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.position.copy(surfacePos);
    ringMesh.lookAt(surfacePos.clone().multiplyScalar(2));
    group.add(ringMesh);

    // 4. Outer sweep radar ring
    const radarGeo = new THREE.RingGeometry(isProminent ? 3.8 : 2.4, isProminent ? 5.2 : 3.4, 32);
    const radarMat = new THREE.MeshBasicMaterial({
      color: riskColor,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const radarMesh = new THREE.Mesh(radarGeo, radarMat);
    radarMesh.position.copy(surfacePos);
    radarMesh.lookAt(surfacePos.clone().multiplyScalar(2));
    group.add(radarMesh);

    // 5. Earth Pulse dynamic expanding risk pulse wave
    const pulseGeo = new THREE.RingGeometry(isProminent ? 1.6 : 1.0, isProminent ? 2.6 : 1.8, 32);
    const pulseMat = new THREE.MeshBasicMaterial({
      color: riskColor,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });
    const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
    pulseMesh.position.copy(surfacePos);
    pulseMesh.lookAt(surfacePos.clone().multiplyScalar(2));
    group.add(pulseMesh);

    group.userData = {
      ...sp,
      displayLon,
      surfacePos,
      tipPos,
    };

    return group;
  }

  async createSpeciesPins() {
    this.pinGroup = new THREE.Group();
    this.activePinGroup = new THREE.Group();
    this.globeGroup.add(this.pinGroup);
    this.globeGroup.add(this.activePinGroup);

    // Fetch real catalog representative markers from backend
    const markers = await EcoGuardAPI.getSpeciesMarkers(3);

    const speciesList = (markers && markers.length > 0) ? markers : [
      // Fallback with verified empirical dataset values
      { scientific_name: "Polyplectron_schleiermacheri", class_name: "Aves", redlist_category: "Endangered", risk_target: "THREATENED", latitude: 0.235098802 },
      { scientific_name: "Melogale_everetti", class_name: "Mammalia", redlist_category: "Endangered", risk_target: "THREATENED", latitude: 6.014350505 },
      { scientific_name: "Raphus_cucullatus", class_name: "Aves", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: -20.285474804 },
      { scientific_name: "Liocichla_steerii", class_name: "Aves", redlist_category: "Least Concern", risk_target: "LOW_RISK", latitude: 23.73993388 },
      { scientific_name: "Atelopus_chiriquiensis", class_name: "Amphibia", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: 9.254728882 },
      { scientific_name: "Chelonoidis_niger", class_name: "Reptilia", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: -0.971080107 }
    ];

    const count = speciesList.length;
    speciesList.forEach((sp, index) => {
      // Latitude is strictly the verified catalog value.
      // Longitude is an analytical distribution around the parallel for clarity.
      const displayLon = (index * (360 / count)) - 180;
      const beaconObject = this.createScientificBeaconMesh(sp, displayLon, false);
      this.pinGroup.add(beaconObject);
    });
  }

  createGlobalRiskExplorerLayer() {
    this.globalRiskExplorerGroup = new THREE.Group();
    this.globalRiskExplorerGroup.visible = false;
    this.globeGroup.add(this.globalRiskExplorerGroup);

    // Analytical latitude distribution bands across major global biomes
    // Using strictly actual catalog species latitudes
    const explorerSpecies = [
      // Polar & Boreal Species (High Latitude)
      { scientific_name: "Ursus_maritimus", class_name: "Mammalia", redlist_category: "Vulnerable", risk_target: "THREATENED", latitude: 71.2 },
      { scientific_name: "Pinguinus_impennis", class_name: "Aves", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: 64.8 },
      { scientific_name: "Gulo_gulo", class_name: "Mammalia", redlist_category: "Least Concern", risk_target: "LOW_RISK", latitude: 62.0 },
      // Temperate Species
      { scientific_name: "Ectopistes_migratorius", class_name: "Aves", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: 41.5 },
      { scientific_name: "Lynx_pardinus", class_name: "Mammalia", redlist_category: "Endangered", risk_target: "THREATENED", latitude: 38.2 },
      { scientific_name: "Vulpes_vulpes", class_name: "Mammalia", redlist_category: "Least Concern", risk_target: "LOW_RISK", latitude: 45.0 },
      // Subtropical & Tropical Species
      { scientific_name: "Polyplectron_schleiermacheri", class_name: "Aves", redlist_category: "Endangered", risk_target: "THREATENED", latitude: 0.24 },
      { scientific_name: "Melogale_everetti", class_name: "Mammalia", redlist_category: "Endangered", risk_target: "THREATENED", latitude: 6.01 },
      { scientific_name: "Atelopus_chiriquiensis", class_name: "Amphibia", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: 9.25 },
      { scientific_name: "Liocichla_steerii", class_name: "Aves", redlist_category: "Least Concern", risk_target: "LOW_RISK", latitude: 23.74 },
      // Southern Hemisphere
      { scientific_name: "Raphus_cucullatus", class_name: "Aves", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: -20.28 },
      { scientific_name: "Chelonoidis_niger", class_name: "Reptilia", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: -0.97 },
      { scientific_name: "Thylacinus_cynocephalus", class_name: "Mammalia", redlist_category: "Extinct", risk_target: "EXTINCT", latitude: -42.8 },
      { scientific_name: "Spheniscus_magellanicus", class_name: "Aves", redlist_category: "Least Concern", risk_target: "LOW_RISK", latitude: -52.4 }
    ];

    explorerSpecies.forEach((sp, idx) => {
      const displayLon = (idx * (360 / explorerSpecies.length)) - 180;
      const beacon = this.createScientificBeaconMesh(sp, displayLon, true);
      this.globalRiskExplorerGroup.add(beacon);

      // Create subtle analytical latitude parallel for this taxon
      const latRad = (sp.latitude * Math.PI) / 180;
      const y = 70.6 * Math.sin(latRad);
      const r = 70.6 * Math.cos(latRad);

      if (r > 0.5) {
        const segments = 48;
        const points = [];
        for (let i = 0; i <= segments; i++) {
          const theta = (i / segments) * Math.PI * 2;
          points.push(new THREE.Vector3(r * Math.cos(theta), y, r * Math.sin(theta)));
        }
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const color = sp.risk_target === 'EXTINCT' ? 0xef4444 :
                      sp.risk_target === 'THREATENED' ? 0xf59e0b : 0x10b981;
        const lineMat = new THREE.LineBasicMaterial({
          color,
          transparent: true,
          opacity: 0.35,
          linewidth: 1,
        });
        const ring = new THREE.LineLoop(lineGeo, lineMat);
        this.globalRiskExplorerGroup.add(ring);
      }
    });
  }

  setGlobalRiskExplorerVisible(visible) {
    this.isGlobalRiskExplorerActive = visible;
    if (this.globalRiskExplorerGroup) {
      this.globalRiskExplorerGroup.visible = visible;
    }
  }

  updateActiveLatitudeRing(lat, color = 0x06b6d4) {
    if (this.activeLatitudeRing) {
      this.globeGroup.remove(this.activeLatitudeRing);
      if (this.activeLatitudeRing.geometry) this.activeLatitudeRing.geometry.dispose();
      if (this.activeLatitudeRing.material) this.activeLatitudeRing.material.dispose();
      this.activeLatitudeRing = null;
    }

    const latRad = (lat * Math.PI) / 180;
    const y = 70.7 * Math.sin(latRad);
    const r = 70.7 * Math.cos(latRad);

    if (r < 0.2) return; // poles

    const segments = 64;
    const points = [];
    for (let i = 0; i <= segments; i++) {
      const theta = (i / segments) * Math.PI * 2;
      points.push(new THREE.Vector3(r * Math.cos(theta), y, r * Math.sin(theta)));
    }
    const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
    const lineMat = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.85,
      linewidth: 2,
    });
    this.activeLatitudeRing = new THREE.LineLoop(lineGeo, lineMat);
    this.globeGroup.add(this.activeLatitudeRing);
  }

  clearActiveSpecies() {
    if (this.activeLatitudeRing) {
      this.globeGroup.remove(this.activeLatitudeRing);
      if (this.activeLatitudeRing.geometry) this.activeLatitudeRing.geometry.dispose();
      if (this.activeLatitudeRing.material) this.activeLatitudeRing.material.dispose();
      this.activeLatitudeRing = null;
    }
    if (this.activePinGroup) {
      while (this.activePinGroup.children.length > 0) {
        const obj = this.activePinGroup.children[0];
        if (obj.children) {
          obj.children.forEach((child) => {
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
          });
        }
        this.activePinGroup.remove(obj);
      }
    }
  }

  setActiveSpecies(speciesData) {
    if (!speciesData || typeof speciesData.latitude !== 'number') return;
    const lat = speciesData.latitude;
    const riskColor = speciesData.risk_target === 'EXTINCT' ? 0xef4444 :
                      speciesData.risk_target === 'THREATENED' ? 0xf59e0b : 0x10b981;

    // 1. Draw glowing real latitude parallel ring
    this.updateActiveLatitudeRing(lat, riskColor);

    // 2. Clear previous active beacon
    this.clearActiveSpecies();
    this.updateActiveLatitudeRing(lat, riskColor);

    // 3. Find if species already exists in general pin group
    let matchPin = null;
    if (this.pinGroup) {
      this.pinGroup.children.forEach((p) => {
        if (p.userData && p.userData.scientific_name === speciesData.scientific_name) {
          matchPin = p;
        }
      });
    }

    const displayLon = matchPin ? matchPin.userData.displayLon : 0;
    const activeBeacon = this.createScientificBeaconMesh(
      { ...speciesData, risk_target: speciesData.risk_target },
      displayLon,
      true
    );

    this.activePinGroup.add(activeBeacon);

    // Smoothly fly camera to face the species latitude with comfortable framing
    this.flyToLocation(lat, displayLon, 185);
  }

  updateActiveSpeciesRisk(riskTarget) {
    const riskColor = riskTarget === 'EXTINCT' ? 0xef4444 :
                      riskTarget === 'THREATENED' ? 0xf59e0b : 0x10b981;

    // Update active pin color
    if (this.activePinGroup && this.activePinGroup.children.length > 0) {
      const activePin = this.activePinGroup.children[0];
      if (activePin.children) {
        activePin.children.forEach((child) => {
          if (child.material && child.material.color) {
            child.material.color.setHex(riskColor);
          }
        });
      }
    }

    // Update active latitude ring color
    if (this.activeLatitudeRing && this.activeLatitudeRing.material) {
      this.activeLatitudeRing.material.color.setHex(riskColor);
    }
  }

  onCanvasPointerMove(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const searchTargets = [];
    if (this.pinGroup) searchTargets.push(...this.pinGroup.children);
    if (this.activePinGroup) searchTargets.push(...this.activePinGroup.children);
    if (this.isGlobalRiskExplorerActive && this.globalRiskExplorerGroup) {
      searchTargets.push(...this.globalRiskExplorerGroup.children);
    }

    const intersects = this.raycaster.intersectObjects(searchTargets, true);

    if (intersects.length > 0) {
      let hit = intersects[0].object;
      while (hit.parent && !hit.userData?.scientific_name && !hit.userData?.name) {
        hit = hit.parent;
      }
      const data = hit.userData;
      if (data && (data.scientific_name || data.name)) {
        const sciName = (data.scientific_name || data.name).replace(/_/g, ' ');
        const latVal = typeof data.latitude === 'number' ? data.latitude.toFixed(2) : 'N/A';
        const latSign = parseFloat(latVal) >= 0 ? '+' : '';
        const redlist = data.redlist_category || data.status || 'Evaluated';
        const target = data.risk_target || '';
        const className = data.class_name || 'Tetrapod';

        const color = target === 'EXTINCT' ? '#ef4444' : target === 'THREATENED' ? '#fbbf24' : '#34d399';

        if (this.tooltip) {
          this.tooltip.innerHTML = `
            <div class="tooltip-sci-name">${sciName}</div>
            <div class="tooltip-badge" style="color: ${color}; border-color: ${color}44; background: ${color}18;">${redlist} &bull; ${className}</div>
            <div class="tooltip-coord">Centroid Latitude: <strong>${latSign}${latVal}°</strong> (Dataset Centroid)</div>
            <div class="tooltip-action">Click to inspect in Intelligence Panel</div>
          `;
          const posX = Math.min(event.clientX + 16, window.innerWidth - 290);
          const posY = Math.min(event.clientY + 16, window.innerHeight - 130);
          this.tooltip.style.left = `${Math.max(12, posX)}px`;
          this.tooltip.style.top = `${Math.max(12, posY)}px`;
          this.tooltip.classList.add('visible');
        }
        this.renderer.domElement.style.cursor = 'pointer';
        return;
      }
    }

    if (this.tooltip) {
      this.tooltip.classList.remove('visible');
    }
    this.renderer.domElement.style.cursor = 'grab';
  }

  onCanvasClick(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const searchTargets = [];
    if (this.pinGroup) searchTargets.push(...this.pinGroup.children);
    if (this.activePinGroup) searchTargets.push(...this.activePinGroup.children);
    if (this.isGlobalRiskExplorerActive && this.globalRiskExplorerGroup) {
      searchTargets.push(...this.globalRiskExplorerGroup.children);
    }

    const intersects = this.raycaster.intersectObjects(searchTargets, true);

    if (intersects.length > 0) {
      let hit = intersects[0].object;
      while (hit.parent && !hit.userData?.scientific_name && !hit.userData?.name) {
        hit = hit.parent;
      }
      const data = hit.userData;
      if (data && (data.scientific_name || data.name)) {
        const sciName = data.scientific_name || data.name;
        const lat = typeof data.latitude === 'number' ? data.latitude : 0;
        const lon = typeof data.displayLon === 'number' ? data.displayLon : 0;
        this.flyToLocation(lat, lon, 185);
        if (this.onSelectSpecies) {
          this.onSelectSpecies(sciName);
        }
      }
    }
  }

  flyToLocation(lat, lon, targetDistance = 185) {
    const targetPos = this.latLonToVector3(lat, lon, targetDistance);
    
    // Smooth camera transition with sinusoidal ease
    const startPos = this.camera.position.clone();
    const duration = 1200;
    const startTime = performance.now();
    this.isAutoRotating = false;

    const animateCamera = (now) => {
      const progress = Math.min(1.0, (now - startTime) / duration);
      const ease = 0.5 - (0.5 * Math.cos(progress * Math.PI)); // smooth easeInOut

      this.camera.position.lerpVectors(startPos, targetPos, ease);
      this.controls.update();

      if (progress < 1.0) {
        requestAnimationFrame(animateCamera);
      }
    };
    requestAnimationFrame(animateCamera);
  }

  onWindowResize() {
    const width = this.container.clientWidth || window.innerWidth;
    const height = this.container.clientHeight || window.innerHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));

    // Smooth planetary rotation with realistic inertia
    if (this.isAutoRotating && this.globeGroup) {
      this.globeGroup.rotation.y += 0.0011;
    }

    // Decoupled cloud drift at differential altitude speeds
    if (this.cloudMesh) {
      this.cloudMesh.rotation.y += 0.00042;
    }
    if (this.cloudMeshOuter) {
      this.cloudMeshOuter.rotation.y += 0.00022;
    }

    // Earth Pulse visualization: dynamic risk-calibrated geospatial pulse waves
    const time = performance.now() * 0.003;
    const pulsePins = (group) => {
      if (!group) return;
      group.children.forEach((pin) => {
        if (!pin.children) return;
        const diamond = pin.children[1];
        const innerRing = pin.children[2];
        const radarRing = pin.children[3];
        const pulseWave = pin.children[4];
        const riskTarget = pin.userData?.risk_target || 'LOW_RISK';

        if (diamond) {
          diamond.rotation.y = time * 1.5;
        }
        if (innerRing) {
          const s = 1.0 + 0.18 * Math.sin(time);
          innerRing.scale.set(s, s, s);
        }
        if (radarRing) {
          const s2 = 1.0 + 0.32 * Math.sin(time * 1.2 + 0.3);
          radarRing.scale.set(s2, s2, s2);
        }
        if (pulseWave) {
          // Dynamic risk-calibrated frequency:
          // EXTINCT: 2.4x urgency cadence
          // THREATENED: 1.6x warning cadence
          // LOW_RISK: 0.9x tranquil breathing cadence
          const freq = riskTarget === 'EXTINCT' ? 2.4 : (riskTarget === 'THREATENED' ? 1.6 : 0.9);
          const cycle = (time * freq) % 1.0; // 0 to 1
          const waveScale = 1.0 + cycle * 3.4;
          pulseWave.scale.set(waveScale, waveScale, waveScale);
          if (pulseWave.material) {
            pulseWave.material.opacity = Math.max(0, 0.85 * (1.0 - cycle));
          }
        }
      });
    };

    pulsePins(this.pinGroup);
    pulsePins(this.activePinGroup);
    if (this.isGlobalRiskExplorerActive) {
      pulsePins(this.globalRiskExplorerGroup);
    }

    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
