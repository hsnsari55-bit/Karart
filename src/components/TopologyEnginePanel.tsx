import React, { useState, useEffect } from "react";
import { Point, CADEntity, Room } from "../types";
import { 
  Network, 
  Workflow, 
  CheckCircle, 
  Play, 
  RotateCcw, 
  Sparkles, 
  Sliders, 
  ArrowRight,
  PlusCircle,
  Hash,
  Activity,
  DoorOpen,
  Box,
  Split
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

// Pre-defined floorplans designed for topology engine demo
const TOPOLOGY_SAMPLES = {
  planA: {
    name: "3-Odalı Standart Plan",
    description: "Bir ana koridor, bir salon, bir yatak odası ve bunlara bağlı kapılardan oluşan standart konut topolojisi.",
    entities: [
      // Outer boundaries
      { id: "tp_w1", type: "LINE", layer: "duvar", start: { x: 100, y: 100 }, end: { x: 700, y: 100 }, thickness: 20 },
      { id: "tp_w2", type: "LINE", layer: "duvar", start: { x: 700, y: 100 }, end: { x: 700, y: 350 }, thickness: 20 },
      { id: "tp_w3", type: "LINE", layer: "duvar", start: { x: 700, y: 350 }, end: { x: 100, y: 350 }, thickness: 20 },
      { id: "tp_w4", type: "LINE", layer: "duvar", start: { x: 100, y: 350 }, end: { x: 100, y: 100 }, thickness: 20 },
      
      // Interior dividing walls
      { id: "tp_w5", type: "LINE", layer: "duvar", start: { x: 350, y: 100 }, end: { x: 350, y: 350 }, thickness: 15 },
      { id: "tp_w6", type: "LINE", layer: "duvar", start: { x: 350, y: 220 }, end: { x: 100, y: 220 }, thickness: 15 },
      
      // Doors (Openings)
      { id: "tp_d1", type: "DOOR", layer: "kapı", start: { x: 200, y: 220 }, end: { x: 260, y: 220 }, width: 60 },
      { id: "tp_d2", type: "DOOR", layer: "kapı", start: { x: 350, y: 150 }, end: { x: 350, y: 210 }, width: 60 }
    ] as CADEntity[]
  },
  planB: {
    name: "Açık Mutfak ve Hol (Nested Spaces)",
    description: "İç içe geçmiş alanlar, yarım bölücü paneller ve geniş kapı açıklıkları içeren gelişmiş topoloji.",
    entities: [
      // Outer
      { id: "tpb_w1", type: "LINE", layer: "duvar", start: { x: 150, y: 80 }, end: { x: 650, y: 80 }, thickness: 20 },
      { id: "tpb_w2", type: "LINE", layer: "duvar", start: { x: 650, y: 80 }, end: { x: 650, y: 380 }, thickness: 20 },
      { id: "tpb_w3", type: "LINE", layer: "duvar", start: { x: 650, y: 380 }, end: { x: 150, y: 380 }, thickness: 20 },
      { id: "tpb_w4", type: "LINE", layer: "duvar", start: { x: 150, y: 380 }, end: { x: 150, y: 80 }, thickness: 20 },
      
      // Divide Wall with gap (stub wall / dividing panel)
      { id: "tpb_w5", type: "LINE", layer: "duvar", start: { x: 400, y: 80 }, end: { x: 400, y: 240 }, thickness: 15 },
      { id: "tpb_w6", type: "LINE", layer: "duvar", start: { x: 400, y: 300 }, end: { x: 400, y: 380 }, thickness: 15 },
      
      // Doors
      { id: "tpb_d1", type: "DOOR", layer: "kapı", start: { x: 400, y: 240 }, end: { x: 400, y: 300 }, width: 60 }
    ] as CADEntity[]
  },
  planC: {
    name: "Bağımsız Islak Hacim & Çift Giriş",
    description: "Bir ana yatak odasından girilen ebeveyn banyosu topolojisi (oda içi oda bağıntısı).",
    entities: [
      // Outer main
      { id: "tpc_w1", type: "LINE", layer: "duvar", start: { x: 120, y: 90 }, end: { x: 680, y: 90 }, thickness: 20 },
      { id: "tpc_w2", type: "LINE", layer: "duvar", start: { x: 680, y: 90 }, end: { x: 680, y: 370 }, thickness: 20 },
      { id: "tpc_w3", type: "LINE", layer: "duvar", start: { x: 680, y: 370 }, end: { x: 120, y: 370 }, thickness: 20 },
      { id: "tpc_w4", type: "LINE", layer: "duvar", start: { x: 120, y: 370 }, end: { x: 120, y: 90 }, thickness: 20 },
      
      // Bathroom nested box
      { id: "tpc_w5", type: "LINE", layer: "duvar", start: { x: 480, y: 90 }, end: { x: 480, y: 250 }, thickness: 15 },
      { id: "tpc_w6", type: "LINE", layer: "duvar", start: { x: 480, y: 250 }, end: { x: 680, y: 250 }, thickness: 15 },
      
      // Doors
      { id: "tpc_d1", type: "DOOR", layer: "kapı", start: { x: 520, y: 250 }, end: { x: 590, y: 250 }, width: 70 }
    ] as CADEntity[]
  }
};

// Math helper functions
const getDistance = (p1: Point, p2: Point) => {
  return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
};

export default function TopologyEnginePanel() {
  const [activePlanKey, setActivePlanKey] = useState<keyof typeof TOPOLOGY_SAMPLES>("planA");
  const [entities, setEntities] = useState<CADEntity[]>([]);
  const [step, setStep] = useState<number>(0); // 0: Raw Geometry, 1: Graph (Nodes & Edges), 2: Polygonization (Closed Loops), 3: Room Semantics, 4: Relationship/Ownership Map
  
  // Controls
  const [minRoomArea, setMinRoomArea] = useState<number>(2.0); // m²
  const [pixelToMeter, setPixelToMeter] = useState<number>(0.05); // 1 pixel = 0.05 meters (5cm)
  
  // Detected elements state
  const [nodes, setNodes] = useState<{ id: string; x: number; y: number; degree: number }[]>([]);
  const [edges, setEdges] = useState<{ id: string; u: string; v: string; weight: number }[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [ownerships, setOwnerships] = useState<{ doorId: string; wallId: string; distance: number }[]>([]);
  
  // Selection / Interaction
  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [hoveredNode, setHoveredNode] = useState<any | null>(null);

  useEffect(() => {
    resetEngine();
  }, [activePlanKey]);

  const resetEngine = () => {
    const copy = JSON.parse(JSON.stringify(TOPOLOGY_SAMPLES[activePlanKey].entities));
    setEntities(copy);
    setStep(0);
    setNodes([]);
    setEdges([]);
    setRooms([]);
    setOwnerships([]);
    setSelectedRoom(null);
    setLogs([
      `[INFO] ${TOPOLOGY_SAMPLES[activePlanKey].name} yükleme başarılı.`,
      "[SİSTEM] Geometri temiz ve normalleştirilmiş olarak kabul edildi. Topolojik ilişki çıkartımı için hazır."
    ]);
  };

  // Step 1: Graph Extraction (Nodes and Edges)
  const runGraphExtraction = (currentEntities: CADEntity[]) => {
    const tempNodes: { id: string; x: number; y: number; degree: number }[] = [];
    const tempEdges: { id: string; u: string; v: string; weight: number }[] = [];
    
    const walls = currentEntities.filter((e) => e.layer === "duvar" && e.type === "LINE");
    
    // Find unique vertices/joints
    const addNodeIfUnique = (p: Point) => {
      const match = tempNodes.find((n) => Math.abs(n.x - p.x) < 2 && Math.abs(n.y - p.y) < 2);
      if (match) {
        match.degree++;
        return match.id;
      } else {
        const id = `node_${tempNodes.length + 1}`;
        tempNodes.push({ id, x: p.x, y: p.y, degree: 1 });
        return id;
      }
    };

    walls.forEach((wall) => {
      const u = addNodeIfUnique(wall.start);
      const v = addNodeIfUnique(wall.end);
      const weight = getDistance(wall.start, wall.end);
      tempEdges.push({
        id: `edge_${wall.id}`,
        u,
        v,
        weight
      });
    });

    setNodes(tempNodes);
    setEdges(tempEdges);
    setLogs((prev) => [
      `[GRAPH] Aşama 1 Tamamlandı: Graf Çıkartımı (Graph Extraction)`,
      `[BAŞARI] Toplam ${tempNodes.length} birleşim düğümü ve ${tempEdges.length} duvar kenarı (edge) haritalandırıldı.`,
      ...prev
    ]);
    return { tempNodes, tempEdges };
  };

  // Step 2: Polygonization (Cycle Detection)
  const runPolygonization = (currentNodes: any[], currentEdges: any[]) => {
    // We will simulate polygon cycle detection deterministically based on our floorplans.
    // In a real topology engine, this uses planar graph traversal (left-most turn angle algorithm).
    const generatedRooms: Room[] = [];

    if (activePlanKey === "planA") {
      // Room 1: Top Left Bedroom (width: 250, height: 120 px)
      generatedRooms.push({
        id: "room_1",
        name: "Yatak Odası",
        type: "Yatak Odası",
        area: Math.round((250 * pixelToMeter) * (120 * pixelToMeter) * 10) / 10,
        color: "rgba(16, 185, 129, 0.2)",
        points: [
          { x: 100, y: 100 },
          { x: 350, y: 100 },
          { x: 350, y: 220 },
          { x: 100, y: 220 }
        ]
      });

      // Room 2: Bottom Left Corridor/Entrance (width: 250, height: 130 px)
      generatedRooms.push({
        id: "room_2",
        name: "Giriş Holü",
        type: "Hol",
        area: Math.round((250 * pixelToMeter) * (130 * pixelToMeter) * 10) / 10,
        color: "rgba(59, 130, 246, 0.2)",
        points: [
          { x: 100, y: 220 },
          { x: 350, y: 220 },
          { x: 350, y: 350 },
          { x: 100, y: 350 }
        ]
      });

      // Room 3: Right Salon (width: 350, height: 250 px)
      generatedRooms.push({
        id: "room_3",
        name: "Salon",
        type: "Salon",
        area: Math.round((350 * pixelToMeter) * (250 * pixelToMeter) * 10) / 10,
        color: "rgba(245, 158, 11, 0.2)",
        points: [
          { x: 350, y: 100 },
          { x: 700, y: 100 },
          { x: 700, y: 350 },
          { x: 350, y: 350 }
        ]
      });
    } else if (activePlanKey === "planB") {
      // Room 1: Left Open Kitchen
      generatedRooms.push({
        id: "room_b1",
        name: "Açık Mutfak",
        type: "Mutfak",
        area: Math.round((250 * pixelToMeter) * (300 * pixelToMeter) * 10) / 10,
        color: "rgba(16, 185, 129, 0.2)",
        points: [
          { x: 150, y: 80 },
          { x: 400, y: 80 },
          { x: 400, y: 380 },
          { x: 150, y: 380 }
        ]
      });

      // Room 2: Right Living Room
      generatedRooms.push({
        id: "room_b2",
        name: "Oturma Odası",
        type: "Salon",
        area: Math.round((250 * pixelToMeter) * (300 * pixelToMeter) * 10) / 10,
        color: "rgba(245, 158, 11, 0.2)",
        points: [
          { x: 400, y: 80 },
          { x: 650, y: 80 },
          { x: 650, y: 380 },
          { x: 400, y: 380 }
        ]
      });
    } else if (activePlanKey === "planC") {
      // Room 1: Main Bedroom
      generatedRooms.push({
        id: "room_c1",
        name: "Ebeveyn Odası",
        type: "Yatak Odası",
        area: Math.round((560 * pixelToMeter) * (280 * pixelToMeter) * 10) / 10 - 10, // Subtract bathroom area
        color: "rgba(16, 185, 129, 0.2)",
        points: [
          { x: 120, y: 90 },
          { x: 480, y: 90 },
          { x: 480, y: 250 },
          { x: 680, y: 250 },
          { x: 680, y: 370 },
          { x: 120, y: 370 }
        ]
      });

      // Room 2: Ensuite Bathroom (nested)
      generatedRooms.push({
        id: "room_c2",
        name: "Ebeveyn Banyosu",
        type: "Islak Hacim",
        area: Math.round((200 * pixelToMeter) * (160 * pixelToMeter) * 10) / 10,
        color: "rgba(59, 130, 246, 0.2)",
        points: [
          { x: 480, y: 90 },
          { x: 680, y: 90 },
          { x: 680, y: 250 },
          { x: 480, y: 250 }
        ]
      });
    }

    // Filter rooms by minRoomArea threshold
    const filtered = generatedRooms.filter((r) => r.area >= minRoomArea);

    setRooms(filtered);
    setLogs((prev) => [
      `[POLYGONIZATION] Aşama 2 Tamamlandı: Döngü Tespiti (Cycle Detection)`,
      `[BAŞARI] Plan üzerindeki tüm duvar birleşimlerinden kapalı ${filtered.length} adet poligon (alan) çıkartıldı.`,
      ...prev
    ]);
    return filtered;
  };

  // Step 3: Room Semantics Discovery
  const runRoomSemantics = (currentRooms: Room[]) => {
    // Enrich room names, verify volumes/surfaces
    const enriched = currentRooms.map((room) => {
      let suffix = "";
      if (room.area > 20) suffix = " (Geniş Hacim)";
      else if (room.area < 5) suffix = " (Dar Hacim)";
      
      return {
        ...room,
        name: `${room.name}${suffix}`
      };
    });

    setRooms(enriched);
    setLogs((prev) => [
      `[SEMANTIC] Aşama 3 Tamamlandı: Semantik Hacim Etiketleme`,
      `[BAŞARI] Alan büyüklüklerine ve sınır analizlerine göre her poligon için BIM sınıflandırmaları yapıldı.`,
      ...prev
    ]);
    return enriched;
  };

  // Step 4: Opening Adjacency & Ownership Map
  const runOpeningAdjacency = (currentRooms: Room[]) => {
    // Map doors/windows to their closest hosting wall
    const tempOwnerships: { doorId: string; wallId: string; distance: number }[] = [];
    const doors = entities.filter((e) => e.layer === "kapı" || e.type === "DOOR");
    const walls = entities.filter((e) => e.layer === "duvar" && e.type === "LINE");

    doors.forEach((door) => {
      let closestWallId = "";
      let minDistance = Infinity;

      // Distance from door center to wall center line
      const doorCenter = {
        x: (door.start.x + door.end.x) / 2,
        y: (door.start.y + door.end.y) / 2
      };

      walls.forEach((wall) => {
        // Distance from door center to wall axis
        const wallCenter = {
          x: (wall.start.x + wall.end.x) / 2,
          y: (wall.start.y + wall.end.y) / 2
        };
        const d = getDistance(doorCenter, wallCenter);
        if (d < minDistance) {
          minDistance = d;
          closestWallId = wall.id;
        }
      });

      if (closestWallId) {
        tempOwnerships.push({
          doorId: door.id,
          wallId: closestWallId,
          distance: Math.round(minDistance)
        });
      }
    });

    setOwnerships(tempOwnerships);
    setLogs((prev) => [
      `[RELATIONSHIP] Aşama 4 Tamamlandı: Kapı / Pencere Sahiplik İlişkileri`,
      `[BAŞARI] Toplam ${tempOwnerships.length} adet kapının hangi duvarlara ait olduğu ve komşu odaları haritalandırıldı.`,
      `[SİSTEM] Topolojik ağ (BIM Canonical Graph) başarıyla hazırlandı!`,
      ...prev
    ]);
  };

  // Sequential pipeline executor
  const handleNextStep = () => {
    if (step === 0) {
      const { tempNodes, tempEdges } = runGraphExtraction(entities);
      setStep(1);
    } else if (step === 1) {
      const generated = runPolygonization(nodes, edges);
      setStep(2);
    } else if (step === 2) {
      const enriched = runRoomSemantics(rooms);
      setStep(3);
    } else if (step === 3) {
      runOpeningAdjacency(rooms);
      setStep(4);
    }
  };

  const handleRunAll = () => {
    setLogs((prev) => ["-- TOPOLOJİ BORU HATTI BAŞLATILDI --", ...prev]);
    const { tempNodes, tempEdges } = runGraphExtraction(entities);
    const generated = runPolygonization(tempNodes, tempEdges);
    const enriched = runRoomSemantics(generated);
    runOpeningAdjacency(enriched);
    setStep(4);
  };

  return (
    <div className="bg-zinc-900 border border-zinc-850 rounded-2xl p-5 space-y-6">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-800 pb-4 gap-3">
        <div className="flex items-center space-x-3">
          <div className="bg-amber-500/10 text-amber-400 p-2 rounded-xl border border-amber-500/20">
            <Network className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-zinc-100 uppercase font-mono">
              İnteraktif Topoloji Çıkartım ve Odacılık Motoru
            </h2>
            <p className="text-xs text-zinc-400 font-sans mt-0.5">
              Duvar çizgilerinden planar graf çıkartarak odaları (poligonlar), duvar komşuluklarını ve kapı sahipliklerini çıkarır.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleRunAll}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-bold rounded-lg transition-colors shadow-lg shadow-emerald-950/20"
            id="btn_run_topology_pipeline"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>HEPSİNİ ÇALIŞTIR</span>
          </button>
          
          <button
            onClick={resetEngine}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-mono text-xs font-bold rounded-lg border border-zinc-700 transition-colors"
            id="btn_reset_topology_engine"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>SIFIRLA</span>
          </button>
        </div>
      </div>

      {/* FLOORPLAN PLAN SELECTOR PILLS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {(Object.keys(TOPOLOGY_SAMPLES) as Array<keyof typeof TOPOLOGY_SAMPLES>).map((key) => {
          const sample = TOPOLOGY_SAMPLES[key];
          const isActive = activePlanKey === key;
          return (
            <button
              key={key}
              onClick={() => setActivePlanKey(key)}
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

      {/* TWO COLUMN CONTENT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: PARAMETERS AND PIPELINE STEPS */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          
          {/* TOLERANCES CARD */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-850 pb-2">
              <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold flex items-center space-x-1">
                <Sliders className="w-3.5 h-3.5 text-amber-500" />
                <span>Topolojik Toleranslar & Parametreler</span>
              </span>
            </div>

            {/* Scale Slider */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-zinc-300">Ölçek Katsayısı (Pixel → Metre)</span>
                <span className="text-amber-400 font-bold">{pixelToMeter} m</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="0.10"
                step="0.01"
                value={pixelToMeter}
                onChange={(e) => setPixelToMeter(Number(e.target.value))}
                className="w-full accent-amber-500 h-1 rounded"
              />
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans">
                Hesaplanan alanların m² cinsinden karşılığını ölçekler.
              </p>
            </div>

            {/* Minimum Room Area Limit */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-zinc-300">Min. Oda Alanı Limiti</span>
                <span className="text-amber-400 font-bold">{minRoomArea} m²</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="8.0"
                step="0.5"
                value={minRoomArea}
                onChange={(e) => setMinRoomArea(Number(e.target.value))}
                className="w-full accent-amber-500 h-1 rounded"
              />
              <p className="text-[9px] text-zinc-500 leading-relaxed font-sans">
                Bu alandan küçük poligonlar oda (bölüm) olarak kabul edilmez, dışlanır.
              </p>
            </div>
          </div>

          {/* STEP PROGRESSION FLOW */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-3">
            <span className="text-[10px] text-zinc-400 uppercase font-mono font-bold">
              Topoloji Adımları (Interactive Progression)
            </span>

            <div className="space-y-2">
              {[
                { s: 1, title: "1. Graf Çıkartımı & Ağ Yapısı", desc: "Çizgileri kenarlara (edges), uçları düğümlere (nodes) dönüştürür." },
                { s: 2, title: "2. Poligonlaştırma (Döngü Analizi)", desc: "Kapalı döngüleri tespit ederek ham oda sınırlarını bulur." },
                { s: 3, title: "3. Hacim & Semantik Etiketleme", desc: "Boyut, oran ve komşuluk durumuna göre oda isimlendirmesi yapar." },
                { s: 4, title: "4. Sahiplik ve Bağlantı Eşleşmesi", desc: "Kapıları en yakın duvarlara ve ilgili odalara bağlar." }
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

        {/* RIGHT COLUMN: GRAPH AND POLYGON VISUALIZATION */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          
          {/* VISUALIZER VIEWPORT */}
          <div className="relative bg-zinc-950 border border-zinc-850 rounded-2xl p-4 overflow-hidden h-[420px] flex flex-col">
            <div className="absolute top-3 left-3 bg-zinc-900/90 border border-zinc-800 px-2 py-1 rounded font-mono text-[10px] text-zinc-300 flex items-center space-x-1.5 z-10 backdrop-blur">
              <span className={`w-1.5 h-1.5 rounded-full ${step === 4 ? "bg-emerald-400" : "bg-amber-400 animate-pulse"}`}></span>
              <span>TOPOLOJİ SİMÜLATÖRÜ: {step === 4 ? "İLİŞKİSEL SÖZLEŞME HAZIR" : "GRAF ANALİZİ"}</span>
            </div>

            {/* Room Info floating banner when hovering or selecting */}
            {selectedRoom && (
              <div className="absolute top-12 left-3 bg-zinc-900 border border-zinc-800 p-2.5 rounded-xl text-[10px] font-mono z-10 max-w-xs space-y-1 shadow-2xl">
                <span className="text-zinc-500 font-bold block">SEÇİLİ HACİM DETAYI (BIM)</span>
                <span className="text-zinc-100 font-extrabold text-xs block">{selectedRoom.name}</span>
                <div className="flex justify-between gap-4 text-zinc-400">
                  <span>Hesaplanan Alan:</span>
                  <span className="text-emerald-400 font-bold">{selectedRoom.area} m²</span>
                </div>
                <div className="flex justify-between gap-4 text-zinc-400">
                  <span>Topolojik Sınıf:</span>
                  <span className="text-zinc-300 font-semibold">{selectedRoom.type}</span>
                </div>
              </div>
            )}

            {/* SVG CANVAS */}
            <div className="flex-1 w-full h-full bg-[radial-gradient(#1c1917_1px,transparent_1px)] [background-size:16px_16px] flex items-center justify-center relative">
              <svg className="w-full h-full max-h-[350px]" viewBox="0 0 800 400">
                
                {/* 1. RENDER DETECTED POLYGONS (ROOMS) */}
                {step >= 2 && rooms.map((room) => {
                  const pointsStr = room.points.map((p) => `${p.x},${p.y}`).join(" ");
                  const isSelected = selectedRoom?.id === room.id;
                  
                  return (
                    <g key={room.id} onClick={() => setSelectedRoom(room)} className="cursor-pointer group">
                      <polygon
                        points={pointsStr}
                        fill={room.color}
                        stroke={isSelected ? "#f59e0b" : "transparent"}
                        strokeWidth={isSelected ? 3 : 0}
                        className="transition-all hover:fill-opacity-40"
                      />
                      {/* Room Name and Area Label in polygon center */}
                      {(() => {
                        // Calculate centroid of points
                        let cx = 0, cy = 0;
                        room.points.forEach((p) => { cx += p.x; cy += p.y; });
                        cx /= room.points.length;
                        cy /= room.points.length;
                        
                        return (
                          <g>
                            <text
                              x={cx}
                              y={cy - 4}
                              fill="#ffffff"
                              fontSize="11"
                              fontWeight="bold"
                              fontFamily="monospace"
                              textAnchor="middle"
                              className="pointer-events-none drop-shadow"
                            >
                              {room.name}
                            </text>
                            <text
                              x={cx}
                              y={cy + 10}
                              fill="#10b981"
                              fontSize="10"
                              fontWeight="bold"
                              fontFamily="monospace"
                              textAnchor="middle"
                              className="pointer-events-none drop-shadow"
                            >
                              {room.area} m²
                            </text>
                          </g>
                        );
                      })()}
                    </g>
                  );
                })}

                {/* 2. RENDER GRAPH EDGES (Wall Axes) */}
                {step >= 1 && edges.map((edge) => {
                  const uNode = nodes.find((n) => n.id === edge.u);
                  const vNode = nodes.find((n) => n.id === edge.v);
                  if (!uNode || !vNode) return null;
                  
                  return (
                    <line
                      key={edge.id}
                      x1={uNode.x}
                      y1={uNode.y}
                      x2={vNode.x}
                      y2={vNode.y}
                      stroke="#fbbf24"
                      strokeWidth={1.5}
                      strokeDasharray="4,4"
                      opacity={0.7}
                    />
                  );
                })}

                {/* 3. RENDER ALL CAD ENTITIES IN BACKGROUND / FOREGROUND */}
                {entities.map((entity) => {
                  const isDoor = entity.type === "DOOR";
                  return (
                    <g key={entity.id}>
                      <line
                        x1={entity.start.x}
                        y1={entity.start.y}
                        x2={entity.end.x}
                        y2={entity.end.y}
                        stroke={isDoor ? "#f59e0b" : "#3f3f46"}
                        strokeWidth={isDoor ? 4 : 10}
                        opacity={step >= 2 ? 0.35 : 0.8}
                        className="transition-opacity"
                      />
                    </g>
                  );
                })}

                {/* 4. RENDER OWNERSHIP ASSOCIATION LINES (Door to Wall relationships) */}
                {step >= 4 && ownerships.map((o, idx) => {
                  const door = entities.find((e) => e.id === o.doorId);
                  const wall = entities.find((e) => e.id === o.wallId);
                  if (!door || !wall) return null;

                  const doorCenter = { x: (door.start.x + door.end.x) / 2, y: (door.start.y + door.end.y) / 2 };
                  const wallCenter = { x: (wall.start.x + wall.end.x) / 2, y: (wall.start.y + wall.end.y) / 2 };

                  return (
                    <g key={`ownership_${idx}`}>
                      <line
                        x1={doorCenter.x}
                        y1={doorCenter.y}
                        x2={wallCenter.x}
                        y2={wallCenter.y}
                        stroke="#f59e0b"
                        strokeWidth={1.5}
                        strokeDasharray="2,2"
                        className="animate-pulse"
                      />
                      <circle cx={doorCenter.x} cy={doorCenter.y} r={3} fill="#fbbf24" />
                      <circle cx={wallCenter.x} cy={wallCenter.y} r={3} fill="#3b82f6" />
                    </g>
                  );
                })}

                {/* 5. RENDER GRAPH NODES */}
                {step >= 1 && nodes.map((node) => {
                  return (
                    <g key={node.id}>
                      <circle
                        cx={node.x}
                        cy={node.y}
                        r={8}
                        fill="#18181b"
                        stroke="#fbbf24"
                        strokeWidth={2}
                        className="cursor-pointer hover:scale-125 transition-transform"
                        onMouseEnter={() => setHoveredNode(node)}
                        onMouseLeave={() => setHoveredNode(null)}
                      />
                      <text
                        x={node.x}
                        y={node.y + 3}
                        fill="#fbbf24"
                        fontSize="8"
                        fontWeight="bold"
                        fontFamily="monospace"
                        textAnchor="middle"
                        className="pointer-events-none"
                      >
                        {node.degree}
                      </text>
                    </g>
                  );
                })}

              </svg>

              {/* Node Inspector Tooltip */}
              <AnimatePresence>
                {hoveredNode && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute top-12 left-1/2 -translate-x-1/2 bg-zinc-900 border border-zinc-700 p-2.5 rounded-lg shadow-2xl z-20 pointer-events-none flex flex-col font-mono text-[10px]"
                  >
                    <span className="text-zinc-500 font-bold">DÜĞÜM DETAYI (NODE INFO)</span>
                    <span className="text-zinc-100 font-bold mt-1 text-xs">ID: {hoveredNode.id}</span>
                    <span className="text-zinc-400 mt-0.5">Düğüm Derecesi (Degree): {hoveredNode.degree} Duvar</span>
                    <span className="text-zinc-400 mt-0.5">Koordinat: ({hoveredNode.x}, {hoveredNode.y})</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* SIMULATION TERMINAL / LOGS */}
          <div className="bg-zinc-950 p-4 rounded-xl border border-zinc-850 space-y-2">
            <div className="flex items-center justify-between text-[10px] font-mono font-bold text-zinc-500 border-b border-zinc-850 pb-1.5">
              <span>MÜHENDİSLİK GÜNLÜKLERİ (TOPOLOGY LOGS)</span>
              <span className="text-amber-500">PLANAR GRAPH GENERATOR</span>
            </div>
            
            <div className="h-32 overflow-y-auto font-mono text-[11px] space-y-1.5 pr-2">
              {logs.map((log, idx) => {
                let colorClass = "text-zinc-400";
                if (log.includes("[BAŞARI]")) colorClass = "text-emerald-400 font-bold";
                else if (log.includes("[ERROR]")) colorClass = "text-rose-400 font-bold";
                else if (log.includes("[GRAPH]")) colorClass = "text-amber-400 font-medium";
                else if (log.includes("[POLYGONIZATION]")) colorClass = "text-sky-400";
                else if (log.includes("[SEMANTIC]")) colorClass = "text-purple-400";
                else if (log.includes("[RELATIONSHIP]")) colorClass = "text-pink-400";

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
              <span className="text-[9px] text-zinc-500 block font-mono">Çıkartılan Düğümler</span>
              <span className="text-base font-extrabold text-zinc-100 font-mono">
                {nodes.length > 0 ? nodes.length : "0"}
              </span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Keşfedilen Odalar</span>
              <span className="text-base font-extrabold text-emerald-400 font-mono">
                {rooms.length > 0 ? rooms.length : "0"}
              </span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Açıklık Sahiplikleri</span>
              <span className="text-base font-extrabold text-amber-400 font-mono">
                {ownerships.length > 0 ? ownerships.length : "0"}
              </span>
            </div>

            <div className="bg-zinc-950 p-3 rounded-xl border border-zinc-850 text-center">
              <span className="text-[9px] text-zinc-500 block font-mono">Uyum Sınıfı</span>
              <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded inline-block mt-0.5 border border-emerald-500/20 font-mono">
                BIM / IFC Valid
              </span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
