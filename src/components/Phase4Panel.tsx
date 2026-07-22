import React, { useState } from "react";
import { Floor } from "../types";
import { 
  Cloud, 
  Users, 
  History, 
  Coins, 
  Server, 
  Check, 
  ArrowRight, 
  RefreshCw, 
  Database, 
  GitCommit, 
  Share2, 
  ChevronRight,
  TrendingDown,
  Activity,
  Info
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface Phase4PanelProps {
  floor: Floor;
}

export default function Phase4Panel({ floor }: Phase4PanelProps) {
  const [activeSubTab, setActiveSubTab] = useState<"sync" | "team" | "costs">("costs");
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncLogs, setSyncLogs] = useState<string[]>([]);
  const [teamMembers, setTeamMembers] = useState([
    { name: "Hasan Hüseyin Sarıoğlu", role: "Baş Mimar (Siz)", active: true, action: "Zemin Kat Duvarlarını Düzenliyor" },
    { name: "Selin Yılmaz", role: "BIM Koordinatörü", active: true, action: "Statik Kolon Doğrulamasını İnceliyor" },
    { name: "Ahmet Demir", role: "3D Modelleme Uzmanı", active: false, action: "En son 3 saat önce aktifti" }
  ]);

  // Dynamic cost parameters
  const [activeArchitects, setActiveArchitects] = useState(10);
  const [processedDxfPerMonth, setProcessedDxfPerMonth] = useState(250);

  // Sync simulation triggers
  const triggerCloudSync = () => {
    setIsSyncing(true);
    setSyncLogs([
      "[Yerel SQLite] Yerel veritabanında son 3 sürüm değişikliği tespit edildi.",
      "[Maliyet Tasarrufu] Ağ optimizasyonu aktif: 3D mesh gönderilmeyecek, sadece 4.2 KB'lık akıllı JSON delta diff paketlendi.",
      "[Bulut Ağ Geçidi] Güvenli tünel üzerinden el sıkışma gerçekleştiriliyor...",
      "[Firebase Auth] hsnsari55@gmail.com kullanıcısı için OAuth token'ı doğrulandı.",
      "[Firestore] 'twin_villa_ground' belgesinde 2 adet duvar koordinatı güncellendi.",
      "[Tarihçe] Yeni sürüm etiketi oluşturuldu: v1.0.4 - Saniye bazlı versiyon kilidi başarılı."
    ]);

    setTimeout(() => {
      setIsSyncing(false);
      setSyncLogs(l => [...l, "[SİSTEM] Bulut eşitlemesi başarıyla tamamlandı. Tüm ekip üyelerine bildirim gönderildi!"]);
    }, 1500);
  };

  // Math for Hybrid vs Standard Cloud cost models
  const totalVertices = 1840;
  const rawDataPerProjectMB = 15; // Raw 3D files inside typical platforms
  const canonicalJSONSizeKB = 4.8; // KaRar's clean metadata format

  // Under Standard system (Cloud does the 3D extrusion, runs CAD parser server side):
  const standardCloudComputePerHour = 0.08; // AWS ec2 instance or heavy serverless container running python + ezdxf + shapely
  const standardNetworkCostPerGB = 0.12;
  const standardMonthlyBill = (
    (processedDxfPerMonth * 4 * standardCloudComputePerHour) + // ~4 hours of compute per month
    ((processedDxfPerMonth * rawDataPerProjectMB / 1024) * standardNetworkCostPerGB) * activeArchitects
  );

  // Under KaRar's Hybrid system (Local Tauri app does parsing + geometry + 3D rendering. Cloud only hosts thin JSON metadata metadata sync):
  const kararCloudComputeMonthly = 0; // Completely free-tier serverless Firestore / FastAPI scaling down to 0 when not requested
  const kararNetworkCostMonthly = (processedDxfPerMonth * (canonicalJSONSizeKB / 1024 / 1024) * standardNetworkCostPerGB) * activeArchitects;
  
  // Realistically, database read/writes in Firebase/Firestore are free up to 50k writes/day, so the cost is effectively $0.00
  const finalKaRarCost = Math.max(0.00, parseFloat((kararNetworkCostMonthly + 0.15).toFixed(2)));
  const percentageSavings = Math.round(((standardMonthlyBill - finalKaRarCost) / standardMonthlyBill) * 100);

  return (
    <div className="bg-zinc-950 text-zinc-100 p-6 rounded-2xl border border-zinc-800 space-y-6">
      
      {/* PANEL HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-800 pb-4 gap-4">
        <div className="flex items-center space-x-2.5">
          <div className="bg-emerald-500/10 p-2 rounded-lg text-emerald-400 border border-emerald-500/20">
            <Cloud className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-sm font-extrabold uppercase tracking-widest font-mono text-zinc-200">
              FAZ 4 | BULUT & İŞ BİRLİĞİ SİSTEMLERİ
            </h2>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Takım arkadaşlarınızla eş zamanlı (Real-time) çalışın, projelerinizin sınırsız sürüm geçmişini tutun ve maliyetleri sıfıra indirin.
            </p>
          </div>
        </div>

        {/* Dynamic Cloud connection status */}
        <div className="flex items-center space-x-2 bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg text-[10px] font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-zinc-400">BULUT DURUMU:</span>
          <span className="text-emerald-400 font-bold">HYBRID ONLINE</span>
        </div>
      </div>

      {/* THREE VALUE CARDS FOR HYBRID VALUE */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
        <div className="bg-zinc-900/40 border border-zinc-850 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-[10px] text-zinc-500 uppercase">
            <span>Maksimum Eş Zamanlılık</span>
            <Users className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <span className="text-lg font-bold text-zinc-100 block">Canlı İş Birliği</span>
          <p className="text-[10px] text-zinc-400 font-sans leading-tight">Aynı projede, aynı anda çalışan tüm mimarların ekranına anında senkronizasyon.</p>
        </div>

        <div className="bg-zinc-900/40 border border-zinc-850 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-[10px] text-zinc-500 uppercase">
            <span>Sınırsız Sürüm Tarihçesi</span>
            <History className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <span className="text-lg font-bold text-zinc-100 block">Sonsuz Geri Alma</span>
          <p className="text-[10px] text-zinc-400 font-sans leading-tight">Yaptığınız her duvar snap, kolon yerleştirme değişikliği git benzeri commit geçmişinde saklanır.</p>
        </div>

        <div className="bg-emerald-950/10 border border-emerald-900/20 p-4 rounded-xl space-y-1">
          <div className="flex items-center justify-between text-[10px] text-emerald-500 uppercase">
            <span>Maliyet Sınırlandırma</span>
            <Coins className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <span className="text-lg font-bold text-emerald-400 block">%98 Tasarruflu Mimari</span>
          <p className="text-[10px] text-zinc-400 font-sans leading-tight">Ağır CAD hesaplamaları sunucuda DEĞİL, yerelde çalıştığı için aylık devasa bulut faturaları oluşmaz.</p>
        </div>
      </div>

      {/* FAZ 4 NAVIGATION SUB TABS */}
      <div className="flex space-x-1 border-b border-zinc-850 p-1 bg-zinc-900/40 rounded-xl max-w-xl">
        <button
          onClick={() => setActiveSubTab("costs")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "costs"
              ? "bg-zinc-800 text-emerald-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          💰 Bulut Maliyet Hesaplayıcı
        </button>
        <button
          onClick={() => setActiveSubTab("sync")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "sync"
              ? "bg-zinc-800 text-emerald-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          🔄 Akıllı Sürüm Geçmişi
        </button>
        <button
          onClick={() => setActiveSubTab("team")}
          className={`flex-1 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            activeSubTab === "team"
              ? "bg-zinc-800 text-emerald-400 border border-zinc-700/60 shadow-lg"
              : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          👥 Eş Zamanlı Çalışma (Team)
        </button>
      </div>

      {/* SUB TAB LAYOUT CONTENT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* TAB 1: BULUT MALİYET HESAPLAYICI (Directly resolves user query) */}
        {activeSubTab === "costs" && (
          <>
            <div className="lg:col-span-8 space-y-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider block">
                  İnteraktif Mimari Bulut Gideri Karşılaştırma Matrisi
                </span>
                <span className="text-[10px] text-zinc-500 font-mono">Birim Fiyat: GCP Serverless / SQLite-Hybrid</span>
              </div>

              {/* SIMULATION SLIDERS */}
              <div className="bg-zinc-900/50 border border-zinc-800 p-5 rounded-xl space-y-4 font-mono">
                <h4 className="text-xs font-bold text-zinc-200 uppercase">Ekip & Proje Yoğunluk Parametreleri</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Active Architects slider */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-zinc-400">Aktif Çalışan Mimar</span>
                      <span className="text-emerald-400 font-bold">{activeArchitects} Kişi</span>
                    </div>
                    <input 
                      type="range" 
                      min="1" 
                      max="100" 
                      value={activeArchitects}
                      onChange={(e) => setActiveArchitects(parseInt(e.target.value))}
                      className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                    <span className="text-[9px] text-zinc-500 block">Aynı anda bulut veri havuzuna bağlanan lisans sayısı.</span>
                  </div>

                  {/* Monthly plans processed */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-zinc-400">Aylık Yüklenen Plan Sayısı</span>
                      <span className="text-emerald-400 font-bold">{processedDxfPerMonth} DXF / DWG</span>
                    </div>
                    <input 
                      type="range" 
                      min="20" 
                      max="2000" 
                      step="20"
                      value={processedDxfPerMonth}
                      onChange={(e) => setProcessedDxfPerMonth(parseInt(e.target.value))}
                      className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                    <span className="text-[9px] text-zinc-500 block">Sisteme atılan ve temizlenip BIM'e dönüştürülen toplam kat adedi.</span>
                  </div>
                </div>
              </div>

              {/* COST GRAPH COMPARISON CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Standard system cost card */}
                <div className="bg-zinc-900/30 border border-zinc-850 rounded-xl p-4 space-y-3 font-mono">
                  <span className="text-xs font-bold text-zinc-400 block uppercase">Klasik Bulut Mimari Sistemleri</span>
                  <div className="text-[10px] text-zinc-500 font-sans">
                    Tüm DXF okuma, temizleme, 3B katı model çıkarma ve Three.js dosyalarını bulut sunucularında (AWS/Azure) işleyen sistemler.
                  </div>
                  
                  <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-900 space-y-1.5 text-[11px]">
                    <div className="flex justify-between text-zinc-500">
                      <span>Serverless Compute</span>
                      <span className="text-zinc-300">Yüksek RAM & CPU Gideri</span>
                    </div>
                    <div className="flex justify-between text-zinc-500">
                      <span>Aylık Ortalama Fatura</span>
                      <span className="text-red-400 font-extrabold text-sm">${standardMonthlyBill.toFixed(2)} / ay</span>
                    </div>
                  </div>
                </div>

                {/* KaRar system cost card */}
                <div className="bg-emerald-950/10 border border-emerald-900/30 rounded-xl p-4 space-y-3 font-mono">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400 uppercase">KaRar Hybrid-Local Sistemi</span>
                    <span className="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 text-[8px] rounded font-bold animate-pulse">EN VERİMLİ</span>
                  </div>
                  <div className="text-[10px] text-zinc-400 font-sans">
                    Sıfır işlemci yükü! 3D katı model çıkarma ve CAD temizleme <strong>yerelde (Tauri/Rust)</strong> koşturulur. Bulut sadece minimal JSON sürüm verisini senkronize eder.
                  </div>
                  
                  <div className="bg-zinc-950 p-3 rounded-lg border border-emerald-950/30 space-y-1.5 text-[11px]">
                    <div className="flex justify-between text-zinc-500">
                      <span>Serverless Compute</span>
                      <span className="text-emerald-400 font-bold">Tamamen Ücretsiz Limit</span>
                    </div>
                    <div className="flex justify-between text-zinc-500">
                      <span>Aylık Ortalama Fatura</span>
                      <span className="text-emerald-400 font-extrabold text-sm">${finalKaRarCost.toFixed(2)} / ay</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* DYNAMIC EFFICIENCY SUMMARY */}
              <div className="bg-gradient-to-r from-emerald-950/10 to-zinc-950 border border-emerald-900/20 p-4 rounded-xl flex items-center justify-between font-mono">
                <div className="space-y-1">
                  <span className="text-xs text-zinc-400 uppercase block tracking-wider">KaRar Mimari Tasarruf Oranı</span>
                  <p className="text-2xl font-extrabold text-emerald-400">
                    %{percentageSavings} Bulut Altyapı Tasarrufu
                  </p>
                  <p className="text-[10px] text-zinc-500 font-sans leading-normal">
                    Yerel bilgisayarın (Tauri) işlem gücünü kullandığımız için, AWS/Firebase faturanız her zaman ücretsiz sınırların altında veya ona çok yakın kalır.
                  </p>
                </div>
                <div className="bg-emerald-500/10 p-3.5 rounded-xl border border-emerald-500/20 text-emerald-400 flex flex-col items-center">
                  <TrendingDown className="w-8 h-8" />
                  <span className="text-[9px] font-bold mt-1">DÜŞÜK GİDER</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 space-y-4">
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-3">
                <h3 className="text-xs font-mono font-bold text-zinc-200 flex items-center gap-1.5 uppercase">
                  <Info className="w-4 h-4 text-emerald-400" />
                  <span>Neden Bulut?</span>
                </h3>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  İş yükü yerel bilgisayarda çözülse de, bulut sisteminin varlığı iki ana ticari fayda sağlar:
                </p>
                <div className="space-y-2.5 pt-1 text-[11px] font-sans">
                  <div className="p-2 bg-zinc-950 rounded border border-zinc-900">
                    <strong className="text-emerald-400 block mb-0.5">1. Güvenlik ve Yedeklilik</strong>
                    Bilgisayarınız bozulsa veya çalınsa dahi, yerel SQLite'taki tüm projeler şifrelenmiş olarak bulut kopyasında saklanır.
                  </div>
                  <div className="p-2 bg-zinc-950 rounded border border-zinc-900">
                    <strong className="text-sky-400 block mb-0.5">2. Ekip İçi Ortak Çalışma</strong>
                    Ofisinizdeki diğer mimarlar yaptığınız değişiklikleri anında görebilir ve ortak revizyonlar saniyeler içinde tamamlanır.
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* TAB 2: AKILLI SÜRÜM GEÇMİŞİ */}
        {activeSubTab === "sync" && (
          <>
            <div className="lg:col-span-8 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider block">
                  Git Tarzı Katmanlı BIM Sürüm Ağacı ve Commit Tarihçesi
                </span>

                <button
                  onClick={triggerCloudSync}
                  disabled={isSyncing}
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-850 text-white rounded-lg text-xs font-mono font-bold transition-all shadow-md cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                  <span>{isSyncing ? "Veri Paketleniyor..." : "YENİ SÜRÜM COMMİT ET (BULUT)"}</span>
                </button>
              </div>

              {/* Visual commits list */}
              <div className="space-y-2.5 font-mono text-[11px]">
                
                {/* Commit 3 */}
                <div className="bg-zinc-900/60 border border-zinc-850 p-3 rounded-lg flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-emerald-500/10 p-1.5 rounded text-emerald-400 border border-emerald-500/20">
                      <GitCommit className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <strong className="text-zinc-200">v1.0.3 - Statik Kolon Düzenlemeleri</strong>
                        <span className="px-1.5 py-0.2 bg-emerald-500/10 text-emerald-400 text-[8px] rounded">Aktif Sürüm</span>
                      </div>
                      <span className="text-[10px] text-zinc-500 font-sans block mt-0.5">
                        Yazar: hsnsari55@gmail.com | 20 dakika önce | Değişiklik: 12 kolon eklemesi yapıldı.
                      </span>
                    </div>
                  </div>
                  <span className="text-zinc-400 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-900 font-bold text-[9px]">4.8 KB</span>
                </div>

                {/* Commit 2 */}
                <div className="bg-zinc-900/20 border border-zinc-850 p-3 rounded-lg flex items-center justify-between">
                  <div className="flex items-center space-x-3 opacity-80">
                    <div className="bg-zinc-800 p-1.5 rounded text-zinc-400 border border-zinc-700/60">
                      <GitCommit className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <strong className="text-zinc-300">v1.0.2 - Çevre Dış Duvarları Kapatıldı</strong>
                        <span className="px-1.5 py-0.2 bg-zinc-800 text-zinc-500 text-[8px] rounded">Eski Revizyon</span>
                      </div>
                      <span className="text-[10px] text-zinc-500 font-sans block mt-0.5">
                        Yazar: selinyilmaz@karar.com | Dün 16:45 | Değişiklik: Snapping algoritmaları çözüldü.
                      </span>
                    </div>
                  </div>
                  <span className="text-zinc-500 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-900 text-[9px]">4.1 KB</span>
                </div>

                {/* Commit 1 */}
                <div className="bg-zinc-900/20 border border-zinc-850 p-3 rounded-lg flex items-center justify-between">
                  <div className="flex items-center space-x-3 opacity-60">
                    <div className="bg-zinc-800 p-1.5 rounded text-zinc-400 border border-zinc-700/60">
                      <GitCommit className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <strong className="text-zinc-400">v1.0.1 - İlk AutoCAD Ham DXF Okuması</strong>
                        <span className="px-1.5 py-0.2 bg-zinc-800 text-zinc-500 text-[8px] rounded">İlk Sürüm</span>
                      </div>
                      <span className="text-[10px] text-zinc-500 font-sans block mt-0.5">
                        Yazar: hsnsari55@gmail.com | 3 gün önce | Değişiklik: Ham veriler temizlenerek sisteme ilk giriş yapıldı.
                      </span>
                    </div>
                  </div>
                  <span className="text-zinc-600 bg-zinc-950 px-2 py-0.5 rounded border border-zinc-900 text-[9px]">3.8 KB</span>
                </div>

              </div>

              {/* LIVE COOPERATIVE SYNC LOGS */}
              {syncLogs.length > 0 && (
                <div className="space-y-1.5 pt-2">
                  <span className="text-[10px] font-mono text-emerald-400 block">Sürüm Eşitleme Sinyalleri</span>
                  <div className="bg-zinc-950 border border-emerald-950/40 p-3 rounded-lg font-mono text-[9px] text-emerald-500 space-y-1 max-h-36 overflow-y-auto">
                    {syncLogs.map((log, idx) => (
                      <div key={idx}>{log}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-4 space-y-4">
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-3 font-mono text-[11px]">
                <h3 className="text-xs font-bold text-zinc-200 flex items-center gap-1.5 uppercase">
                  <Database className="w-4 h-4 text-emerald-400" />
                  <span>Versiyon Detayları</span>
                </h3>

                <div className="space-y-2 pt-2 border-t border-zinc-800/60 text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Mevcut Aktif Proje</span>
                    <span className="text-zinc-300">Twin Villa Projesi</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Kayıtlı Sürüm Sayısı</span>
                    <span className="text-emerald-400">3 Sürüm Bulutta</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">Çift Yönlü Çatışma Önleme</span>
                    <span className="text-zinc-300">Aktif (Lock Engine)</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* TAB 3: EŞ ZAMANLI ÇALIŞMA (TEAM) */}
        {activeSubTab === "team" && (
          <>
            <div className="lg:col-span-8 space-y-4">
              <span className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider block">
                Eş Zamanlı Tasarım Odası ve Ekip Koordinasyon Paneli
              </span>

              {/* Active members workspace status */}
              <div className="space-y-3">
                {teamMembers.map((member, idx) => (
                  <div 
                    key={idx} 
                    className={`bg-zinc-900/40 border p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${
                      member.active ? "border-emerald-950/40" : "border-zinc-850 opacity-60"
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      {/* Avatar initial or green indicator */}
                      <div className="relative">
                        <div className="w-9 h-9 bg-zinc-800 border border-zinc-700 text-zinc-200 text-xs font-extrabold flex items-center justify-center rounded-full font-mono">
                          {member.name.split(" ").map(n => n[0]).join("")}
                        </div>
                        {member.active && (
                          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 border-2 border-zinc-950 rounded-full animate-ping"></span>
                        )}
                      </div>
                      
                      <div>
                        <div className="flex items-center space-x-2">
                          <strong className="text-xs text-zinc-200">{member.name}</strong>
                          <span className="px-1.5 py-0.2 bg-zinc-950 text-zinc-500 border border-zinc-900 text-[8px] font-mono rounded">{member.role}</span>
                        </div>
                        <span className="text-[10px] text-zinc-400 block font-mono mt-0.5">{member.action}</span>
                      </div>
                    </div>

                    {/* Active work token */}
                    <span className={`text-[10px] font-mono px-2 py-1 rounded ${
                      member.active ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-950 text-zinc-600"
                    }`}>
                      {member.active ? "🔴 Canlı Odada" : "💤 Çevrimdışı"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-4 space-y-4">
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 space-y-3 font-sans text-xs">
                <h3 className="text-xs font-mono font-bold text-zinc-200 flex items-center gap-1.5 uppercase">
                  <Share2 className="w-4 h-4 text-emerald-400" />
                  <span>Real-Time Eşitleme Teknolojisi</span>
                </h3>
                <p className="text-zinc-400 leading-relaxed text-[11px]">
                  Mimar odasında yapılan tüm çizgisel müdahaleler <strong>WebSockets</strong> köprüsü ile bağlı olan tüm diğer takım üyelerinin ekranına 100ms'nin altında bir gecikmeyle yansıtılır.
                </p>
                <div className="p-2 bg-zinc-950 rounded border border-zinc-900 text-[10px] font-mono text-zinc-500">
                  <span className="text-sky-300 block mb-0.5">Conflict Resolution:</span>
                  Aynı duvara müdahale edilirse, sistem sürüm kilidi uygulayarak çakışmaları otomatik önler.
                </div>
              </div>
            </div>
          </>
        )}

      </div>

    </div>
  );
}
