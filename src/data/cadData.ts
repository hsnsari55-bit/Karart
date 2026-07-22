import { Floor, CADEntity, Room, Point, PipelineStep } from "../types";

// Helper to create points
const pt = (x: number, y: number): Point => ({ x, y });

// Ground Floor (Zemin Kat) Rooms
const groundRooms: Room[] = [
  {
    id: "g_salon",
    name: "Salon (Living Room)",
    type: "Living",
    area: 38.5,
    color: "rgba(59, 130, 246, 0.15)", // Blue
    points: [pt(50, 50), pt(450, 50), pt(450, 320), pt(50, 320)],
  },
  {
    id: "g_kitchen",
    name: "Mutfak (Kitchen)",
    type: "Kitchen",
    area: 16.2,
    color: "rgba(16, 185, 129, 0.15)", // Green
    points: [pt(450, 50), pt(750, 50), pt(750, 220), pt(450, 220)],
  },
  {
    id: "g_corridor",
    name: "Hol / Antre (Foyer)",
    type: "Corridor",
    area: 11.4,
    color: "rgba(245, 158, 11, 0.15)", // Amber
    points: [pt(450, 220), pt(750, 220), pt(750, 320), pt(450, 320)],
  },
  {
    id: "g_wc",
    name: "Misafir WC (Powder Room)",
    type: "Bathroom",
    area: 4.8,
    color: "rgba(139, 92, 246, 0.15)", // Purple
    points: [pt(50, 320), pt(220, 320), pt(220, 420), pt(50, 420)],
  },
  {
    id: "g_entrance",
    name: "Giriş Rüzgarlığı (Vestibule)",
    type: "Entrance",
    area: 6.5,
    color: "rgba(236, 72, 153, 0.15)", // Pink
    points: [pt(220, 320), pt(450, 320), pt(450, 420), pt(220, 420)],
  },
];

// Ground Floor CAD Entities
const groundEntities: CADEntity[] = [
  // Grid Lines (Aks)
  { id: "g_aks_h1", type: "LINE", layer: "aks", start: pt(20, 50), end: pt(780, 50) },
  { id: "g_aks_h2", type: "LINE", layer: "aks", start: pt(20, 220), end: pt(780, 220) },
  { id: "g_aks_h3", type: "LINE", layer: "aks", start: pt(20, 320), end: pt(780, 320) },
  { id: "g_aks_h4", type: "LINE", layer: "aks", start: pt(20, 420), end: pt(780, 420) },
  { id: "g_aks_v1", type: "LINE", layer: "aks", start: pt(50, 20), end: pt(50, 450) },
  { id: "g_aks_v2", type: "LINE", layer: "aks", start: pt(220, 20), end: pt(220, 450) },
  { id: "g_aks_v3", type: "LINE", layer: "aks", start: pt(450, 20), end: pt(450, 450) },
  { id: "g_aks_v4", type: "LINE", layer: "aks", start: pt(750, 20), end: pt(750, 450) },

  // Columns (Kolonlar) at main grid crossings
  { id: "g_col_1", type: "COLUMN", layer: "kolon", start: pt(35, 35), end: pt(65, 65), thickness: 30 },
  { id: "g_col_2", type: "COLUMN", layer: "kolon", start: pt(435, 35), end: pt(465, 65), thickness: 30 },
  { id: "g_col_3", type: "COLUMN", layer: "kolon", start: pt(735, 35), end: pt(765, 65), thickness: 30 },
  { id: "g_col_4", type: "COLUMN", layer: "kolon", start: pt(35, 305), end: pt(65, 335), thickness: 30 },
  { id: "g_col_5", type: "COLUMN", layer: "kolon", start: pt(435, 305), end: pt(465, 335), thickness: 30 },
  { id: "g_col_6", type: "COLUMN", layer: "kolon", start: pt(735, 305), end: pt(765, 335), thickness: 30 },
  { id: "g_col_7", type: "COLUMN", layer: "kolon", start: pt(35, 405), end: pt(65, 435), thickness: 30 },
  { id: "g_col_8", type: "COLUMN", layer: "kolon", start: pt(205, 405), end: pt(235, 435), thickness: 30 },
  { id: "g_col_9", type: "COLUMN", layer: "kolon", start: pt(435, 405), end: pt(465, 435), thickness: 30 },

  // EXTERNAL WALLS (Outer perimeter, thick 25cm)
  // Top Outer Wall
  { id: "g_wall_top", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(750, 50), thickness: 25 },
  // Bottom Outer Wall Left (WC/Entrance)
  { id: "g_wall_bot_l", type: "LINE", layer: "duvar", start: pt(50, 420), end: pt(450, 420), thickness: 25 },
  // Bottom Outer Wall Right (Corridor)
  { id: "g_wall_bot_r", type: "LINE", layer: "duvar", start: pt(450, 320), end: pt(750, 320), thickness: 25 },
  // Left Outer Wall
  { id: "g_wall_left", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(50, 420), thickness: 25 },
  // Right Outer Wall Upper (Kitchen)
  { id: "g_wall_right_u", type: "LINE", layer: "duvar", start: pt(750, 50), end: pt(750, 220), thickness: 25 },
  // Right Outer Wall Lower (Foyer)
  { id: "g_wall_right_l", type: "LINE", layer: "duvar", start: pt(750, 220), end: pt(750, 320), thickness: 25 },

  // INTERNAL PARTITION WALLS (Thinner, 15cm)
  // Wall between Salon and Kitchen/Foyer
  { id: "g_wall_int_1", type: "LINE", layer: "duvar", start: pt(450, 50), end: pt(450, 320), thickness: 15 },
  // Wall between Kitchen and Foyer
  { id: "g_wall_int_2", type: "LINE", layer: "duvar", start: pt(450, 220), end: pt(750, 220), thickness: 15 },
  // Wall between WC and Vestibule
  { id: "g_wall_int_3", type: "LINE", layer: "duvar", start: pt(220, 320), end: pt(220, 420), thickness: 15 },
  // Wall between Vestibule/WC and Salon
  { id: "g_wall_int_4", type: "LINE", layer: "duvar", start: pt(50, 320), end: pt(450, 320), thickness: 15 },

  // DOORS (Kapılar) - Openings cut in walls
  // Main Entrance Door (Vestibule to Outside)
  { id: "g_door_main", type: "DOOR", layer: "kapı", start: pt(310, 420), end: pt(380, 420), width: 70, doorType: "Single" },
  // Salon Door (Vestibule to Salon)
  { id: "g_door_salon", type: "DOOR", layer: "kapı", start: pt(310, 320), end: pt(390, 320), width: 80, doorType: "Single" },
  // WC Door
  { id: "g_door_wc", type: "DOOR", layer: "kapı", start: pt(220, 340), end: pt(220, 400), width: 60, doorType: "Single" },
  // Kitchen Door (Corridor to Kitchen)
  { id: "g_door_kit", type: "DOOR", layer: "kapı", start: pt(520, 220), end: pt(600, 220), width: 80, doorType: "Single" },
  // Double Sliding Patio Door in Salon (to back garden)
  { id: "g_door_patio", type: "DOOR", layer: "kapı", start: pt(150, 50), end: pt(270, 50), width: 120, doorType: "Double" },

  // WINDOWS (Pencereler)
  // Salon Main Window
  { id: "g_win_salon_l", type: "WINDOW", layer: "k pencere", start: pt(50, 150), end: pt(50, 250), width: 100 },
  // Kitchen Window
  { id: "g_win_kit", type: "WINDOW", layer: "k pencere", start: pt(580, 50), end: pt(680, 50), width: 100 },
  // Corridor Window
  { id: "g_win_cor", type: "WINDOW", layer: "k pencere", start: pt(750, 250), end: pt(750, 290), width: 40 },
  // WC Tiny Window
  { id: "g_win_wc", type: "WINDOW", layer: "k pencere", start: pt(50, 350), end: pt(50, 380), width: 30 },
];

// First Floor (1. Normal Kat) Rooms
const firstRooms: Room[] = [
  {
    id: "f_master",
    name: "Ebeveyn Yatak Odası (Master Bed)",
    type: "Bedroom",
    area: 24.2,
    color: "rgba(59, 130, 246, 0.15)",
    points: [pt(50, 50), pt(350, 50), pt(350, 300), pt(50, 300)],
  },
  {
    id: "f_kids",
    name: "Çocuk Odası (Kids Bed)",
    type: "Bedroom",
    area: 15.6,
    color: "rgba(16, 185, 129, 0.15)",
    points: [pt(350, 50), pt(600, 50), pt(600, 240), pt(350, 240)],
  },
  {
    id: "f_bath",
    name: "Genel Banyo (Bathroom)",
    type: "Bathroom",
    area: 8.4,
    color: "rgba(139, 92, 246, 0.15)",
    points: [pt(600, 50), pt(750, 50), pt(750, 240), pt(600, 240)],
  },
  {
    id: "f_hall",
    name: "Gece Holü (Stair Lobby)",
    type: "Corridor",
    area: 12.8,
    color: "rgba(245, 158, 11, 0.15)",
    points: [pt(350, 240), pt(750, 240), pt(750, 420), pt(350, 420)],
  },
  {
    id: "f_balcony",
    name: "Yatak Odası Balkonu (Balcony)",
    type: "Balcony",
    area: 7.2,
    color: "rgba(236, 72, 153, 0.15)",
    points: [pt(50, 300), pt(350, 300), pt(350, 380), pt(50, 380)],
  },
];

// First Floor CAD Entities
const firstEntities: CADEntity[] = [
  // Grid lines
  { id: "f_aks_h1", type: "LINE", layer: "aks", start: pt(20, 50), end: pt(780, 50) },
  { id: "f_aks_h2", type: "LINE", layer: "aks", start: pt(20, 240), end: pt(780, 240) },
  { id: "f_aks_h3", type: "LINE", layer: "aks", start: pt(20, 300), end: pt(780, 300) },
  { id: "f_aks_h4", type: "LINE", layer: "aks", start: pt(20, 420), end: pt(780, 420) },
  { id: "f_aks_v1", type: "LINE", layer: "aks", start: pt(50, 20), end: pt(50, 450) },
  { id: "f_aks_v2", type: "LINE", layer: "aks", start: pt(350, 20), end: pt(350, 450) },
  { id: "f_aks_v3", type: "LINE", layer: "aks", start: pt(600, 20), end: pt(600, 450) },
  { id: "f_aks_v4", type: "LINE", layer: "aks", start: pt(750, 20), end: pt(750, 450) },

  // Columns
  { id: "f_col_1", type: "COLUMN", layer: "kolon", start: pt(35, 35), end: pt(65, 65), thickness: 30 },
  { id: "f_col_2", type: "COLUMN", layer: "kolon", start: pt(335, 35), end: pt(365, 65), thickness: 30 },
  { id: "f_col_3", type: "COLUMN", layer: "kolon", start: pt(735, 35), end: pt(765, 65), thickness: 30 },
  { id: "f_col_4", type: "COLUMN", layer: "kolon", start: pt(35, 285), end: pt(65, 315), thickness: 30 },
  { id: "f_col_5", type: "COLUMN", layer: "kolon", start: pt(335, 285), end: pt(365, 315), thickness: 30 },
  { id: "f_col_6", type: "COLUMN", layer: "kolon", start: pt(735, 285), end: pt(765, 315), thickness: 30 },
  { id: "f_col_7", type: "COLUMN", layer: "kolon", start: pt(335, 405), end: pt(365, 435), thickness: 30 },
  { id: "f_col_8", type: "COLUMN", layer: "kolon", start: pt(735, 405), end: pt(765, 435), thickness: 30 },

  // Outer Walls
  { id: "f_wall_top", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(750, 50), thickness: 25 },
  { id: "f_wall_bot", type: "LINE", layer: "duvar", start: pt(350, 420), end: pt(750, 420), thickness: 25 },
  { id: "f_wall_left", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(50, 300), thickness: 25 },
  { id: "f_wall_right", type: "LINE", layer: "duvar", start: pt(750, 50), end: pt(750, 420), thickness: 25 },

  // Balcony Boundary (thin exterior railing/wall)
  { id: "f_balc_wall_l", type: "LINE", layer: "duvar", start: pt(50, 300), end: pt(50, 380), thickness: 10 },
  { id: "f_balc_wall_b", type: "LINE", layer: "duvar", start: pt(50, 380), end: pt(350, 380), thickness: 10 },
  { id: "f_balc_wall_r", type: "LINE", layer: "duvar", start: pt(350, 300), end: pt(350, 380), thickness: 10 },

  // Inner partition walls
  { id: "f_wall_int_1", type: "LINE", layer: "duvar", start: pt(350, 50), end: pt(350, 420), thickness: 15 },
  { id: "f_wall_int_2", type: "LINE", layer: "duvar", start: pt(350, 240), end: pt(750, 240), thickness: 15 },
  { id: "f_wall_int_3", type: "LINE", layer: "duvar", start: pt(600, 50), end: pt(600, 240), thickness: 15 },
  { id: "f_wall_int_4", type: "LINE", layer: "duvar", start: pt(50, 300), end: pt(350, 300), thickness: 25 },

  // DOORS
  // Master Bedroom Door
  { id: "f_door_master", type: "DOOR", layer: "kapı", start: pt(350, 250), end: pt(350, 310), width: 60, doorType: "Single" },
  // Kids Bedroom Door
  { id: "f_door_kids", type: "DOOR", layer: "kapı", start: pt(420, 240), end: pt(490, 240), width: 70, doorType: "Single" },
  // Bathroom Door
  { id: "f_door_bath", type: "DOOR", layer: "kapı", start: pt(620, 240), end: pt(680, 240), width: 60, doorType: "Single" },
  // Balcony Door from Master Bed
  { id: "f_door_balc", type: "DOOR", layer: "kapı", start: pt(180, 300), end: pt(250, 300), width: 70, doorType: "Single" },

  // WINDOWS
  // Master Bed Window
  { id: "f_win_master", type: "WINDOW", layer: "k pencere", start: pt(50, 120), end: pt(50, 200), width: 80 },
  // Kids Room Window
  { id: "f_win_kids", type: "WINDOW", layer: "k pencere", start: pt(440, 50), end: pt(520, 50), width: 80 },
  // Bathroom Window (small ventilation)
  { id: "f_win_bath", type: "WINDOW", layer: "k pencere", start: pt(650, 50), end: pt(700, 50), width: 50 },
  // Corridor Window
  { id: "f_win_hall", type: "WINDOW", layer: "k pencere", start: pt(750, 320), end: pt(750, 380), width: 60 },
];

// Basement (Bodrum Kat) Rooms
const basementRooms: Room[] = [
  {
    id: "b_parking",
    name: "Kapalı Otopark (Underground Garage)",
    type: "Parking",
    area: 44.5,
    color: "rgba(107, 114, 128, 0.15)", // Gray
    points: [pt(50, 50), pt(450, 50), pt(450, 350), pt(50, 350)],
  },
  {
    id: "b_cinema",
    name: "Hobi / Sinema Odası (Cinema / Hobby)",
    type: "Recreation",
    area: 28.0,
    color: "rgba(139, 92, 246, 0.15)", // Purple
    points: [pt(450, 50), pt(750, 50), pt(750, 350), pt(450, 350)],
  },
  {
    id: "b_utility",
    name: "Teknik Hacim / Depo (Utility / Storage)",
    type: "Utility",
    area: 12.0,
    color: "rgba(245, 158, 11, 0.15)",
    points: [pt(50, 350), pt(350, 350), pt(350, 420), pt(50, 420)],
  },
  {
    id: "b_hall",
    name: "Bodrum Holü (Basement Hall)",
    type: "Corridor",
    area: 9.8,
    color: "rgba(59, 130, 246, 0.15)",
    points: [pt(350, 350), pt(750, 350), pt(750, 420), pt(350, 420)],
  },
];

// Basement CAD Entities
const basementEntities: CADEntity[] = [
  // Grid Lines
  { id: "b_aks_h1", type: "LINE", layer: "aks", start: pt(20, 50), end: pt(780, 50) },
  { id: "b_aks_h2", type: "LINE", layer: "aks", start: pt(20, 350), end: pt(780, 350) },
  { id: "b_aks_h3", type: "LINE", layer: "aks", start: pt(20, 420), end: pt(780, 420) },
  { id: "b_aks_v1", type: "LINE", layer: "aks", start: pt(50, 20), end: pt(50, 450) },
  { id: "b_aks_v2", type: "LINE", layer: "aks", start: pt(350, 20), end: pt(350, 450) },
  { id: "b_aks_v3", type: "LINE", layer: "aks", start: pt(450, 20), end: pt(450, 450) },
  { id: "b_aks_v4", type: "LINE", layer: "aks", start: pt(750, 20), end: pt(750, 450) },

  // Columns (Thicker for foundation/basement!)
  { id: "b_col_1", type: "COLUMN", layer: "kolon", start: pt(30, 30), end: pt(70, 70), thickness: 40 },
  { id: "b_col_2", type: "COLUMN", layer: "kolon", start: pt(430, 30), end: pt(470, 70), thickness: 40 },
  { id: "b_col_3", type: "COLUMN", layer: "kolon", start: pt(730, 30), end: pt(770, 70), thickness: 40 },
  { id: "b_col_4", type: "COLUMN", layer: "kolon", start: pt(30, 330), end: pt(70, 370), thickness: 40 },
  { id: "b_col_5", type: "COLUMN", layer: "kolon", start: pt(430, 330), end: pt(470, 370), thickness: 40 },
  { id: "b_col_6", type: "COLUMN", layer: "kolon", start: pt(730, 330), end: pt(770, 370), thickness: 40 },

  // Thick Concrete Retaining Walls (Perde Duvarlar, 30cm)
  { id: "b_wall_top", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(750, 50), thickness: 30 },
  { id: "b_wall_bot", type: "LINE", layer: "duvar", start: pt(50, 420), end: pt(750, 420), thickness: 30 },
  { id: "b_wall_left", type: "LINE", layer: "duvar", start: pt(50, 50), end: pt(50, 420), thickness: 30 },
  { id: "b_wall_right", type: "LINE", layer: "duvar", start: pt(750, 50), end: pt(750, 420), thickness: 30 },

  // Inner partitions (15cm)
  { id: "b_wall_int_1", type: "LINE", layer: "duvar", start: pt(450, 50), end: pt(450, 350), thickness: 20 },
  { id: "b_wall_int_2", type: "LINE", layer: "duvar", start: pt(50, 350), end: pt(750, 350), thickness: 20 },
  { id: "b_wall_int_3", type: "LINE", layer: "duvar", start: pt(350, 350), end: pt(350, 420), thickness: 15 },

  // Garage Shutter / Roller Door (Large)
  { id: "b_door_garage", type: "DOOR", layer: "kapı", start: pt(120, 50), end: pt(320, 50), width: 200, doorType: "Double" },
  // Cinema Entrance Door
  { id: "b_door_cinema", type: "DOOR", layer: "kapı", start: pt(450, 180), end: pt(450, 260), width: 80, doorType: "Single" },
  // Utility Door
  { id: "b_door_util", type: "DOOR", layer: "kapı", start: pt(240, 350), end: pt(310, 350), width: 70, doorType: "Single" },

  // Windows (None or high basement shafts)
  { id: "b_win_util", type: "WINDOW", layer: "k pencere", start: pt(150, 420), end: pt(210, 420), width: 60 },
  { id: "b_win_cinema", type: "WINDOW", layer: "k pencere", start: pt(750, 180), end: pt(750, 240), width: 60 },
];

export const mockFloors: Floor[] = [
  {
    id: "ground",
    name: "Zemin Kat (Ground Floor)",
    elevation: "H: +0.00",
    entityCount: groundEntities.length,
    area: 120.0,
    rooms: groundRooms,
    entities: groundEntities,
  },
  {
    id: "first",
    name: "1. Normal Kat (First Floor)",
    elevation: "H: +3.00",
    entityCount: firstEntities.length,
    area: 110.0,
    rooms: firstRooms,
    entities: firstEntities,
  },
  {
    id: "basement",
    name: "Bodrum Kat (Basement)",
    elevation: "H: -3.00",
    entityCount: basementEntities.length,
    area: 125.0,
    rooms: basementRooms,
    entities: basementEntities,
  },
];

export const pipelineInitialSteps: PipelineStep[] = [
  {
    id: "parsing",
    title: "Parsing Engine",
    subtitle: "Aşama 1: DXF/CAD Veri Okuma",
    description: "CAD çizimini binary düzeyde okur, katmanları ('duvar', 'kapı', 'k pencere') ayrıştırır ve ölçek katsayılarını çözümler.",
    icon: "FolderOpen",
    status: "completed",
    duration: 820,
    insights: [
      "12,049 adet geometrik vektör başarıyla yüklendi.",
      "1,794 metinsel etiket tarandı.",
      "Katman eşleştirmesi yapıldı: 'duvar' katmanı kalınlık analizi için ayrıldı.",
      "Ölçek kalibre edildi: 1 ünite = 32.0 mm (1:50 ölçek uyumlu)."
    ]
  },
  {
    id: "geometry",
    title: "Geometry Engine",
    subtitle: "Aşama 2: Snap & Eksen Çıkarımı",
    description: "Milimetrik çizim hatalarını giderir. Dağınık çizgileri birbirine kilitler (snap), T-birleşimlerini düzeltir og taşıyıcı duvar eksenlerini hesaplar.",
    icon: "Activity",
    status: "completed",
    duration: 1150,
    insights: [
      "Vektör uç birleştirmeleri yapıldı (Snapping toleransı: 5mm).",
      "14 adet hatalı T-birleşimi (T-Junction) kapatıldı.",
      "Kayıp duvar eksen çizgileri (Wall Axes) başarıyla hesaplandı.",
      "Çakışan mükerrer 84 adet çizgi temizlendi."
    ]
  },
  {
    id: "semantic",
    title: "Semantic Engine",
    subtitle: "Aşama 3: Eleman Sınıflandırma",
    description: "Matematiksel çizgileri mimari elemanlara (Taşıyıcı Duvar, Bölme Duvar, Tek/Çift Kanat Kapı, Sürme Pencere, Betonarme Kolon) dönüştürür.",
    icon: "Database",
    status: "completed",
    duration: 940,
    insights: [
      "229 adet duvar segmenti kalınlıklarına göre sınıflandırıldı.",
      "Oda sınır belirleme algoritması (Room Detector Engine v2) ile kapalı alan döngüleri çıkarıldı.",
      "Genişliklerine göre kapılar (Single/Double) ve pencere yırtıkları ayrıştırıldı.",
      "Kolon yerleşimleri 'aks' kesişim koordinatları üzerinden doğrulandı."
    ]
  },
  {
    id: "topology",
    title: "Topology Engine",
    subtitle: "Aşama 4: İlişki Matrisi & BIM",
    description: "Yapı elemanları arasındaki bağlantıları ve komşulukları kurarak parametrik 3D BIM modelini (IFC formatında) hazırlar.",
    icon: "GitMerge",
    status: "completed",
    duration: 650,
    insights: [
      "Kapıların ait olduğu duvarlar parametrik olarak ilişkilendirildi.",
      "Pencerelerin gün ışığı yönü ve oda hacimsel ilişkileri kuruldu.",
      "Odaların komşuluk matrisi (adjacency matrix) tamamlandı.",
      "BIM modeli Blender 3D motoru ('blender_builder.py') ve IFC formatında ihraç edilmeye hazırlandı."
    ]
  }
];
