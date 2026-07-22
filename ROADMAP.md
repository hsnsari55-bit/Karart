# KaRar CAD-to-BIM Platform Yol Haritası (Roadmap)

Bu yol haritası, 2D mimari DXF çizimlerinin deterministik algoritmalarla çözümlenerek tek doğruluk kaynağı olan Canonical BIM Model'e dönüştürülmesi ve bu modelden çıktı üretilmesini içeren 9 aşamalı standardı kapsar.

---

## 1. Parser (Giriş Katmanı - Kararlı)
- **Hassas Karakter ve Kodlama**: Türkçe karakter desteği (`cp1254`) ile DXF başlıklarının ve özniteliklerinin eksiksiz okunması.
- **Entity Ayrıştırma**: `LINE`, `ARC`, `LWPOLYLINE`, `TEXT`, `MTEXT` ve `INSERT` (bloklar) elemanlarının ayrıştırılarak ham JSON formatına (`dxf_raw.json`) aktarılması.

## 2. Geometry Engine (Çekirdek - Aktif Geliştirme / Optimizasyon)
- **Koordinat Normalizasyonu**: AutoCAD orijininden çok uzaktaki haritacılık koordinatlarının temizlenmesi ve çizimin ortak sıfır noktasına (`0,0`) taşınması.
- **Geometri Onarımı (Repair)**: Gürültü filtreleme, mikron seviyesindeki kısa çizgilerin elenmesi, üst üste binen mükerrer elemanların birleştirilmesi.
- **Duvar Eksenlerinin İndirgenmesi**: Çift çizgili duvarların kalibre edilmiş toleranslarla temiz tekil eksen çizgilerine (`walls_clean.json`) dönüştürülmesi.

## 3. Topology Engine (Çekirdek - Aktif Geliştirme / Optimizasyon)
- **Uç Nokta Kenetleme (Snapping)**: Milimetrik çizim boşluklarının matematiksel tolerans dahilinde kapatılması.
- **Kesişim Ayrıştırma (Split/Union)**: Duvar çizgilerinin kesişim noktalarından (T-birleşimi, köşe) bölünerek kararlı bir düğüm-kenar grafına dönüştürülmesi.
- **Poligonizasyon (Polygonize)**: Geometrik duvar döngülerinden kapalı oda alan sınırlarının (B-Rep sınırları) türetilmesi ve topolojik komşuluk matrisinin çıkarılması (`geometry_graph.json`).

## 4. Canonical BIM Model (Single Source of Truth - Aktif Geliştirme / Sıkılaştırma)
- **Ortak Sözleşme (Contract)**: Blender, IFC, WebGL ve tüm diğer tüketici katmanların besleneceği tek ve resmi doğrulanabilir JSON şeması sözleşmesi.
- **Tip Güvenliği**: TypeScript tip tanımlamaları ve Python doğrulama katmanlarıyla model bütünlüğünün her işlemde garanti edilmesi (`bim_clean.json`).

## 5. Semantic Enrichment (Aktif Geliştirme)
- **Taşıyıcı ve Bölücü Sınıflandırması**: Duvar kalınlıkları ve katman bilgilerine göre kolon, kiriş ve duvar elemanlarının ayrıştırılması.
- **Açıklık ve Boşluk Tespiti**: Duvar eksenleri üzerindeki kapı ve pencere boşluklarının geometrik analizi.
- **Mekansal Etiketleme**: Oda poligonlarının alan büyüklüğü ve mimari yerleşim kurallarına göre işlevsel olarak sınıflandırılması (Salon, Mutfak, vb.).

## 6. Blender Builder (Çıktı Üretici - Planlanan / Sadece Canonical Model Tüketicisi)
- **Parametrik Katı Modelleme**: Sadece kararlı Canonical BIM JSON modelini girdi alarak Blender Python API (`bpy`) üzerinden 3D B-Rep modellerinin türetilmesi.
- **Mesh Optimizasyonu**: WebGL için optimize edilmiş GLB/GLTF çıktı üretimi.

## 7. IFC Export (Çıktı Üretici - Planlanan / Sadece Canonical Model Tüketicisi)
- **openBIM Uyumluluğu**: Canonical BIM Model verisinden standart IFC (Industry Foundation Classes) şemasına parametrik veri dönüştürümü (`IfcOpenShell` entegrasyonu).

## 8. Engineering Dashboard (UI - Aktif Geliştirme)
- **Mühendislik İzleme Paneli**: Pazarlama veya bitmiş ürün odaklı değil; Geometry, Topology ve Canonical Model’in sağlık durumunu, test sonuçlarını, tolerans kalibrasyonlarını ve hata oranlarını gösteren teknik panel.

## 9. Cloud & Collaboration (Gelecek Planı)
- **Eş Zamanlı İş Birliği**: WebSockets üzerinden çoklu kullanıcı senkronizasyonu ve merkezi model kalite kontrolü.
