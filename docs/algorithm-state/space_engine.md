# Space Engine Durum Kartı

## Amaç
Topolojik ağdan geçerli oda/space üretmek ve gap closing stratejilerini kontrollü biçimde uygulamak.

## Giriş / Çıkış
- Giriş: topolojik ağ ve yüz adayları
- Çıkış: geçerli space listesi

## İnvariant'lar
- Geometriyi yeniden üretmez
- Gap closing denemeleri izlenebilir olmalıdır
- Çıktı deterministik ve testlenebilir olmalıdır

## Bilinen Riskler
- Açıklık kapatma eşiği büyüdükçe false-positive space üretimi riski artar
- Küçük planlarda 0 space çıktısı yanıltıcı olabilir

## Önce Okunacak Dosyalar
- `backend/space_engine.py`
- `backend/tests/test_modern_pipeline.py`

## Önce Çalıştırılacak Komut
- `npm run test:pipeline`
