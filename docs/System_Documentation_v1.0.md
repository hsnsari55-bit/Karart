# KaRar AI BIM Platform - Sistem ve Geliştirici Dokümantasyonu (v1.0.0-RC1)

Bu doküman, **KaRar Platformu**'nun sistem mimarisi, veri akışları, JSON şemaları, kurulum rehberleri ve kullanıcı kılavuzunu içeren ana başvuru kaynağıdır.

---

## 1. Sistem Mimarisi (System Architecture)

KaRar, CAD (DXF) çizimlerini tam otomatik ve deterministik bir yaklaşımla Yapı Bilgi Modellemesi (BIM) standardına dönüştüren, **Node.js/Express** ve **Python** tabanlı hibrit bir mikromimari üzerine inşa edilmiştir.

### Bileşen Mimarisi (Component Architecture)
```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                       │ (3D Görüntüleme, Raporlama ve QA Panelleri)
└───────────────────────────┬─────────────────────────────┘
                            │ (REST HTTP API)
┌───────────────────────────▼─────────────────────────────┐
│                    Node.js Server                       │ (Spawning, Otomasyon & API Router)
└───────────────────────────┬─────────────────────────────┘
                            │ (Spawn Process / Environment venv)
┌───────────────────────────▼─────────────────────────────┐
│                 6-Aşamalı Python Pipeline               │ (Çekirdek BIM Motoru)
│                                                         │
│  1. DXFParser ──► 2. Geometry ──► 3. Topology           │
│                                      │                  │
│  6. BIMCore  ◄──  5. Space    ◄── 4. Semantic           │
└─────────────────────────────────────────────────────────┘
```

1. **İletişim Katmanı (Vite + React / Tailwind CSS):** Kullanıcının projelerini yüklediği, pipeline adımlarını çalıştırdığı ve sonuçları (2B çizimler, 3B modeller ve metraj tabloları) görselleştirdiği modern arayüz.
2. **Orkestrasyon Katmanı (Node.js/Express - server.ts):** Python sanal ortamını (venv) kontrol eden, işlem adımlarını sırasıyla tetikleyen ve API isteklerini karşılayan yönetim katmanı.
3. **Analiz ve Model Üretim Katmanı (Python 3.11):** 6 adet birbirine bağlı deterministik motordan oluşan çekirdek pipeline.

---

## 2. Veri Akışı (Data Flow)

KaRar veri akışında her motorun çıktısı bir sonraki motor için girdi teşkil eder:

```
[DXF Dosyası]
     │
     ▼ (ezdxf)
1. DXFParser ───────────► [dxf_raw.json]
                             │
                             ▼ (shapely & r-tree)
2. GeometryEngine ──────► [walls_clean.json]
                             │
                             ▼ (unary_union & planar graph)
3. TopologyEngine ──────► [geometry_graph.json]
                             │
                             ▼ (rule-based heuristic classification)
4. SemanticEngine ──────► [bim_semantics.json]
                             │
                             ▼ (polygonization & leaking seals)
5. SpaceEngine ─────────► [spaces.json]
                             │
                             ▼ (uuid map & validation)
6. BIMCoreEngine ───────► [bim_model.json] ──► [model.ifc] / [model.glb]
```

---

## 3. JSON Şemaları (JSON Schemas)

### 3.1 `dxf_raw.json` (Ayrıştırılmış Ham Çizim Verisi)
```json
{
  "project": "Proje Adi",
  "bounding_box": { "min_x": 0.0, "min_y": 0.0, "max_x": 100.0, "max_y": 100.0 },
  "entities": [
    {
      "type": "LINE",
      "layer": "duvar",
      "start": { "x": 0.0, "y": 0.0, "z": 0.0 },
      "end": { "x": 10.0, "y": 0.0, "z": 0.0 }
    }
  ]
}
```

### 3.2 `bim_model.json` (Kanonik BIM Modeli)
```json
{
  "project": "Proje Adi",
  "version": "v1.0.0-RC1",
  "walls": [
    {
      "uuid": "439b1a50-8b17-4638-9cf7-cbffbe1d69d7",
      "points": [[0.0, 0.0], [10.0, 0.0]],
      "thickness": 250.0,
      "height": 3000.0
    }
  ],
  "spaces": [
    {
      "uuid": "98cc2b54-ff11-477c-a49d-fa77ff54cb3d",
      "name": "Salon",
      "area": 24.5,
      "polygon": [[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0], [0.0, 0.0]]
    }
  ]
}
```

---

## 4. Kurulum Kılavuzu (Installation Guide)

### Sistem Gereksinimleri
- Node.js 18 veya üzeri
- Python 3.11 veya üzeri
- `libspatialindex-dev` (R-Tree kütüphanesi için zorunludur)

### Tek Komutla Kurulum (Single-Command Install)
```bash
npm run install-all
```
Bu komut sırasıyla:
1. Node dependencies paketlerini kurar.
2. Python sanal ortamını (`venv`) oluşturur.
3. Gerekli Python kütüphanelerini (`ezdxf`, `shapely`, `rtree`, `ifcopenshell`, `numpy`, `trimesh`) kurar.

---

## 5. Geliştirici Dokümantasyonu (Developer Docs)

### Yeni Test Eklemek
Yeni unit veya integration testleri `/backend/tests/` dizini altında python dosyaları olarak eklenmeli ve aşağıdaki komutla çalıştırılmalıdır:
```bash
npm run test:python
```

### Kod Kalitesi ve Linter
React arayüzü ve sunucu kodlarının kontrolü için:
```bash
npm run lint
```

---

## 6. Kullanıcı Dokümantasyonu (User Docs)

### Adım Adım Kullanım Rehberi
1. **Dosya Yükleme:** React web arayüzünden sürükle-bırak yöntemiyle bir `.dxf` mimari kat planı yükleyin.
2. **Katman Doğrulama:** Çizimdeki katman adlarının KaRar standartları (`duvar`, `kolon`, `kapı`, `k pencere`) ile eşleştiğini teyit edin.
3. **Pipeline Başlatma:** "Entegrasyonu Çalıştır" butonuna basarak 6 aşamalı süreci tetikleyin.
4. **Sonuçları İzleme:** 
   - **2D Panel:** Duvar çizgileri ve odaların kapalı alanlarının visual overlay'lerini inceleyin.
   - **3D Panel:** Çizimden üretilen 3 boyutlu mesh modelini döndürerek inceleyin.
   - **Rapor ve Metraj:** Çıkarılan toplam duvar uzunlukları, oda alanları ve metraj listesini dışa aktarın.
