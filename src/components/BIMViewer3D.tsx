import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { CoreBIMModel } from "../types";
import { Box, Eye, Sun, Layers } from "lucide-react";

interface BIMViewer3DProps {
  bimModel: CoreBIMModel;
  renderMode: "blueprint" | "semantic" | "realistic";
  wallHeight: number; // in cm equivalents, default e.g. 70
}

export default function BIMViewer3D({
  bimModel,
  renderMode,
  wallHeight = 70,
}: BIMViewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);

  const [cameraView, setCameraView] = useState<"perspective" | "top">("perspective");
  const [lightsOn, setLightsOn] = useState(true);
  const lightsRef = useRef<THREE.Group | null>(null);

  const centerXRef = useRef<number>(350);
  const centerZRef = useRef<number>(200);
  const maxDimRef = useRef<number>(500);

  useEffect(() => {
    if (!containerRef.current || !bimModel) return;

    // 1. INITIALIZE THREE.JS RUNTIME
    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 450;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#09090b"); 
    scene.fog = new THREE.FogExp2("#09090b", 0.0012);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 5000);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.05;
    controls.minDistance = 5;
    controls.maxDistance = 4000;
    controlsRef.current = controls;

    // 1.5 CALCULATE COORDINATE NORMALIZATION OFFSETS (For UTM/large coordinate systems like GÜZELCE)
    let offsetX = 0;
    let offsetZ = 0;
    let maxModelX = 0;
    let maxModelZ = 0;
    let hasLargeCoords = false;

    // Scan all spaces and walls to find bounding box
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    if (bimModel.spaces && Array.isArray(bimModel.spaces)) {
      bimModel.spaces.forEach((space) => {
        let poly: number[][] = [];
        if (space.polygon && space.polygon.length > 0) {
          poly = space.polygon;
        } else if ((space as any).boundary && (space as any).boundary.length > 0) {
          poly = (space as any).boundary.map((pt: any) => [pt.x, pt.y]);
        }
        poly.forEach(([x, y]) => {
          if (x > 10000 || y > 10000) hasLargeCoords = true;
          if (x < minX) minX = x;
          if (y < minY) minY = y;
          if (x > maxX) maxX = x;
          if (y > maxY) maxY = y;
        });
      });
    }

    if (bimModel.walls && Array.isArray(bimModel.walls)) {
      bimModel.walls.forEach((wall) => {
        const pts = wall.points || (wall as any).geometry?.points;
        if (pts) {
          pts.forEach(([x, y]) => {
            if (x > 10000 || y > 10000) hasLargeCoords = true;
            if (x < minX) minX = x;
            if (y < minY) minY = y;
            if (x > maxX) maxX = x;
            if (y > maxY) maxY = y;
          });
        }
      });
    }

    if (hasLargeCoords && minX !== Infinity && minY !== Infinity) {
      offsetX = minX;
      offsetZ = minY;
      maxModelX = maxX - minX;
      maxModelZ = maxY - minY;
    } else if (minX !== Infinity && minY !== Infinity) {
      maxModelX = maxX;
      maxModelZ = maxY;
    } else {
      maxModelX = 700;
      maxModelZ = 400;
    }

    // Default to origin coordinates if GÜZELCE bounding box is too tiny/large
    const centerX = maxModelX / 2;
    const centerZ = maxModelZ / 2;
    const maxDim = Math.max(maxModelX, maxModelZ) || 500;

    centerXRef.current = centerX;
    centerZRef.current = centerZ;
    maxDimRef.current = maxDim;

    controls.target.set(centerX, 0, centerZ);
    camera.position.set(centerX + maxDim * 0.6, maxDim * 0.7, centerZ + maxDim * 1.1);
    controls.update();

    // 2. LIGHTS SETUP
    const lightsGroup = new THREE.Group();
    
    const ambientLight = new THREE.AmbientLight(0xffffff, lightsOn ? 0.35 : 0.05);
    lightsGroup.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xfff7e6, lightsOn ? 0.8 : 0.1);
    dirLight.position.set(centerX + 200, 600, centerZ + 300);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 3000;
    const d = Math.max(maxDim, 500);
    dirLight.shadow.camera.left = -d;
    dirLight.shadow.camera.right = d;
    dirLight.shadow.camera.top = d;
    dirLight.shadow.camera.bottom = -d;
    lightsGroup.add(dirLight);

    const helperLight = new THREE.DirectionalLight(0x80b0ff, lightsOn ? 0.35 : 0.05);
    helperLight.position.set(centerX - 300, 400, centerZ - 200);
    lightsGroup.add(helperLight);

    scene.add(lightsGroup);
    lightsRef.current = lightsGroup;

    const grid = new THREE.GridHelper(maxDim * 2.5, 64, 0x3f3f46, 0x27272a);
    grid.position.set(centerX, 0.1, centerZ);
    scene.add(grid);

    // 3. GENERATE 3D MESHES PURELY FROM CANONICAL BIM MODEL
    const materials = getBIMMaterials(renderMode);

    // Helper: Geometry Generator
    const heightScale = wallHeight; 
    
    // 3.1 RENDER SPACES (ROOMS)
    if (bimModel.spaces && Array.isArray(bimModel.spaces)) {
      bimModel.spaces.forEach((space) => {
        let poly: number[][] = [];
        if (space.polygon && space.polygon.length >= 3) {
          poly = space.polygon;
        } else if ((space as any).boundary && (space as any).boundary.length >= 3) {
          poly = (space as any).boundary.map((pt: any) => [pt.x, pt.y]);
        }
        
        if (poly.length < 3) return;
        
        const shape = new THREE.Shape();
        shape.moveTo(poly[0][0] - offsetX, poly[0][1] - offsetZ);
        for (let i = 1; i < poly.length; i++) {
          shape.lineTo(poly[i][0] - offsetX, poly[i][1] - offsetZ);
        }
        
        const floorGeo = new THREE.ShapeGeometry(shape);
        const floorMesh = new THREE.Mesh(floorGeo, materials.roomFloor);
        floorMesh.rotation.x = -Math.PI / 2;
        floorMesh.position.y = 0.2; // Slightly above grid
        floorMesh.receiveShadow = true;
        scene.add(floorMesh);
      });
    }

    // 3.2 RENDER WALLS
    if (bimModel.walls && Array.isArray(bimModel.walls)) {
      bimModel.walls.forEach((wall) => {
        const pts = wall.points || (wall as any).geometry?.points;
        if (!pts || pts.length < 2) return;
        
        const x0 = pts[0][0] - offsetX;
        const z0 = pts[0][1] - offsetZ;
        const x1 = pts[1][0] - offsetX;
        const z1 = pts[1][1] - offsetZ;
        
        const dx = x1 - x0;
        const dz = z1 - z0;
        const length = Math.hypot(dx, dz);
        const angle = Math.atan2(-dz, dx);
        
        const cx = (x0 + x1) / 2.0;
        const cz = (z0 + z1) / 2.0;
        
        const thickness = (wall.thickness || 200) / 10.0; // mm to cm
        
        const wallGeo = new THREE.BoxGeometry(length, heightScale, thickness);
        const wallMesh = new THREE.Mesh(wallGeo, materials.wall);
        
        wallMesh.position.set(cx, heightScale / 2, cz);
        wallMesh.rotation.y = angle;
        wallMesh.castShadow = true;
        wallMesh.receiveShadow = true;
        
        scene.add(wallMesh);
      });
    }

    // 3.3 RENDER COLUMNS
    if (bimModel.columns && Array.isArray(bimModel.columns)) {
      bimModel.columns.forEach((col) => {
        const pts = col.points || (col as any).geometry?.points;
        if (!pts || pts.length === 0) return;
        
        let cx = 0, cz = 0, sizeX = 15, sizeZ = 15;
        if (pts.length >= 4) {
          const xs = pts.map(p => p[0] - offsetX);
          const zs = pts.map(p => p[1] - offsetZ);
          const minX = Math.min(...xs);
          const maxX = Math.max(...xs);
          const minZ = Math.min(...zs);
          const maxZ = Math.max(...zs);
          cx = (minX + maxX) / 2.0;
          cz = (minZ + maxZ) / 2.0;
          sizeX = maxX - minX;
          sizeZ = maxZ - minZ;
        } else {
          cx = pts[0][0] - offsetX;
          cz = pts[0][1] - offsetZ;
        }

        if (sizeX < 5) sizeX = 30;
        if (sizeZ < 5) sizeZ = 30;

        const colGeo = new THREE.BoxGeometry(sizeX, heightScale + 2, sizeZ);
        const colMesh = new THREE.Mesh(colGeo, materials.column);
        colMesh.position.set(cx, (heightScale + 2) / 2, cz);
        colMesh.castShadow = true;
        colMesh.receiveShadow = true;
        scene.add(colMesh);
      });
    }

    // 3.4 RENDER WINDOWS
    if (bimModel.windows && Array.isArray(bimModel.windows)) {
      bimModel.windows.forEach((win) => {
        const pts = win.points || (win as any).geometry?.points;
        if (!pts || pts.length < 2) return;
        
        const x0 = pts[0][0] - offsetX;
        const z0 = pts[0][1] - offsetZ;
        const x1 = pts[1][0] - offsetX;
        const z1 = pts[1][1] - offsetZ;
        
        const dx = x1 - x0;
        const dz = z1 - z0;
        const length = Math.hypot(dx, dz);
        const angle = Math.atan2(-dz, dx);
        
        const cx = (x0 + x1) / 2.0;
        const cz = (z0 + z1) / 2.0;
        
        const sillHeight = heightScale * 0.3;
        const windowHeight = heightScale * 0.5;
        const thickness = 18;

        const winGroup = new THREE.Group();
        winGroup.position.set(cx, sillHeight + windowHeight / 2, cz);
        winGroup.rotation.y = angle;

        // Frame
        const frameGeo = new THREE.BoxGeometry(length, windowHeight, thickness);
        const frameMesh = new THREE.Mesh(frameGeo, materials.windowFrame);
        frameMesh.castShadow = true;
        winGroup.add(frameMesh);

        // Glass
        const glassGeo = new THREE.BoxGeometry(length - 4, windowHeight - 4, thickness - 2);
        const glassMesh = new THREE.Mesh(glassGeo, materials.windowGlass);
        winGroup.add(glassMesh);

        scene.add(winGroup);
      });
    }
    
    // 3.5 RENDER DOORS
    if (bimModel.doors && Array.isArray(bimModel.doors)) {
      bimModel.doors.forEach((door) => {
        const pts = door.points || (door as any).geometry?.points;
        if (!pts || pts.length < 2) return;
        
        const x0 = pts[0][0] - offsetX;
        const z0 = pts[0][1] - offsetZ;
        const x1 = pts[1][0] - offsetX;
        const z1 = pts[1][1] - offsetZ;
        
        const dx = x1 - x0;
        const dz = z1 - z0;
        const length = Math.hypot(dx, dz);
        const angle = Math.atan2(-dz, dx);
        
        const cx = (x0 + x1) / 2.0;
        const cz = (z0 + z1) / 2.0;
        
        const doorHeight = heightScale * 0.8;
        
        const doorGroup = new THREE.Group();
        doorGroup.position.set(cx, doorHeight / 2, cz);
        doorGroup.rotation.y = angle;
        
        // Door panel
        const panelGeo = new THREE.BoxGeometry(length, doorHeight, 5);
        const panelMesh = new THREE.Mesh(panelGeo, materials.door);
        panelMesh.position.z = 2.5; // Offset to one side
        panelMesh.castShadow = true;
        doorGroup.add(panelMesh);
        
        scene.add(doorGroup);
      });
    }

    // RENDER LOOP
    const animate = () => {
      animationFrameIdRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // CLEANUP
    const handleResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current);
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
    };
  }, [bimModel, renderMode, wallHeight, lightsOn]);

  // View toggles
  useEffect(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    const cx = centerXRef.current;
    const cz = centerZRef.current;
    const maxDim = maxDimRef.current;

    if (cameraView === "top") {
      cameraRef.current.position.set(cx, maxDim * 1.5, cz);
      controlsRef.current.target.set(cx, 0, cz);
    } else {
      cameraRef.current.position.set(cx + maxDim * 0.6, maxDim * 0.7, cz + maxDim * 1.1);
      controlsRef.current.target.set(cx, 0, cz);
    }
    controlsRef.current.update();
  }, [cameraView]);

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden bg-[#09090b] ring-1 ring-white/10 shadow-2xl">
      <div ref={containerRef} className="absolute inset-0" />

      {/* Floating Toolbar */}
      <div className="absolute top-4 right-4 flex items-center gap-2 p-2 bg-zinc-900/80 backdrop-blur-md border border-white/10 rounded-full shadow-lg z-10">
        <button
          onClick={() => setCameraView(cameraView === "perspective" ? "top" : "perspective")}
          className="p-2 rounded-full text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          title="Toggle Perspective/Top Down"
        >
          {cameraView === "perspective" ? <Eye className="w-4 h-4" /> : <Box className="w-4 h-4" />}
        </button>
        <button
          onClick={() => setLightsOn(!lightsOn)}
          className={`p-2 rounded-full transition-colors ${
            lightsOn ? "text-amber-400 hover:bg-white/10" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/10"
          }`}
          title="Toggle Global Illumination"
        >
          <Sun className="w-4 h-4" />
        </button>
      </div>

      <div className="absolute bottom-4 left-4 flex items-center gap-2 p-2 px-4 bg-zinc-900/80 backdrop-blur-md border border-white/10 rounded-full shadow-lg z-10 pointer-events-none">
        <Layers className="w-4 h-4 text-emerald-400" />
        <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Canonical BIM Model View</span>
      </div>
    </div>
  );
}

// =====================================
// MATERIALS FACTORY
// =====================================
function getBIMMaterials(mode: "blueprint" | "semantic" | "realistic") {
  // Realistic (Architectural default)
  if (mode === "realistic") {
    return {
      wall: new THREE.MeshStandardMaterial({ color: 0xf4f4f5, roughness: 0.9, metalness: 0.0 }), // Zinc 100 plaster
      column: new THREE.MeshStandardMaterial({ color: 0xd4d4d8, roughness: 0.7, metalness: 0.1 }), // Concrete
      door: new THREE.MeshStandardMaterial({ color: 0x8b5a2b, roughness: 0.8, metalness: 0.1 }), // Wood
      windowFrame: new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.5, metalness: 0.8 }), // Dark Aluminium
      windowGlass: new THREE.MeshPhysicalMaterial({
        color: 0xbae6fd,
        metalness: 0.9,
        roughness: 0.1,
        transmission: 0.8, // glass effect
        transparent: true,
      }),
      roomFloor: new THREE.MeshStandardMaterial({ color: 0xe4e4e7, roughness: 0.9, metalness: 0.0 }),
    };
  }
  
  // Semantic (Color Coded Analysis)
  if (mode === "semantic") {
    return {
      wall: new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 1.0, wireframe: false }), // Blue walls
      column: new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 1.0 }), // Red columns
      door: new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 1.0 }), // Emerald doors
      windowFrame: new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 1.0 }), // Amber windows
      windowGlass: new THREE.MeshBasicMaterial({ color: 0xfcd34d, transparent: true, opacity: 0.5 }),
      roomFloor: new THREE.MeshStandardMaterial({ color: 0x8b5cf6, transparent: true, opacity: 0.3 }), // Purple rooms
    };
  }

  // Blueprint (X-Ray / Technical)
  return {
    wall: new THREE.MeshBasicMaterial({ color: 0x60a5fa, wireframe: true, transparent: true, opacity: 0.6 }),
    column: new THREE.MeshBasicMaterial({ color: 0xf87171, wireframe: true, transparent: true, opacity: 0.8 }),
    door: new THREE.MeshBasicMaterial({ color: 0x34d399, wireframe: true }),
    windowFrame: new THREE.MeshBasicMaterial({ color: 0xfbbf24, wireframe: true }),
    windowGlass: new THREE.MeshBasicMaterial({ color: 0xfef08a, transparent: true, opacity: 0.2 }),
    roomFloor: new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.1, wireframe: true }),
  };
}
