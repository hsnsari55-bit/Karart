# KaRar Project State

## Current Status
- **GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf** gerçek mimari projesi üzerinde çekirdek boru hattı (pipeline) verileri çıkartılmış ve doğrulanmıştır.
- Çekirdek geometri ve topoloji çıktıları (`outputs/dxf_raw.json`, `outputs/walls_clean.json`, `outputs/geometry_graph.json`, `outputs/bim_clean.json`) oluşturulmuş ve arayüze bağlanmıştır.
- Ancak, tüm sistemin kararlı ve %100 deterministik çalışması için **Geometri Motoru (Geometry Engine)**, **Topoloji Motoru (Topology Engine)**, **Canonical BIM Model** sözleşmesi ve **Test Stratejisi** aktif geliştirme ve optimizasyon aşamasındadır.

## Progress Summary (Aktif Geliştirme Alanları)
1. **Geometry Engine (Aktif / Geliştiriliyor)**:
   - AutoCAD koordinatlarının ortak orijine normalizasyonu, gürültü temizliği ve kısa çizgilerin elenmesi (Repair).
   - Gerçek DXF analizi kapsamında: toplam okunan 102.191 grup kodu çiftinden 633 adet normalize edilmiş geometri segmenti.
2. **Topology Engine (Aktif / Geliştiriliyor)**:
   - Duvar çizgileri arasında kenetleme (Snapping) ve kapalı oda poligonlarının tespiti.
   - Topolojik ağ yapısının kurulması (94 Düğüm, 321 Kenar).
3. **Semantic Enrichment (Planlandı / Geliştiriliyor)**:
   - Geometrik ve topolojik verilere göre kapı, pencere, kolon ayrımı ve oda işlevlerinin etiketlenmesi.
4. **Canonical BIM Model (Aktif / Geliştiriliyor)**:
   - Blender, IFC ve arayüzün besleneceği tek doğruluk kaynağı olan resmi JSON Şeması sözleşmesi.
5. **Pipeline Contract & Test Strategy (Aktif / Geliştiriliyor)**:
   - Katmanlar arası otomatik geçişlerin birim (Unit) ve entegrasyon testleriyle doğrulanması.

## Next Steps
- Geometri ve topoloji algoritmalarındaki kenetleme (snapping) hassasiyetini ve kapalı poligon bulma determinizmini artırmak.
- Canonical BIM JSON model şemasını sıkılaştırmak ve TypeScript arayüz tipleri ile korumak.
- Blender 3D Builder ve IFC Export modüllerini, ancak Canonical BIM Model tamamen kararlı hale geldikten sonra bu ortak sözleşme üzerinden inşa etmek.
- UI ve bulut özelliklerini, çekirdek motor tamamen olgunlaşana dek salt görselleştirme katmanı olarak tutmak.

## Resolved & Archived Technical Debts
- **[RESOLVED & ARCHIVED] Sabit Windows Yolları (Hardcoded C:\ Paths)**: `backend/bim_validator.py`, `backend/geometry_validator.py` ve `backend/geometry_core.py` içindeki Windows odaklı mutlak dosya yolları kaldırıldı. Dinamik, çoklu platform uyumlu `PathManager` entegrasyonu sağlandı.
- **[RESOLVED & ARCHIVED] Kırık Birim Testleri (Broken Unit Tests & Imports)**: `backend/window_detector.py` içindeki eksik `config` kütüphanesi ve `DXF` import hatası nedeniyle çöken test süiti tamamen onarıldı. `python3 -m unittest` komutuyla 31 adet birim testinin tamamı başarıyla yeşile döndürüldü (`OK`).


