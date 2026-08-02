# Canonical BIM Core Durum Kartı

## Amaç
Geometry, Topology ve Space/Semantic çıktılarını tek doğruluk kaynağı olan Canonical BIM Model altında toplamak.

## Giriş / Çıkış
- Giriş: doğrulanmış çekirdek motor çıktıları
- Çıkış: canonical BIM JSON ve ilişkisel varlık grafı

## İnvariant'lar
- Tek SSoT kaynağıdır
- Çıktı sırası/hash deterministik olmalıdır
- Downstream katmanlar kendi geometri varsayımı üretmemelidir

## Bilinen Riskler
- Opening ownership ve parent wall ilişkileri regresyonlara açık olabilir
- Şema genişlemesi backward-compatibility riskleri doğurabilir

## Önce Okunacak Dosyalar
- `backend/bim_core.py`
- `backend/tests/test_regression_bim_core_opening_parent_wall.py`
- `backend/tests/test_modern_pipeline.py`

## Önce Çalıştırılacak Komut
- `npm run test:bim`
