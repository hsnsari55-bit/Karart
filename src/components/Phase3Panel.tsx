import React, { useState, useEffect } from "react";
import { Floor } from "../types";
import { 
  Monitor, 
  Terminal, 
  FileCode, 
  Settings, 
  Upload, 
  Check, 
  HardDrive, 
  Cpu, 
  Zap, 
  Database,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  FolderOpen,
  Sliders,
  Play
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Phase3PanelProps {
  floor: Floor;
}

export default function Phase3Panel({ floor }: Phase3PanelProps) {
  const [activeSubTab, setActiveSubTab] = useState<"tauri" | "canvas" | "offline">("tauri");
  const [isDxfProcessing, setIsDxfProcessing] = useState(false);
  const [dxfLogs, setDxfLogs] = useState<string[]>([]);
  const [offlineSyncing, setOfflineSyncing] = useState(false);
  const [ipcCommand, setIpcCommand] = useState<string>("cargo tauri dev");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  // Tauri mock metrics
  const [fps, setFps] = useState(60);
  const [ramUsage, setRamUsage] = useState(42); // MB
  const [gpuUsage, setGpuUsage] = useState(18); // %
  const [rustExecutionTime, setRustExecutionTime] = useState<number | null>(null);

  // Drag-and-drop state simulation
  const [isDragging, setIsDragging] = useState(false);

  // Generate dynamic Rust IPC logs
  const generateRustLogs = (fileName: string) => {
    setIsDxfProcessing(true);
    setRustExecutionTime(null);
    setDxfLogs([
      `[Rust] IPC Event 'tauri_open_dxf' triggered with file: ${fileName}`,
      `[Rust] Initializing fast local DXF parser engine...`,
      `[Rust] Accessing native system file buffer at: C:\\Users\\hsnsari\\Documents\\KaRar_CAD\\${fileName}`,
      `[Rust] Mapping ezdxf structures to fast C++ B-Rep memory pointer...`
    ]);

    let progress = 0;
    const interval = setInterval(() => {
      progress += 25;
      if (progress === 25) {
        setDxfLogs(l => [...l, `[Rust] Thread pool spawned. Parsed 142 basic entities (LWPOLYLINE, INSERT, LINE).`]);
      } else if (progress === 50) {
        setDxfLogs(l => [...l, `[Rust] [CRITICAL_PATH] Executing Rust native Snapping Solver (0.012ms).`]);
      } else if (progress === 75) {
        setDxfLogs(l => [...l, `[Rust] Topology loops closed: 4 main rooms identified & tagged.`]);
      } else if (progress === 100) {
        clearInterval(interval);
        const execTime = parseFloat((Math.random() * 8 + 4).toFixed(3));
        setRustExecutionTime(execTime);
        setDxfLogs(l => [
          ...l, 
          `[Rust] Canonical JSON generated in memory! Size: 4.8 KB.`,
          `[JS-Bridge] IPC Callback 'tauri_open_dxf_response' dispatched.`,
          `[SİSTEM] Yerel dosya başarıyla modellendi. İşlem süresi: ${execTime}ms. (0 bulut maliyeti)`
        ]);
        setIsDxfProcessing(false);
      }
    }, 250);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const name = files[0].name;
      setSelectedFile(name);
      generateRustLogs(name);
    }
  };

  const handleSelectSimulatedFile = (name: string) => {
    setSelectedFile(name);
    generateRustLogs(name);
  };

  const triggerOfflineSync = () => {
    setOfflineSyncing(true);
    setTimeout(() => {
      setOfflineSyncing(false);
    }, 1200);
  };

  return (
    <div className="bg-zinc-950 text-zinc-100 p-6 rounded-2xl border border-zinc-800 space-y-6">
      
      {/* PANEL HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-800 pb-4 gap-4">
        <div className="flex items-center space-x-2.5">
          <div className="bg-purple-500/10 p-2 rounded-lg text-purple-400 border border-purple-500/20">
            <Monitor className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-sm font-extrabold uppercase tracking-widest font-mono text-zinc-200">
              FAZ 3 | YEREL MASAÜSTÜ İSTEMCİ & TAURI ENTEGRASYONU
            </h2>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              İnternetten bağımsız, sıfır sunucu maliyetli, yerel disk erişimli ve GPU hızlandırmalı masaüstü istemci simülatörü.
            </p>
          </div>
        </div>

        {/* Dynamic telemetry status */}
        <div className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg text-[10px] font-mono">
          <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></span>
          <span className="text-zinc-400">TAURI ENGINE:</span>
          <span className="text-purple-400 font-bold">RUST-IPC ACTIVE</span>
        </div>
      </div>

      {/* METRIC STRIP TELEMETRY */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-zinc-900/40 border border-zinc-850 p-3 rounded-xl">
          <span className="text-[10px] font-mono text-zinc-500 block">DESKTOP GRAPHICS (FPS)</span>
          <span className="text-xs font-bold text-zinc-200 mt-1 block flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>{fps} FPS (V-Sync)</span>
          </span>
        </div>
        <div className="bg-zinc-900/40 border border-zinc-850 p-3 rounded-xl">
          <span className="text-[10px] font-mono text-zinc-500 block">YEREL RUST RAM KULLANIMI</span>
          <span className="text-xs font-bold text-purple-400 mt-1 block">
            {ramUsage} MB <span className="text-[9px] text-zinc-500 font-normal">(Sıfır Bulut Gideri)</span>
          </span>
        </div>
        <div className="bg-zinc-900/40 border border-zinc-850 p-3 rounded-xl">
          <span className="text-[10px] font-mono text-zinc-500 block">LOCAL GPU DESTEKLİ CANVAS</span>
          <span className="text-xs font-bold text-sky-400 mt-1 block">
            %{gpuUsage} GPU Yükü
          </span>
        </div>
        <div className="bg-zinc-900/40 border border-zinc-850 p-3 rounded-xl">
          <span className="text-[10px] font-mono text-zinc-500 block">NATIVE FILE BINDING (I/O)</span>
          <span className="text-xs font-bold text-emerald-400 mt-1 block flex items-center gap-1">
            <Check className="w-3.5 h-3.5" />
            <span>SQLite + Direct FS</span>
          </span>
        </div>
      </div>

      {/* FAZ 3 NAVIGATION SUB TABS */}
      <div className="flex space-x-1 border-b border-zinc-850 p-1 bg-zinc-900/40 rounded-xl max-w-xl">
        <button
          onClick={() => setActiveSubTab("tauri")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "tauri"
              ? "bg-zinc-800 text-purple-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          🦀 Tauri & Rust IPC
        </button>
        <button
          onClick={() => setActiveSubTab("canvas")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "canvas"
              ? "bg-zinc-800 text-purple-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          🎨 Parametrik 2D Canvas
        </button>
        <button
          onClick={() => setActiveSubTab("offline")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "offline"
              ? "bg-zinc-800 text-purple-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          💾 SQLite & Çevrimdışı Bellek
        </button>
      </div>

      {/* SUB TAB LAYOUT CONTENT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* TAB 1: TAURI & RUST IPC */}
        {activeSubTab === "tauri" && (
          <>
            <div className="lg:col-span-8 space-y-4">
              
              {/* FILE DROP SIMULATION ZONE */}
              <div 
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleFileDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                  isDragging 
                    ? "border-purple-500 bg-purple-950/10" 
                    : "border-zinc-800 hover:border-zinc-700 bg-zinc-900/20"
                }`}
              >
                <div className="max-w-md mx-auto space-y-3">
                  <div className="mx-auto w-12 h-12 bg-purple-500/10 text-purple-400 rounded-full flex items-center justify-center border border-purple-500/20">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-zinc-200">
                      Yerel AutoCAD DXF/DWG Dosyası Sürükleyin
                    </h3>
                    <p className="text-[11px] text-zinc-500 mt-1 font-sans">
                      Dosyalarınız bulut sunucularına <span className="text-purple-400 font-bold">gitmez</span>. 
                      Doğrudan bilgisayarınızın işlemcisi üzerinde native Rust thread'leri tarafından saniyeler içinde çözümlenir.
                    </p>
                  </div>

                  {/* PRESET LOCAL FILES TEST */}
                  <div className="pt-3 border-t border-zinc-900/60">
                    <span className="text-[10px] font-mono text-zinc-500 block uppercase mb-2">Veya Örnek Yerel Dosya Seçin</span>
                    <div className="flex flex-wrap justify-center gap-2">
                      <button
                        onClick={() => handleSelectSimulatedFile("GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf")}
                        className="px-2.5 py-1 bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-800 text-[10px] font-mono text-emerald-300 rounded cursor-pointer font-bold transition-colors"
                      >
                        ✨ GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf
                      </button>
                      <button
                        onClick={() => handleSelectSimulatedFile("test_plan.dxf")}
                        className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] font-mono rounded cursor-pointer transition-colors"
                      >
                        📄 test_plan.dxf
                      </button>
                      <button
                        onClick={() => handleSelectSimulatedFile("twin_villa_ground.dxf")}
                        className="px-2.5 py-1 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[10px] font-mono rounded cursor-pointer transition-colors"
                      >
                        📄 twin_villa_ground.dxf
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* RUSTIPC CONSOLE LOGS */}
              <div className="space-y-2">
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="text-zinc-400 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-purple-400" />
                    <span>Tauri Rust-to-JS IPC Köprü Konsolu</span>
                  </span>
                  {rustExecutionTime !== null && (
                    <span className="text-emerald-400 font-bold">İşlem Süresi: {rustExecutionTime} ms</span>
                  )}
                </div>

                <div className="bg-zinc-950 border border-zinc-850 rounded-xl p-4 h-52 overflow-y-auto font-mono text-[10px] text-purple-400 leading-normal space-y-1 scrollbar-thin">
                  {dxfLogs.length === 0 ? (
                    <div className="text-zinc-600 italic">Yerel bir DXF/DWG dosyasını yükleyin veya seçin. Rust IPC tetikleme sinyalleri burada listelenecektir...</div>
                  ) : (
                    dxfLogs.map((log, idx) => (
                      <div key={idx} className={log.includes("[Rust]") ? "text-purple-400" : log.includes("[JS") ? "text-sky-400" : "text-emerald-400"}>
                        {log}
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>

            <div className="lg:col-span-4 space-y-4">
              
              {/* RUST AR-GE BENEFITS */}
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-4">
                <h3 className="text-xs font-mono font-bold text-zinc-200 flex items-center gap-1.5 uppercase">
                  <ShieldCheck className="w-4 h-4 text-purple-400" />
                  <span>Sıfır Bulut Maliyetli Ölçeklenme</span>
                </h3>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  KaRar'ın Faz 3 mimarisindeki en büyük ticari değeri, AutoCAD işlem yükünün tamamen 
                  <strong> kullanıcının kendi yerel bilgisayarında</strong> (Rust + WebGL) koşturulmasıdır.
                </p>
                <ul className="text-[11px] text-zinc-400 font-sans space-y-2 pt-2 border-t border-zinc-800/60">
                  <li className="flex items-start gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span><strong>0 $ Sunucu Gideri:</strong> Milyonlarca dosya işlense dahi AWS/GCP faturası kabarmaz.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span><strong>100% Gizlilik:</strong> Çizim verileri asla bir sunucuya yüklenmeyerek KVKK/GDPR uyumu sağlar.</span>
                  </li>
                  <li className="flex items-start gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5 text-purple-500 mt-0.5 flex-shrink-0" />
                    <span><strong>Anında Yanıt:</strong> Bulut ağ gecikmesi olmaksızın milisaniyeler düzeyinde analiz.</span>
                  </li>
                </ul>
              </div>

              {/* RUST COMMAND PREVIEW */}
              <div className="bg-zinc-900/30 border border-zinc-850 p-4 rounded-xl font-mono text-[11px] space-y-2">
                <span className="text-zinc-300 font-bold block text-xs">Rust Komut Şablonu (Native API)</span>
                <div className="bg-zinc-950 p-2.5 rounded border border-zinc-900 text-zinc-400 text-[10px] break-all leading-normal">
                  <code className="text-sky-300">#[tauri::command]</code><br />
                  <code>fn parse_dxf_local(path: String) -&gt; Result&lt;BimModel, String&gt; &#123;</code><br />
                  <code>  let dxf = dxf::File::open(&amp;path).map_err(|e| e.to_string())?;</code><br />
                  <code>  let bim = solve_topology(dxf);</code><br />
                  <code>  Ok(bim)</code><br />
                  <code>&#125;</code>
                </div>
              </div>

            </div>
          </>
        )}

        {/* TAB 2: INTERACTIVE 2D CANVAS CONTROLLER SIMULATOR */}
        {activeSubTab === "canvas" && (
          <>
            <div className="lg:col-span-8 space-y-4">
              <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider block">
                GPU Hızlandırmalı 2D Parametrik Vektör Canvas Simülatörü
              </span>

              <div className="relative bg-zinc-950 border border-zinc-850 rounded-xl h-[360px] overflow-hidden flex items-center justify-center">
                
                {/* Simulated grid */}
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#a855f7_1px,transparent_1px)] [background-size:16px_16px]"></div>

                {/* Simulated Canvas Render */}
                <div className="relative w-full h-full p-6 flex flex-col justify-between">
                  
                  {/* Canvas Toolbar Info Overlay */}
                  <div className="flex justify-between items-start z-10">
                    <div className="bg-zinc-900/90 border border-purple-900/40 px-2.5 py-1.5 rounded-lg text-[10px] font-mono space-y-1">
                      <div className="text-zinc-400">Aktif Katman: <strong className="text-purple-400">duvar (exterior_wall)</strong></div>
                      <div className="text-zinc-500">Mause: (x: 412.5, y: 198.0) | Snapping: ON</div>
                    </div>

                    <div className="bg-zinc-900/90 border border-zinc-800 px-2.5 py-1 rounded-md text-[10px] font-mono text-zinc-400">
                      Model: {floor.name}
                    </div>
                  </div>

                  {/* Real-time Dynamic wireframe drawing representation */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="relative w-80 h-48 border border-purple-500/30 rounded bg-purple-500/5 flex items-center justify-center">
                      
                      {/* Bounding box corners */}
                      <span className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-purple-400"></span>
                      <span className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-purple-400"></span>
                      <span className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-purple-400"></span>
                      <span className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-purple-400"></span>

                      {/* Simulated floor-plan outline */}
                      <div className="w-64 h-32 border-4 border-zinc-700 relative">
                        <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-zinc-700"></div>
                        <div className="absolute left-1/4 top-1/2 right-0 h-1 bg-zinc-700"></div>
                        {/* Door opening arc */}
                        <div className="absolute left-[52%] top-[45%] w-12 h-12 border-t border-r border-sky-400/80 rounded-tr-full pointer-events-none"></div>
                        <span className="absolute left-[54%] top-[25%] text-[8px] font-mono text-sky-400 uppercase">KAPI_90cm</span>
                      </div>

                    </div>
                  </div>

                  {/* Bottom details status bar inside canvas */}
                  <div className="flex justify-between items-center z-10">
                    <span className="text-[10px] font-mono text-zinc-500">Hızlandırma Tipi: Native WebGL V-Sync</span>
                    <span className="text-[10px] font-mono text-emerald-400">Gecikme Yok (0.1ms render)</span>
                  </div>

                </div>

              </div>
            </div>

            <div className="lg:col-span-4 space-y-4">
              
              {/* CANVAS CONTROLS */}
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-4">
                <h3 className="text-xs font-mono font-bold text-zinc-200 uppercase tracking-wider">
                  Çizim ve Canvas Parametreleri
                </h3>

                {/* FPS Slider */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[11px] font-mono">
                    <span className="text-zinc-400">Ekran Yenileme Sınırı</span>
                    <span className="text-purple-400 font-bold">{fps} Hz</span>
                  </div>
                  <input 
                    type="range" 
                    min="30" 
                    max="144" 
                    step="15"
                    value={fps}
                    onChange={(e) => setFps(parseInt(e.target.value))}
                    className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  />
                  <span className="text-[9px] text-zinc-500 block">Kullanıcının ekranına göre dinamik V-Sync (30 - 144 Hz).</span>
                </div>

                {/* Toggles */}
                <div className="space-y-3 pt-3 border-t border-zinc-800/60 font-mono text-[11px]">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-300">Izgara Kenetlenmesi (Grid Snap)</span>
                    <span className="text-purple-400 font-bold">AKTİF</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-300">Köşegen Snap (Intersection)</span>
                    <span className="text-emerald-400 font-bold">AÇIK (5cm)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-300">B-Rep Kalınlık Çizgileri</span>
                    <span className="text-zinc-500">GİZLİ</span>
                  </div>
                </div>
              </div>

              {/* COMPILING BENCHMARKS */}
              <div className="bg-purple-950/10 border border-purple-900/20 p-4 rounded-xl">
                <h4 className="text-[10px] font-mono text-purple-400 uppercase tracking-wider mb-1 font-bold">WebGL vs Server-Side Render</h4>
                <p className="text-[11px] text-zinc-400 font-sans leading-relaxed">
                  Faz 3 arayüzü sayesinde tarayıcıda ağır SVG yükleri yerine, doğrudan HTML5 Canvas WebGL API kullanılır. Bu sayede 10.000'den fazla duvar çizgisi içeren devasa projeler bile donmadan saniyede 60 kare hızla manipüle edilebilir.
                </p>
              </div>

            </div>
          </>
        )}

        {/* TAB 3: OFFLINE MODE & SQLITE DB */}
        {activeSubTab === "offline" && (
          <>
            <div className="lg:col-span-8 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider">
                  SQLite Yerel Veritabanı ve Proje Önbellek Denetleyicisi
                </span>
                
                <button
                  onClick={triggerOfflineSync}
                  disabled={offlineSyncing}
                  className="flex items-center space-x-1.5 px-3 py-1 bg-purple-950/40 border border-purple-900/50 hover:border-purple-500 rounded text-[11px] font-mono text-purple-300 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${offlineSyncing ? "animate-spin" : ""}`} />
                  <span>{offlineSyncing ? "Veriler Eşitleniyor..." : "SQLITE VERİLERİNİ EŞİTLE"}</span>
                </button>
              </div>

              {/* SQLite table view representation */}
              <div className="bg-zinc-950 border border-zinc-850 rounded-xl overflow-hidden font-mono text-[11px]">
                <div className="bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-300 border-b border-zinc-800 flex justify-between">
                  <span>SQLite &quot;karar_projects_cache&quot; Tablosu</span>
                  <span className="text-[10px] text-purple-400">Offline-Storage Modu</span>
                </div>
                
                <div className="divide-y divide-zinc-900 overflow-auto max-h-72">
                  <div className="grid grid-cols-12 gap-2 p-3 bg-zinc-900/40 text-zinc-500 text-[10px] uppercase font-bold">
                    <span className="col-span-1">ID</span>
                    <span className="col-span-3">Proje İsmi</span>
                    <span className="col-span-2">Kat Sayısı</span>
                    <span className="col-span-3">Son Düzenleme</span>
                    <span className="col-span-3">Yerel Senkron</span>
                  </div>

                  <div className="grid grid-cols-12 gap-2 p-3 hover:bg-zinc-900/20 text-zinc-300">
                    <span className="col-span-1 text-purple-400 font-bold">#1</span>
                    <span className="col-span-3 font-sans font-bold">Twin Villa Projesi</span>
                    <span className="col-span-2">2 Katlı</span>
                    <span className="col-span-3">2026-07-20 07:55</span>
                    <span className="col-span-3 text-emerald-400 font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span>SQLite Eşitlendi</span>
                    </span>
                  </div>

                  <div className="grid grid-cols-12 gap-2 p-3 hover:bg-zinc-900/20 text-zinc-300">
                    <span className="col-span-1 text-purple-400 font-bold">#2</span>
                    <span className="col-span-3 font-sans font-bold">Apartman Rezidansı</span>
                    <span className="col-span-2">10 Katlı</span>
                    <span className="col-span-3">2026-07-19 14:22</span>
                    <span className="col-span-3 text-emerald-400 font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      <span>SQLite Eşitlendi</span>
                    </span>
                  </div>

                  <div className="grid grid-cols-12 gap-2 p-3 hover:bg-zinc-900/20 text-zinc-300">
                    <span className="col-span-1 text-purple-400 font-bold">#3</span>
                    <span className="col-span-3 font-sans font-bold">Ticari Ofis Bloğu</span>
                    <span className="col-span-2">1 Katlı</span>
                    <span className="col-span-3">2026-07-18 10:05</span>
                    <span className="col-span-3 text-amber-400 font-bold flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-ping"></span>
                      <span>Önbellekte (Bekliyor)</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 space-y-4">
              
              {/* SQLite stats details card */}
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-4 font-mono text-[11px]">
                <h3 className="text-xs font-bold text-zinc-200 flex items-center gap-1.5 uppercase">
                  <Database className="w-4 h-4 text-purple-400" />
                  <span>SQLite Cache Metrikleri</span>
                </h3>

                <div className="space-y-2 pt-2 border-t border-zinc-800/60 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">DB Sürücüsü</span>
                    <span className="text-purple-300">rusqlite (Rust Wrapper)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Önbellek Boyutu</span>
                    <span className="text-zinc-300">12.4 MB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Yerel Tablo Sayısı</span>
                    <span className="text-zinc-300">4 adet ana tablo</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Senkronizasyon Sıklığı</span>
                    <span className="text-sky-400">Anlık (Her kayıtta tetiklenir)</span>
                  </div>
                </div>
              </div>

              {/* OFFLINE CAPABILITY TEXT */}
              <div className="bg-purple-950/10 border border-purple-900/20 p-4 rounded-xl text-zinc-400 text-[11px] leading-relaxed">
                <span className="text-purple-300 font-bold block mb-1">Tauri Offline-First Standartları</span>
                İnternet bağlantısı koptuğunda dahi uygulama hiç duraksamaz. Proje verileriniz ve yapılan tüm parametrik manuel müdahaleler anlık olarak SQLite veri havuzuna depolanır. Bağlantı tekrar kurulduğunda, bulut havuzuyla (Faz 4) otomatik olarak çift yönlü senkronizasyon tamamlanır.
              </div>

            </div>
          </>
        )}

      </div>

    </div>
  );
}
