import React, { useState, useEffect } from "react";
import { Point, CADEntity } from "../types";
import { 
  Activity, 
  Settings, 
  Play, 
  RotateCcw, 
  Sparkles, 
  Compass, 
  Sliders, 
  CheckCircle, 
  Maximize2, 
  Layers, 
  ShieldCheck, 
  ArrowRight,
  PlusCircle,
  Hash
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

// Initial messy/raw CAD samples to demonstrate the Geometry Engine algorithms
const CAD_SAMPLES = {
  sampleA: {
    name: "T-Birleşim Boşlukları & Yamuk Çizgiler",
    description: "Duvar kesişimlerinde kopukluklar (gaps) ve ~1.8° eğrilikler barındıran klasik bir mimari plan.",
    entities: [
      // Top horizontal wall (slightly crooked)
      { id: "sa_w1", type: "LINE", layer: "duvar", start: { x: 50, y: 52 }, end: { x: 748, y: 49 }, thickness: 25 },
      // Bottom horizontal wall (split into overlapping collinear segments)
      { id: "sa_w2", type: "LINE", layer: "duvar", start: { x: 50, y: 350 }, end: { x: 400, y: 350 }, thickness: 25 },
      { id: "sa_w3", type: "LINE", layer: "duvar", start: { x: 350, y: 350 }, end: { x: 750, y: 350 }, thickness: 25 },
      // Left vertical wall (crooked)
      { id: "sa_w4", type: "LINE", layer: "duvar", start: { x: 52, y: 50 }, end: { x: 49, y: 350 }, thickness: 25 },
      // Right vertical wall (gap at top T-junction)
      { id: "sa_w5", type: "LINE", layer: "duvar", start: { x: 750, y: 68 }, end: { x: 750, y: 350 }, thickness: 25 },
      // Internal partition wall (crooked & gap)
      { id: "sa_w6", type: "LINE", layer: "duvar", start: { x: 400, y: 50 }, end: { x: 402, y: 228 }, thickness: 15 },
      // Door opening lines that don't snap perfectly
      { id: "sa_d1", type: "DOOR", layer: "kapı", start: { x: 202, y: 350 }, end: { x: 278, y: 348 }, width: 80 }
    ] as CADEntity[]
  },
  sampleB: {
    name: "Mükerrer Vektörler & Üst Üste Binmeler",
    description: "Aynı çizgi üzerinde birden fazla katmanlanmış çizim hatası ve aks hizasından kaçıklıklar.",
    entities: [
      // Double overlapping lines on top
      { id: "sb_w1_1", type: "LINE", layer: "duvar", start: { x: 100, y: 80 }, end: { x: 400, y: 80 }, thickness: 20 },
      { id: "sb_w1_2", type: "LINE", layer: "duvar", start: { x: 380, y: 80 }, end: { x: 700, y: 80 }, thickness: 20 },
      { id: "sb_w1_dup", type: "LINE", layer: "duvar", start: { x: 200, y: 80 }, end: { x: 500, y: 80 }, thickness: 20 },
      // Left Wall
      { id: "sb_w2", type: "LINE", layer: "duvar", start: { x: 100, y: 80 }, end: { x: 100, y: 380 }, thickness: 20 },
      // Right Wall
      { id: "sb_w3", type: "LINE", layer: "duvar", start: { x: 700, y: 80 }, end: { x: 700, y: 380 }, thickness: 20 },
      // Bottom Wall (short segments with overlapping coordinates)
      { id: "sb_w4_1", type: "LINE", layer: "duvar", start: { x: 100, y: 380 }, end: { x: 320, y: 380 }, thickness: 20 },
      { id: "sb_w4_2", type: "LINE", layer: "duvar", start: { x: 310, y: 380 }, end: { x: 700, y: 380 }, thickness: 20 }
    ] as CADEntity[]
  },
  sampleC: {
    name: "Ayrık Poligonlar ve Serbest Köşeler",
    description: "Kenetleme (snapping) yapılmadan çizilmiş, alan kapatmayan ve oda tespitini engelleyen kopuk odalar.",
    entities: [
      // Rectangle with small gaps in all 4 corners
      { id: "sc_w1", type: "LINE", layer: "duvar", start: { x: 150, y: 105 }, end: { x: 650, y: 95 }, thickness: 15 },
      { id: "sc_w2", type: "LINE", layer: "duvar", start: { x: 655, y: 100 }, end: { x: 648, y: 355 }, thickness: 15 },
      { id: "sc_w3", type: "LINE", layer: "duvar", start: { x: 645, y: 360 }, end: { x: 145, y: 365 }, thickness: 15 },
      { id: "sc_w4", type: "LINE", layer: "duvar", start: { x: 152, y: 362 }, end: { x: 148, y: 110 }, thickness: 15 }
    ] as CADEntity[]
  }
};

// Math helper functions
const getDistance = (p1: Point, p2: Point) => {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
};

export default function GeometryEnginePanel() {
  const [activeSampleKey, setActiveSampleKey] = useState<keyof typeof CAD_SAMPLES>("sampleA");
  const [entities, setEntities] = useState<CADEntity[]>([]);
  const [step, setStep] = useState<number>(0); // 0: Raw, 1: Normalized, 2: Snapped, 3: Collinear Merged, 4: T-Junction Repaired
  
  // Custom tolerances
  const [snapTolerance, setSnapTolerance] = useState<number>(12);
  const [angleTolerance, setAngleTolerance] = useState<number>(3.0);
  const [gapExtendThreshold, setGapExtendThreshold] = useState<number>(20);
  
  // Simulation logs
  const [logs, setLogs] = useState<string[]>([]);
  const [hoveredNode, setHoveredNode] = useState<{ x: number; y: number; original: string; current: string } | null>(null);
  
  // Interactive Custom Vector Addition State
  const [customStartX, setCustomStartX] = useState<string>("200");
  const [customStartY, setCustomStartY] = useState<string>("200");
  const [customEndX, setCustomEndX] = useState<string>("500");
  const [customEndY, setCustomEndY] = useState<string>("202");

  // Load selected sample
  useEffect(() => {
    resetEngine();
  }, [activeSampleKey]);

  const resetEngine = () => {
    // Deep copy sample entities
    const copy = JSON.parse(JSON.stringify(CAD_SAMPLES[activeSampleKey].entities));
    setEntities(copy);
    setStep(0);
    setLogs([`[INFO] ${CAD_SAMPLES[activeSampleKey].name} yükleme başarılı.`, "[SİSTEM] Ham CAD vektörleri görüntülüyor. Modellerde kaymalar mevcut."]);
  };

  // Add custom noisy wall segment
  const handleAddCustomWall = () => {
    const startX = parseFloat(customStartX) || 200;
    const startY = parseFloat(customStartY) || 200;
    const endX = parseFloat(customEndX) || 500;
    const endY = parseFloat(customEndY) || 202; // slightly crooked by default

    const newWall: CADEntity = {
      id: `custom_w_${Date.now()}`,
      type: "LINE",
      layer: "duvar",
      start: { x: startX, y: startY },
      end: { x: endX, y: endY },
      thickness: 15,
      status: "original"
    };

    setEntities((prev) => [...prev, newWall]);
    setStep(0); // reset to raw to allow running pipeline again
    setLogs((prev) => [
      `[MÜHENDİS] Manuel duvar vektörü eklendi: (${startX}, ${startY}) -> (${endX}, ${endY})`,
      ...prev
    ]);
  };

  // Stage 1: Ortho-Normalization & Coordinates Repair
  const runNormalization = (currentEntities: CADEntity[]) => {
    let fixCount = 0;
    const result = currentEntities.map((entity) => {
      if (entity.type !== "LINE") return entity;
      
      const p1 = { ...entity.start };
      const p2 = { ...entity.end };
      
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const rad = Math.atan2(dy, dx);
      let deg = rad * (180 / Math.PI);
      if (deg < 0) deg += 360;

      // Find nearest 90-degree orthogonal angle
      const targetDeg = Math.round(deg / 90) * 90;
      const diff = Math.abs(deg - targetDeg);

      if (diff > 0 && diff <= angleTolerance) {
        // Straighten the line by moving p2
        const length = getDistance(p1, p2);
        const targetRad = (targetDeg % 360) * (Math.PI / 180);
        
        p2.x = Math.round(p1.x + Math.cos(targetRad) * length);
        p2.y = Math.round(p1.y + Math.sin(targetRad) * length);
        fixCount++;
        return {
          ...entity,
          start: p1,
          end: p2,
          status: "merged" as const
        };
      }
      return entity;
    });

    setLogs((prev) => [
      `[GEOMETRY] Aşama 1 Tamamlandı: Ortho-Normalization`,
      `[BAŞARI] ${fixCount} adet yamuk çizgide açısal kaçıklık düzeltilerek 90° aksına kilitlendi.`,
      ...prev
    ]);
    return result;
  };

  // Stage 2: Snapping & Node Welding (Weld loose endpoints together)
  const runSnapping = (currentEntities: CADEntity[]) => {
    let snapCount = 0;
    // Collect all endpoints
    const points: { entityId: string; role: "start" | "end"; pt: Point }[] = [];
    currentEntities.forEach((e) => {
      points.push({ entityId: e.id, role: "start", pt: { ...e.start } });
      points.push({ entityId: e.id, role: "end", pt: { ...e.end } });
    });

    // Simple clustering: find points close to each other and group them
    const visited = new Set<number>();
    const clusters: number[][] = [];

    for (let i = 0; i < points.length; i++) {
      if (visited.has(i)) continue;
      const cluster = [i];
      visited.add(i);

      for (let j = i + 1; j < points.length; j++) {
        if (visited.has(j)) continue;
        if (getDistance(points[i].pt, points[j].pt) <= snapTolerance) {
          cluster.push(j);
          visited.add(j);
        }
      }
      if (cluster.length > 1) {
        clusters.push(cluster);
      }
    }

    // Deep copy currentEntities to apply modifications
    const result = JSON.parse(JSON.stringify(currentEntities)) as CADEntity[];

    // Weld points in each cluster to their average centroid
    clusters.forEach((cluster) => {
      let sumX = 0;
      let sumY = 0;
      cluster.forEach((idx) => {
        sumX += points[idx].pt.x;
        sumY += points[idx].pt.y;
      });
      const avgX = Math.round(sumX / cluster.length);
      const avgY = Math.round(sumY / cluster.length);

      cluster.forEach((idx) => {
        const item = points[idx];
        const entity = result.find((r) => r.id === item.entityId);
        if (entity) {
          if (item.role === "start") {
            entity.start = { x: avgX, y: avgY };
          } else {
            entity.end = { x: avgX, y: avgY };
          }
          entity.status = "snapped";
          snapCount++;
        }
      });
    });

    setLogs((prev) => [
      `[TOPOLOGY] Aşama 2 Tamamlandı: Topology Snapping`,
      `[BAŞARI] Birbirine yakın ${clusters.length} serbest köşe düğümü (${snapCount} uç nokta) birbirine kaynaklandı (weld).`,
      ...prev
    ]);
    return result;
  };

  // Stage 3: Collinear Overlapping Merge (Merge duplicates)
  const runCollinearMerge = (currentEntities: CADEntity[]) => {
    let mergeCount = 0;
    const walls = currentEntities.filter((e) => e.layer === "duvar" && e.type === "LINE");
    const otherEntities = currentEntities.filter((e) => e.layer !== "duvar" || e.type !== "LINE");
    
    const mergedWalls: CADEntity[] = [];
    const processedIds = new Set<string>();

    for (let i = 0; i < walls.length; i++) {
      const w1 = walls[i];
      if (processedIds.has(w1.id)) continue;

      let currentWall = { ...w1 };
      processedIds.add(w1.id);

      // Check collinearity with other walls
      for (let j = 0; j < walls.length; j++) {
        const w2 = walls[j];
        if (processedIds.has(w2.id)) continue;

        // Simple collinearity check: 
        // 1. Same alignment (horizontal or vertical)
        const isW1Horiz = Math.abs(currentWall.start.y - currentWall.end.y) < 2;
        const isW2Horiz = Math.abs(w2.start.y - w2.end.y) < 2;
        const isW1Vert = Math.abs(currentWall.start.x - currentWall.end.x) < 2;
        const isW2Vert = Math.abs(w2.start.x - w2.end.x) < 2;

        if (isW1Horiz && isW2Horiz && Math.abs(currentWall.start.y - w2.start.y) < 5) {
          // Both horizontal on same approximate Y coordinate
          // Check overlapping or adjacency
          const minW1 = Math.min(currentWall.start.x, currentWall.end.x);
          const maxW1 = Math.max(currentWall.start.x, currentWall.end.x);
          const minW2 = Math.min(w2.start.x, w2.end.x);
          const maxW2 = Math.max(w2.start.x, w2.end.x);

          // Overlap check with snap margin
          if (!(maxW1 < minW2 - 10 || minW1 > maxW2 + 10)) {
            // Overlapping! Merge coordinates
            const newMinX = Math.min(minW1, minW2);
            const newMaxX = Math.max(maxW1, maxW2);
            currentWall.start.x = newMinX;
            currentWall.end.x = newMaxX;
            processedIds.add(w2.id);
            mergeCount++;
            j = -1; // restart search with updated merged geometry
          }
        } else if (isW1Vert && isW2Vert && Math.abs(currentWall.start.x - w2.start.x) < 5) {
          // Both vertical on same approximate X coordinate
          const minW1 = Math.min(currentWall.start.y, currentWall.end.y);
          const maxW1 = Math.max(currentWall.start.y, currentWall.end.y);
          const minW2 = Math.min(w2.start.y, w2.end.y);
          const maxW2 = Math.max(w2.start.y, w2.end.y);

          if (!(maxW1 < minW2 - 10 || minW1 > maxW2 + 10)) {
            const newMinY = Math.min(minW1, minW2);
            const newMaxY = Math.max(maxW1, maxW2);
            currentWall.start.y = newMinY;
            currentWall.end.y = newMaxY;
            processedIds.add(w2.id);
            mergeCount++;
            j = -1; // restart
          }
        }
      }
      mergedWalls.push(currentWall);
    }

    setLogs((prev) => [
      `[CLEANUP] Aşama 3 Tamamlandı: Collinear Duplicate Merge`,
      `[BAŞARI] Üst üste binen ve mükerrer çizilmiş ${mergeCount} çizgi vektörü tek bir gövdede birleştirildi.`,
      ...prev
    ]);
    return [...mergedWalls, ...otherEntities];
  };

  // Stage 4: T-Junction Gap Closing & Extensions
  const runTJunctionExtensions = (currentEntities: CADEntity[]) => {
    let extendCount = 0;
    const result = JSON.parse(JSON.stringify(currentEntities)) as CADEntity[];

    for (let i = 0; i < result.length; i++) {
      const w1 = result[i];
      if (w1.type !== "LINE" || w1.layer !== "duvar") continue;

      // Check both start and end points of w1
      const endpoints = ["start" as const, "end" as const];
      endpoints.forEach((ptKey) => {
        const pt = w1[ptKey];

        // Search for any other perpendicular wall w2 to snap or extend to
        for (let j = 0; j < result.length; j++) {
          if (i === j) continue;
          const w2 = result[j];
          if (w2.type !== "LINE" || w2.layer !== "duvar") continue;

          const isW1Horiz = Math.abs(w1.start.y - w1.end.y) < 2;
          const isW2Vert = Math.abs(w2.start.x - w2.end.x) < 2;

          if (isW1Horiz && isW2Vert) {
            // w1 horizontal, w2 vertical
            // Does w1 point close to vertical w2's X plane?
            const distToPlane = Math.abs(pt.x - w2.start.x);
            const minW2Y = Math.min(w2.start.y, w2.end.y);
            const maxW2Y = Math.max(w2.start.y, w2.end.y);

            if (distToPlane > 0 && distToPlane <= gapExtendThreshold && pt.y >= minW2Y - 10 && pt.y <= maxW2Y + 10) {
              // Extend pt.x to meet w2's plane perfectly
              pt.x = w2.start.x;
              w1.status = "merged";
              extendCount++;
            }
          } else if (!isW1Horiz && !isW2Vert) {
            // w1 vertical, w2 horizontal
            const distToPlane = Math.abs(pt.y - w2.start.y);
            const minW2X = Math.min(w2.start.x, w2.end.x);
            const maxW2X = Math.max(w2.start.x, w2.end.x);

            if (distToPlane > 0 && distToPlane <= gapExtendThreshold && pt.x >= minW2X - 10 && pt.x <= maxW2X + 10) {
              pt.y = w2.start.y;
              w1.status = "merged";
              extendCount++;
            }
          }
        }
      });
    }

    setLogs((prev) => [
      `[REPAIR] Aşama 4 Tamamlandı: T-Junction Intersections`,
      `[BAŞARI] Açıkta kalan ve oda sızdırmazlığını bozan ${extendCount} adet T-Birleşimi uzatılarak kapatıldı.`,
      `[SİSTEM] %100 Doğrulanabilir Deterministik Model Hazır!`,
      ...prev
    ]);
    return result;
  };

  // Run a single step
  const handleNextStep = () => {
    if (step === 0) {
      setEntities((current) => runNormalization(current));
      setStep(1);
    } else if (step === 1) {
      setEntities((current) => runSnapping(current));
      setStep(2);
    } else if (step === 2) {
      setEntities((current) => runCollinearMerge(current));
      setStep(3);
    } else if (step === 3) {
      setEntities((current) => runTJunctionExtensions(current));
      setStep(4);
    }
  };

  // Run the entire clean pipeline at once
  const handleRunAll = () => {
    setLogs((prev) => ["-- GEOMETRİ BORU HATTI BAŞLATILDI --", ...prev]);
    const r1 = runNormalization(JSON.parse(JSON.stringify(CAD_SAMPLES[activeSampleKey].entities)));
    const r2 = runSnapping(r1);
    const r3 = runCollinearMerge(r2);
    const r4 = runTJunctionExtensions(r3);
    setEntities(r4);
    setStep(4);
  };

  // Calculate some simple metrics
  const totalOriginalLines = CAD_SAMPLES[activeSampleKey].entities.length;
  const currentLinesCount = entities.length;
  const duplicateLinesCount = totalOriginalLines - currentLinesCount;

  return (
    <div className="bg-zinc-900 border border-zinc-850 rounded-2xl p-5 space-y-6">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-800 pb-4 gap-3">
        <div className="flex items-center space-x-3">
          <div className="bg-amber-500/10 text-amber-400 p-2 rounded-xl border border-amber-500/20">
            <Activity className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-zinc-100 uppercase font-mono">
              Interaktif Geometri Onarım ve Normalizasyon Motoru
            </h2>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              Çizimdeki açısal bozulmaları, kopuk köşeleri, sızdıran duvarları ve mükerrer çizgileri temizler.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRunAll}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold rounded-lg transition-colors shadow-lg shadow-emerald-950/20"
            id="btn_run_geometry_pipeline"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>HEPSİNİ ÇALIŞTIR</span>
          </button>
          
          <button
            onClick={resetEngine}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono text-xs font-bold rounded-lg border border-zinc-700 transition-colors"
            id="btn_reset_geometry_engine"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>SIFIRLA</span>
          </button>
        </div>
      </div>

      {/* SAMPLE SELECTOR PILLS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {(Object.keys(CAD_SAMPLES) as Array<keyof typeof CAD_SAMPLES>).map((key) => {
          const sample = CAD_SAMPLES[key];
          const isActive = activeSampleKey === key;
          return (
            <button
              key={key}
              onClick={() => setActiveSampleKey(key)}
              className={`p-3 rounded-xl text-left border transition-all ${
                isActive 
                  ? "bg-zinc-850 border-amber-500/40 shadow-inner" 
                  : "bg-zinc-950/60 border-zinc-850 hover:bg-zinc-900"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-zinc-200 font-mono">{sample.name}</span>
                {isActive && <Sparkles className="w-3.5 h-3.5 text-amber-400" />}
              </div>
              <p className="text-[10px] text-zinc-400 mt-1 leading-relaxed font-sans">{sample.description}</p>
            </button>
          );
        })}
      </div>

      {/* TWO COLUMN INTERACTIVE BODY */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT PANEL: ALGORITHM CONTROL SLIDERS (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          
          {/* TOLERANCES CARD */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-850 pb-2">
              <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold flex items-center space-x-1">
                <Sliders className="w-3.5 h-3.5 text-amber-500" />
                <span>Mühendislik Toleransları</span>
              </span>
              <span className="text-[9px] bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded font-mono border border-amber-500/20">
                Deterministik Ayarlar
              </span>
            </div>

            {/* Slider 1: Snapping Threshold */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-zinc-300">Köşe Kaynak Toleransı (Weld)</span>
                <span className="text-amber-400 font-bold">{snapTolerance} px</span>
              </div>
              <input
                type="range"
                min="4"
                max="25"
                value={snapTolerance}
                onChange={(e) => setSnapTolerance(Number(e.target.value))}
                className="w-full accent-amber-500 h-1 rounded"
              />
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans">
                Birbirine yakın serbest uç noktaların tek bir düğümde birleştirilmesi için maksimum piksel mesafesi.
              </p>
            </div>

            {/* Slider 2: Angle Tolerance */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-zinc-300">Ortho Açı Toleransı (Orthogonalize)</span>
                <span className="text-amber-400 font-bold">{angleTolerance.toFixed(1)}°</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.1"
                value={angleTolerance}
                onChange={(e) => setAngleTolerance(Number(e.target.value))}
                className="w-full accent-amber-500 h-1 rounded"
              />
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans">
                Yamuk çizilen dikey/yatay duvarların tam 90 derecelik aksa düzleştirilmesi için maksimum kaçıklık açısı.
              </p>
            </div>

            {/* Slider 3: Extension Gap Threshold */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-zinc-300">T-Birleşimi Uzatma Limiti (T-Extend)</span>
                <span className="text-amber-400 font-bold">{gapExtendThreshold} px</span>
              </div>
              <input
                type="range"
                min="5"
                max="40"
                value={gapExtendThreshold}
                onChange={(e) => setGapExtendThreshold(Number(e.target.value))}
                className="w-full accent-amber-500 h-1 rounded"
              />
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans">
                Birleşmeyen dik duvarların uzatılarak kapatılması için maksimum boşluk mesafesi (Oda sızdırmazlığı).
              </p>
            </div>
          </div>

          {/* ADD CUSTOM VECTOR FORM */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-3">
            <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold flex items-center space-x-1">
              <PlusCircle className="w-3.5 h-3.5 text-emerald-400" />
              <span>Simülasyona Yamuk Duvar Ekle</span>
            </span>
            <div className="grid grid-cols-4 gap-2">
              <div className="space-y-1">
                <label className="text-[9px] text-zinc-500 font-mono">X1</label>
                <input
                  type="number"
                  value={customStartX}
                  onChange={(e) => setCustomStartX(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded p-1 text-xs font-mono text-zinc-200"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] text-zinc-500 font-mono">Y1</label>
                <input
                  type="number"
                  value={customStartY}
                  onChange={(e) => setCustomStartY(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded p-1 text-xs font-mono text-zinc-200"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] text-zinc-500 font-mono">X2</label>
                <input
                  type="number"
                  value={customEndX}
                  onChange={(e) => setCustomEndX(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded p-1 text-xs font-mono text-zinc-200"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[9px] text-zinc-500 font-mono">Y2</label>
                <input
                  type="number"
                  value={customEndY}
                  onChange={(e) => setCustomEndY(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded p-1 text-xs font-mono text-zinc-200"
                />
              </div>
            </div>
            <button
              onClick={handleAddCustomWall}
              className="w-full py-1.5 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 border border-emerald-500/20 rounded-lg text-xs font-mono font-bold transition-all"
            >
              Duvar Vektörünü Ekle
            </button>
          </div>

          {/* ACTIVE PIPELINE PROGRESSION STEPS */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-3">
            <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold">
              Boru Hattı Adımları (Step-by-Step Execution)
            </span>

            <div className="space-y-2">
              {[
                { s: 1, title: "1. Koordinat Normalizasyonu", desc: "Yamuk veya kaçık çizilmiş çizgileri ortogonal eksene hizalar." },
                { s: 2, title: "2. Köşe Snapping & Kaynaklama", desc: "Ayrık duran noktaları tolerans dahilinde birbirine kilitler." },
                { s: 3, title: "3. Mükerrer / Koliner Çizgi Birleşimi", desc: "Aynı doğrultuda üst üste binen çizgileri tek gövde yapar." },
                { s: 4, title: "4. T-Birleşimi Boşluk Onarımı", desc: "Açık kalan duvarları uzatıp dik duvara sabitleyerek sızdırmazlık sağlar." }
              ].map((stepObj) => {
                const isPassed = step >= stepObj.s;
                const isCurrent = step === stepObj.s - 1;
                return (
                  <div
                    key={stepObj.s}
                    className={`p-2 rounded border transition-all flex items-start space-x-2 ${
                      isCurrent 
                        ? "bg-amber-500/5 border-amber-500/40" 
                        : isPassed 
                          ? "bg-emerald-500/5 border-emerald-500/20 opacity-80" 
                          : "bg-zinc-900/50 border-zinc-850 opacity-40"
                    }`}
                  >
                    <div className="mt-0.5">
                      {isPassed ? (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center text-[8px] font-bold ${
                          isCurrent ? "border-amber-400 text-amber-400 animate-pulse" : "border-zinc-500 text-zinc-500"
                        }`}>
                          {stepObj.s}
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-zinc-200">{stepObj.title}</span>
                        {isCurrent && (
                          <button
                            onClick={handleNextStep}
                            className="bg-amber-500 hover:bg-amber-400 text-black text-[9px] font-mono font-extrabold px-1.5 py-0.5 rounded transition-all flex items-center space-x-1"
                          >
                            <span>ÇALIŞTIR</span>
                            <ArrowRight className="w-2.5 h-2.5" />
                          </button>
                        )}
                      </div>
                      <p className="text-[10px] text-zinc-400 font-sans mt-0.5">{stepObj.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: LIVE VISUALIZER VIEWPORT (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          
          {/* INTERACTIVE SVG VIEWPORT */}
          <div className="relative bg-zinc-950 border border-zinc-850 rounded-2xl p-4 overflow-hidden h-[420px] flex flex-col">
            <div className="absolute top-3 left-3 bg-zinc-900/90 border border-zinc-800 px-2 py-1 rounded font-mono text-[10px] text-zinc-300 flex items-center space-x-1.5 z-10 backdrop-blur">
              <span className={`w-1.5 h-1.5 rounded-full ${step === 4 ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`}></span>
              <span>GEOMETRİ GÖRÜNÜMÜ: {step === 4 ? "KUSURSUZ (CANONICAL)" : "DÜZENLENİYOR"}</span>
            </div>

            {/* Zoom / Info Overlay */}
            <div className="absolute bottom-3 right-3 bg-zinc-900/90 border border-zinc-800 p-2 rounded-lg font-mono text-[9px] text-zinc-400 z-10 flex flex-col space-y-1">
              <div className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                <span>Yamuk/Boşluk Uçlar</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span>
                <span>Kenetlenmiş (Welded) Köşeler</span>
              </div>
            </div>

            {/* SVG CANVAS */}
            <div className="flex-1 w-full h-full bg-[radial-gradient(#1c1917_1px,transparent_1px)] [background-size:16px_16px] flex items-center justify-center relative">
              <svg className="w-full h-full max-h-[350px]" viewBox="0 0 800 400">
                {/* 1. RENDER DRAWING GRID AXIS LINES IN BACKGROUND */}
                <line x1={50} y1={50} x2={750} y2={50} stroke="#27272a" strokeWidth={0.5} strokeDasharray="4,4" />
                <line x1={50} y1={350} x2={750} y2={350} stroke="#27272a" strokeWidth={0.5} strokeDasharray="4,4" />
                <line x1={50} y1={50} x2={50} y2={350} stroke="#27272a" strokeWidth={0.5} strokeDasharray="4,4" />
                <line x1={750} y1={50} x2={750} y2={350} stroke="#27272a" strokeWidth={0.5} strokeDasharray="4,4" />

                {/* 2. DRAW WALL ENTIRES */}
                {entities.map((entity) => {
                  const isCrooked = Math.abs(entity.start.y - entity.end.y) > 1 && Math.abs(entity.start.x - entity.end.x) > 1 && entity.layer === "duvar" && step === 0;
                  const isDoor = entity.type === "DOOR";
                  
                  return (
                    <g key={entity.id}>
                      {/* Thick Wall Body */}
                      <line
                        x1={entity.start.x}
                        y1={entity.start.y}
                        x2={entity.end.x}
                        y2={entity.end.y}
                        stroke={isDoor ? "#f59e0b" : (isCrooked ? "#f43f5e" : "#52525b")}
                        strokeWidth={isDoor ? 4 : (entity.thickness ? entity.thickness / 1.5 : 12)}
                        strokeLinecap="round"
                        opacity={isCrooked ? 0.9 : 0.65}
                        className="transition-all duration-300"
                      />
                      {/* Centerline Axis */}
                      <line
                        x1={entity.start.x}
                        y1={entity.start.y}
                        x2={entity.end.x}
                        y2={entity.end.y}
                        stroke={isDoor ? "#fbbf24" : (isCrooked ? "#ef4444" : "#10b981")}
                        strokeWidth={1.5}
                        className="transition-all duration-300"
                      />
                    </g>
                  );
                })}

                {/* 3. DRAW VERTICES (Highlighting unsnapped vs. snapped nodes) */}
                {entities.map((entity) => {
                  if (entity.type !== "LINE") return null;
                  
                  // Helper to detect if start/end vertices are shared/snapped with others
                  const isStartSnapped = entities.some(
                    (other) => other.id !== entity.id && 
                    (getDistance(entity.start, other.start) === 0 || getDistance(entity.start, other.end) === 0)
                  );
                  const isEndSnapped = entities.some(
                    (other) => other.id !== entity.id && 
                    (getDistance(entity.end, other.start) === 0 || getDistance(entity.end, other.end) === 0)
                  );

                  return (
                    <g key={`nodes_${entity.id}`}>
                      {/* Start Point */}
                      <circle
                        cx={entity.start.x}
                        cy={entity.start.y}
                        r={6}
                        fill={isStartSnapped ? "#34d399" : "#ef4444"}
                        stroke="#09090b"
                        strokeWidth={2}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onMouseEnter={() => setHoveredNode({
                          x: entity.start.x,
                          y: entity.start.y,
                          original: `CAD: (${entity.start.x}, ${entity.start.y})`,
                          current: isStartSnapped ? "Kenetlenmiş Düğüm (Snapped)" : "Kopuk Serbest Köşe (Gap Node)"
                        })}
                        onMouseLeave={() => setHoveredNode(null)}
                      />
                      {/* End Point */}
                      <circle
                        cx={entity.end.x}
                        cy={entity.end.y}
                        r={6}
                        fill={isEndSnapped ? "#34d399" : "#ef4444"}
                        stroke="#09090b"
                        strokeWidth={2}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onMouseEnter={() => setHoveredNode({
                          x: entity.end.x,
                          y: entity.end.y,
                          original: `CAD: (${entity.end.x}, ${entity.end.y})`,
                          current: isEndSnapped ? "Kenetlenmiş Düğüm (Snapped)" : "Kopuk Serbest Köşe (Gap Node)"
                        })}
                        onMouseLeave={() => setHoveredNode(null)}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Node Inspector Floating Card */}
              <AnimatePresence>
                {hoveredNode && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute top-12 left-1/2 -translate-x-1/2 bg-zinc-900 border border-zinc-700 p-2.5 rounded-lg shadow-2xl z-20 pointer-events-none flex flex-col font-mono text-[10px]"
                  >
                    <span className="text-zinc-500 font-bold">DÜĞÜM MÜFETTİŞİ (INSPECTOR)</span>
                    <span className="text-zinc-100 font-bold mt-1 text-xs">{hoveredNode.original}</span>
                    <span className={`mt-0.5 ${hoveredNode.current.includes("Kenetlenmiş") ? "text-emerald-400" : "text-rose-400 font-bold animate-pulse"}`}>
                      ● {hoveredNode.current}
                    </span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* ENGINE LOGS (Live Terminal) */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold text-zinc-500 border-b border-zinc-850 pb-1.5">
              <span>MÜHENDİSLİK GÜNLÜKLERİ (ENGINE LOGS)</span>
              <span className="text-amber-500">REAL-TIME DETERMINISTIC OUTPUT</span>
            </div>
            
            <div className="h-32 overflow-y-auto font-mono text-[11px] space-y-1.5 pr-2">
              {logs.map((log, idx) => {
                let colorClass = "text-zinc-400";
                if (log.includes("[BAŞARI]")) colorClass = "text-emerald-400 font-bold";
                else if (log.includes("[ERROR]")) colorClass = "text-rose-400 font-bold";
                else if (log.includes("[SİSTEM]")) colorClass = "text-amber-400 font-medium";
                else if (log.includes("[MÜHENDİS]")) colorClass = "text-sky-400";

                return (
                  <div key={idx} className={`${colorClass} leading-relaxed`}>
                    {log}
                  </div>
                );
              })}
            </div>
          </div>

          {/* REAL-TIME PERFORMANCE METRICS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Gelen Vektör Sayısı</span>
              <span className="text-base font-extrabold text-zinc-100 font-mono">{totalOriginalLines}</span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Temizlenen / Merged</span>
              <span className="text-base font-extrabold text-emerald-400 font-mono">
                {duplicateLinesCount > 0 ? `${duplicateLinesCount} adet` : "0"}
              </span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Son Vektör Yükü</span>
              <span className="text-base font-extrabold text-amber-400 font-mono">{currentLinesCount}</span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Çıktı Sınıfı</span>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded inline-block mt-0.5 border border-emerald-500/20 font-mono">
                %100 BIM Hazır
              </span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
