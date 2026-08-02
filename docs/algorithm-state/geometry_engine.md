# Geometry Engine Durum Kartı

## Amaç
Ham CAD geometri verisini normalize etmek, gürültüyü temizlemek, kısa ve bozuk segmentleri ayıklamak ve topolojiye uygun temiz duvar segmentleri üretmek.

## Giriş / Çıkış
- Giriş: parser/ham DXF geometri verisi
- Çıkış: temizlenmiş wall segment listesi ve ara doğrulama çıktıları

## İnvariant'lar
- Semantik karar vermez
- Deterministik tolerans politikası kullanır
- Aynı girişte aynı temiz geometriyi üretir

## Bilinen Riskler
- Snap tolerance ve kısa segment onarımı veri setine duyarlı olabilir
- Dirty DXF çizimlerde gereksiz birleşme riski oluşabilir

## Önce Okunacak Dosyalar
- `backend/geometry_engine.py`
- `backend/tests/test_modern_pipeline.py`
- `backend/tests/benchmark_geometry.py`

## Önce Çalıştırılacak Komut
- `npm run test:geometry`
