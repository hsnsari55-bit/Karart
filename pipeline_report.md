# KaRar AI - Production Validation & Benchmark Report (v1.0.0-RC1)

**Rapor Tarihi:** 2026-07-22 09:03:39
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
- **Toplam İşlem Süresi:** 1.061 saniye
- **Proje Başına Ortalama Süre:** 53.0 ms

## 4. Proje Bazlı Detaylı Doğrulama Tablosu (Validation Matrix)
| No | Proje Adı | Parser | Geometry | Topology | Semantic | Space | BIM | 3D | IFC | Durum | Süre (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | `01_konut_standard.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 02 | `02_konut_luks.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 52 |
| 03 | `03_villa_dublex.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 51 |
| 04 | `04_villa_triplex.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 56 |
| 05 | `05_ofis_openplan.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 54 |
| 06 | `06_ofis_bento.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 07 | `07_hastane_clinic.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 65 |
| 08 | `08_hastane_emergency.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 61 |
| 09 | `09_okul_siniflar.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 62 |
| 10 | `10_okul_idari.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 57 |
| 11 | `11_otel_kat.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 69 |
| 12 | `12_otel_suite.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 13 | `13_restoran_bistro.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 47 |
| 14 | `14_restoran_mutfak.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 43 |
| 15 | `15_spor_gym.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 16 | `16_muze_gallery.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 56 |
| 17 | `17_kutuphane_calisma.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 51 |
| 18 | `18_lab_kimya.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 49 |
| 19 | `19_kafe_shop.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 37 |
| 20 | `20_market_gida.dxf` | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | **✅ SUCCESS** | 39 |

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
| 01 | `01_konut_standard.dxf` | ✅ Deterministic | `16e0aa0e1b43` | 7 | 857.14 seg/s | ✅ Deterministic | `403c2f872e42` | 9 | 1111.11 edge/s |
| 02 | `02_konut_luks.dxf` | ✅ Deterministic | `59d13ffea118` | 4 | 1750.0 seg/s | ✅ Deterministic | `805c731afdaa` | 9 | 1444.44 edge/s |
| 03 | `03_villa_dublex.dxf` | ✅ Deterministic | `df25eeab6524` | 4 | 1500.0 seg/s | ✅ Deterministic | `247ded516038` | 10 | 1000.0 edge/s |
| 04 | `04_villa_triplex.dxf` | ✅ Deterministic | `b8ca2042e1ae` | 6 | 1166.67 seg/s | ✅ Deterministic | `c60925a9a887` | 9 | 1444.44 edge/s |
| 05 | `05_ofis_openplan.dxf` | ✅ Deterministic | `41f8039b67d7` | 6 | 833.33 seg/s | ✅ Deterministic | `4f19968da2f8` | 10 | 700.0 edge/s |
| 06 | `06_ofis_bento.dxf` | ✅ Deterministic | `d1ddcb136104` | 5 | 1400.0 seg/s | ✅ Deterministic | `7249ef87da94` | 15 | 866.67 edge/s |
| 07 | `07_hastane_clinic.dxf` | ✅ Deterministic | `dca973cec449` | 4 | 2000.0 seg/s | ✅ Deterministic | `36518e62e67f` | 7 | 2285.71 edge/s |
| 08 | `08_hastane_emergency.dxf` | ✅ Deterministic | `f35b6f72e8a9` | 5 | 1800.0 seg/s | ✅ Deterministic | `de0614145b9f` | 10 | 1900.0 edge/s |
| 09 | `09_okul_siniflar.dxf` | ✅ Deterministic | `c1a9b3f5544e` | 6 | 1166.67 seg/s | ✅ Deterministic | `d206fbfaf319` | 13 | 1000.0 edge/s |
| 10 | `10_okul_idari.dxf` | ✅ Deterministic | `c56d82c2d169` | 5 | 1200.0 seg/s | ✅ Deterministic | `61659f57e83c` | 7 | 1428.57 edge/s |
| 11 | `11_otel_kat.dxf` | ✅ Deterministic | `91e79d0ab4b7` | 8 | 1125.0 seg/s | ✅ Deterministic | `35d859df511c` | 9 | 2111.11 edge/s |
| 12 | `12_otel_suite.dxf` | ✅ Deterministic | `7749d5ae9c0d` | 5 | 1200.0 seg/s | ✅ Deterministic | `de4536a3903a` | 12 | 833.33 edge/s |
| 13 | `13_restoran_bistro.dxf` | ✅ Deterministic | `98d452949316` | 4 | 1250.0 seg/s | ✅ Deterministic | `43cbb5c94dc6` | 8 | 875.0 edge/s |
| 14 | `14_restoran_mutfak.dxf` | ✅ Deterministic | `097da2ee5a05` | 4 | 1250.0 seg/s | ✅ Deterministic | `cb01b1d8b888` | 6 | 1166.67 edge/s |
| 15 | `15_spor_gym.dxf` | ✅ Deterministic | `af670bf778fe` | 5 | 1000.0 seg/s | ✅ Deterministic | `1bf4564ef763` | 6 | 1166.67 edge/s |
| 16 | `16_muze_gallery.dxf` | ✅ Deterministic | `fb69b6283cd2` | 10 | 600.0 seg/s | ✅ Deterministic | `f427ccce454f` | 7 | 1428.57 edge/s |
| 17 | `17_kutuphane_calisma.dxf` | ✅ Deterministic | `353d90cdde71` | 8 | 750.0 seg/s | ✅ Deterministic | `8df526938e5e` | 8 | 1250.0 edge/s |
| 18 | `18_lab_kimya.dxf` | ✅ Deterministic | `49950159de24` | 6 | 1000.0 seg/s | ✅ Deterministic | `0181386c57ee` | 7 | 1428.57 edge/s |
| 19 | `19_kafe_shop.dxf` | ✅ Deterministic | `858cd4a413e6` | 4 | 1250.0 seg/s | ✅ Deterministic | `86e5af78cda1` | 5 | 1400.0 edge/s |
| 20 | `20_market_gida.dxf` | ✅ Deterministic | `e2642b069303` | 4 | 1250.0 seg/s | ✅ Deterministic | `0886f397c57d` | 5 | 1400.0 edge/s |

## 7. Edge-Case & Sentetik Stres Benchmark Testleri
| Test Senaryosu | Açıklama | Girdi Adedi | Çıktı / Mahal | Determinizm | Süre (ms) | Durum |
|---|---|---|---|---|---|---|
| **Sıfır Uzunluklu Segmentler (Zero-Length)** | Başlangıç ve bitiş noktası aynı olan (0,0)->(0,0) hatalı segmentlerin filtrelenmesi | 4 | 2 | ✅ Yes (SHA-256) | 3 ms | **PASSED** |
| **Mikro Boşluklar & Kolineer Çakışmalar (Micro-Gaps & Overlaps)** | 0.005mm mikro boşluk ve üst üste binen kolineer duvar segmentlerinin birleştirilmesi | 3 | 2 | ✅ Yes (SHA-256) | 3 ms | **PASSED** |
| **Açık Poligonlar & Serbest Uçlar (Open Loops & Dangling)** | Kapanmamış duvar uçlarında SpaceEngine dinamik sınır kapama (room leakage sealing) | 4 | 2 | ✅ Yes (SHA-256) | 10 ms | **PASSED** |
| **İç İçe Blok Hiyerarşisi (Nested Block INSERT)** | Blok içi (Block Name) lokal koordinatlarda tanımlanmış duvar gruplarının dönüştürülmesi | 4 | 4 | ✅ Yes (SHA-256) | 4 ms | **PASSED** |
| **Büyük CAD Ölçeği (Synthetic Large Grid - 1,220 Segment)** | 1,220 duvar segmentinden oluşan karmaşık 20x20 oda izgarası stres testi | 42 | 840 | ✅ Yes (SHA-256) | 313 ms | **PASSED** |

## 8. Stabilizasyon & Hata Analizi (Root Cause Analysis)
- **Collinear Merge Geliştirmesi:** Duvar birleştirme algoritmasındaki hassasiyet ayarlanarak, üst üste binen veya ardışık kolineer çizgiler tam bir bütün haline getirilmiştir. Bu durum, topoloji motorundaki T ve X tipi birleşim hatalarını tamamen sıfırlamıştır.
- **Dangling Node Tolerans Aralığı:** Sık karşılaşılan açık uçlu duvar (leakage) hataları, `space_engine` içindeki dinamik sınır kapama algoritmasıyla sızdırmaz hale getirilmiş, böylece tüm kapalı mahal (Room) sınırları firesiz bir şekilde çıkartılmıştır.
- **BIM Core Standardizasyonu:** Geliştirilen test ve entegrasyon şemaları ile, tüm CAD katmanlarındaki veriler (duvarlar, pencereler, kolonlar ve odalar) tek bir ortak JSON şeması (`bim_model.json`) altında toplanmıştır. Bu durum downstream 3D ve IFC çıktı kalitesini garanti altına almaktadır.

---

**Sonuç:** KaRar v1.0 Release Candidate 1 (RC1) çekirdek mimari pipeline'ı, test edilen 20 referans proje ve sentetik edge-case stres testlerinde **kararlı ve ölçülebilir performans** göstermiştir. *(Başarı ve determinizm metrikleri yalnızca test edilen 20 DXF referans kümesi ve sentetik benchmark senaryoları için doğrulanmıştır.)*