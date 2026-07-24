# KaRar AI - P2 Ground Truth Validation Framework: Teknik Tasarım Belgesi (Design Document)

**Sürüm:** v1.0.0-RC1  
**Durum:** Tasarım Onaylandı (Kod Yazımı Yasaktır)  
**Hedef Modül:** P2 — Ground Truth Validation Framework / Pipeline (Yer Doğruluk Doğrulama Çerçevesi)  

---

## 1. Yönetici Özeti ve Kapsam

P1 (Geometry Engine ve Deterministik Doğrulama) aşaması başarıyla tamamlanmış ve `v1.0.0-RC1` Release Candidate olarak dondurulmuştur. 

**P2 (Ground Truth Validation Framework)** kesinlikle bir üretim motoru (production engine) DEĞİLDİR. P2; mevcut Geometry Engine, Topology Engine, Semantic Engine, Space Engine ve Canonical BIM SSoT (`outputs/bim_model.json`) çıktıları üzerinde **yalnızca doğrulama, benchmark denetimi ve metrik hesaplama** gerçekleştiren bağımsız bir doğrulama boru hattıdır (validation & benchmark pipeline).

---

## 2. Temel Mimari Prensipler ve Kalıcı Mimari Sözleşme (Architectural Contract)

1. **Hiçbir CAD Verisi Yeniden Ayrıştırılmaz (No CAD Parsing):**
   - P2 boru hattı ham DXF/DWG veya CAD dosyalarını doğrudan okumaz, çözmez veya ayrıştırmaz.
2. **Hiçbir Geometri Üretilmez (No Geometry Generation):**
   - P2 yeni nokta, doğru, poligon, duvar veya koordinat hesaplaması yapmaz; geometri türetmez.
3. **Hiçbir Semantik Karar Verilmez (No Semantic Decision-Making):**
   - P2 duvar, kapı, pencere, kolon veya oda sınıflandırma mantığı çalıştırmaz; semantik karar vermez.
4. **Tek Yönlü Veri Akışı (One-Way Data Flow):**
   - Veri akışı kesin olarak `Canonical BIM → Validation Pipeline` yönündedir. Validation Pipeline hiçbir zaman üretim hattını geri besleyemez.
5. **Yan Etkisizlik (Side-Effect Free):**
   - P2 mevcut hiçbir dosyayı veya SSoT verisini değiştirmez; yalnızca yeni rapor ve metrik dosyaları üretir.
6. **Deterministiklik (Determinism):**
   - Aynı Canonical BIM ve aynı Ground Truth girdileri her çalıştırmada %100 özdeş metrikleri üretir.
7. **Modüler Bağımsızlık (Loose Decoupling):**
   - P2; Geometry Engine, Topology Engine, Semantic Engine veya Space Engine iç modüllerine doğrudan bağımlı değildir; yalnızca tanımlı JSON çıktı dosyalarını okur.
8. **Kod Üretimi Onay Şartı:**
   - Kullanıcı onay verene kadar P2 kapsamında Python veya TypeScript uygulama kodu yazılmaz. Sadece tasarım ve mimari dokümantasyon güncellenir.

---

## 3. Metrik Tanımları ve Değerlendirme Algoritmaları

### 3.1. Duvar Eşleme ve $F_1$-Skoru ($Wall\ F_1$)
Canonical BIM modelindeki duvar segmentlerinin Ground Truth referans duvarlarıyla uzamsal kesişim (spatial intersection) analizi:
- **Precision (Kesinlik):** $\frac{\text{Doğru Eşleşen Tahmini Duvar Uzunluğu}}{\text{Toplam Tahmini Duvar Uzunluğu}}$
- **Recall (Duyarlılık):** $\frac{\text{Doğru Eşleşen Tahmini Duvar Uzunluğu}}{\text{Ground Truth Referans Duvar Uzunluğu}}$
- **$F_1$-Score:** $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} \ge 0.985$

### 3.2. Oda Poligonu Kesişim Oranı ($Room\ IoU$)
Canonical BIM modelindeki mekan poligonları ($P_{pred}$) ile referans ground truth oda poligonları ($P_{gt}$) arasındaki alan kesişimi (Intersection over Union):
$$IoU = \frac{\text{Area}(P_{pred} \cap P_{gt})}{\text{Area}(P_{pred} \cup P_{gt})} \ge 99.0\%$$

### 3.3. Semantik ve Açıklık Eşleme Doğruluğu ($Semantic\ \&\ Opening\ Accuracy$)
Kapı (Door), pencere (Window) ve kolon (Column) nesnelerinin doğru ilişkilendirme ve sınıflandırma doğrulama oranı:
$$\text{Accuracy} = \frac{\text{Doğru Sınıflandırılan Nesne Sayısı}}{\text{Toplam Ground Truth Nesne Sayısı}} \ge 99.5\%$$

---

## 4. Girdi ve Çıktı Sözleşmesi (I/O Schema Contract)

### 4.1. Girdiler (Salt Okunur / Read-Only)
- `outputs/bim_model.json` (Canonical BIM SSoT)
- `outputs/walls_clean.json` (Geometry Engine Çıktısı)
- `outputs/geometry_graph.json` (Topology Engine Çıktısı)
- `datasets/ground_truth/{project_id}_gt.json` (Ground Truth Referans Verisi)

### 4.2. Çıktılar (Yalnızca Doğrulama ve Benchmark Raporları)
- `outputs/p2_validation_summary.json` (Metrik hesaplama sonuçları ve SHA-256 doğrulama mührü)
- `outputs/P2_Validation_Report.md` (İnsan tarafından incelenebilir detaylı benchmark raporu)

---

## 5. Doğrulama ve Kabul Kriterleri (Acceptance Criteria)
1. **Sıfır Kod ve Veri Mutasyonu:** P1 ve tüm üretim modüllerinde (Geometry, Topology, Semantic, Space, BIM Core) hiçbir kod veya BIM verisi değiştirilmemiştir.
2. **Piyasa/Üretim Bağımsızlığı:** P2 tamamen izole bir doğrulama ve benchmark aracıdır.
3. **Teknik Tasarım Uyumluğu:** P2 tasarım belgesi belirlenen tüm mimari kısıtlara %100 uygundur.

