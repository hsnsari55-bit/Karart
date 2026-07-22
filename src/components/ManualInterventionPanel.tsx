import React, { useState, useEffect } from "react";
import { Floor, CADEntity, Point } from "../types";
import { 
  Wrench, 
  Trash2, 
  Plus, 
  Layers, 
  Sliders, 
  HelpCircle, 
  Cpu, 
  RotateCcw,
  Sparkles,
  Info
} from "lucide-react";

interface ManualInterventionPanelProps {
  floor: Floor;
  selectedEntityId: string | null;
  onSelectEntity: (id: string | null) => void;
  onUpdateFloorEntities: (updatedEntities: CADEntity[]) => void;
}

export default function ManualInterventionPanel({
  floor,
  selectedEntityId,
  onSelectEntity,
  onUpdateFloorEntities,
}: ManualInterventionPanelProps) {
  // Local state for adding new CAD/BIM elements
  const [newType, setNewType] = useState<"LINE" | "COLUMN" | "DOOR" | "WINDOW">("LINE");
  const [newX0, setNewX0] = useState<number>(100);
  const [newY0, setNewY0] = useState<number>(100);
  const [newX1, setNewX1] = useState<number>(200);
  const [newY1, setNewY1] = useState<number>(100);
  const [newThickness, setNewThickness] = useState<number>(25);
  const [newWidth, setNewWidth] = useState<number>(80);

  // Find currently selected element
  const selectedEntity = floor.entities.find((e) => e.id === selectedEntityId) || null;

  // Local state for editing the active selection
  const [editX0, setEditX0] = useState<number>(0);
  const [editY0, setEditY0] = useState<number>(0);
  const [editX1, setEditX1] = useState<number>(0);
  const [editY1, setEditY1] = useState<number>(0);
  const [editThickness, setEditThickness] = useState<number>(25);
  const [editWidth, setEditWidth] = useState<number>(80);

  // Sync edits state when selection changes
  useEffect(() => {
    if (selectedEntity) {
      setEditX0(selectedEntity.start.x);
      setEditY0(selectedEntity.start.y);
      setEditX1(selectedEntity.end ? selectedEntity.end.x : selectedEntity.start.x);
      setEditY1(selectedEntity.end ? selectedEntity.end.y : selectedEntity.start.y);
      setEditThickness(selectedEntity.thickness || 25);
      setEditWidth(selectedEntity.width || 80);
    }
  }, [selectedEntityId, selectedEntity]);

  // Handle adding new custom CAD entity
  const handleAddEntity = () => {
    let layer: "duvar" | "kolon" | "kapı" | "k pencere" | "aks" = "duvar";
    if (newType === "COLUMN") layer = "kolon";
    else if (newType === "DOOR") layer = "kapı";
    else if (newType === "WINDOW") layer = "k pencere";

    const customId = `manual_${newType.toLowerCase()}_${Math.random().toString(36).substr(2, 6)}`;
    const newEntity: CADEntity = {
      id: customId,
      type: newType,
      layer,
      start: { x: newX0, y: newY0 },
      end: { x: newX1, y: newY1 },
      thickness: newType === "LINE" || newType === "COLUMN" ? newThickness : undefined,
      width: newType === "DOOR" || newType === "WINDOW" ? newWidth : undefined,
      status: "original",
    };

    const updated = [...floor.entities, newEntity];
    onUpdateFloorEntities(updated);
    onSelectEntity(customId); // auto-select new entity
  };

  // Handle saving edits of the selected element
  const handleSaveEdit = () => {
    if (!selectedEntity) return;

    const updated = floor.entities.map((e) => {
      if (e.id === selectedEntity.id) {
        return {
          ...e,
          start: { ...e.start, x: editX0, y: editY0 },
          end: e.end ? { ...e.end, x: editX1, y: editY1 } : { x: editX1, y: editY1 },
          thickness: e.type === "LINE" || e.type === "COLUMN" ? editThickness : undefined,
          width: e.type === "DOOR" || e.type === "WINDOW" ? editWidth : undefined,
        };
      }
      return e;
    });

    onUpdateFloorEntities(updated);
  };

  // Handle deleting the selected element
  const handleDeleteEntity = (idToDelete: string) => {
    const updated = floor.entities.filter((e) => e.id !== idToDelete);
    onUpdateFloorEntities(updated);
    onSelectEntity(null);
  };

  // Quick preset helper to trigger standard test floor plan adjustments
  const handleResetPresets = () => {
    // Reload original floor plan
    window.location.reload();
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col space-y-6">
      
      {/* SECTION HEADER */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="bg-emerald-500/10 p-1.5 rounded text-emerald-400 border border-emerald-500/20">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-zinc-100 flex items-center space-x-1.5">
              <span>MANUEL MÜDAHALE VE PARAMETRİK EDİTÖR</span>
              <span className="bg-amber-500/10 text-amber-400 text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border border-amber-500/20">
                Ar-Ge Kontrolü
              </span>
            </h2>
            <p className="text-[10px] text-zinc-400 font-mono mt-0.5">
              3DS MAX/BLENDER MODELLEME SÜRECİNİ DAKİKALARA İNDİREN REVİZYON SİSTEMİ
            </p>
          </div>
        </div>
      </div>

      {/* AR-GE BUSINESS PITCH INTRO */}
      <div className="bg-zinc-950/60 border border-zinc-800/80 p-3 rounded-lg flex items-start space-x-3 text-xs text-zinc-400 leading-relaxed">
        <Sparkles className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-zinc-200">KOSGEB & Proje Destekleri İçin Değer Önerisi:</span> Bu arayüz, 
          klasik çizimlerden elde edilen parametrik geometrilerin mühendis veya tasarımcı tarafından 
          <span className="text-emerald-400 font-semibold"> tek tıkla canlı olarak manipüle edilmesini</span> sağlar. 
          Böylece 3D Max veya AutoCAD üzerinde günlerce sürecek duvar kalınlığı, kapı yerleşimi ve 
          aks düzeltme revizyonları saniyeler içinde tamamlanır ve 3D WebGL render ortamı anında güncellenir.
        </div>
      </div>

      {/* EDIT & CONTROL LAYOUT */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: ELEMENTS DIRECTORY (5 COLS) */}
        <div className="md:col-span-5 flex flex-col space-y-3">
          <label className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider flex items-center justify-between">
            <span>BIM Nesne Dizini ({floor.entities.length})</span>
            <span className="text-[9px] text-zinc-600">Seçmek için listeden veya çizimden tıklayın</span>
          </label>

          <div className="bg-zinc-950 border border-zinc-800/80 rounded-lg overflow-y-auto max-h-[350px] p-2 space-y-1.5">
            {floor.entities.map((e) => {
              const isSelected = e.id === selectedEntityId;
              let badgeColor = "bg-zinc-800 text-zinc-400";
              let labelText: string = e.type;

              if (e.layer === "duvar") {
                badgeColor = "bg-emerald-950/30 text-emerald-400 border border-emerald-900/30";
                labelText = `Duvar (${e.thickness || 15}cm)`;
              } else if (e.layer === "kolon") {
                badgeColor = "bg-red-950/30 text-red-400 border border-red-900/30";
                labelText = `Kolon (${e.thickness || 30}x${e.thickness || 30})`;
              } else if (e.layer === "kapı") {
                badgeColor = "bg-amber-950/30 text-amber-400 border border-amber-900/30";
                labelText = `Kapı (${e.width || 80}cm)`;
              } else if (e.layer === "k pencere") {
                badgeColor = "bg-sky-950/30 text-sky-400 border border-sky-900/30";
                labelText = `Pencere (${e.width || 80}cm)`;
              }

              return (
                <button
                  key={e.id}
                  onClick={() => onSelectEntity(isSelected ? null : e.id)}
                  className={`w-full flex items-center justify-between p-2 rounded text-left transition-all text-xs font-mono border ${
                    isSelected
                      ? "bg-zinc-800 border-amber-500 text-white shadow"
                      : "bg-zinc-900/50 border-transparent text-zinc-400 hover:bg-zinc-900 hover:border-zinc-800"
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${badgeColor}`}>
                      {e.layer}
                    </span>
                    <span className="truncate">{labelText}</span>
                  </div>
                  <span className="text-[10px] text-zinc-500">
                    x:{Math.round(e.start.x)}, y:{Math.round(e.start.y)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* RIGHT COLUMN: DETAILED EDITS & ADDITIONS (7 COLS) */}
        <div className="md:col-span-7 flex flex-col space-y-4">
          
          {/* 1. SELECTION PARAMETER CONTROLS */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3.5 space-y-3.5">
            <h3 className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              <span>Seçili Nesne Parametreleri</span>
            </h3>

            {selectedEntity ? (
              <div className="space-y-4 animate-fade-in text-xs font-mono">
                
                {/* ID & Fast Delete */}
                <div className="flex items-center justify-between bg-zinc-900/80 p-2 rounded border border-zinc-800">
                  <span className="text-[11px] text-zinc-400">Nesne ID: <strong className="text-emerald-400">{selectedEntity.id}</strong></span>
                  <button
                    onClick={() => handleDeleteEntity(selectedEntity.id)}
                    className="flex items-center space-x-1 px-2 py-1 bg-red-950/40 text-red-400 hover:bg-red-900 hover:text-white rounded transition-colors text-[10px]"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Nesneyi Sil</span>
                  </button>
                </div>

                {/* Coordinate Adjustments */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] text-zinc-500 block mb-1">Başlangıç Noktası (X0, Y0)</label>
                    <div className="flex space-x-1">
                      <input
                        type="number"
                        value={editX0}
                        onChange={(e) => { setEditX0(Number(e.target.value)); }}
                        onBlur={handleSaveEdit}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                      />
                      <input
                        type="number"
                        value={editY0}
                        onChange={(e) => { setEditY0(Number(e.target.value)); }}
                        onBlur={handleSaveEdit}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  </div>

                  {selectedEntity.type !== "COLUMN" && (
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">Bitiş Noktası (X1, Y1)</label>
                      <div className="flex space-x-1">
                        <input
                          type="number"
                          value={editX1}
                          onChange={(e) => { setEditX1(Number(e.target.value)); }}
                          onBlur={handleSaveEdit}
                          className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                        />
                        <input
                          type="number"
                          value={editY1}
                          onChange={(e) => { setEditY1(Number(e.target.value)); }}
                          onBlur={handleSaveEdit}
                          className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Dimensions (Thickness / Width) */}
                <div className="grid grid-cols-2 gap-3 border-t border-zinc-900 pt-3">
                  {(selectedEntity.type === "LINE" || selectedEntity.type === "COLUMN") && (
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">
                        Duvar / Kolon Kalınlığı (cm)
                      </label>
                      <input
                        type="number"
                        value={editThickness}
                        onChange={(e) => { setEditThickness(Number(e.target.value)); }}
                        onBlur={handleSaveEdit}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  )}

                  {(selectedEntity.type === "DOOR" || selectedEntity.type === "WINDOW") && (
                    <div>
                      <label className="text-[10px] text-zinc-500 block mb-1">
                        Açıklık Genişliği (cm)
                      </label>
                      <input
                        type="number"
                        value={editWidth}
                        onChange={(e) => { setEditWidth(Number(e.target.value)); }}
                        onBlur={handleSaveEdit}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  )}
                </div>

                {/* Info Text */}
                <p className="text-[9px] text-zinc-500 flex items-center space-x-1">
                  <Info className="w-3 h-3 text-amber-500 flex-shrink-0" />
                  <span>Kutulardaki değerleri değiştirdiğinizde CAD ve 3D render görünümleri otomatik güncellenir.</span>
                </p>

              </div>
            ) : (
              <div className="text-center py-10 text-zinc-500 text-xs italic border border-dashed border-zinc-800 rounded">
                Düzenlemek için listeden veya 2D çizimden bir eleman seçin.
              </div>
            )}
          </div>

          {/* 2. ADD NEW CAD / BIM ELEMENTS FORM */}
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-3.5 space-y-3">
            <h3 className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span>Yeni Parametrik Eleman Ekle</span>
            </h3>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="text-[10px] text-zinc-500 block mb-1">Eleman Tipi</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value as any)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="LINE">Duvar (LINE)</option>
                  <option value="COLUMN">Kolon (COLUMN)</option>
                  <option value="DOOR">Kapı (DOOR)</option>
                  <option value="WINDOW">Pencere (WINDOW)</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] text-zinc-500 block mb-1">
                  {newType === "LINE" || newType === "COLUMN" ? "Kalınlık (cm)" : "Genişlik (cm)"}
                </label>
                <input
                  type="number"
                  value={newType === "LINE" || newType === "COLUMN" ? newThickness : newWidth}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    if (newType === "LINE" || newType === "COLUMN") setNewThickness(val);
                    else setNewWidth(val);
                  }}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            {/* Placement Coordinates */}
            <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-1">
              <div>
                <label className="text-[10px] text-zinc-500 block mb-1">Başlangıç (X0, Y0)</label>
                <div className="flex space-x-1">
                  <input
                    type="number"
                    value={newX0}
                    onChange={(e) => setNewX0(Number(e.target.value))}
                    placeholder="X0"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200"
                  />
                  <input
                    type="number"
                    value={newY0}
                    onChange={(e) => setNewY0(Number(e.target.value))}
                    placeholder="Y0"
                    className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200"
                  />
                </div>
              </div>

              {newType !== "COLUMN" && (
                <div>
                  <label className="text-[10px] text-zinc-500 block mb-1">Bitiş (X1, Y1)</label>
                  <div className="flex space-x-1">
                    <input
                      type="number"
                      value={newX1}
                      onChange={(e) => setNewX1(Number(e.target.value))}
                      placeholder="X1"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200"
                    />
                    <input
                      type="number"
                      value={newY1}
                      onChange={(e) => setNewY1(Number(e.target.value))}
                      placeholder="Y1"
                      className="w-full bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-zinc-200"
                    />
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleAddEntity}
              className="w-full mt-2 flex items-center justify-center space-x-1.5 py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-mono rounded font-bold transition-all text-xs cursor-pointer shadow"
            >
              <Plus className="w-4 h-4" />
              <span>BIM MODELİNE YENİ ELEMAN EKLE</span>
            </button>
          </div>

        </div>

      </div>

      {/* REVERT / CONTROL FOOTER */}
      <div className="flex items-center justify-between border-t border-zinc-800/80 pt-4 text-[10px] font-mono text-zinc-500">
        <span className="flex items-center space-x-1">
          <Wrench className="w-3.5 h-3.5 text-zinc-400" />
          <span>Tüm geometrik veriler saf JS nesneleri olarak bellektedir. Değişiklikler anlıktır.</span>
        </span>
        <button
          onClick={handleResetPresets}
          className="flex items-center space-x-1 px-2.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white rounded border border-zinc-700 transition-all cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5 text-amber-500" />
          <span>Sıfırla & Orijinal Çizimi Yükle</span>
        </button>
      </div>

    </div>
  );
}
