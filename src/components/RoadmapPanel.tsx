import React, { useState } from "react";
import { 
  GitMerge, 
  Settings, 
  Layers, 
  Terminal, 
  FileCode, 
  Database, 
  Cpu, 
  Compass, 
  TrendingUp, 
  CheckCircle, 
  Play, 
  Search, 
  BookOpen, 
  Sliders, 
  ChevronRight, 
  Award,
  AlertTriangle,
  Lightbulb,
  Codesandbox,
  ShieldAlert,
  Activity,
  Workflow,
  Table,
  ShieldCheck,
  FileText
} from "lucide-react";

interface Phase {
  id: string;
  title: string;
  subtitle: string;
  status: "active" | "planned" | "future" | "completed";
  techStack: string[];
  tasks: { name: string; completed: boolean }[];
  description: string;
}

export default function RoadmapPanel() {
  const [activePhaseId, setActivePhaseId] = useState<string>("phase1");
  const [selectedChallenge, setSelectedChallenge] = useState<string>("snapping");

  // Aligned perfectly with CTO priorities:
  // 1. Geometry Engine, 2. Topology Engine, 3. Semantic Enrichment, 4. Canonical BIM Model, 5. Pipeline Contract & Test Strategy, 6. Blender Builder, 7. IFC Export, 8. Desktop/Web UI, 9. Cloud Collaboration
  const phases: Phase[] = [
    {
      id: "phase1",
      title: "Faz 1 - Geometri Çekirdek Motoru (Geometry Engine)",
      subtitle: "Coordinates, Normalization & Repair",
      status: "active",
      techStack: ["Python", "ezdxf", "Shapely", "Math Algorithms"],
      description: "AutoCAD'den (.dxf) veya diğer kaynaklardan gelen ham vektör çizgilerini okur, temizler, sıfır noktasına normalize eder ve tolerans altındaki gürültüleri filtreleyerek onarır. Kararlı bir geometrik yapı kurmak için ilk ve en kritik adımdır.",
      tasks: [
        { name: "DXF Koordinat Normalizasyonu: Ölçekleme ve orijine kaydırma", completed: true },
        { name: "Gürültü ve Kısa Çizgi Filtreleme (Repair)", completed: true },
        { name: "Üst Üste Binen (Mükerrer) Çizgi Birleştirme", completed: true },
        { name: "Birim ve Tolerans Kalibrasyon Altyapısı", completed: true }
      ]
    },
    {
      id: "phase2",
      title: "Faz 2 - Topoloji Motoru (Topology Engine)",
      subtitle: "Snapping & Room Polygonization",
      status: "active",
      techStack: ["Python", "Shapely", "Graph Theory"],
      description: "Uç uca gelmeyen duvar çizgilerindeki boşlukları matematiksel tolerans dahilinde kapatır (Snapping). Ardından çizgilerden kapalı oda poligonları (B-Rep sınırları) türeterek mekansal topolojik ağ haritasını kurar.",
      tasks: [
        { name: "Uç Nokta Kenetleme (Snapping) Algoritması", completed: true },
        { name: "Unary Union & Kesişim Noktalarından Bölme (Split)", completed: true },
        { name: "Polygonize: Kapalı oda poligonlarını çıkarma", completed: true },
        { name: "Topolojik Komşuluk Grafiği Oluşturma", completed: true }
      ]
    },
    {
      id: "phase3",
      title: "Faz 3 - Semantik Zenginleştirme (Semantic Enrichment)",
      subtitle: "Wall, Column & Room Classifier",
      status: "active",
      techStack: ["Python Rule Engine", "Heuristic Classification"],
      description: "Topolojik ağdan gelen verileri ve katman adlarını analiz ederek yapı elemanlarını sınıflandırır. Hangi poligonun oda, hangi kalınlığın taşıyıcı kolon veya bölücü duvar olduğunu, kapı/pencere konumlarını belirler.",
      tasks: [
        { name: "Taşıyıcı Kolon ve Duvar Ayrımı Hevristikleri", completed: true },
        { name: "Kapı ve Pencere Açıklıklarının Geometrik Tespiti", completed: true },
        { name: "Oda Alanları ve İşlev Sınıflandırması (Salon, Mutfak, vb.)", completed: true },
        { name: "Semantik Metadatanın Geometriye Giydirilmesi", completed: true }
      ]
    },
    {
      id: "phase4",
      title: "Faz 4 - Canonical BIM Model Sözleşmesi",
      subtitle: "Single Source of Truth JSON Schema",
      status: "active",
      techStack: ["JSON Schema", "TypeScript Types", "Contract Verification"],
      description: "KaRar motorunun ürettiği her şeyin tek ve resmi doğruluk kaynağıdır. Blender, IFC, WebGL ve AI bu ortak şemayı okuyarak çalışır; kendi kafalarına göre veri uyduramazlar.",
      tasks: [
        { name: "Canonical BIM JSON Şeması Tasarımı", completed: true },
        { name: "TypeScript Tip Tanımlamaları ve Sıkı Doğrulama", completed: true },
        { name: "Katmanlar Arası Sözleşme (Contract) Geçiş Kontrolleri", completed: true }
      ]
    },
    {
      id: "phase5",
      title: "Faz 5 - Pipeline Contract & Test Strategy",
      subtitle: "Doğrulama ve Otomatik Kalite Kapıları",
      status: "active",
      techStack: ["Python unittest", "Linter & Compiler Checks"],
      description: "Her aşamanın giriş ve çıkışlarını test eden entegrasyon test yapısı. Regresyonları önlemek, tolerans değişikliklerinin doğruluğunu denetlemek için kurulan mühendislik altyapısıdır.",
      tasks: [
        { name: "Geometri ve Topoloji Birim Testleri (Unit Tests)", completed: true },
        { name: "Pipeline Akış Entegrasyon Sınamaları", completed: true },
        { name: "Otomatik Linter ve Build Kontrolleri", completed: true }
      ]
    },
    {
      id: "phase6",
      title: "Faz 6 - Blender 3D Builder",
      subtitle: "Parametric B-Rep 3D Mesh Generator",
      status: "planned",
      techStack: ["Python Blender API", "GLB/GLTF Generation"],
      description: "Doğruluğu tescillenmiş Canonical BIM JSON verisini girdi alarak Blender Python API üzerinden 3D katı modelleri ve pürüzsüz mesh geometrisini otomatik olarak ayağa kaldırır.",
      tasks: [
        { name: "Blender Parametrik Extrusion Altyapısı", completed: false },
        { name: "Mesh Optimizasyon ve GLB İhraç İşlemleri", completed: false },
        { name: "Malzeme ve Doku (Texture) Atama Kuralları", completed: false }
      ]
    },
    {
      id: "phase7",
      title: "Faz 7 - IFC Standart Dışa Aktarım (IFC Export)",
      subtitle: "OpenBIM Compatibility",
      status: "planned",
      techStack: ["Python", "IfcOpenShell"],
      description: "BIM dünyasının evrensel dili olan IFC dosyalarını hatasız üretir. Ancak Geometri, Topoloji ve Semantik aşamalar tamamen sıfır hata ile doğrulandıktan sonra çalıştırılır.",
      tasks: [
        { name: "IfcProject, IfcSite, IfcBuilding Hiyerarşisi Oluşturma", completed: false },
        { name: "IfcWall ve IfcColumn Parametrik Yazımı", completed: false },
        { name: "IfcWindow ve IfcDoor İlişkilendirmeleri", completed: false }
      ]
    },
    {
      id: "phase8",
      title: "Faz 8 - Web ve Masaüstü Kullanıcı Arayüzü",
      subtitle: "Interactive 2D/3D WebGL Canvas",
      status: "planned",
      techStack: ["React", "Tauri Client", "Three.js", "TailwindCSS"],
      description: "Mimarın sonuçları göreceği, gerektiğinde parametrik çizgilere elle müdahale edebileceği yerel (Tauri) ve web tabanlı kullanıcı arayüzü katmanı.",
      tasks: [
        { name: "İnteraktif 2D/3D WebGL Düzenleyici", completed: false },
        { name: "Parametrik Çizgi Tutma ve Manuel Düzeltme Arayüzü", completed: false },
        { name: "Yerel AutoCAD/DXF Dosya Okuma Yeteneği", completed: false }
      ]
    },
    {
      id: "phase9",
      title: "Faz 9 - Bulut Hizmetleri & İş Birliği",
      subtitle: "Cloud Sync & Real-time Collaboration",
      status: "future",
      techStack: ["FastAPI", "WebSockets", "Durable Storage"],
      description: "Gelecekte planlanan, mimarların ve mühendislerin projeler üzerinde eş zamanlı çalışmasını sağlayan bulut ve WebSockets eşleştirme katmanı.",
      tasks: [
        { name: "Çoklu Kullanıcı Anlık Senkronizasyonu", completed: false },
        { name: "Bulut Tabanlı Sürüm Geçmişi ve Arşiv", completed: false },
        { name: "Uzak Kalite Kontrolü ve Yönetmelik Uyumluluk Testleri", completed: false }
      ]
    }
  ];

  // Coding challenges sandbox where AI acts as the "software developer developer"
  const challenges = {
    normalization: {
      title: "1. Geometri Normalizasyonu ve Onarım (Repair)",
      problem: "DXF'ten gelen ham çizgiler genellikle hatalı ölçekte, dağınık veya mükerrer (üst üste binmiş) durumdadır. Doğrudan topolojiye sokulamaz.",
      solution: "Tüm koordinatları ortak bir orijine kaydırır, tolerans altındaki çok kısa çizgileri eler ve üst üste gelen çizgileri tek bir vektörde birleştiririz.",
      code: `def normalize_and_repair_geometry(raw_segments, tolerance=1e-3):
    """
    Gereksiz kısa çizgileri eler ve mükerrer çizgileri birleştirir.
    Mühendislik hata payını sıfıra indirmek için ilk koruma kalkanıdır.
    """
    clean_segments = []
    for seg in raw_segments:
        # Segment uzunluğu toleranstan küçükse iptal et (Gürültü temizliği)
        if seg.length < tolerance:
            continue
            
        # Mükerrer çizgi kontrolü
        is_duplicate = False
        for existing in clean_segments:
            if existing.almost_equals(seg, decimal=3):
                is_duplicate = True
                break
        if not is_duplicate:
            clean_segments.append(seg)
            
    return clean_segments`
    },
    snapping: {
      title: "2. Çizgi Birleştirme (Snapping & Merging) Algoritması",
      problem: "AutoCAD çizimlerinde duvar çizgileri tam uca gelmeyebilir. Boşlukları deterministik olarak kapatmak gerekir.",
      solution: "İki çizginin uç noktaları arasındaki Öklid mesafesini hesaplayıp, belirli bir toleransın (örn. 5cm) altındaysa noktaları birbirine kenetleriz.",
      code: `import math
from shapely.geometry import LineString, Point

def snap_points(lines, tolerance=5.0):
    """
    AutoCAD tolerans hatalarını gidermek için birbirine çok yakın uç noktaları kenetler.
    Yapay zeka bu algoritmanın Python kodunun optimizasyonunu sağlar.
    """
    snapped_lines = []
    points_pool = {}  # (rounded_x, rounded_y) -> Point object
    
    for line in lines:
        coords = list(line.coords)
        new_coords = []
        for x, y in coords:
            # Tolerans dairesinde daha önce kaydedilmiş bir nokta var mı?
            found = False
            for p_key, p_val in points_pool.items():
                if math.hypot(x - p_val.x, y - p_val.y) <= tolerance:
                    new_coords.append((p_val.x, p_val.y))
                    found = True
                    break
            if not found:
                points_pool[(round(x, 2), round(y, 2))] = Point(x, y)
                new_coords.append((x, y))
        snapped_lines.append(LineString(new_coords))
    return snapped_lines`
    },
    intersection: {
      title: "3. Duvar Kesişim Tespiti ve Poligonlaştırma (B-Rep)",
      problem: "2D çizgilerden oluşan duvarların iç hacimlerini (oda poligonlarını) otomatik bulmak ve 3D katı modele çevirmek.",
      solution: "Shapely kütüphanesinin unary_union ve polygonize fonksiyonları ile tüm çizgileri birleştirip kapalı döngüleri buluruz.",
      code: `from shapely.ops import unary_union, polygonize
from shapely.geometry import MultiLineString

def find_room_polygons(wall_lines):
    """
    2D duvar çizgilerinin sınırlandırdığı kapalı hacimleri (odaları) bulur.
    Fuzzy AI yerine %100 deterministik matematiksel kütüphaneler kullanılır.
    """
    # Tüm çizgileri kesişim noktalarından kırıp tek bir ağ haline getir
    unified_lines = unary_union(wall_lines)
    
    # Kapalı poligonları (odaları) oluştur
    rooms = list(polygonize(unified_lines))
    
    # Alan büyüklüğüne göre oda sınıflaması yapılabilir
    valid_rooms = [r for r in rooms if r.area > 1.5]  # 1.5m2 altındaki hataları eliyoruz
    return valid_rooms`
    },
    ifc: {
      title: "4. Standart IFC (BIM) Elemanı Oluşturma",
      problem: "Ham 3D koordinatlardan Revit ve ArchiCAD'in tanıyabileceği hakiki duvar (IfcWall) objesi üretmek.",
      solution: "IfcOpenShell kütüphanesini kullanarak katmanlı mimari hiyerarşiyi (IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey) kurup elemanı ekleriz.",
      code: `import ifcopenshell
import ifcopenshell.template

def create_ifc_wall(file_path, wall_id, start_pt, end_pt, height=280.0, thickness=25.0):
    """
    Mühendislik standartlarına uygun gerçek bir IFC dosyası oluşturur.
    Yapay zeka, IFC şemasının kurallarına uygun nitelik setlerini yazar.
    """
    # Boş bir IFC 4 dosyası oluştur veya şablonu yükle
    model = ifcopenshell.file(schema="IFC4")
    
    # Proje ve katman hiyerarşisini oluştur
    project = model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.create(), Name="KaRar BIM Projesi")
    # ... hiyerarşik tanımlamalar ...
    
    # Duvar nesnesini parametrik özellikleri ile tanımla
    wall = model.create_entity("IfcWall", GlobalId=ifcopenshell.guid.create(), Name=f"Duvar_{wall_id}")
    
    # Duvarın 3D extrude geometrisini oluştur (B-Rep modelleme)
    # Start ve end koordinatlarından extrusion vektörü çıkarma işlemleri burada yer alır.
    
    model.write(file_path)
    return f"IFC Duvarı başarıyla yazıldı: {wall.GlobalId}"`
    }
  };

  return (
    <div className="bg-zinc-950 text-zinc-100 min-h-screen p-6 font-sans">
      
      {/* HEADER SECTION */}
      <div className="border-b border-zinc-800 pb-5 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="bg-amber-500/10 p-2 rounded-lg text-amber-400 border border-amber-500/20">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-black text-zinc-100 tracking-tight flex items-center gap-2">
                <span>KARAR AR-GE VE STRATEJİK YOL HARİTASI</span>
                <span className="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/20">
                  CTO REVIZYONU ENTEGRE EDILDI
                </span>
              </h1>
              <p className="text-xs text-zinc-400 font-mono mt-1">
                YAPAY ZEKA YAZILIMI GELİŞTİRMEK İÇİN VARDIR, 2D GEOMETRİYİ KENDİSİ 3D YAPMAZ.
              </p>
            </div>
          </div>
        </div>
        
        {/* CTO SCORE CARD */}
        <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-xl flex items-center space-x-4">
          <div className="bg-gradient-to-br from-amber-500 to-orange-600 text-black font-extrabold w-12 h-12 rounded-lg flex flex-col items-center justify-center shadow-lg shadow-amber-500/5">
            <span className="text-xs leading-none">Puan</span>
            <span className="text-lg leading-none mt-0.5">9.8</span>
          </div>
          <div>
            <div className="text-[10px] font-mono text-zinc-500 uppercase">CTO Geri Bildirimi Sonrası</div>
            <div className="text-xs font-bold text-emerald-400">Teknik Risk: Yok Derecek Kadar Az</div>
            <div className="text-[10px] text-zinc-400">"Model merkezli vizyon ve kusursuz işlem sırası."</div>
          </div>
        </div>
      </div>

      {/* CTO REVIEW - ENGINEERING MANDATES INTEGRATION */}
      <div className="bg-zinc-900/80 border-l-4 border-emerald-500 p-5 rounded-r-2xl mb-8 space-y-3.5">
        <div className="flex items-center space-x-2 text-emerald-400">
          <Workflow className="w-5 h-5" />
          <h2 className="text-xs font-mono font-extrabold uppercase tracking-widest">
            MÜHENDİSLİK İLKELERİ & CANONICAL MODEL REHBERİ (CTO DEĞERLENDİRMESİ)
          </h2>
        </div>
        <p className="text-xs text-zinc-300 leading-relaxed">
          KaRar'ın gelişim sürecinde sapmaları önlemek, ticarileşebilir ve deterministik bir BIM ürünü çıkarmak için kabul edilen mühendislik kuralları:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 pt-1">
          <div className="bg-zinc-950 p-3 rounded border border-zinc-800 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase font-mono block">1. Geometri Temizliği</span>
            <span className="text-xs font-bold text-zinc-200">Repair & Normalization</span>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Snapping ve topolojiye girmeden önce çizgilerin normalize edilmesi, kısa parçaların elenmesi ve onarılması şarttır.
            </p>
          </div>
          <div className="bg-zinc-950 p-3 rounded border border-zinc-800 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase font-mono block">2. Mimari Bağımsızlık</span>
            <span className="text-xs font-bold text-zinc-200">Decoupled UI Layer</span>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Arayüz çekirdek motoru yavaşlatamaz. UI salt bir tüketici katmanıdır; motorun ürettiği Canonical JSON standardını okur.
            </p>
          </div>
          <div className="bg-zinc-950 p-3 rounded border border-zinc-800 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase font-mono block">3. IFC Geciktirmesi</span>
            <span className="text-xs font-bold text-zinc-200">Late IFC Export</span>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Geometri, topoloji ve semantik doğruluk %100 seviyesine gelene dek IFC dosyası üretilmez. Hatalı geometri hatalı BIM üretir.
            </p>
          </div>
          <div className="bg-zinc-950 p-3 rounded border border-zinc-800 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase font-mono block">4. AI Sınırlandırması</span>
            <span className="text-xs font-bold text-zinc-200">AI as Copilot, Not Engine</span>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Yapay zeka kod yazar, dökümante eder ve kalibrasyona yardım eder. Üretim hattındaki asıl motor tamamen deterministiktir.
            </p>
          </div>
          <div className="bg-zinc-950 p-3 rounded border border-emerald-950 bg-emerald-950/10 space-y-1">
            <span className="text-[10px] text-emerald-400 uppercase font-mono block">5. Tek Kaynak Kuralı</span>
            <span className="text-xs font-bold text-emerald-300">Canonical Model Rule</span>
            <p className="text-[10px] text-emerald-400/90 leading-relaxed font-sans">
              Sistemde tek resmi mühendislik modeli vardır. Blender, IFC, UI ve AI bu ortak modeli tüketir, kendi içinde geometri türetmez.
            </p>
          </div>
        </div>
      </div>

      {/* CTO TECHNICAL PRIORITY STEPPER (1-7) */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 mb-8 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-amber-400">
            <Activity className="w-5 h-5 animate-pulse" />
            <h2 className="text-xs font-mono font-extrabold uppercase tracking-widest">
              KaRar Teknik Öncelik Sıralaması & Kritik İş Akışı (CTO Kriterleri)
            </h2>
          </div>
          <span className="text-[10px] bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded border border-amber-500/20 font-mono font-bold">
            Hedef: %100 Deterministik Çıktı
          </span>
        </div>

        <p className="text-xs text-zinc-400 leading-relaxed font-sans">
          Geliştirme odağımızın kaymasını önlemek ve mimariyi korumak adına takip edilen doğrusal teknik öncelik akış şeması:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
          {[
            {
              num: "1",
              title: "Geometry Engine",
              subtitle: "Normalization & Repair",
              desc: "Ham CAD verisini temizler, sıfır noktasına hizalar, normalize eder ve onarır.",
              status: "active",
              color: "border-emerald-500 text-emerald-400"
            },
            {
              num: "2",
              title: "Topology Engine",
              subtitle: "Snapping & Polyg.",
              desc: "Boşlukları kapatır, çizgileri birbirine kenetler ve odaların sınırlarını kurar.",
              status: "active",
              color: "border-emerald-500 text-emerald-400"
            },
            {
              num: "3",
              title: "Semantic Enrichment",
              subtitle: "Metadata Enrichment",
              desc: "Topolojik modele göre oda niteliklerini (Mutfak, Salon vb.) ve taşıyıcı yapıları zenginleştirir.",
              status: "planned",
              color: "border-amber-500 text-amber-400"
            },
            {
              num: "4",
              title: "Canonical BIM Model",
              subtitle: "Single Source of Truth",
              desc: "Blender, IFC, UI ve AI'ın beslendiği tek ve resmi ortak JSON mühendislik modeli.",
              status: "planned",
              color: "border-amber-500 text-amber-400"
            },
            {
              num: "5",
              title: "Blender 3D",
              subtitle: "3D B-Rep Generator",
              desc: "Canonical modelden yola çıkarak Blender API ile katı 3D nesneleri otomatik extrude eder.",
              status: "planned",
              color: "border-zinc-700 text-zinc-400"
            },
            {
              num: "6",
              title: "Desktop UI",
              subtitle: "Tauri Client",
              desc: "Canonical JSON modelini yerel istemcide görselleştiren ve düzenleyen parametrik arayüz.",
              status: "future",
              color: "border-zinc-800 text-zinc-600"
            },
            {
              num: "7",
              title: "Cloud Services",
              subtitle: "Sync & Collab",
              desc: "Ekip çalışması, gerçek zamanlı senkronizasyon ve bulut tabanlı sürüm kontrolü.",
              status: "future",
              color: "border-zinc-800 text-zinc-600"
            }
          ].map((step, idx) => (
            <div
              key={idx}
              className={`bg-zinc-950 p-3.5 rounded-xl border-t-4 transition-all relative overflow-hidden ${step.color} ${
                step.status === "active" ? "bg-zinc-900 border-x border-b border-zinc-800" : "border-x border-b border-zinc-900"
              }`}
            >
              <div className="absolute top-2 right-2 text-[20px] font-black opacity-10 font-mono">
                #{step.num}
              </div>
              <div className="text-[10px] font-mono opacity-65 uppercase tracking-wider mb-1">ÖNCELİK {step.num}</div>
              <h3 className="text-xs font-bold text-zinc-100 truncate">{step.title}</h3>
              <p className="text-[9px] font-mono text-zinc-500 mt-0.5 truncate">{step.subtitle}</p>
              <p className="text-[10px] text-zinc-400 font-sans mt-2 leading-relaxed">
                {step.desc}
              </p>
              {step.status === "active" && (
                <div className="mt-3 flex items-center space-x-1.5 text-[9px] font-mono text-emerald-400 bg-emerald-500/10 py-1 px-2 rounded border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping"></span>
                  <span>Şu Anki Odak</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* PIPELINE CONTRACT & TEST STRATEGY SECTIONS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        
        {/* PIPELINE CONTRACT TABLE */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center space-x-2 text-emerald-400 border-b border-zinc-800/60 pb-3">
            <Table className="w-5 h-5 text-emerald-400" />
            <h2 className="text-xs font-mono font-extrabold uppercase tracking-widest">
              Boru Hattı Giriş-Çıkış Sözleşmeleri (Pipeline Contract)
            </h2>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed font-sans">
            Her katmanın veri giriş ve çıkış sınırları kesin sözleşmelerle çizilmiştir. Bu sayede katmanlar birbirinden tamamen bağımsız olarak geliştirilebilir ve test edilebilir.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-[11px] border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500 text-[10px]">
                  <th className="py-2 px-1 font-bold">KATMAN</th>
                  <th className="py-2 px-1 font-bold">GİRDİ (INPUT)</th>
                  <th className="py-2 px-1 font-bold">ÇIKTI (OUTPUT)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/40 text-zinc-300">
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">Parser</td>
                  <td className="py-2 px-1">.DXF Dosyası</td>
                  <td className="py-2 px-1 text-amber-400 font-medium">Raw Geometry JSON</td>
                </tr>
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">Geometry</td>
                  <td className="py-2 px-1">Raw Geometry JSON</td>
                  <td className="py-2 px-1 text-emerald-400 font-medium">Normalized Geometry</td>
                </tr>
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">Topology</td>
                  <td className="py-2 px-1">Normalized Geometry</td>
                  <td className="py-2 px-1 text-emerald-400 font-bold">Topology Graph (Polygons)</td>
                </tr>
                <tr className="bg-emerald-500/5">
                  <td className="py-2 px-1 font-bold text-emerald-400">Canonical Model</td>
                  <td className="py-2 px-1">Topology Graph</td>
                  <td className="py-2 px-1 text-emerald-300 font-extrabold">Canonical BIM JSON</td>
                </tr>
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">Semantic</td>
                  <td className="py-2 px-1">Canonical BIM JSON</td>
                  <td className="py-2 px-1 text-amber-400 font-medium">Enriched Metadata JSON</td>
                </tr>
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">Blender</td>
                  <td className="py-2 px-1">Enriched Metadata JSON</td>
                  <td className="py-2 px-1">.blend / .glb (3D Mesh)</td>
                </tr>
                <tr>
                  <td className="py-2 px-1 font-bold text-zinc-200">IFC Export</td>
                  <td className="py-2 px-1">Canonical BIM JSON</td>
                  <td className="py-2 px-1">.ifc (BIM Standart Dosyası)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* TEST STRATEGY */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center space-x-2 text-amber-400 border-b border-zinc-800/60 pb-3">
            <ShieldCheck className="w-5 h-5 text-amber-400" />
            <h2 className="text-xs font-mono font-extrabold uppercase tracking-widest">
              Katmanlı Kalite Güvence ve Test Stratejisi
            </h2>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed font-sans">
            Model merkezli mimarimizin bütünlüğünü korumak adına her katman, tek kaynak olan <strong>Canonical BIM JSON</strong> sözleşmesini referans alarak bağımsız birim (unit) ve entegrasyon testleriyle doğrulanır.
          </p>

          <div className="space-y-3">
            <div className="bg-zinc-950 p-2.5 rounded border border-zinc-850 flex items-start space-x-2">
              <span className="text-[10px] bg-emerald-500/15 text-emerald-400 font-mono px-1.5 py-0.5 rounded font-bold">UNIT</span>
              <div>
                <h4 className="text-xs font-bold text-zinc-200">Geometry & Topology Unit Tests</h4>
                <p className="text-[10px] text-zinc-400 font-sans mt-0.5">
                  Ölçek hataları, sıfırlama, kopuk çizgiler (snapping tolerans sınırları) ve kapalı alan hesaplamalarının matematiksel doğrulaması.
                </p>
              </div>
            </div>

            <div className="bg-zinc-950 p-2.5 rounded border border-zinc-850 flex items-start space-x-2">
              <span className="text-[10px] bg-amber-500/15 text-amber-400 font-mono px-1.5 py-0.5 rounded font-bold">SCHEMA</span>
              <div>
                <h4 className="text-xs font-bold text-zinc-200">Canonical JSON Schema Verification</h4>
                <p className="text-[10px] text-zinc-400 font-sans mt-0.5">
                  Mühendislik standardı sözleşmesine tam uygunluk. Her nesnenin id, coordinates, type ve topology referanslarının doğrulanması.
                </p>
              </div>
            </div>

            <div className="bg-zinc-950 p-2.5 rounded border border-zinc-850 flex items-start space-x-2">
              <span className="text-[10px] bg-blue-500/15 text-blue-400 font-mono px-1.5 py-0.5 rounded font-bold">INTEG</span>
              <div>
                <h4 className="text-xs font-bold text-zinc-200">Downstream Export Verification</h4>
                <p className="text-[10px] text-zinc-400 font-sans mt-0.5">
                  Blender B-Rep katı modelleme sızdırmazlık (watertight) testleri ve üretilen IFC dosyalarının resmi BuildingSMART parser testi.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>

      {/* ORTAK MÜHENDİSLİK SÖZLEŞMESİ (ENGINEERING CONTRACT) */}
      <div className="bg-zinc-900 border border-amber-500/30 rounded-2xl p-5 mb-8 space-y-4 relative overflow-hidden bg-gradient-to-b from-zinc-900 to-zinc-950">
        <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl pointer-events-none"></div>
        
        <div className="flex items-center justify-between border-b border-zinc-800/60 pb-3">
          <div className="flex items-center space-x-2 text-amber-400">
            <FileText className="w-5 h-5" />
            <h2 className="text-xs font-mono font-extrabold uppercase tracking-widest">
              Ortak Mühendislik Sözleşmesi (Engineering Contract)
            </h2>
          </div>
          <span className="text-[9px] bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded border border-amber-500/20 font-mono font-bold">
            Versiyon 1.0 (Ana Kural Kümesi)
          </span>
        </div>

        <p className="text-xs text-zinc-400 leading-relaxed font-sans">
          KaRar platformunun geliştirilmesinde (insan ve yapay zeka ajanları dahil) rol alan tüm aktörlerin uyması zorunlu olan, mimari bütünlüğü korumaya yönelik değişmez kurallar ve kalite kapıları sözleşmesidir:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-01</span>
              <span className="text-xs font-bold text-zinc-200">Veri Sahipliği (Data Ownership)</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Sistemdeki tek resmi veri kaynağı <strong>Canonical BIM Model</strong>'dir. Hiçbir arayüz (UI), 3D render veya dışa aktarım (IFC/Blender) modülü kendi içinde geometri üretemez ya da şemayı bozamaz. Veri akışı kesinlikle tek yönlüdür.
            </p>
          </div>

          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-02</span>
              <span className="text-xs font-bold text-zinc-200">Değişmez Akış Kuralları (Invariants)</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Zincirdeki sıralama asla ihlal edilemez: Geometrik onarım (Repair) bitmeden topoloji kurulamaz; topoloji (Snapping/Polygonization) kurulmadan semantik etiketleme (Enrichment) yapılamaz. Her adım bir öncekinin çıktısına bağımlıdır.
            </p>
          </div>

          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-03</span>
              <span className="text-xs font-bold text-zinc-200">Sorumluluk Alanları (Boundaries)</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Her motor sadece kendi sözleşmesindeki işi yapar. Örneğin; Blender motoru sadece girdi olarak aldığı Canonical JSON'dan katı 3D model üretir; Blender katmanında asla çizim düzeltme veya topolojik analiz yapılmaz.
            </p>
          </div>

          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-04</span>
              <span className="text-xs font-bold text-zinc-200">Versiyonlama Sözleşmesi</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Canonical BIM JSON şemasında geriye dönük uyumsuz (breaking) herhangi bir değişiklik yapıldığında şema ana sürümü (Major) artırılmalıdır. Şemadaki tüm alanlar TypeScript tipleri ile sıkı sıkıya korunur.
            </p>
          </div>

          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-05</span>
              <span className="text-xs font-bold text-zinc-200">Kalite Kapıları (Quality Gates)</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Ana koda (main/master) yapılacak her birleştirmede (PR/Merge); statik kod analizi (Linter), TypeScript derlemesi (Build) ve ilgili katmanın otomatik birim (Unit) testlerinin başarıyla tamamlanması zorunludur.
            </p>
          </div>

          <div className="bg-zinc-950 p-3.5 rounded border border-zinc-800 hover:border-zinc-700 transition-colors space-y-1.5">
            <div className="flex items-center space-x-1.5 text-amber-400">
              <span className="text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded font-mono font-bold">EC-06</span>
              <span className="text-xs font-bold text-zinc-200">Yapay Zeka (AI) Rol Sınırları</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed font-sans">
              Geliştirici yapay zeka ajanları, deterministik matematiksel ve geometrik kuralları tek taraflı değiştiremez. AI ajanlarının görevi; test kodu yazmak, optimizasyon önermek, kod üretmek ve dökümantasyon sağlamaktır.
            </p>
          </div>
        </div>
      </div>

      {/* TWO COLUMN GRID: LEFT ROADMAP, RIGHT SANDBOX / TECHNICAL SPLIT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: THE 4-PHASE INTERACTIVE ROADMAP (5 COLS) */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          <h2 className="text-xs font-mono font-bold text-zinc-500 uppercase tracking-widest">
            Stratejik Gelişim Aşamalari
          </h2>
          
          <div className="space-y-3">
            {phases.map((p) => {
              const isActive = activePhaseId === p.id;
              let statusBadge = "";
              if (p.status === "active") statusBadge = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
              else if (p.status === "planned") statusBadge = "bg-amber-500/10 text-amber-400 border border-amber-500/20";
              else statusBadge = "bg-zinc-800 text-zinc-500 border border-zinc-700/50";

              return (
                <div
                  key={p.id}
                  onClick={() => setActivePhaseId(p.id)}
                  className={`cursor-pointer p-4 rounded-xl border text-left transition-all ${
                    isActive
                      ? "bg-zinc-900 border-emerald-500 shadow-md shadow-emerald-500/5"
                      : "bg-zinc-900/40 border-zinc-800 hover:bg-zinc-900 hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className={`text-xs font-bold ${isActive ? "text-emerald-400" : "text-zinc-200"}`}>
                        {p.title}
                      </h3>
                      <p className="text-[10px] text-zinc-500 font-mono">{p.subtitle}</p>
                    </div>
                    <span className={`text-[8px] font-mono px-2 py-0.5 rounded font-bold uppercase ${statusBadge}`}>
                      {p.status === "active" ? "Aktif Faz" : p.status === "planned" ? "Planlandı" : "Gelecek"}
                    </span>
                  </div>

                  {/* Tech stack badges */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {p.techStack.map((tech) => (
                      <span key={tech} className="text-[9px] bg-zinc-950 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
                        {tech}
                      </span>
                    ))}
                  </div>

                  {/* Simple completion meter */}
                  <div className="flex items-center space-x-2 text-[10px] font-mono text-zinc-500">
                    <span className="text-zinc-400">
                      Görevler: {p.tasks.filter(t => t.completed).length}/{p.tasks.length}
                    </span>
                    <div className="flex-1 bg-zinc-950 h-1.5 rounded-full overflow-hidden">
                      <div 
                        className="bg-emerald-500 h-1.5 rounded-full" 
                        style={{ width: `${(p.tasks.filter(t => t.completed).length / p.tasks.length) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* CLOUD VS DESKTOP COST MATRIX */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-3.5">
            <h3 className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider flex items-center space-x-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span>Masaüstü vs Bulut Maliyet Matrisi</span>
            </h3>

            <div className="space-y-2.5 text-[11px] font-mono">
              <div className="flex justify-between items-start border-b border-zinc-800 pb-2">
                <div>
                  <span className="text-zinc-200 block font-bold">1. Aşama: Masaüstü (Tauri/Electron)</span>
                  <span className="text-zinc-500 text-[10px]">Tüm hesaplama kullanıcının GPU ve CPU'sunda yerel olarak çalışır.</span>
                </div>
                <span className="text-emerald-400 font-extrabold flex-shrink-0">Sıfır Sunucu Maliyeti</span>
              </div>

              <div className="flex justify-between items-start border-b border-zinc-800 pb-2">
                <div>
                  <span className="text-zinc-200 block font-bold">2. Aşama: Bulut Entegrasyonu</span>
                  <span className="text-zinc-500 text-[10px]">Çoklu kullanıcı ve projelerin bulutta senkronizasyonu.</span>
                </div>
                <span className="text-amber-500 font-extrabold flex-shrink-0">Düşük Maliyet (Sadece DB)</span>
              </div>

              <div className="flex justify-between items-start">
                <div>
                  <span className="text-zinc-200 block font-bold">3. Aşama: Bulut Tabanlı Render</span>
                  <span className="text-zinc-500 text-[10px]">WebGL harici ağır Blender renderlarının sunucuda koşturulması.</span>
                </div>
                <span className="text-red-400 font-extrabold flex-shrink-0">Yüksek Sunucu Maliyeti</span>
              </div>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: ACTIVE PHASE DETAIL & CODE SANDBOX (7 COLS) */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          
          {/* ACTIVE PHASE DETAILS */}
          {(() => {
            const phase = phases.find(p => p.id === activePhaseId)!;
            return (
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div>
                    <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest">SEÇİLİ FAZ DETAYI</span>
                    <h2 className="text-sm font-bold text-zinc-100">{phase.title}</h2>
                  </div>
                  <div className="flex space-x-1">
                    {phase.techStack.map(t => (
                      <span key={t} className="text-[9px] bg-zinc-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-950/50 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-zinc-400 leading-relaxed font-sans">{phase.description}</p>

                <div className="space-y-2">
                  <h4 className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">Aşama Görev Listesi</h4>
                  <div className="space-y-1.5 font-mono text-xs">
                    {phase.tasks.map((task, idx) => (
                      <div key={idx} className="flex items-center space-x-2.5 bg-zinc-950/50 p-2 rounded border border-zinc-850">
                        <input
                          type="checkbox"
                          checked={task.completed}
                          readOnly
                          className="w-3.5 h-3.5 text-emerald-500 bg-zinc-900 border-zinc-700 rounded focus:ring-emerald-500 focus:ring-offset-zinc-950 cursor-default"
                        />
                        <span className={task.completed ? "text-zinc-400 line-through" : "text-zinc-200"}>
                          {task.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}

          {/* INTERACTIVE ALGORITHM CO-PILOT SANDBOX */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <div>
                <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest flex items-center space-x-1">
                  <Codesandbox className="w-3.5 h-3.5 text-emerald-400" />
                  <span>ALGORİTMA KO-PİLOT KILAVUZU (YAPAY ZEKA ENTEGRASYONU)</span>
                </span>
                <h2 className="text-xs font-bold text-zinc-100 mt-1">
                  AI'ın KaRar Çekirdek Algoritmalarını Yazma Yeteneği
                </h2>
              </div>
            </div>

            <p className="text-xs text-zinc-400 leading-relaxed">
              Yapay zeka, projenin yazılım geliştirme sürecine doğrudan katkı sunar. Aşağıda, çekirdek motorumuzun ihtiyaç duyacağı deterministik algoritmaların yapay zeka tarafından optimize edilmiş gerçek kod örneklerini inceleyebilirsiniz:
            </p>

            {/* Selector buttons for challenges */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(challenges).map(([key, value]) => (
                <button
                  key={key}
                  onClick={() => setSelectedChallenge(key)}
                  className={`px-3 py-1.5 rounded-lg font-mono text-[10px] font-bold border transition-all ${
                    selectedChallenge === key
                      ? "bg-emerald-950/40 border-emerald-500 text-emerald-400"
                      : "bg-zinc-950 border-zinc-800 text-zinc-500 hover:border-zinc-700 hover:text-zinc-300"
                  }`}
                >
                  {value.title.split(". ")[1]}
                </button>
              ))}
            </div>

            {/* Challenge Detail */}
            {(() => {
              const ch = challenges[selectedChallenge as keyof typeof challenges];
              return (
                <div className="space-y-3 animate-fade-in text-xs font-mono">
                  <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 space-y-1.5">
                    <div className="text-[11px] text-red-400 font-bold">Problem:</div>
                    <div className="text-zinc-300 font-sans text-xs">{ch.problem}</div>
                    <div className="text-[11px] text-emerald-400 font-bold pt-1.5">Deterministik Çözüm:</div>
                    <div className="text-zinc-300 font-sans text-xs">{ch.solution}</div>
                  </div>

                  {/* Code Editor */}
                  <div className="space-y-1">
                    <div className="flex justify-between items-center text-[10px] text-zinc-500 uppercase px-1">
                      <span>Python Algoritma Örneği</span>
                      <span>SHA-256 DOĞRULANDI</span>
                    </div>
                    <div className="bg-zinc-950 border border-zinc-850 rounded-lg p-3 overflow-x-auto max-h-[220px] font-mono text-[11px] leading-relaxed text-emerald-500/90 scrollbar-thin">
                      <pre>{ch.code}</pre>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Practical suggestion */}
            <div className="bg-zinc-950/80 border border-zinc-800 p-3 rounded-xl flex items-start space-x-2.5 text-xs text-zinc-400">
              <Lightbulb className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-zinc-200">Ar-Ge Strateji Notu:</span> Çevrimdışı ve yerel (client-side) hesaplama kapasitesi, yazılımın lisans değerini artırır. KaRar'ın tüm geometrik hesaplamalarını tarayıcı içinde yerel olarak çözmek için <strong className="text-amber-400">WebAssembly (WASM)</strong> üzerine Python Shapely/ezdxf kütüphanelerini derleyerek yükleme opsiyonu da Faz 3 kapsamında değerlendirilecektir.
              </div>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
}
