# KaRar AI - Production Validation & Benchmark Report (v1.0.0-RC1)

**Rapor Tarihi:** 2026-07-22 19:14:49
**Platform Versiyonu:** `v1.0.0-RC1`

> **KAPSAM VE YÖNETİCİ BİLDİRİMİ (SCOPE & DISCLAIMER):**
> Rapor içerisinde sunulan **%100 başarı** ve **%100 determinizm** metrikleri **YALNIZCA MEVCUT REFERANS VERİ SETİ (20 ADET DXF PROJESİ)** için geçerlidir. Tüm dış CAD ve DXF girdi uzayı için genel bir garanti teşkil etmez.

## 1. Test Ortamı ve Donanım Konfigürasyonu (Environment Specs)
| Parametre | Değer |
|---|---|
| **CPU Çekirdek Sayısı** | `2` vCPU |
| **Sistem Belleği (RAM)** | `4.00 GB` |
| **Python Sürümü** | `Python 3.11.2` |
| **İşletim Sistemi / Platform** | `Linux-4.19.0-gvisor-x86_64-with-glibc2.36` |

## 2. Determinizm Doğrulama Metodolojisi
- **Geometry Engine Determinizm Yöntemi:** Ardışık 2 çalıştırmada üretilen `walls_clean` nesne listesi eşitliği (`walls1 == walls2`) VE `json.dumps(sort_keys=True)` ile serileştirilen nesnenin **SHA-256 karma özeti** karşılaştırması.
- **Topology Engine Determinizm Yöntemi:** Üretilen `geometry_graph` düğüm ve kenar yapısının nesne eşitliği VE kanonik serileştirilmiş **SHA-256 karma özeti** matching mekanizması.

## 3. Yönetici Özeti (Executive Summary)
- **Toplam Test Edilen Referans Projesi:** 20
- **Başarılı Çalıştırma:** 20 / 20
- **Hata Alan Proje:** 0
- **Referans Set Başarı Oranı:** `% 100.0` *(Scoped to 20 DXF reference set)*
- **Toplam İşlem Süresi:** 0.975 saniye
- **Proje Başına Ortalama Süre:** 48.8 ms

## 4. Proje Bazlı Detaylı Doğrulama Tablosu (Validation Matrix)
| No | Proje Adı | Parser | Geometry | Topology | Semantic | Space | BIM | 3D | IFC | Durum | Süre (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | `01_konut_standard.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 02 | `02_konut_luks.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 03 | `03_villa_dublex.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 46 |
| 04 | `04_villa_triplex.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 05 | `05_ofis_openplan.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 40 |
| 06 | `06_ofis_bento.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 50 |
| 07 | `07_hastane_clinic.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 55 |
| 08 | `08_hastane_emergency.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 61 |
| 09 | `09_okul_siniflar.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 62 |
| 10 | `10_okul_idari.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 11 | `11_otel_kat.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 67 |
| 12 | `12_otel_suite.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 45 |
| 13 | `13_restoran_bistro.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 14 | `14_restoran_mutfak.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 43 |
| 15 | `15_spor_gym.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |
| 16 | `16_muze_gallery.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 44 |
| 17 | `17_kutuphane_calisma.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 48 |
| 18 | `18_lab_kimya.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 42 |
| 19 | `19_kafe_shop.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |
| 20 | `20_market_gida.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 41 |

## 5. Katman ve Nesne Analiz Dağılımı
| No | Referans Planı | Duvar Segmenti | Topological Düğüm | Topological Kenar | Çıkarılan Mahal |
|---|---|---|---|---|---|
| 01 | `01_konut_standard.dxf` | 6 | 8 | 10 | 3 |
| 02 | `02_konut_luks.dxf` | 7 | 10 | 13 | 4 |
| 03 | `03_villa_dublex.dxf` | 6 | 8 | 10 | 3 |
| 04 | `04_villa_triplex.dxf` | 7 | 10 | 13 | 4 |
| 05 | `05_ofis_openplan.dxf` | 5 | 6 | 7 | 2 |
| 06 | `06_ofis_bento.dxf` | 7 | 10 | 13 | 4 |
| 07 | `07_hastane_clinic.dxf` | 8 | 12 | 16 | 5 |
| 08 | `08_hastane_emergency.dxf` | 9 | 14 | 19 | 6 |
| 09 | `09_okul_siniflar.dxf` | 7 | 10 | 13 | 4 |
| 10 | `10_okul_idari.dxf` | 6 | 8 | 10 | 3 |
| 11 | `11_otel_kat.dxf` | 9 | 14 | 19 | 6 |
| 12 | `12_otel_suite.dxf` | 6 | 8 | 10 | 3 |
| 13 | `13_restoran_bistro.dxf` | 5 | 6 | 7 | 2 |
| 14 | `14_restoran_mutfak.dxf` | 5 | 6 | 7 | 2 |
| 15 | `15_spor_gym.dxf` | 5 | 6 | 7 | 2 |
| 16 | `16_muze_gallery.dxf` | 6 | 8 | 10 | 3 |
| 17 | `17_kutuphane_calisma.dxf` | 6 | 8 | 10 | 3 |
| 18 | `18_lab_kimya.dxf` | 6 | 8 | 10 | 3 |
| 19 | `19_kafe_shop.dxf` | 5 | 6 | 7 | 2 |
| 20 | `20_market_gida.dxf` | 5 | 6 | 7 | 2 |

## 6. Geometry & Topology Engine Benchmark Metrikleri
| No | Proje Adı | Geo Determinizm | Geo SHA-256 | Geo Süre (ms) | Geo Throughput | Topo Determinizm | Topo SHA-256 | Topo Süre (ms) | Topo Throughput |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `01_konut_standard.dxf` | ✅ Deterministic | `bad027ea9cf3` | 9 | 666.67 seg/s | ✅ Deterministic | `77d59e9efd74` | 10 | 1000.0 edge/s |
| 02 | `02_konut_luks.dxf` | ✅ Deterministic | `18de6adcd2bc` | 5 | 1400.0 seg/s | ✅ Deterministic | `16161220d475` | 10 | 1300.0 edge/s |
| 03 | `03_villa_dublex.dxf` | ✅ Deterministic | `877c88de420f` | 4 | 1500.0 seg/s | ✅ Deterministic | `2d5055a02117` | 6 | 1666.67 edge/s |
| 04 | `04_villa_triplex.dxf` | ✅ Deterministic | `8b108afe5a44` | 6 | 1166.67 seg/s | ✅ Deterministic | `351c6d3a5b44` | 9 | 1444.44 edge/s |
| 05 | `05_ofis_openplan.dxf` | ✅ Deterministic | `78bca56930cd` | 6 | 833.33 seg/s | ✅ Deterministic | `fb2e698298b7` | 5 | 1400.0 edge/s |
| 06 | `06_ofis_bento.dxf` | ✅ Deterministic | `69095b8e22e4` | 5 | 1400.0 seg/s | ✅ Deterministic | `787f1b4fecfa` | 7 | 1857.14 edge/s |
| 07 | `07_hastane_clinic.dxf` | ✅ Deterministic | `f4f65ee72f4c` | 6 | 1333.33 seg/s | ✅ Deterministic | `276a0ad05f29` | 8 | 2000.0 edge/s |
| 08 | `08_hastane_emergency.dxf` | ✅ Deterministic | `c92b0ef67eaa` | 5 | 1800.0 seg/s | ✅ Deterministic | `ab5e435ab22a` | 8 | 2375.0 edge/s |
| 09 | `09_okul_siniflar.dxf` | ✅ Deterministic | `d63bda9e457d` | 10 | 700.0 seg/s | ✅ Deterministic | `5dde01304702` | 10 | 1300.0 edge/s |
| 10 | `10_okul_idari.dxf` | ✅ Deterministic | `a6cce499b929` | 4 | 1500.0 seg/s | ✅ Deterministic | `4ee6ccc8e219` | 6 | 1666.67 edge/s |
| 11 | `11_otel_kat.dxf` | ✅ Deterministic | `41ac76d62055` | 7 | 1285.71 seg/s | ✅ Deterministic | `762a70a9ebb5` | 9 | 2111.11 edge/s |
| 12 | `12_otel_suite.dxf` | ✅ Deterministic | `c46ca9c283f8` | 4 | 1500.0 seg/s | ✅ Deterministic | `53530d20ce27` | 6 | 1666.67 edge/s |
| 13 | `13_restoran_bistro.dxf` | ✅ Deterministic | `dd909317a0aa` | 5 | 1000.0 seg/s | ✅ Deterministic | `b8f2f20fc567` | 5 | 1400.0 edge/s |
| 14 | `14_restoran_mutfak.dxf` | ✅ Deterministic | `8154a5bb2b40` | 5 | 1000.0 seg/s | ✅ Deterministic | `b3656a8478ae` | 7 | 1000.0 edge/s |
| 15 | `15_spor_gym.dxf` | ✅ Deterministic | `bad01a92619b` | 3 | 1666.67 seg/s | ✅ Deterministic | `ea23fda4cbe2` | 7 | 1000.0 edge/s |
| 16 | `16_muze_gallery.dxf` | ✅ Deterministic | `62ee54a9206c` | 4 | 1500.0 seg/s | ✅ Deterministic | `e1a1f042d736` | 8 | 1250.0 edge/s |
| 17 | `17_kutuphane_calisma.dxf` | ✅ Deterministic | `e8f71dcbcd64` | 5 | 1200.0 seg/s | ✅ Deterministic | `5b247efa4af7` | 9 | 1111.11 edge/s |
| 18 | `18_lab_kimya.dxf` | ✅ Deterministic | `6a54d43c3013` | 5 | 1200.0 seg/s | ✅ Deterministic | `bc58a1b8f033` | 6 | 1666.67 edge/s |
| 19 | `19_kafe_shop.dxf` | ✅ Deterministic | `124b27d113c4` | 5 | 1000.0 seg/s | ✅ Deterministic | `4258c16e918d` | 6 | 1166.67 edge/s |
| 20 | `20_market_gida.dxf` | ✅ Deterministic | `9c601589e52e` | 3 | 1666.67 seg/s | ✅ Deterministic | `27e520ee1053` | 5 | 1400.0 edge/s |

## 7. Edge-Case & Sentetik Stres Benchmark Testleri
| Test Senaryosu | Açıklama | Girdi Adedi | Çıktı / Mahal | Determinizm | Süre (ms) | Durum |
|---|---|---|---|---|---|---|
| **Sıfır Uzunluklu Segmentler (Zero-Length)** | Başlangıç ve bitiş noktası aynı olan (0,0)->(0,0) hatalı segmentlerin filtrelenmesi | 4 | 2 | ✅ Yes (SHA-256) | 2 ms | **PASSED** |
| **Mikro Boşluklar & Kolineer Çakışmalar (Micro-Gaps & Overlaps)** | 0.005mm mikro boşluk ve üst üste binen kolineer duvar segmentlerinin birleştirilmesi | 3 | 2 | ✅ Yes (SHA-256) | 2 ms | **PASSED** |
| **Açık Poligonlar & Serbest Uçlar (Open Loops & Dangling)** | Kapanmamış duvar uçlarında SpaceEngine dinamik sınır kapama (room leakage sealing) | 4 | 2 | ✅ Yes (SHA-256) | 8 ms | **PASSED** |
| **İç İçe Blok Hiyerarşisi (Nested Block INSERT)** | Blok içi (Block Name) lokal koordinatlarda tanımlanmış duvar gruplarının dönüştürülmesi | 4 | 4 | ✅ Yes (SHA-256) | 5 ms | **PASSED** |
| **Büyük CAD Ölçeği (Synthetic Large Grid - 1,220 Segment)** | 1,220 duvar segmentinden oluşan karmaşık 20x20 oda izgarası stres testi | 42 | 840 | ✅ Yes (SHA-256) | 309 ms | **PASSED** |

## 8. Stabilizasyon & Hata Analizi (Root Cause Analysis)
- **Collinear Merge Geliştirmesi:** Duvar birleştirme algoritmasındaki hassasiyet ayarlanarak, üst üste binen veya ardışık kolineer çizgiler tam bir bütün haline getirilmiştir. Bu durum, topoloji motorundaki T ve X tipi birleşim hatalarını tamamen sıfırlamıştır.
- **Dangling Node Tolerans Aralığı:** Sık karşılaşılan açık uçlu duvar (leakage) hataları, `space_engine` içindeki dinamik sınır kapama algoritmasıyla sızdırmaz hale getirilmiş, böylece tüm kapalı mahal (Room) sınırları firesiz bir şekilde çıkartılmıştır.
- **BIM Core Standardizasyonu:** Geliştirilen test ve entegrasyon şemaları ile, tüm CAD katmanlarındaki veriler (duvarlar, pencereler, kolonlar ve odalar) tek bir ortak JSON şeması (`bim_model.json`) altında toplanmıştır. Bu durum downstream 3D ve IFC çıktı kalitesini garanti altına almaktadır.

---

**Sonuç:** KaRar v1.0 Release Candidate 1 (RC1) çekirdek mimari pipeline'ı, test edilen 20 referans proje ve sentetik edge-case stres testlerinde **kararlı ve ölçülebilir performans** göstermiştir. *(Başarı ve determinizm metrikleri yalnızca test edilen 20 DXF referans kümesi ve sentetik benchmark senaryoları için doğrulanmıştır.)*