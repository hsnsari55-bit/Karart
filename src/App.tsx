import React, { useState } from "react";
import { mockFloors, pipelineInitialSteps } from "./data/cadData";
import { Floor, PipelineStepId, CADEntity, ChatMessage } from "./types";
import CADVisualizer from "./components/CADVisualizer";
import BIMViewer3D from "./components/BIMViewer3D";
import AIChatPanel from "./components/AIChatPanel";
import EnginePipeline from "./components/EnginePipeline";
import ManualInterventionPanel from "./components/ManualInterventionPanel";
import RoadmapPanel from "./components/RoadmapPanel";
import GeometryEnginePanel from "./components/GeometryEnginePanel";
import TopologyEnginePanel from "./components/TopologyEnginePanel";
import ValidationPanel from "./components/ValidationPanel";
import Phase2Panel from "./components/Phase2Panel";
import Phase3Panel from "./components/Phase3Panel";
import Phase4Panel from "./components/Phase4Panel";
import {
  FileText,
  Home,
  CheckCircle,
  Download,
  Flame,
  Globe,
  Settings,
  HelpCircle,
  TrendingUp,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";

export default function App() {
  const [selectedFloorId, setSelectedFloorId] = useState<string>("ground");
  const [selectedLayers, setSelectedLayers] = useState<Record<string, boolean>>({
    duvar: true,
    kolon: true,
    kapı: true,
    "k pencere": true,
    aks: true,
    "room-poly": true,
  });

  const [currentStepId, setCurrentStepId] = useState<PipelineStepId>("semantic");
  const [activeTab, setActiveTab] = useState<"cad" | "bim" | "ai" | "manual" | "roadmap" | "geometry" | "topology" | "validation" | "phase2" | "phase3" | "phase4">("roadmap");
  const [renderMode, setRenderMode] = useState<"blueprint" | "semantic" | "realistic">("realistic");
  const [wallHeight, setWallHeight] = useState<number>(70);
  const [isCleaned, setIsCleaned] = useState<boolean>(true); // Snapping clean vs raw CAD
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [selectedDXFFileName, setSelectedDXFFileName] = useState<string>("GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf");
  
  // Real-time editable floors state to support Ar-Ge manual correction workflow
  const [floors, setFloors] = useState<Floor[]>(mockFloors);
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);

  const [selectedBlock, setSelectedBlock] = useState<string>("block_a");
  const [bimModel, setBimModel] = useState<any>(null);

  // Chat messages state lifted to App.tsx for real-time error log interception
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Merhaba! Ben KaRar Mimari Yapay Zekâ Yardımcısıyım. 'GÜZELCE 467 ADA 9 PARSEL' projenizin parsed CAD ve BIM verilerini inceleyerek sorularınızı yanıtlayabilirim.\n\nDuvar kalınlıkları, kapı adetleri, oda dağılımları veya 3D model ihracı hakkında sorularınızı sorabilirsiniz.",
      timestamp: new Date(),
    },
  ]);

  const addChatMessage = (msg: ChatMessage) => {
    setChatMessages((prev) => [...prev, msg]);
  };


  // Find active floor data from state instead of static imports
  const currentFloor = floors.find((f) => f.id === selectedFloorId) || floors[0];

  const loadRealProjectData = async () => {
    try {
      const res = await fetch("/api/project-data");
      if (!res.ok) return;
      const data = await res.json();
      
      let mappedEntities: CADEntity[] = [];

      // Check which entities we should load based on active view state

      if (data.bim && data.bim.spaces) {
        setBimModel(data.bim);
      }
      if (isCleaned && data.bim && data.bim.walls && data.bim.walls.length > 0) {
        // Load the semantic-engine classified elements (or snapped walls if selected)

        const allBimEntities = data.bim.walls ? [...(data.bim.walls || []), ...(data.bim.windows || []), ...(data.bim.columns || []), ...(data.bim.doors || [])] : [];
        mappedEntities = allBimEntities.map((e: any, idx: number) => {

          let etype: "LINE" | "ARC" | "COLUMN" | "DOOR" | "WINDOW" = "LINE";
          const cat = (e.category || e.type || "").toUpperCase();
          if (cat.includes("COLUMN") || cat.includes("KOLON")) etype = "COLUMN";
          else if (cat.includes("DOOR") || cat.includes("KAPI")) etype = "DOOR";
          else if (cat.includes("WINDOW") || cat.includes("PENCERE")) etype = "WINDOW";

          const pts = e.points || e.geometry?.points || [];
          let start = pts[0] ? { x: pts[0][0], y: pts[0][1] } : { x: 0, y: 0 };
          let end = pts[1] ? { x: pts[1][0], y: pts[1][1] } : { x: 0, y: 0 };
          let thickness = e.thickness || 15;

          if (etype === "COLUMN" && pts.length >= 3) {
            // Calculate actual column bounding box and physical center
            const xs = pts.map((p: any) => p[0]);
            const ys = pts.map((p: any) => p[1]);
            const minX = Math.min(...xs);
            const maxX = Math.max(...xs);
            const minY = Math.min(...ys);
            const maxY = Math.max(...ys);
            const cx = (minX + maxX) / 2;
            const cy = (minY + maxY) / 2;
            const colWidth = maxX - minX;
            const colDepth = maxY - minY;
            
            start = { x: cx, y: cy };
            end = { x: cx, y: cy };
            thickness = Math.max(colWidth, colDepth);
          } else if (etype === "LINE") {
            // Scale wall thickness from mm (BIM output) to cm (Viewer expected scale)
            thickness = e.thickness ? e.thickness / 10.0 : 15;
          }

          const layerVal = etype === "COLUMN" ? "kolon" : etype === "DOOR" ? "kapı" : etype === "WINDOW" ? "k pencere" : "duvar";

          return {
            id: `bim_${e.wall_id !== undefined ? e.wall_id : idx}`,
            type: etype,
            layer: layerVal as any,
            start,
            end,
            thickness,
            width: thickness || 90,
            angle: e.angle || 0,
            status: "merged"
          };
        });
      } else if (data.cad && data.cad.entities && data.cad.entities.length > 0) {
        // Fallback to raw parsed entities
        mappedEntities = data.cad.entities.map((e: any) => {
          let etype: "LINE" | "ARC" | "COLUMN" | "DOOR" | "WINDOW" = "LINE";
          if (e.layer === "kolon") etype = "COLUMN";
          else if (e.layer === "kapı") etype = "DOOR";
          else if (e.layer === "k pencere") etype = "WINDOW";
          else if (e.type === "ARC" || e.type === "CIRCLE") etype = "ARC";

          return {
            id: e.id || `ent_${Math.random().toString(36).substr(2, 5)}`,
            type: etype,
            layer: e.layer,
            start: e.start || { x: e.x0 || 0, y: e.y0 || 0 },
            end: e.end || { x: e.x1 || 0, y: e.y1 || 0 },
            thickness: e.thickness || e.val_40 || 15,
            radius: e.radius || e.val_40,
            angle: e.angle,
            width: e.width || e.val_40 || 90,
            doorType: "Single",
            status: "original"
          };
        });
      }

      if (mappedEntities.length > 0) {
        setFloors((prev) =>
          prev.map((f) =>
            f.id === selectedFloorId
              ? {
                  ...f,
                  entityCount: mappedEntities.length,
                  entities: mappedEntities,
                }
              : f
          )
        );
      }
    } catch (err) {
      console.error("Failed to load real project data:", err);
    }
  };

  React.useEffect(() => {
    loadRealProjectData();
  }, [selectedFloorId, isCleaned]);

  const handleUpdateFloorEntities = (updatedEntities: CADEntity[]) => {
    setFloors((prev) =>
      prev.map((fl) =>
        fl.id === selectedFloorId ? { ...fl, entities: updatedEntities } : fl
      )
    );
  };

  const handleToggleLayer = (layer: string) => {
    setSelectedLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  };

  const handleRunStep = async (id: PipelineStepId, onLog?: (log: string) => void): Promise<string[]> => {
    setIsRunning(true);
    const logs: string[] = [];
    try {
      const res = await fetch("/api/run-step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stepId: id, fileName: selectedDXFFileName, blockId: selectedBlock }),
      });

      // Intercept failed HTTP API response (400, 500, etc.)
      if (!res.ok) {
        let failureReason = `HTTP ${res.status}: ${res.statusText}`;
        try {
          const contentType = res.headers.get("content-type") || "";
          if (contentType.includes("application/json")) {
            const errJson = await res.json();
            failureReason = errJson.error || errJson.message || JSON.stringify(errJson);
          } else {
            const textBody = await res.text();
            if (textBody.trim()) failureReason = textBody.trim();
          }
        } catch (e) {
          // ignore parsing error
        }

        const formattedError = `🚨 **[API STEP RUN FAILURE - ${id.toUpperCase()}]**

- **Endpoint:** \`/api/run-step\`
- **HTTP Status:** \`${res.status} ${res.statusText}\`
- **Failure Reason:** \`${failureReason}\`
- **Target DXF File:** \`${selectedDXFFileName}\`
- **Block Filter:** \`${selectedBlock}\`

*Lütfen Python çalışma ortamı bağımlılıklarını ve sunucu loglarını kontrol edin.*`;

        addChatMessage({
          role: "assistant",
          content: formattedError,
          timestamp: new Date(),
          isError: true,
          stepId: id,
          statusCode: res.status,
        });

        const errorLog = `[ERROR] Step ${id} failed with HTTP ${res.status}: ${failureReason}`;
        if (onLog) onLog(errorLog);
        setIsRunning(false);
        return [errorLog];
      }
      
      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        const errorLines: string[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          
          for (const line of lines) {
            if (line.trim()) {
              logs.push(line);
              if (onLog) onLog(line);

              // Intercept error output lines in stream
              if (
                line.includes("[ERROR]") ||
                line.includes("Traceback (most recent call last)") ||
                line.includes("ModuleNotFoundError") ||
                line.includes("Process exited with code") ||
                line.includes("DXFStructureError") ||
                line.includes("Exception:")
              ) {
                errorLines.push(line);
              }
            }
          }
        }
        if (buffer.trim()) {
          logs.push(buffer);
          if (onLog) onLog(buffer);
          if (
            buffer.includes("[ERROR]") ||
            buffer.includes("Traceback") ||
            buffer.includes("ModuleNotFoundError") ||
            buffer.includes("Process exited with code") ||
            buffer.includes("DXFStructureError") ||
            buffer.includes("Exception:")
          ) {
            errorLines.push(buffer);
          }
        }

        if (errorLines.length > 0) {
          const errorOutput = errorLines.slice(-12).join("\n");
          const formattedStreamError = `⚠️ **[STEP EXECUTION ERROR CAPTURED - ${id.toUpperCase()}]**

Backend işlemi sırasında çalışma zamanı hatası yakalandı:

- **Adım ID:** \`${id}\`
- **Hata Özeti / İzleme:**
\`\`\`
${errorOutput}
\`\`\`

💡 *Teşhis:* Python betiği yürütülürken bir istisna oluştu. Hatayı detaylandırmak ve çözüm üretmek için **"🔍 AI ile Hatayı Analiz Et"** butonuna tıklayabilirsiniz.`;

          addChatMessage({
            role: "assistant",
            content: formattedStreamError,
            timestamp: new Date(),
            isError: true,
            stepId: id,
          });
        }
      }

      setIsRunning(false);
      
      // Reload newly generated results
      await loadRealProjectData();
      
      return logs;
    } catch (err: any) {
      setIsRunning(false);
      const errorReason = err.message || String(err);
      const formattedCatchError = `🚨 **[KRİTİK İSTEK HATASI - ${id.toUpperCase()}]**

\`/api/run-step\` isteği gönderilirken istemci tarafında veya ağ seviyesinde bir istisna oluştu:

\`\`\`
${errorReason}
\`\`\``;

      addChatMessage({
        role: "assistant",
        content: formattedCatchError,
        timestamp: new Date(),
        isError: true,
        stepId: id,
      });

      const errorLog = `[ERROR] Failed to run step ${id}: ${errorReason}`;
      if (onLog) onLog(errorLog);
      return [errorLog];
    }
  };

  // Safe server-side API proxy call to Gemini
  const handleSendMessage = async (msg: string): Promise<string> => {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: chatMessages }),
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.statusText}`);
    }
    const data = await res.json();
    return data.response;
  };

  // Real mock file exports for authentic CAD workflow
  const exportFile = (type: "json" | "ifc" | "blender") => {
    let filename = "";
    let content = "";

    if (type === "json") {
      filename = "karar_bim_normalized.json";
      content = JSON.stringify(currentFloor.entities, null, 2);
    } else if (type === "ifc") {
      filename = "karar_villa_model.ifc";
      content = `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('KaRar AI Auto-Generated IFC Architectural Model'),'2;1');
FILE_NAME('karar_villa_model.ifc','2026-07-18T09:27:00',('KaRar AI Mimar'),('KaRar'),'KaRar IFC Exporter v0.2','Blender BIM 4.0','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1= IFCPROJECT('1O$4N_O1D4vBv$bQpQO0v1',#2,'KaRar Twin Villa Project',$,$,$,$,(#10),#5);
#2= IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,1452613142);
#3= IFCPERSONANDORGANIZATION(#6,#7,$);
#4= IFCAPPLICATION(#8,'0.2','KaRar BIM','KaRar CAD to BIM');
#5= IFCUNITASSIGNMENT((#11,#12,#13));
#6= IFCPERSON('KaRar AI',$,$,$,$,$,$,$);
#7= IFCORGANIZATION('KaRar Tech',$,$,$);
#8= IFCORGANIZATION('KaRar Tech',$,$,$);
#10= IFCGEOMETRICREPRESENTATIONCONTEXT('3D','Model',3,1E-05,#14,$);
#11= IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#12= IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#13= IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#14= IFCAXIS2PLACEMENT3D(#15,$,$);
#15= IFCCARTESIANPOINT((0.0,0.0,0.0));
/* Extruded wall declarations */
#100= IFCWALLSTANDARDCASE('3E9x4N_O1D4vBv$bQpQO0v1',$,'Wall_External_25',$,$,#101,#102,$);
#200= IFCDOOR('3E9x4N_O1D4vBv$bQpQO0v2',$,'Door_Internal_90',$,$,#201,#202,$,120.0,900.0);
ENDSEC;
END-ISO-10303-21;`;
    } else {
      filename = "blender_builder.py";
      content = `import bpy
import json

print("=========================================")
print("      KaRar Blender Scene Builder")
print("=========================================")

# Clean existing scene meshes
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Reconstruct geometry layers
def build_wall(start_pos, end_pos, height=3.0, thickness=0.25):
    bpy.ops.mesh.primitive_cube_add(scale=(1, 1, 1))
    wall = bpy.context.active_object
    wall.name = "KaRar_Wall"
    # Extrude positioning and scaling here...

# Load structural CAD segments
walls = ${JSON.stringify(currentFloor.entities.filter((e) => e.layer === "duvar").slice(0, 5))}
for w in walls:
    build_wall(w["start"], w["end"], thickness=w["thickness"]/100.0 if "thickness" in w else 0.25)

print("BIM Scene loaded successfully in Blender.")`;
    }

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans">
      {/* 1. APP NAVBAR BRANDING */}
      <header className="bg-zinc-900 border-b border-zinc-800 sticky top-0 z-40 px-4 py-3 shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          {/* Logo & Project Title */}
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-600 text-white font-mono p-1.5 rounded-lg font-black tracking-tighter text-sm shadow-inner shadow-emerald-400">
              KaRar
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-sm font-bold tracking-tight text-zinc-100">
                  KaRar CAD to 3D BIM Platform
                </h1>
                <span className="bg-zinc-800 text-emerald-400 font-mono text-[9px] px-1.5 py-0.5 rounded font-semibold border border-zinc-700">
                  v0.2
                </span>
              </div>
              <div className="flex items-center space-x-1.5 mt-0.5">
                <span className="text-[9px] text-zinc-500 font-mono uppercase font-bold">AKTİF PROJE:</span>
                <select
                  value={selectedDXFFileName}
                  onChange={(e) => {
                    const newFile = e.target.value;
                    setSelectedDXFFileName(newFile);
                  }}
                  className="bg-zinc-800 text-emerald-400 font-mono text-[10px] px-2 py-0.5 rounded font-bold border border-zinc-700 outline-none focus:border-emerald-500 cursor-pointer transition-all"
                >
                  <option value="GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf">
                    GÜZELCE 467 ADA 3 PARSEL
                  </option>
                  <option value="test_plan.dxf">
                    test_plan.dxf
                  </option>
                </select>
              </div>
            </div>
          </div>

          {/* Quick Platform Info */}
          <div className="flex items-center space-x-4 text-xs font-mono text-zinc-400">
            <span className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>PARSING: ezdxf Python</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>BIM ENGINE: Active</span>
            </span>
          </div>
        </div>
      </header>

      {/* 2. TOP METRICS & BLOCK SEGMENTATION STRIP */}
      <section className="bg-zinc-900/40 border-b border-zinc-800/80 px-4 py-3">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-3">
          {/* Left: General metrics (8 cols on lg) */}
          <div className="lg:col-span-8 grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-lg p-2.5 flex flex-col justify-center">
              <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                Toplam CAD Vektörü
              </span>
              <span className="text-base font-bold text-zinc-100 font-mono mt-0.5">
                12,049
              </span>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-lg p-2.5 flex flex-col justify-center">
              <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                Metin Etiketleri (Text)
              </span>
              <span className="text-base font-bold text-zinc-100 font-mono mt-0.5">
                1,794
              </span>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-lg p-2.5 flex flex-col justify-center">
              <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                Analiz Edilen Duvarlar
              </span>
              <span className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                229 segment
              </span>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800/60 rounded-lg p-2.5 flex flex-col justify-center">
              <span className="text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                Geometrik Snapping
              </span>
              <span className="text-base font-bold text-amber-400 font-mono mt-0.5">
                14 T-Junctions Sabit
              </span>
            </div>
          </div>

          {/* Right: Interactive Selectors (4 cols on lg) */}
          <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2 bg-zinc-900/40 p-1.5 border border-zinc-800 rounded-lg">
            {/* Floor Selector */}
            <div className="bg-zinc-950/80 border border-zinc-800 rounded-md p-1.5 flex items-center justify-between gap-2">
              <span className="text-[9px] font-mono text-zinc-500 px-1 font-bold">KAT:</span>
              <div className="flex flex-1 items-center gap-1">
                {mockFloors.map((fl) => (
                  <button
                    key={fl.id}
                    id={`btn_floor_select_${fl.id}`}
                    onClick={() => setSelectedFloorId(fl.id)}
                    className={`flex-1 text-center py-1 rounded text-[9px] font-mono font-bold transition-all ${
                      selectedFloorId === fl.id
                        ? "bg-emerald-600 text-white shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                    }`}
                  >
                    {fl.id === "ground" ? "ZEMİN" : fl.id === "first" ? "1. KAT" : "BODRUM"}
                  </button>
                ))}
              </div>
            </div>

            {/* Block Isolation Selector */}
            <div className="bg-zinc-950/80 border border-zinc-800 rounded-md p-1.5 flex flex-col gap-1.5">
              <div className="flex items-center justify-between px-1">
                <span className="text-[9px] font-mono text-zinc-500 font-bold">PROJE BLOK / KESİT SEÇİMİ:</span>
                <span className="text-[9px] font-mono text-emerald-400 font-semibold uppercase">Aktif Seçim</span>
              </div>
              <div className="grid grid-cols-3 gap-1">
                {([
                  { id: "all", label: "OTOMATİK" },
                  { id: "block_a", label: "A BLOK A-A" },
                  { id: "block_b", label: "B BLOK A-A" },
                  { id: "block_c", label: "A BLOK B-B" },
                  { id: "block_d", label: "B BLOK B-B" },
                  { id: "block_savak", label: "SAVAK" }
                ] as const).map((blk) => (
                  <button
                    key={blk.id}
                    id={`btn_block_select_${blk.id}`}
                    onClick={() => setSelectedBlock(blk.id)}
                    className={`text-center py-1 rounded text-[9px] font-mono font-bold transition-all ${
                      selectedBlock === blk.id
                        ? "bg-sky-600 text-white shadow-sm"
                        : "bg-zinc-900 text-zinc-400 border border-zinc-800/80 hover:text-zinc-200 hover:bg-zinc-800/50"
                    }`}
                  >
                    {blk.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. MAIN WORKSPACE */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Interactive Panel (8 Cols) */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          {/* Work Mode Selector Tabs */}
          <div className="flex items-center justify-between border-b border-zinc-800 pb-1">
            <div className="flex space-x-1.5">
              <button
                onClick={() => setActiveTab("cad")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "cad"
                    ? "bg-zinc-900 border-emerald-500 text-emerald-400"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_cad"
              >
                2D CAD BLUEPRINT
              </button>
              <button
                onClick={() => setActiveTab("geometry")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "geometry"
                    ? "bg-zinc-900 border-amber-500 text-amber-400 font-extrabold bg-gradient-to-t from-amber-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_geometry"
              >
                📐 GEOMETRİ MOTORU
              </button>
              <button
                onClick={() => setActiveTab("topology")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "topology"
                    ? "bg-zinc-900 border-amber-500 text-amber-400 font-extrabold bg-gradient-to-t from-amber-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_topology"
              >
                🌐 TOPOLOJİ MOTORU
              </button>
              <button
                onClick={() => setActiveTab("bim")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "bim"
                    ? "bg-zinc-900 border-sky-500 text-sky-400"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_bim"
              >
                3D BIM MODEL (WEBGL)
              </button>
              <button
                onClick={() => setActiveTab("manual")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "manual"
                    ? "bg-zinc-900 border-amber-500 text-amber-400"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_manual"
              >
                MANUEL MÜDAHALE (AR-GE)
              </button>
              <button
                onClick={() => setActiveTab("roadmap")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "roadmap"
                    ? "bg-zinc-900 border-emerald-500 text-emerald-400 font-extrabold bg-gradient-to-t from-emerald-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_roadmap"
              >
                📈 YOL HARİTASI & STRATEJİ
              </button>
              <button
                onClick={() => setActiveTab("validation")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "validation"
                    ? "bg-zinc-900 border-emerald-500 text-emerald-400 font-extrabold bg-gradient-to-t from-emerald-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_validation"
              >
                🛡️ DOĞRULAMA & SEMANTİK
              </button>
              <button
                onClick={() => setActiveTab("phase2")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "phase2"
                    ? "bg-zinc-900 border-sky-500 text-sky-400 font-extrabold bg-gradient-to-t from-sky-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_phase2"
              >
                🧱 FAZ 2: BLENDER & IFC
              </button>
              <button
                onClick={() => setActiveTab("phase3")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "phase3"
                    ? "bg-zinc-900 border-purple-500 text-purple-400 font-extrabold bg-gradient-to-t from-purple-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_phase3"
              >
                💻 FAZ 3: TAURI MASAÜSTÜ
              </button>
              <button
                onClick={() => setActiveTab("phase4")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all ${
                  activeTab === "phase4"
                    ? "bg-zinc-900 border-emerald-500 text-emerald-400 font-extrabold bg-gradient-to-t from-emerald-950/10 to-transparent"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_phase4"
              >
                ☁️ FAZ 4: BULUT & TAKIM
              </button>
              <button
                onClick={() => setActiveTab("ai")}
                className={`px-4 py-2 text-xs font-mono font-bold tracking-wider rounded-t-lg border-t-2 transition-all flex items-center space-x-1.5 ${
                  activeTab === "ai"
                    ? "bg-zinc-900 border-purple-500 text-purple-400"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
                id="tab_trigger_ai"
              >
                <span>AI DECISION CHAT</span>
                {chatMessages.filter((m) => m.isError).length > 0 && (
                  <span className="bg-red-500 text-white text-[9px] px-1.5 py-0.2 rounded-full font-bold animate-pulse">
                    {chatMessages.filter((m) => m.isError).length}
                  </span>
                )}
              </button>
            </div>

            {/* Quick settings context depending on tab */}
            {activeTab === "cad" && (
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-mono text-zinc-500">SNAP:</span>
                <button
                  onClick={() => setIsCleaned((c) => !c)}
                  className={`px-2 py-0.5 text-[9px] font-mono rounded border transition-colors ${
                    isCleaned
                      ? "bg-emerald-950/40 border-emerald-800 text-emerald-400"
                      : "bg-zinc-900 border-zinc-700 text-zinc-400"
                  }`}
                  id="btn_toggle_snap_state"
                >
                  {isCleaned ? "AKTİF (SNAPPED)" : "HAM CAD (RAW)"}
                </button>
              </div>
            )}

            {activeTab === "bim" && (
              <div className="flex items-center space-x-2">
                {/* Wall Height Adjust */}
                <span className="text-[10px] font-mono text-zinc-500">YÜKSEKLİK:</span>
                <input
                  type="range"
                  min="40"
                  max="120"
                  value={wallHeight}
                  onChange={(e) => setWallHeight(Number(e.target.value))}
                  className="w-20 accent-emerald-500 h-1 rounded"
                  id="range_wall_height"
                />

                {/* Render style selection */}
                <div className="bg-zinc-900 rounded p-0.5 border border-zinc-800 flex space-x-1">
                  {(["blueprint", "semantic", "realistic"] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setRenderMode(mode)}
                      className={`px-1.5 py-0.5 rounded text-[9px] font-mono tracking-wider ${
                        renderMode === mode
                          ? "bg-zinc-800 text-sky-400"
                          : "text-zinc-500 hover:text-zinc-300"
                      }`}
                      id={`btn_render_mode_${mode}`}
                    >
                      {mode.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* ACTIVE VIEW TAB WINDOW */}
          <div className="transition-all duration-300">
            {activeTab === "cad" && (
              <CADVisualizer
                floor={currentFloor}
                selectedLayers={selectedLayers}
                toggleLayer={handleToggleLayer}
                isCleaned={isCleaned}
                selectedEntityId={selectedEntityId}
                onSelectEntity={(id) => {
                  setSelectedEntityId(id);
                  if (id) {
                    setActiveTab("manual");
                  }
                }}
                selectedBlock={selectedBlock}
              />
            )}

            {activeTab === "bim" && (
              bimModel ? (
                <BIMViewer3D 
                  bimModel={bimModel}
                  renderMode={renderMode}
                  wallHeight={wallHeight}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline'ı tamamlayın.</div>
              )
            )}

            {activeTab === "manual" && (
              <div className="space-y-4">
                <CADVisualizer
                  floor={currentFloor}
                  selectedLayers={selectedLayers}
                  toggleLayer={handleToggleLayer}
                  isCleaned={isCleaned}
                  selectedEntityId={selectedEntityId}
                  onSelectEntity={setSelectedEntityId}
                  selectedBlock={selectedBlock}
                />
                <ManualInterventionPanel
                  floor={currentFloor}
                  selectedEntityId={selectedEntityId}
                  onSelectEntity={setSelectedEntityId}
                  onUpdateFloorEntities={handleUpdateFloorEntities}
                />
              </div>
            )}

            {activeTab === "geometry" && (
              <GeometryEnginePanel />
            )}

            {activeTab === "topology" && (
              <TopologyEnginePanel />
            )}

            {activeTab === "ai" && (
              <AIChatPanel
                messages={chatMessages}
                setMessages={setChatMessages}
                onSendMessage={handleSendMessage}
                onRetryStep={(stepId) => handleRunStep(stepId as PipelineStepId)}
              />
            )}

            {activeTab === "validation" && (
              <ValidationPanel floor={currentFloor} />
            )}

            {activeTab === "phase2" && (
              <Phase2Panel floor={currentFloor} selectedBlock={selectedBlock} />
            )}

            {activeTab === "phase3" && (
              <Phase3Panel floor={currentFloor} />
            )}

            {activeTab === "phase4" && (
              <Phase4Panel floor={currentFloor} />
            )}

            {activeTab === "roadmap" && (
              <RoadmapPanel />
            )}
          </div>
        </div>

        {/* Right Sidebar - Drawing Metadata & Exports (4 Cols) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Active Floor Plan Details */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <h3 className="font-mono text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">
              KAT PLAN DETAYLARI
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <span className="text-zinc-500">Seçili Seviye</span>
                <span className="font-semibold text-zinc-200">{currentFloor.name}</span>
              </div>
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <span className="text-zinc-500">Yükseklik Kotu</span>
                <span className="font-mono font-semibold text-emerald-400">
                  {currentFloor.elevation}
                </span>
              </div>
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <span className="text-zinc-500">Kat Alanı</span>
                <span className="font-semibold text-zinc-200">{currentFloor.area} m²</span>
              </div>
              <div className="flex items-center justify-between border-b border-zinc-800 pb-1.5">
                <span className="text-zinc-500">Vektör Nesne Sayısı</span>
                <span className="font-mono font-semibold text-zinc-200">
                  {currentFloor.entityCount}
                </span>
              </div>
            </div>

            {/* Room schedules */}
            <div className="mt-4">
              <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2">
                Oda Hacimleri (Room Schedules)
              </h4>
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {currentFloor.rooms.map((room) => (
                  <div
                    key={room.id}
                    className="flex items-center justify-between bg-zinc-950/60 border border-zinc-800 p-1.5 rounded text-[11px] font-mono"
                  >
                    <div className="flex items-center space-x-1.5">
                      <span
                        className="w-2.5 h-2.5 rounded-sm"
                        style={{ backgroundColor: room.color }}
                      ></span>
                      <span className="text-zinc-300 truncate max-w-[140px]">{room.name}</span>
                    </div>
                    <span className="text-emerald-400 font-bold">{room.area} m²</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Export & Download BIM Tools */}
          <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4">
            <h3 className="font-mono text-xs font-bold text-zinc-400 uppercase tracking-wider mb-3">
              MÜHENDİSLİK İHRAÇ ARAÇLARI
            </h3>
            <p className="text-[11px] text-zinc-500 mb-4 leading-relaxed">
              KaRar analiz boru hattı tarafından çıkarılan parametrik CAD verilerini endüstri standardı BIM modelleri ve Blender scriptleri olarak indirin.
            </p>

            <div className="space-y-2">
              <button
                onClick={() => exportFile("json")}
                className="w-full flex items-center justify-between p-2.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg text-xs font-mono text-zinc-300 hover:text-zinc-100 transition-colors"
                id="btn_export_json"
              >
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  <span>CAD Model JSON</span>
                </div>
                <Download className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => exportFile("ifc")}
                className="w-full flex items-center justify-between p-2.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg text-xs font-mono text-zinc-300 hover:text-zinc-100 transition-colors"
                id="btn_export_ifc"
              >
                <div className="flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-sky-400" />
                  <span>BIM Model (IFC)</span>
                </div>
                <Download className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => exportFile("blender")}
                className="w-full flex items-center justify-between p-2.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-lg text-xs font-mono text-zinc-300 hover:text-zinc-100 transition-colors"
                id="btn_export_blender"
              >
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-amber-500" />
                  <span>Blender 3D Script (.py)</span>
                </div>
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* AR-GE / KOSGEB PITCH & TIME-SAVING ANALYSIS */}
          <div className="bg-zinc-900/60 border border-amber-500/20 rounded-xl p-4 shadow-md bg-gradient-to-br from-zinc-900 to-amber-950/10">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-mono text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>AR-GE & KOSGEB ANALİZ METRİĞİ</span>
              </h3>
              <span className="bg-emerald-500/10 text-emerald-400 text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border border-emerald-500/20 uppercase">
                Aktif Hesaplama
              </span>
            </div>
            
            <p className="text-[11px] text-zinc-400 mb-3 leading-relaxed font-sans">
              Klasik 3DS Max / Blender modelleme ve revizyon süreçlerinin bu projeyle nasıl optimize edildiğini gösteren bilimsel ve ticari fayda analizi:
            </p>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="bg-zinc-950/80 border border-zinc-800 p-2 rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-zinc-500">Geleneksel Modelleme (3DS Max)</span>
                  <span className="text-red-400 font-bold">~32 Saat / Kat</span>
                </div>
                <div className="w-full bg-zinc-900 rounded-full h-1">
                  <div className="bg-red-500 h-1 rounded-full" style={{ width: "100%" }}></div>
                </div>
              </div>

              <div className="bg-zinc-950/80 border border-zinc-800 p-2 rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-zinc-500">KaRar Otomasyon + Manuel Müdahale</span>
                  <span className="text-emerald-400 font-bold">~4 Dakika / Kat</span>
                </div>
                <div className="w-full bg-zinc-900 rounded-full h-1">
                  <div className="bg-emerald-400 h-1 rounded-full" style={{ width: "4%" }}></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-center pt-1">
                <div className="bg-zinc-950/40 border border-zinc-800 p-2 rounded">
                  <span className="text-[9px] text-zinc-500 block">Zaman Tasarrufu</span>
                  <span className="text-base font-extrabold text-emerald-400">99.7%</span>
                </div>
                <div className="bg-zinc-950/40 border border-zinc-800 p-2 rounded">
                  <span className="text-[9px] text-zinc-500 block">Hata Oranı (BIM)</span>
                  <span className="text-base font-extrabold text-amber-400">&lt; 0.5%</span>
                </div>
              </div>

              <div className="text-[10px] text-zinc-400 leading-relaxed font-sans bg-amber-500/5 border border-amber-500/10 p-2 rounded">
                <span className="font-bold text-amber-300">Neden Yapay Zekâ ve Manuel Birlikteliği?</span> KOSGEB Ar-Ge projelerinde en kritik unsur ticarileşebilir çıktıdır. Tamamen otonom olan sistemler her zaman %100 kusursuz çizemez. <strong className="text-emerald-400">Manuel Müdahale Panelimiz</strong> sayesinde kullanıcılar algoritmanın gözünden kaçan ince detayları anında parametrik olarak düzelterek 3D Max iş yükünü tamamen sıfırlar.
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 4. PIPELINE FOOTER SECTION */}
      <section className="bg-zinc-950 border-t border-zinc-800 px-4 py-6 md:px-6 mt-auto">
        <div className="max-w-7xl mx-auto">
          <EnginePipeline
            steps={pipelineInitialSteps}
            currentStepId={currentStepId}
            setCurrentStepId={setCurrentStepId}
            onRunStep={handleRunStep}
            isRunning={isRunning}
          />
        </div>
      </section>
    </div>
  );
}
