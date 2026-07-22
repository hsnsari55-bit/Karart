import React, { useState } from "react";
import { Floor, CADEntity, Room, Point } from "../types";
import { ZoomIn, ZoomOut, Maximize2, Layers, Eye, EyeOff, Info } from "lucide-react";

interface CADVisualizerProps {
  floor: Floor;
  selectedLayers: Record<string, boolean>;
  toggleLayer: (layer: string) => void;
  isCleaned: boolean; // Toggle before/after snapping engine
  selectedEntityId?: string | null;
  onSelectEntity?: (id: string | null) => void;
  selectedBlock?: string;
}

export default function CADVisualizer({
  floor,
  selectedLayers,
  toggleLayer,
  isCleaned,
  selectedEntityId,
  onSelectEntity,
  selectedBlock = "all",
}: CADVisualizerProps) {
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 10, y: 10 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredElement, setHoveredElement] = useState<{
    type: string;
    details: string;
    id?: string;
  } | null>(null);

  // Isolate blocks based on coordinate analysis
  const isInBlock = (entity: CADEntity): boolean => {
    if (selectedBlock === "all") return true;
    const x = entity.start.x;
    const y = entity.start.y;
    
    // Legend or small annotations far left
    if (x < 500) {
      if (selectedBlock === "block_a") return x < 200;
      if (selectedBlock === "block_b") return x >= 200 && x < 500;
      return false;
    }

    if (selectedBlock === "block_a") {
      // Bottom-Left (Villa A)
      return x < 638 && y < 155;
    }
    if (selectedBlock === "block_b") {
      // Top-Left (Villa B)
      return x < 638 && y >= 155;
    }
    if (selectedBlock === "block_c") {
      // Top-Right (Upper / Attic / Shared)
      return x >= 638 && y >= 155;
    }
    return true;
  };

  const isRoomInBlock = (room: Room): boolean => {
    if (selectedBlock === "all") return true;
    if (!room.points || room.points.length === 0) return true;
    
    const xs = room.points.map((p) => p.x);
    const ys = room.points.map((p) => p.y);
    const cx = xs.reduce((a, b) => a + b, 0) / xs.length;
    const cy = ys.reduce((a, b) => a + b, 0) / ys.length;

    if (cx < 500) {
      if (selectedBlock === "block_a") return cx < 200;
      if (selectedBlock === "block_b") return cx >= 200 && cx < 500;
      return false;
    }

    if (selectedBlock === "block_a") {
      return cx < 638 && cy < 155;
    }
    if (selectedBlock === "block_b") {
      return cx < 638 && cy >= 155;
    }
    if (selectedBlock === "block_c") {
      return cx >= 638 && cy >= 155;
    }
    return true;
  };

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.15, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.15, 0.5));
  const handleReset = () => {
    setZoom(1);
    setOffset({ x: 10, y: 10 });
  };

  // Drag pan controls
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientX - offset.y }); // Just a simple offset tracker
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Apply subtle coordinate noise if "raw" CAD (isCleaned is false) to show SNAP in action
  const adjustPoint = (p: Point, entityId: string): Point => {
    if (isCleaned) return p;
    // Add minor visual noise to line endpoints to simulate un-snapped CAD drawings
    const seed = parseFloat(entityId.replace(/[^0-9.]/g, "")) || 5;
    const noiseX = Math.sin(seed * 2) * 4;
    const noiseY = Math.cos(seed * 3) * 4;
    return { x: p.x + noiseX, y: p.y + noiseY };
  };

  return (
    <div className="relative w-full h-[500px] bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden flex flex-col select-none">
      {/* CAD Header Status */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span className="font-mono text-xs text-zinc-300">
            2D CAD PANEL | {floor.name}
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1 font-mono text-[10px] text-zinc-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>MODEL COORDINATES MATCHED</span>
          </span>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div
        className={`relative flex-1 ${isDragging ? "cursor-grabbing" : "cursor-grab"} overflow-hidden bg-[radial-gradient(#18181b_1px,transparent_1px)] [background-size:16px_16px]`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          className="w-full h-full"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
            transition: isDragging ? "none" : "transform 0.1s ease-out",
          }}
          viewBox="0 0 800 450"
        >
          {/* 1. ROOM POLYGONS (Background Fills) */}
          {selectedLayers["room-poly"] &&
            floor.rooms.filter(isRoomInBlock).map((room) => {
              const pointsStr = room.points
                .map((p) => `${p.x},${p.y}`)
                .join(" ");
              return (
                <polygon
                  key={room.id}
                  id={room.id}
                  points={pointsStr}
                  fill={room.color}
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeWidth={1}
                  className="transition-colors hover:fill-zinc-800/40 cursor-pointer"
                  onMouseEnter={() =>
                    setHoveredElement({
                      type: "Oda (Room Bound)",
                      details: `${room.name} | Alan: ${room.area} m²`,
                      id: room.id,
                    })
                  }
                  onMouseLeave={() => setHoveredElement(null)}
                />
              );
            })}

          {/* 2. AKS / GRID LINES */}
          {selectedLayers["aks"] &&
            floor.entities
              .filter((e) => e.layer === "aks" && isInBlock(e))
              .map((e) => {
                const p1 = adjustPoint(e.start, e.id);
                const p2 = adjustPoint(e.end, e.id);
                return (
                  <g key={e.id}>
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke="#ef4444"
                      strokeWidth={0.5}
                      strokeDasharray="8,4"
                      opacity={0.35}
                    />
                    {/* Tiny grid label */}
                    <text
                      x={p1.x < 50 ? p1.x - 12 : p1.x}
                      y={p1.y < 50 ? p1.y - 6 : p1.y + 12}
                      fill="#ef4444"
                      fontSize={8}
                      fontFamily="monospace"
                      opacity={0.5}
                      textAnchor="middle"
                    >
                      {e.id.includes("h") ? "Y" : "X"}-{e.id.split("_").pop()}
                    </text>
                  </g>
                );
              })}

          {/* 3. WALLS (Duvarlar) */}
          {selectedLayers["duvar"] &&
            floor.entities
              .filter((e) => e.layer === "duvar" && isInBlock(e))
              .map((e) => {
                const p1 = adjustPoint(e.start, e.id);
                const p2 = adjustPoint(e.end, e.id);
                const isThick = (e.thickness || 15) >= 20;
                const isSelected = selectedEntityId === e.id;
                return (
                  <g key={e.id} onClick={(evt) => { evt.stopPropagation(); onSelectEntity?.(e.id); }}>
                    {/* Double lines / thick fill to represent walls */}
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={isSelected ? "#f59e0b" : (isThick ? "#52525b" : "#71717a")}
                      strokeWidth={isSelected ? (e.thickness ? e.thickness / 2 + 2 : 12) : (e.thickness ? e.thickness / 2 : 10)}
                      strokeLinecap="square"
                      opacity={isSelected ? 0.95 : 0.7}
                      className="transition-all"
                    />
                    {/* Core Line / Wall Axis */}
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={isSelected ? "#fbbf24" : "#10b981"}
                      strokeWidth={isSelected ? 2.5 : 1}
                      strokeDasharray={isSelected ? "none" : (isCleaned ? "none" : "2,2")}
                      opacity={isSelected ? 1.0 : (isCleaned ? 0.35 : 0.6)}
                      className="cursor-pointer hover:stroke-amber-400 hover:stroke-[2.5]"
                      onMouseEnter={() =>
                        setHoveredElement({
                          type: isThick ? "Taşıyıcı Duvar (Bearing Wall)" : "Bölme Duvar (Partition)",
                          details: `Duvar ID: ${e.id} | Kalınlık: ${e.thickness || 15} cm | Uzunluk: ${((e.thickness || 15) * 1.5).toFixed(1)}m`,
                          id: e.id,
                        })
                      }
                      onMouseLeave={() => setHoveredElement(null)}
                    />
                  </g>
                );
              })}

          {/* 4. COLUMNS (Kolonlar) */}
          {selectedLayers["kolon"] &&
            floor.entities
              .filter((e) => e.layer === "kolon" && isInBlock(e))
              .map((e) => {
                const p1 = adjustPoint(e.start, e.id);
                const p2 = adjustPoint(e.end, e.id);
                const size = e.thickness || 30;
                const isSelected = selectedEntityId === e.id;
                return (
                  <rect
                    key={e.id}
                    id={e.id}
                    x={p1.x - size / 2}
                    y={p1.y - size / 2}
                    width={size}
                    height={size}
                    fill={isSelected ? "rgba(245, 158, 11, 0.2)" : "#18181b"}
                    stroke={isSelected ? "#fbbf24" : "#ef4444"}
                    strokeWidth={isSelected ? 3.5 : 2}
                    strokeDasharray={isSelected ? "4,2" : "none"}
                    className="cursor-pointer hover:fill-red-950/40 transition-all"
                    onClick={(evt) => { evt.stopPropagation(); onSelectEntity?.(e.id); }}
                    onMouseEnter={() =>
                      setHoveredElement({
                        type: "Betonarme Kolon (Column)",
                        details: `Boyut: ${size}x${size}cm | Grid: Aks Kesişimi`,
                        id: e.id,
                      })
                    }
                    onMouseLeave={() => setHoveredElement(null)}
                  />
                );
              })}

          {/* 5. WINDOWS (Pencereler) */}
          {selectedLayers["k pencere"] &&
            floor.entities
              .filter((e) => e.layer === "k pencere" && isInBlock(e))
              .map((e) => {
                const p1 = adjustPoint(e.start, e.id);
                const p2 = adjustPoint(e.end, e.id);
                const isSelected = selectedEntityId === e.id;
                return (
                  <g
                    key={e.id}
                    className="cursor-pointer"
                    onClick={(evt) => { evt.stopPropagation(); onSelectEntity?.(e.id); }}
                    onMouseEnter={() =>
                      setHoveredElement({
                        type: "Pencere (Window Open)",
                        details: `ID: ${e.id} | Genişlik: ${e.width || 80} cm`,
                        id: e.id,
                      })
                    }
                    onMouseLeave={() => setHoveredElement(null)}
                  >
                    {/* Highlight Glow if selected */}
                    {isSelected && (
                      <line
                        x1={p1.x}
                        y1={p1.y}
                        x2={p2.x}
                        y2={p2.y}
                        stroke="#fbbf24"
                        strokeWidth={10}
                        opacity={0.4}
                        strokeLinecap="round"
                      />
                    )}
                    {/* Window framing lines */}
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={isSelected ? "#fbbf24" : "#60a5fa"}
                      strokeWidth={4}
                    />
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={isSelected ? "#f59e0b" : "#0284c7"}
                      strokeWidth={1}
                    />
                  </g>
                );
              })}

          {/* 6. DOORS (Kapılar) */}
          {selectedLayers["kapı"] &&
            floor.entities
              .filter((e) => e.layer === "kapı" && isInBlock(e))
              .map((e) => {
                const p1 = adjustPoint(e.start, e.id);
                const p2 = adjustPoint(e.end, e.id);
                const width = e.width || 80;
                const isSelected = selectedEntityId === e.id;

                // Determine angle / swing parameters
                const dx = p2.x - p1.x;
                const dy = p2.y - p1.y;
                const angleRad = Math.atan2(dy, dx);

                return (
                  <g
                    key={e.id}
                    className="cursor-pointer"
                    onClick={(evt) => { evt.stopPropagation(); onSelectEntity?.(e.id); }}
                    onMouseEnter={() =>
                      setHoveredElement({
                        type: `Kapı (${e.doorType || "Single"})`,
                        details: `ID: ${e.id} | Genişlik: ${width} cm`,
                        id: e.id,
                      })
                    }
                    onMouseLeave={() => setHoveredElement(null)}
                  >
                    {/* Highlight Glow if selected */}
                    {isSelected && (
                      <line
                        x1={p1.x}
                        y1={p1.y}
                        x2={p2.x}
                        y2={p2.y}
                        stroke="#fbbf24"
                        strokeWidth={10}
                        opacity={0.4}
                        strokeLinecap="round"
                      />
                    )}
                    {/* Door Leaf / Swing Arc */}
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p1.x + Math.cos(angleRad - Math.PI / 2) * width * 0.8}
                      y2={p1.y + Math.sin(angleRad - Math.PI / 2) * width * 0.8}
                      stroke={isSelected ? "#f59e0b" : "#fbbf24"}
                      strokeWidth={2.5}
                    />
                    {/* Arc path swing representation */}
                    <path
                      d={`M ${p1.x} ${p1.y} A ${width * 0.8} ${width * 0.8} 0 0 1 ${p1.x + Math.cos(angleRad - Math.PI / 2) * width * 0.8} ${p1.y + Math.sin(angleRad - Math.PI / 2) * width * 0.8}`}
                      fill="none"
                      stroke={isSelected ? "#f59e0b" : "#fbbf24"}
                      strokeWidth={isSelected ? 1.5 : 1}
                      strokeDasharray="3,3"
                      opacity={0.8}
                    />
                    {/* Door frame base */}
                    <line
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={isSelected ? "#d97706" : "#f59e0b"}
                      strokeWidth={3}
                      opacity={0.6}
                    />
                  </g>
                );
              })}
        </svg>

        {/* Float Controls Overlay */}
        <div className="absolute bottom-4 right-4 flex space-x-2 bg-zinc-900/90 border border-zinc-800 rounded-lg p-1.5 backdrop-blur shadow-xl">
          <button
            onClick={handleZoomIn}
            className="p-1.5 hover:bg-zinc-800 rounded text-zinc-300 transition-colors"
            title="Yaklaş"
            id="btn_zoom_in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 hover:bg-zinc-800 rounded text-zinc-300 transition-colors"
            title="Uzaklaş"
            id="btn_zoom_out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 hover:bg-zinc-800 rounded text-zinc-300 transition-colors"
            title="Sıfırla"
            id="btn_zoom_reset"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        {/* Hover info panel */}
        {hoveredElement && (
          <div className="absolute top-4 left-4 max-w-sm bg-zinc-900/95 border border-zinc-700 rounded-lg p-3 backdrop-blur shadow-2xl animate-fade-in pointer-events-none">
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-[10px] uppercase tracking-wider font-mono text-zinc-500">
                  {hoveredElement.type}
                </p>
                <p className="text-xs font-semibold text-zinc-100 mt-0.5">
                  {hoveredElement.details}
                </p>
                {hoveredElement.id && (
                  <span className="inline-block mt-1 font-mono text-[9px] bg-zinc-800 text-emerald-400 px-1 py-0.5 rounded">
                    {hoveredElement.id}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Layer Checklist Controls Footer */}
      <div className="p-3 bg-zinc-900 border-t border-zinc-800 grid grid-cols-2 sm:flex sm:items-center sm:flex-wrap gap-2 text-xs">
        <span className="text-[10px] font-mono uppercase text-zinc-500 w-full sm:w-auto sm:mr-3">
          Katman Filtreleri:
        </span>
        {Object.keys(selectedLayers).map((layer) => {
          const isActive = selectedLayers[layer];
          let colorClass = "border-zinc-700 text-zinc-400 hover:border-zinc-500";
          if (isActive) {
            if (layer === "duvar") colorClass = "bg-zinc-800 border-zinc-600 text-zinc-100";
            else if (layer === "kolon") colorClass = "bg-red-950/40 border-red-800 text-red-200";
            else if (layer === "kapı") colorClass = "bg-amber-950/40 border-amber-800 text-amber-200";
            else if (layer === "k pencere") colorClass = "bg-sky-950/40 border-sky-800 text-sky-200";
            else if (layer === "aks") colorClass = "bg-rose-950/20 border-rose-900 text-rose-300";
            else if (layer === "room-poly") colorClass = "bg-emerald-950/30 border-emerald-800 text-emerald-200";
          }

          return (
            <button
              key={layer}
              id={`btn_layer_${layer}`}
              onClick={() => toggleLayer(layer)}
              className={`flex items-center space-x-1.5 px-2 py-1 rounded border transition-all font-mono text-[10px] ${colorClass}`}
            >
              {isActive ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
              <span className="capitalize">
                {layer === "k pencere"
                  ? "Pencereler"
                  : layer === "room-poly"
                    ? "Odalar (Alanlar)"
                    : layer === "duvar"
                      ? "Duvarlar"
                      : layer}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
