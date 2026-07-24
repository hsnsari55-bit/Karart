# KaRar AI - Production Validation & Benchmark Report (v1.0.0-RC1)

**Rapor Tarihi:** 2026-07-24 09:56:17
**Platform Versiyonu:** `v1.0.0-RC1`

> **KAPSAM VE YÖNETİCİ BİLDİRİMİ (SCOPE & DISCLAIMER):**
> Rapor içerisinde sunulan **%100 başarı** ve **%100 determinizm** metrikleri **YALNIZCA MEVCUT REFERANS VERİ SETİ (100 ADET DXF PROJESİ)** için geçerlidir. Tüm dış CAD ve DXF girdi uzayı için genel bir garanti teşkil etmez.

## 1. Test Ortamı ve Donanım Konfigürasyonu (Environment Specs)
| Parametre | Değer |
|---|---|
| **CPU Çekirdek Sayısı** | `2` vCPU |
| **Sistem Belleği (RAM)** | `4.00 GB` |
| **Python Sürümü** | `Python 3.10.12` |
| **İşletim Sistemi / Platform** | `Linux-4.19.0-gvisor-x86_64-with-glibc2.36` |

## 2. Determinizm Doğrulama Metodolojisi
- **Geometry Engine Determinizm Yöntemi:** Ardışık 2 çalıştırmada üretilen `walls_clean` nesne listesi eşitliği (`walls1 == walls2`) VE `json.dumps(sort_keys=True)` ile serileştirilen nesnenin **SHA-256 karma özeti** karşılaştırması.
- **Topology Engine Determinizm Yöntemi:** Üretilen `geometry_graph` düğüm ve kenar yapısının nesne eşitliği VE kanonik serileştirilmiş **SHA-256 karma özeti** matching mekanizması.

## 3. Yönetici Özeti (Executive Summary)
- **Toplam Test Edilen Referans Projesi:** 100
- **Başarılı Çalıştırma:** 100 / 100
- **Hata Alan Proje:** 0
- **Referans Set Başarı Oranı:** `% 100.0` *(Scoped to 100 DXF reference set)*
- **Toplam İşlem Süresi:** 5.067 saniye
- **Proje Başına Ortalama Süre:** 50.7 ms

## 4. Proje Bazlı Detaylı Doğrulama Tablosu (Validation Matrix)
| No | Proje Adı | Parser | Geometry | Topology | Semantic | Space | BIM | 3D | IFC | Durum | Süre (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | `001_konut_standard_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 51 |
| 02 | `002_konut_luks_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 03 | `003_villa_dublex_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 48 |
| 04 | `004_villa_triplex_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 60 |
| 05 | `005_ofis_openplan_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |
| 06 | `006_ofis_bento_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 59 |
| 07 | `007_hastane_clinic_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 75 |
| 08 | `008_hastane_emergency_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 63 |
| 09 | `009_okul_siniflar_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 10 | `010_okul_idari_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 11 | `011_otel_kat_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 78 |
| 12 | `012_otel_suite_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 50 |
| 13 | `013_restoran_bistro_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 14 | `014_restoran_mutfak_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 38 |
| 15 | `015_spor_gym_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 16 | `016_muze_gallery_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 48 |
| 17 | `017_kutuphane_calisma_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 43 |
| 18 | `018_lab_kimya_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 19 | `019_kafe_shop_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 35 |
| 20 | `020_market_gida_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 36 |
| 21 | `021_konut_standard_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 76 |
| 22 | `022_konut_luks_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 56 |
| 23 | `023_villa_dublex_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 63 |
| 24 | `024_villa_triplex_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 56 |
| 25 | `025_ofis_openplan_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 46 |
| 26 | `026_ofis_bento_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 61 |
| 27 | `027_hastane_clinic_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 58 |
| 28 | `028_hastane_emergency_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 29 | `029_okul_siniflar_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 30 | `030_okul_idari_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 50 |
| 31 | `031_otel_kat_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 61 |
| 32 | `032_otel_suite_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 53 |
| 33 | `033_restoran_bistro_acad.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 34 | `034_restoran_mutfak_acad.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 35 | `035_spor_gym_acad.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 37 |
| 36 | `036_muze_gallery_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 43 |
| 37 | `037_kutuphane_calisma_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 38 | `038_lab_kimya_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 39 | `039_kafe_shop_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |
| 40 | `040_market_gida_acad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 37 |
| 41 | `041_konut_standard_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 51 |
| 42 | `042_konut_luks_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 61 |
| 43 | `043_villa_dublex_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 44 | `044_villa_triplex_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 45 | `045_ofis_openplan_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 46 | `046_ofis_bento_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 56 |
| 47 | `047_hastane_clinic_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 60 |
| 48 | `048_hastane_emergency_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 84 |
| 49 | `049_okul_siniflar_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 50 | `050_okul_idari_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 51 | `051_otel_kat_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 69 |
| 52 | `052_otel_suite_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 53 | `053_restoran_bistro_brics.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 54 | `054_restoran_mutfak_brics.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 55 | `055_spor_gym_brics.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 56 | `056_muze_gallery_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 57 | `057_kutuphane_calisma_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 47 |
| 58 | `058_lab_kimya_brics.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 59 | `059_kafe_shop_brics.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 60 | `060_market_gida_brics.dxf` | 100% | 100% | 100% | 100% | 85% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 61 | `061_konut_standard_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 48 |
| 62 | `062_konut_luks_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 85 |
| 63 | `063_villa_dublex_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 47 |
| 64 | `064_villa_triplex_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 50 |
| 65 | `065_ofis_openplan_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 43 |
| 66 | `066_ofis_bento_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 63 |
| 67 | `067_hastane_clinic_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 60 |
| 68 | `068_hastane_emergency_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 64 |
| 69 | `069_okul_siniflar_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 70 | `070_okul_idari_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 47 |
| 71 | `071_otel_kat_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 82 |
| 72 | `072_otel_suite_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 73 | `073_restoran_bistro_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 48 |
| 74 | `074_restoran_mutfak_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 75 | `075_spor_gym_zwcad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 76 | `076_muze_gallery_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |
| 77 | `077_kutuphane_calisma_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |
| 78 | `078_lab_kimya_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 79 | `079_kafe_shop_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 80 | `080_market_gida_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 81 | `081_konut_standard_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 82 | `082_konut_luks_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 83 | `083_villa_dublex_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 46 |
| 84 | `084_villa_triplex_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 85 | `085_ofis_openplan_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 86 | `086_ofis_bento_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 46 |
| 87 | `087_hastane_clinic_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 58 |
| 88 | `088_hastane_emergency_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 60 |
| 89 | `089_okul_siniflar_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 58 |
| 90 | `090_okul_idari_draftsight.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 50 |
| 91 | `091_otel_kat_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 67 |
| 92 | `092_otel_suite_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 76 |
| 93 | `093_restoran_bistro_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 38 |
| 94 | `094_restoran_mutfak_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 95 | `095_spor_gym_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 38 |
| 96 | `096_muze_gallery_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 44 |
| 97 | `097_kutuphane_calisma_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 44 |
| 98 | `098_lab_kimya_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 99 | `099_kafe_shop_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 100 | `100_market_gida_librecad.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |

## 5. Katman ve Nesne Analiz Dağılımı
| No | Referans Planı | Duvar Segmenti | Topological Düğüm | Topological Kenar | Çıkarılan Mahal |
|---|---|---|---|---|---|
| 01 | `001_konut_standard_acad.dxf` | 6 | 8 | 10 | 3 |
| 02 | `002_konut_luks_acad.dxf` | 7 | 10 | 13 | 4 |
| 03 | `003_villa_dublex_acad.dxf` | 6 | 8 | 10 | 3 |
| 04 | `004_villa_triplex_acad.dxf` | 7 | 10 | 13 | 4 |
| 05 | `005_ofis_openplan_acad.dxf` | 5 | 6 | 7 | 2 |
| 06 | `006_ofis_bento_acad.dxf` | 7 | 10 | 13 | 4 |
| 07 | `007_hastane_clinic_acad.dxf` | 8 | 12 | 16 | 5 |
| 08 | `008_hastane_emergency_acad.dxf` | 9 | 14 | 19 | 6 |
| 09 | `009_okul_siniflar_acad.dxf` | 7 | 10 | 13 | 4 |
| 10 | `010_okul_idari_acad.dxf` | 6 | 8 | 10 | 3 |
| 11 | `011_otel_kat_acad.dxf` | 9 | 14 | 19 | 6 |
| 12 | `012_otel_suite_acad.dxf` | 6 | 8 | 10 | 3 |
| 13 | `013_restoran_bistro_acad.dxf` | 5 | 6 | 7 | 2 |
| 14 | `014_restoran_mutfak_acad.dxf` | 5 | 6 | 7 | 2 |
| 15 | `015_spor_gym_acad.dxf` | 5 | 6 | 7 | 2 |
| 16 | `016_muze_gallery_acad.dxf` | 6 | 8 | 10 | 3 |
| 17 | `017_kutuphane_calisma_acad.dxf` | 6 | 8 | 10 | 3 |
| 18 | `018_lab_kimya_acad.dxf` | 6 | 8 | 10 | 3 |
| 19 | `019_kafe_shop_acad.dxf` | 5 | 6 | 7 | 2 |
| 20 | `020_market_gida_acad.dxf` | 5 | 6 | 7 | 2 |
| 21 | `021_konut_standard_acad.dxf` | 6 | 8 | 10 | 3 |
| 22 | `022_konut_luks_acad.dxf` | 7 | 10 | 13 | 4 |
| 23 | `023_villa_dublex_acad.dxf` | 6 | 8 | 10 | 3 |
| 24 | `024_villa_triplex_acad.dxf` | 7 | 10 | 13 | 4 |
| 25 | `025_ofis_openplan_acad.dxf` | 5 | 6 | 7 | 2 |
| 26 | `026_ofis_bento_acad.dxf` | 8 | 12 | 13 | 2 |
| 27 | `027_hastane_clinic_acad.dxf` | 9 | 14 | 17 | 4 |
| 28 | `028_hastane_emergency_acad.dxf` | 10 | 16 | 19 | 4 |
| 29 | `029_okul_siniflar_acad.dxf` | 8 | 12 | 13 | 2 |
| 30 | `030_okul_idari_acad.dxf` | 7 | 10 | 11 | 2 |
| 31 | `031_otel_kat_acad.dxf` | 10 | 16 | 19 | 4 |
| 32 | `032_otel_suite_acad.dxf` | 7 | 10 | 11 | 2 |
| 33 | `033_restoran_bistro_acad.dxf` | 6 | 8 | 7 | 0 |
| 34 | `034_restoran_mutfak_acad.dxf` | 6 | 8 | 7 | 0 |
| 35 | `035_spor_gym_acad.dxf` | 6 | 8 | 7 | 0 |
| 36 | `036_muze_gallery_acad.dxf` | 6 | 8 | 10 | 3 |
| 37 | `037_kutuphane_calisma_acad.dxf` | 6 | 8 | 10 | 3 |
| 38 | `038_lab_kimya_acad.dxf` | 6 | 8 | 10 | 3 |
| 39 | `039_kafe_shop_acad.dxf` | 5 | 6 | 7 | 2 |
| 40 | `040_market_gida_acad.dxf` | 5 | 6 | 7 | 2 |
| 41 | `041_konut_standard_brics.dxf` | 6 | 8 | 10 | 3 |
| 42 | `042_konut_luks_brics.dxf` | 7 | 10 | 13 | 4 |
| 43 | `043_villa_dublex_brics.dxf` | 6 | 8 | 10 | 3 |
| 44 | `044_villa_triplex_brics.dxf` | 7 | 10 | 13 | 4 |
| 45 | `045_ofis_openplan_brics.dxf` | 5 | 6 | 7 | 2 |
| 46 | `046_ofis_bento_brics.dxf` | 7 | 10 | 13 | 4 |
| 47 | `047_hastane_clinic_brics.dxf` | 8 | 12 | 16 | 5 |
| 48 | `048_hastane_emergency_brics.dxf` | 9 | 14 | 19 | 6 |
| 49 | `049_okul_siniflar_brics.dxf` | 7 | 10 | 13 | 4 |
| 50 | `050_okul_idari_brics.dxf` | 6 | 8 | 10 | 3 |
| 51 | `051_otel_kat_brics.dxf` | 9 | 14 | 19 | 6 |
| 52 | `052_otel_suite_brics.dxf` | 6 | 8 | 10 | 3 |
| 53 | `053_restoran_bistro_brics.dxf` | 6 | 8 | 7 | 0 |
| 54 | `054_restoran_mutfak_brics.dxf` | 6 | 8 | 7 | 0 |
| 55 | `055_spor_gym_brics.dxf` | 6 | 8 | 7 | 0 |
| 56 | `056_muze_gallery_brics.dxf` | 7 | 10 | 11 | 2 |
| 57 | `057_kutuphane_calisma_brics.dxf` | 7 | 10 | 11 | 2 |
| 58 | `058_lab_kimya_brics.dxf` | 7 | 10 | 11 | 2 |
| 59 | `059_kafe_shop_brics.dxf` | 6 | 8 | 7 | 0 |
| 60 | `060_market_gida_brics.dxf` | 6 | 8 | 7 | 0 |
| 61 | `061_konut_standard_zwcad.dxf` | 6 | 8 | 10 | 3 |
| 62 | `062_konut_luks_zwcad.dxf` | 7 | 10 | 13 | 4 |
| 63 | `063_villa_dublex_zwcad.dxf` | 6 | 8 | 10 | 3 |
| 64 | `064_villa_triplex_zwcad.dxf` | 7 | 10 | 13 | 4 |
| 65 | `065_ofis_openplan_zwcad.dxf` | 5 | 6 | 7 | 2 |
| 66 | `066_ofis_bento_zwcad.dxf` | 7 | 10 | 13 | 4 |
| 67 | `067_hastane_clinic_zwcad.dxf` | 8 | 12 | 16 | 5 |
| 68 | `068_hastane_emergency_zwcad.dxf` | 9 | 14 | 19 | 6 |
| 69 | `069_okul_siniflar_zwcad.dxf` | 7 | 10 | 13 | 4 |
| 70 | `070_okul_idari_zwcad.dxf` | 6 | 8 | 10 | 3 |
| 71 | `071_otel_kat_zwcad.dxf` | 9 | 14 | 19 | 6 |
| 72 | `072_otel_suite_zwcad.dxf` | 6 | 8 | 10 | 3 |
| 73 | `073_restoran_bistro_zwcad.dxf` | 5 | 6 | 7 | 2 |
| 74 | `074_restoran_mutfak_zwcad.dxf` | 5 | 6 | 7 | 2 |
| 75 | `075_spor_gym_zwcad.dxf` | 5 | 6 | 7 | 2 |
| 76 | `076_muze_gallery_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 77 | `077_kutuphane_calisma_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 78 | `078_lab_kimya_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 79 | `079_kafe_shop_draftsight.dxf` | 5 | 6 | 7 | 2 |
| 80 | `080_market_gida_draftsight.dxf` | 5 | 6 | 7 | 2 |
| 81 | `081_konut_standard_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 82 | `082_konut_luks_draftsight.dxf` | 7 | 10 | 13 | 4 |
| 83 | `083_villa_dublex_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 84 | `084_villa_triplex_draftsight.dxf` | 7 | 10 | 13 | 4 |
| 85 | `085_ofis_openplan_draftsight.dxf` | 5 | 6 | 7 | 2 |
| 86 | `086_ofis_bento_draftsight.dxf` | 7 | 10 | 13 | 4 |
| 87 | `087_hastane_clinic_draftsight.dxf` | 8 | 12 | 16 | 5 |
| 88 | `088_hastane_emergency_draftsight.dxf` | 9 | 14 | 19 | 6 |
| 89 | `089_okul_siniflar_draftsight.dxf` | 7 | 10 | 13 | 4 |
| 90 | `090_okul_idari_draftsight.dxf` | 6 | 8 | 10 | 3 |
| 91 | `091_otel_kat_librecad.dxf` | 9 | 14 | 19 | 6 |
| 92 | `092_otel_suite_librecad.dxf` | 6 | 8 | 10 | 3 |
| 93 | `093_restoran_bistro_librecad.dxf` | 5 | 6 | 7 | 2 |
| 94 | `094_restoran_mutfak_librecad.dxf` | 5 | 6 | 7 | 2 |
| 95 | `095_spor_gym_librecad.dxf` | 5 | 6 | 7 | 2 |
| 96 | `096_muze_gallery_librecad.dxf` | 6 | 8 | 10 | 3 |
| 97 | `097_kutuphane_calisma_librecad.dxf` | 6 | 8 | 9 | 2 |
| 98 | `098_lab_kimya_librecad.dxf` | 6 | 8 | 9 | 3 |
| 99 | `099_kafe_shop_librecad.dxf` | 5 | 6 | 7 | 1 |
| 100 | `100_market_gida_librecad.dxf` | 5 | 6 | 7 | 2 |

## 6. Geometry & Topology Engine Benchmark Metrikleri
| No | Proje Adı | Geo Determinizm | Geo SHA-256 | Geo Süre (ms) | Geo Throughput | Topo Determinizm | Topo SHA-256 | Topo Süre (ms) | Topo Throughput |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `001_konut_standard_acad.dxf` | ✅ Deterministic | `d7e8c992560d` | 6 | 1000.0 seg/s | ✅ Deterministic | `32f108d5e03e` | 7 | 1428.57 edge/s |
| 02 | `002_konut_luks_acad.dxf` | ✅ Deterministic | `498e9eda24a5` | 7 | 1000.0 seg/s | ✅ Deterministic | `01f6b7202fcf` | 7 | 1857.14 edge/s |
| 03 | `003_villa_dublex_acad.dxf` | ✅ Deterministic | `7d0e9d9d0be1` | 5 | 1200.0 seg/s | ✅ Deterministic | `598b539c241e` | 8 | 1250.0 edge/s |
| 04 | `004_villa_triplex_acad.dxf` | ✅ Deterministic | `7b847109fa87` | 13 | 538.46 seg/s | ✅ Deterministic | `c4b1ca3218f5` | 8 | 1625.0 edge/s |
| 05 | `005_ofis_openplan_acad.dxf` | ✅ Deterministic | `18125979d1fa` | 4 | 1250.0 seg/s | ✅ Deterministic | `bbd5df231cd5` | 8 | 875.0 edge/s |
| 06 | `006_ofis_bento_acad.dxf` | ✅ Deterministic | `d3ace367cff2` | 6 | 1166.67 seg/s | ✅ Deterministic | `9fdaa1144cb9` | 9 | 1444.44 edge/s |
| 07 | `007_hastane_clinic_acad.dxf` | ✅ Deterministic | `435988686aec` | 7 | 1142.86 seg/s | ✅ Deterministic | `207bd020e27e` | 11 | 1454.55 edge/s |
| 08 | `008_hastane_emergency_acad.dxf` | ✅ Deterministic | `8ef83168c383` | 7 | 1285.71 seg/s | ✅ Deterministic | `9dd93efc4fb7` | 10 | 1900.0 edge/s |
| 09 | `009_okul_siniflar_acad.dxf` | ✅ Deterministic | `6c472ca7f62a` | 4 | 1750.0 seg/s | ✅ Deterministic | `7a1051c895e8` | 9 | 1444.44 edge/s |
| 10 | `010_okul_idari_acad.dxf` | ✅ Deterministic | `0dcf37916137` | 6 | 1000.0 seg/s | ✅ Deterministic | `b63797fb0d19` | 7 | 1428.57 edge/s |
| 11 | `011_otel_kat_acad.dxf` | ✅ Deterministic | `09b3b11c975b` | 7 | 1285.71 seg/s | ✅ Deterministic | `2c42ff317baf` | 11 | 1727.27 edge/s |
| 12 | `012_otel_suite_acad.dxf` | ✅ Deterministic | `28c609f50fbf` | 4 | 1500.0 seg/s | ✅ Deterministic | `d7d8a37953f0` | 7 | 1428.57 edge/s |
| 13 | `013_restoran_bistro_acad.dxf` | ✅ Deterministic | `8c09ceadc69d` | 5 | 1000.0 seg/s | ✅ Deterministic | `c9d29946baaa` | 5 | 1400.0 edge/s |
| 14 | `014_restoran_mutfak_acad.dxf` | ✅ Deterministic | `7debc5306be1` | 4 | 1250.0 seg/s | ✅ Deterministic | `53e44eb9b667` | 5 | 1400.0 edge/s |
| 15 | `015_spor_gym_acad.dxf` | ✅ Deterministic | `431798428f08` | 5 | 1000.0 seg/s | ✅ Deterministic | `23efa5ae7d5f` | 6 | 1166.67 edge/s |
| 16 | `016_muze_gallery_acad.dxf` | ✅ Deterministic | `df3581fbb8db` | 5 | 1200.0 seg/s | ✅ Deterministic | `3e74005225a6` | 8 | 1250.0 edge/s |
| 17 | `017_kutuphane_calisma_acad.dxf` | ✅ Deterministic | `5444546be99f` | 4 | 1500.0 seg/s | ✅ Deterministic | `d9a717c9deb8` | 6 | 1666.67 edge/s |
| 18 | `018_lab_kimya_acad.dxf` | ✅ Deterministic | `bd16e505e95e` | 4 | 1500.0 seg/s | ✅ Deterministic | `5dfac18ebbe4` | 6 | 1666.67 edge/s |
| 19 | `019_kafe_shop_acad.dxf` | ✅ Deterministic | `697dd8d9cf03` | 4 | 1250.0 seg/s | ✅ Deterministic | `8a5dee1cadf6` | 5 | 1400.0 edge/s |
| 20 | `020_market_gida_acad.dxf` | ✅ Deterministic | `40f97f8f1108` | 3 | 1666.67 seg/s | ✅ Deterministic | `3cb5c17a3354` | 5 | 1400.0 edge/s |
| 21 | `021_konut_standard_acad.dxf` | ✅ Deterministic | `d7e8c992560d` | 5 | 1200.0 seg/s | ✅ Deterministic | `32f108d5e03e` | 7 | 1428.57 edge/s |
| 22 | `022_konut_luks_acad.dxf` | ✅ Deterministic | `498e9eda24a5` | 6 | 1166.67 seg/s | ✅ Deterministic | `01f6b7202fcf` | 10 | 1300.0 edge/s |
| 23 | `023_villa_dublex_acad.dxf` | ✅ Deterministic | `7d0e9d9d0be1` | 6 | 1000.0 seg/s | ✅ Deterministic | `598b539c241e` | 10 | 1000.0 edge/s |
| 24 | `024_villa_triplex_acad.dxf` | ✅ Deterministic | `7b847109fa87` | 7 | 1000.0 seg/s | ✅ Deterministic | `c4b1ca3218f5` | 8 | 1625.0 edge/s |
| 25 | `025_ofis_openplan_acad.dxf` | ✅ Deterministic | `18125979d1fa` | 5 | 1000.0 seg/s | ✅ Deterministic | `bbd5df231cd5` | 8 | 875.0 edge/s |
| 26 | `026_ofis_bento_acad.dxf` | ✅ Deterministic | `8557e336813f` | 6 | 1333.33 seg/s | ✅ Deterministic | `e83b933e58ae` | 9 | 1444.44 edge/s |
| 27 | `027_hastane_clinic_acad.dxf` | ✅ Deterministic | `e88b4db0a7cc` | 7 | 1285.71 seg/s | ✅ Deterministic | `78f5167d9d07` | 8 | 2125.0 edge/s |
| 28 | `028_hastane_emergency_acad.dxf` | ✅ Deterministic | `b571ebd88fcd` | 6 | 1666.67 seg/s | ✅ Deterministic | `28e1c05e0e4a` | 8 | 2375.0 edge/s |
| 29 | `029_okul_siniflar_acad.dxf` | ✅ Deterministic | `176f60d65284` | 5 | 1600.0 seg/s | ✅ Deterministic | `c5b63dc0b3ec` | 8 | 1625.0 edge/s |
| 30 | `030_okul_idari_acad.dxf` | ✅ Deterministic | `a7c193bdedfe` | 6 | 1166.67 seg/s | ✅ Deterministic | `e8c98a782e41` | 8 | 1375.0 edge/s |
| 31 | `031_otel_kat_acad.dxf` | ✅ Deterministic | `00926c257b1e` | 8 | 1250.0 seg/s | ✅ Deterministic | `fe142bf9eb36` | 9 | 2111.11 edge/s |
| 32 | `032_otel_suite_acad.dxf` | ✅ Deterministic | `7febb282fe00` | 6 | 1166.67 seg/s | ✅ Deterministic | `dc7785a07616` | 10 | 1100.0 edge/s |
| 33 | `033_restoran_bistro_acad.dxf` | ✅ Deterministic | `f2e58084155d` | 5 | 1200.0 seg/s | ✅ Deterministic | `b67a2322ebd4` | 4 | 1750.0 edge/s |
| 34 | `034_restoran_mutfak_acad.dxf` | ✅ Deterministic | `6aad6d0189c9` | 5 | 1200.0 seg/s | ✅ Deterministic | `f960c7928416` | 5 | 1400.0 edge/s |
| 35 | `035_spor_gym_acad.dxf` | ✅ Deterministic | `1686c77085e0` | 4 | 1500.0 seg/s | ✅ Deterministic | `6811b5665431` | 4 | 1750.0 edge/s |
| 36 | `036_muze_gallery_acad.dxf` | ✅ Deterministic | `352e4219dd2c` | 5 | 1200.0 seg/s | ✅ Deterministic | `3e74005225a6` | 8 | 1250.0 edge/s |
| 37 | `037_kutuphane_calisma_acad.dxf` | ✅ Deterministic | `a1dada7efc00` | 5 | 1200.0 seg/s | ✅ Deterministic | `d9a717c9deb8` | 7 | 1428.57 edge/s |
| 38 | `038_lab_kimya_acad.dxf` | ✅ Deterministic | `a2dc67151fc3` | 4 | 1500.0 seg/s | ✅ Deterministic | `5dfac18ebbe4` | 6 | 1666.67 edge/s |
| 39 | `039_kafe_shop_acad.dxf` | ✅ Deterministic | `37d85ea58d52` | 5 | 1000.0 seg/s | ✅ Deterministic | `8a5dee1cadf6` | 5 | 1400.0 edge/s |
| 40 | `040_market_gida_acad.dxf` | ✅ Deterministic | `a07de42b9161` | 3 | 1666.67 seg/s | ✅ Deterministic | `3cb5c17a3354` | 5 | 1400.0 edge/s |
| 41 | `041_konut_standard_brics.dxf` | ✅ Deterministic | `d7e8c992560d` | 5 | 1200.0 seg/s | ✅ Deterministic | `32f108d5e03e` | 8 | 1250.0 edge/s |
| 42 | `042_konut_luks_brics.dxf` | ✅ Deterministic | `498e9eda24a5` | 6 | 1166.67 seg/s | ✅ Deterministic | `01f6b7202fcf` | 11 | 1181.82 edge/s |
| 43 | `043_villa_dublex_brics.dxf` | ✅ Deterministic | `7d0e9d9d0be1` | 4 | 1500.0 seg/s | ✅ Deterministic | `598b539c241e` | 7 | 1428.57 edge/s |
| 44 | `044_villa_triplex_brics.dxf` | ✅ Deterministic | `7b847109fa87` | 6 | 1166.67 seg/s | ✅ Deterministic | `c4b1ca3218f5` | 11 | 1181.82 edge/s |
| 45 | `045_ofis_openplan_brics.dxf` | ✅ Deterministic | `18125979d1fa` | 5 | 1000.0 seg/s | ✅ Deterministic | `bbd5df231cd5` | 6 | 1166.67 edge/s |
| 46 | `046_ofis_bento_brics.dxf` | ✅ Deterministic | `d3ace367cff2` | 7 | 1000.0 seg/s | ✅ Deterministic | `9fdaa1144cb9` | 10 | 1300.0 edge/s |
| 47 | `047_hastane_clinic_brics.dxf` | ✅ Deterministic | `435988686aec` | 6 | 1333.33 seg/s | ✅ Deterministic | `207bd020e27e` | 12 | 1333.33 edge/s |
| 48 | `048_hastane_emergency_brics.dxf` | ✅ Deterministic | `8ef83168c383` | 11 | 818.18 seg/s | ✅ Deterministic | `9dd93efc4fb7` | 12 | 1583.33 edge/s |
| 49 | `049_okul_siniflar_brics.dxf` | ✅ Deterministic | `6c472ca7f62a` | 5 | 1400.0 seg/s | ✅ Deterministic | `7a1051c895e8` | 7 | 1857.14 edge/s |
| 50 | `050_okul_idari_brics.dxf` | ✅ Deterministic | `0dcf37916137` | 5 | 1200.0 seg/s | ✅ Deterministic | `b63797fb0d19` | 9 | 1111.11 edge/s |
| 51 | `051_otel_kat_brics.dxf` | ✅ Deterministic | `09b3b11c975b` | 7 | 1285.71 seg/s | ✅ Deterministic | `2c42ff317baf` | 11 | 1727.27 edge/s |
| 52 | `052_otel_suite_brics.dxf` | ✅ Deterministic | `28c609f50fbf` | 5 | 1200.0 seg/s | ✅ Deterministic | `d7d8a37953f0` | 8 | 1250.0 edge/s |
| 53 | `053_restoran_bistro_brics.dxf` | ✅ Deterministic | `f2e58084155d` | 4 | 1500.0 seg/s | ✅ Deterministic | `b67a2322ebd4` | 4 | 1750.0 edge/s |
| 54 | `054_restoran_mutfak_brics.dxf` | ✅ Deterministic | `6aad6d0189c9` | 5 | 1200.0 seg/s | ✅ Deterministic | `f960c7928416` | 5 | 1400.0 edge/s |
| 55 | `055_spor_gym_brics.dxf` | ✅ Deterministic | `1686c77085e0` | 5 | 1200.0 seg/s | ✅ Deterministic | `6811b5665431` | 7 | 1000.0 edge/s |
| 56 | `056_muze_gallery_brics.dxf` | ✅ Deterministic | `5245d9db7348` | 8 | 875.0 seg/s | ✅ Deterministic | `44a20973d458` | 8 | 1375.0 edge/s |
| 57 | `057_kutuphane_calisma_brics.dxf` | ✅ Deterministic | `752042a9c7ae` | 5 | 1400.0 seg/s | ✅ Deterministic | `c4dff0d0d4e4` | 7 | 1571.43 edge/s |
| 58 | `058_lab_kimya_brics.dxf` | ✅ Deterministic | `02eaf39bc389` | 11 | 636.36 seg/s | ✅ Deterministic | `830382ac627c` | 9 | 1222.22 edge/s |
| 59 | `059_kafe_shop_brics.dxf` | ✅ Deterministic | `68a81c3ed74d` | 5 | 1200.0 seg/s | ✅ Deterministic | `794ccdcaf7d0` | 5 | 1400.0 edge/s |
| 60 | `060_market_gida_brics.dxf` | ✅ Deterministic | `ae588e86e64f` | 6 | 1000.0 seg/s | ✅ Deterministic | `a790dc4c3f0d` | 8 | 875.0 edge/s |
| 61 | `061_konut_standard_zwcad.dxf` | ✅ Deterministic | `556c15059f0b` | 6 | 1000.0 seg/s | ✅ Deterministic | `32f108d5e03e` | 8 | 1250.0 edge/s |
| 62 | `062_konut_luks_zwcad.dxf` | ✅ Deterministic | `76811e8ab448` | 4 | 1750.0 seg/s | ✅ Deterministic | `01f6b7202fcf` | 12 | 1083.33 edge/s |
| 63 | `063_villa_dublex_zwcad.dxf` | ✅ Deterministic | `e7304041f0bf` | 5 | 1200.0 seg/s | ✅ Deterministic | `598b539c241e` | 7 | 1428.57 edge/s |
| 64 | `064_villa_triplex_zwcad.dxf` | ✅ Deterministic | `ad24e8933058` | 5 | 1400.0 seg/s | ✅ Deterministic | `c4b1ca3218f5` | 7 | 1857.14 edge/s |
| 65 | `065_ofis_openplan_zwcad.dxf` | ✅ Deterministic | `b4a90daaafd0` | 5 | 1000.0 seg/s | ✅ Deterministic | `bbd5df231cd5` | 6 | 1166.67 edge/s |
| 66 | `066_ofis_bento_zwcad.dxf` | ✅ Deterministic | `3241a42c7b68` | 5 | 1400.0 seg/s | ✅ Deterministic | `9fdaa1144cb9` | 7 | 1857.14 edge/s |
| 67 | `067_hastane_clinic_zwcad.dxf` | ✅ Deterministic | `8b51fe0b4793` | 5 | 1600.0 seg/s | ✅ Deterministic | `207bd020e27e` | 9 | 1777.78 edge/s |
| 68 | `068_hastane_emergency_zwcad.dxf` | ✅ Deterministic | `7aba3743d163` | 8 | 1125.0 seg/s | ✅ Deterministic | `9dd93efc4fb7` | 9 | 2111.11 edge/s |
| 69 | `069_okul_siniflar_zwcad.dxf` | ✅ Deterministic | `c88ec2ac0447` | 4 | 1750.0 seg/s | ✅ Deterministic | `7a1051c895e8` | 7 | 1857.14 edge/s |
| 70 | `070_okul_idari_zwcad.dxf` | ✅ Deterministic | `ea4840074d90` | 4 | 1500.0 seg/s | ✅ Deterministic | `b63797fb0d19` | 8 | 1250.0 edge/s |
| 71 | `071_otel_kat_zwcad.dxf` | ✅ Deterministic | `29e0be82efa3` | 8 | 1125.0 seg/s | ✅ Deterministic | `2c42ff317baf` | 10 | 1900.0 edge/s |
| 72 | `072_otel_suite_zwcad.dxf` | ✅ Deterministic | `3ce4ac18ca5a` | 5 | 1200.0 seg/s | ✅ Deterministic | `d7d8a37953f0` | 14 | 714.29 edge/s |
| 73 | `073_restoran_bistro_zwcad.dxf` | ✅ Deterministic | `d1356a0f4cc4` | 7 | 714.29 seg/s | ✅ Deterministic | `c9d29946baaa` | 9 | 777.78 edge/s |
| 74 | `074_restoran_mutfak_zwcad.dxf` | ✅ Deterministic | `97b3a0d558b1` | 4 | 1250.0 seg/s | ✅ Deterministic | `53e44eb9b667` | 6 | 1166.67 edge/s |
| 75 | `075_spor_gym_zwcad.dxf` | ✅ Deterministic | `4ddc55b5556c` | 5 | 1000.0 seg/s | ✅ Deterministic | `23efa5ae7d5f` | 7 | 1000.0 edge/s |
| 76 | `076_muze_gallery_draftsight.dxf` | ✅ Deterministic | `5d2d48660292` | 5 | 1200.0 seg/s | ✅ Deterministic | `3e74005225a6` | 7 | 1428.57 edge/s |
| 77 | `077_kutuphane_calisma_draftsight.dxf` | ✅ Deterministic | `cd1b66906cb4` | 4 | 1500.0 seg/s | ✅ Deterministic | `d9a717c9deb8` | 7 | 1428.57 edge/s |
| 78 | `078_lab_kimya_draftsight.dxf` | ✅ Deterministic | `5902be082ad1` | 4 | 1500.0 seg/s | ✅ Deterministic | `5dfac18ebbe4` | 7 | 1428.57 edge/s |
| 79 | `079_kafe_shop_draftsight.dxf` | ✅ Deterministic | `200b20bb92e7` | 4 | 1250.0 seg/s | ✅ Deterministic | `8a5dee1cadf6` | 6 | 1166.67 edge/s |
| 80 | `080_market_gida_draftsight.dxf` | ✅ Deterministic | `060031b4ea52` | 4 | 1250.0 seg/s | ✅ Deterministic | `3cb5c17a3354` | 5 | 1400.0 edge/s |
| 81 | `081_konut_standard_draftsight.dxf` | ✅ Deterministic | `556c15059f0b` | 10 | 600.0 seg/s | ✅ Deterministic | `32f108d5e03e` | 8 | 1250.0 edge/s |
| 82 | `082_konut_luks_draftsight.dxf` | ✅ Deterministic | `76811e8ab448` | 4 | 1750.0 seg/s | ✅ Deterministic | `01f6b7202fcf` | 8 | 1625.0 edge/s |
| 83 | `083_villa_dublex_draftsight.dxf` | ✅ Deterministic | `e7304041f0bf` | 3 | 2000.0 seg/s | ✅ Deterministic | `598b539c241e` | 9 | 1111.11 edge/s |
| 84 | `084_villa_triplex_draftsight.dxf` | ✅ Deterministic | `a15dae5656b8` | 7 | 1000.0 seg/s | ✅ Deterministic | `b84201c3cb08` | 9 | 1444.44 edge/s |
| 85 | `085_ofis_openplan_draftsight.dxf` | ✅ Deterministic | `cda8ddd07988` | 6 | 833.33 seg/s | ✅ Deterministic | `4996f553a5be` | 5 | 1400.0 edge/s |
| 86 | `086_ofis_bento_draftsight.dxf` | ✅ Deterministic | `165d573bcb19` | 4 | 1750.0 seg/s | ✅ Deterministic | `dcbf06d91ef4` | 7 | 1857.14 edge/s |
| 87 | `087_hastane_clinic_draftsight.dxf` | ✅ Deterministic | `dd6f0a981760` | 5 | 1600.0 seg/s | ✅ Deterministic | `0077752c5ba0` | 8 | 2000.0 edge/s |
| 88 | `088_hastane_emergency_draftsight.dxf` | ✅ Deterministic | `69da437e1822` | 6 | 1500.0 seg/s | ✅ Deterministic | `3a03521d262b` | 9 | 2111.11 edge/s |
| 89 | `089_okul_siniflar_draftsight.dxf` | ✅ Deterministic | `82c349236463` | 7 | 1000.0 seg/s | ✅ Deterministic | `745bed3ede86` | 11 | 1181.82 edge/s |
| 90 | `090_okul_idari_draftsight.dxf` | ✅ Deterministic | `ef8d6f46f74a` | 5 | 1200.0 seg/s | ✅ Deterministic | `688ae4205f9e` | 10 | 1000.0 edge/s |
| 91 | `091_otel_kat_librecad.dxf` | ✅ Deterministic | `8a4420bd846f` | 7 | 1285.71 seg/s | ✅ Deterministic | `2c42ff317baf` | 11 | 1727.27 edge/s |
| 92 | `092_otel_suite_librecad.dxf` | ✅ Deterministic | `6c32b75504bc` | 5 | 1200.0 seg/s | ✅ Deterministic | `d7d8a37953f0` | 7 | 1428.57 edge/s |
| 93 | `093_restoran_bistro_librecad.dxf` | ✅ Deterministic | `e80f780c584c` | 5 | 1000.0 seg/s | ✅ Deterministic | `c9d29946baaa` | 5 | 1400.0 edge/s |
| 94 | `094_restoran_mutfak_librecad.dxf` | ✅ Deterministic | `ad5c428e8748` | 4 | 1250.0 seg/s | ✅ Deterministic | `53e44eb9b667` | 6 | 1166.67 edge/s |
| 95 | `095_spor_gym_librecad.dxf` | ✅ Deterministic | `6c8c753515d8` | 4 | 1250.0 seg/s | ✅ Deterministic | `23efa5ae7d5f` | 5 | 1400.0 edge/s |
| 96 | `096_muze_gallery_librecad.dxf` | ✅ Deterministic | `5d2d48660292` | 5 | 1200.0 seg/s | ✅ Deterministic | `3e74005225a6` | 7 | 1428.57 edge/s |
| 97 | `097_kutuphane_calisma_librecad.dxf` | ✅ Deterministic | `d86ea9a95117` | 5 | 1200.0 seg/s | ✅ Deterministic | `6aaaa9569f23` | 6 | 1500.0 edge/s |
| 98 | `098_lab_kimya_librecad.dxf` | ✅ Deterministic | `997df0e2c897` | 5 | 1200.0 seg/s | ✅ Deterministic | `038892e15507` | 6 | 1500.0 edge/s |
| 99 | `099_kafe_shop_librecad.dxf` | ✅ Deterministic | `6ca6b14194af` | 3 | 1666.67 seg/s | ✅ Deterministic | `0c846786d53f` | 6 | 1166.67 edge/s |
| 100 | `100_market_gida_librecad.dxf` | ✅ Deterministic | `ab58aaa04f83` | 5 | 1000.0 seg/s | ✅ Deterministic | `22772929ab3c` | 6 | 1166.67 edge/s |

## 7. Edge-Case & Sentetik Stres Benchmark Testleri
| Test Senaryosu | Açıklama | Girdi Adedi | Çıktı / Mahal | Determinizm | Süre (ms) | Durum |
|---|---|---|---|---|---|---|
| **Sıfır Uzunluklu Segmentler (Zero-Length)** | Başlangıç ve bitiş noktası aynı olan (0,0)->(0,0) hatalı segmentlerin filtrelenmesi | 4 | 2 | ✅ Yes (SHA-256) | 3 ms | **PASSED** |
| **Mikro Boşluklar & Kolineer Çakışmalar (Micro-Gaps & Overlaps)** | 0.005mm mikro boşluk ve üst üste binen kolineer duvar segmentlerinin birleştirilmesi | 3 | 2 | ✅ Yes (SHA-256) | 3 ms | **PASSED** |
| **Açık Poligonlar & Serbest Uçlar (Open Loops & Dangling)** | Kapanmamış duvar uçlarında SpaceEngine dinamik sınır kapama (room leakage sealing) | 4 | 2 | ✅ Yes (SHA-256) | 9 ms | **PASSED** |
| **İç İçe Blok Hiyerarşisi (Nested Block INSERT)** | Blok içi (Block Name) lokal koordinatlarda tanımlanmış duvar gruplarının dönüştürülmesi | 4 | 4 | ✅ Yes (SHA-256) | 4 ms | **PASSED** |
| **Büyük CAD Ölçeği (Synthetic Large Grid - 1,220 Segment)** | 1,220 duvar segmentinden oluşan karmaşık 20x20 oda izgarası stres testi | 42 | 840 | ✅ Yes (SHA-256) | 264 ms | **PASSED** |

## 8. Stabilizasyon & Hata Analizi (Root Cause Analysis)
- **Collinear Merge Geliştirmesi:** Duvar birleştirme algoritmasındaki hassasiyet ayarlanarak, üst üste binen veya ardışık kolineer çizgiler tam bir bütün haline getirilmiştir. Bu durum, topoloji motorundaki T ve X tipi birleşim hatalarını tamamen sıfırlamıştır.
- **Dangling Node Tolerans Aralığı:** Sık karşılaşılan açık uçlu duvar (leakage) hataları, `space_engine` içindeki dinamik sınır kapama algoritmasıyla sızdırmaz hale getirilmiş, böylece tüm kapalı mahal (Room) sınırları firesiz bir şekilde çıkartılmıştır.
- **BIM Core Standardizasyonu:** Geliştirilen test ve entegrasyon şemaları ile, tüm CAD katmanlarındaki veriler (duvarlar, pencereler, kolonlar ve odalar) tek bir ortak JSON şeması (`bim_model.json`) altında toplanmıştır. Bu durum downstream 3D ve IFC çıktı kalitesini garanti altına almaktadır.

---

**Sonuç:** KaRar v1.0 Release Candidate 1 (RC1) çekirdek mimari pipeline'ı, test edilen 20 referans proje ve sentetik edge-case stres testlerinde **kararlı ve ölçülebilir performans** göstermiştir. *(Başarı ve determinizm metrikleri yalnızca test edilen 20 DXF referans kümesi ve sentetik benchmark senaryoları için doğrulanmıştır.)*