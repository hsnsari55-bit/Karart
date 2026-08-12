# KaRar Current Focus

Bu dosya, oturumlar arasında **anlık önceliği kaybetmemek** ve ajanların/katılımcıların aynı hedefe hizalı kalmasını sağlamak için tutulur.

## 0. Stratejik Çerçeve
- Program modu: **kanıt-güdümlü deterministik çekirdek programı**
- Aktif program fazı: **P0 — Ölçüm ve Güvence Katmanı**
- Kuzey yıldızı dosyası: `docs/STRATEGIC_ROADMAP.md`
- Öncelik filtresi: çekirdek doğruluk / determinizm / sağlamlık / performans etkisi ölçülemeyen işler ertelenir

## 1. Aktif Hedef
- Hedef modül: `backend/run_regression_tests.py`, `backend/output_manifest.py`, `backend/output_metrics.py`, `datasets/golden_manifests/modern_pipeline_outputs.json`, `datasets/golden_manifests/modern_pipeline_metrics.json`
- Hedef problem: Parser-backed determinism artık `DXFParser -> GeometryEngine -> TopologyEngine -> SemanticEngine -> SpaceEngine -> BIMCoreEngine` zincirinde regression ile yeşil. Aktif iş, regression runner ve golden manifest/metrics katmanında **çekirdek deterministik sözleşme** ile run-bağımlı provenance/ölçüm ve beklenen negatif senaryo log gürültüsü arasındaki sınırı daha netleştirmek. Bu oturumda özel olarak topology health görünürlüğü ile bloklayıcı kabul otoritesi ayrımı netleştirildi; amaç, gerçek Geometry/Topology/Canonical BIM sapmalarını görünür tutarken topology health özetini diagnostik/izlenebilirlik katmanı olarak korumak ve gerçek bloklamayı `TopologyValidator` invariant'larında toplamak.
- Neden şimdi: Bu adım doğrudan Geometry/Topology/Canonical BIM güvence katmanını ölçülebilir biçimde sertleştiriyor. Regression runner, çekirdek pipeline'ın kapılayıcı gözlem katmanı olduğundan burada gerçek sözleşme ihlali ile beklenen negatif senaryo çıktılarının ayrıştırılması P0 için yüksek öncelikli.

## 2. Başarı Kriteri
- Geçmesi gereken regression / golden sözleşme testleri:
  - `backend/tests/test_output_manifest.py`
  - `backend/tests/test_output_metrics.py`
  - `backend/tests/test_regression_topology_report_path.py`
- Korunması gereken determinism / entegrasyon testleri:
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic`
- Beklenen davranış: Golden manifest/metrics/topology-health katmanı, gerçekten bozuk Geometry/Topology/Canonical BIM çıktılarında kırmızıya düşmeli; negatif test senaryolarının beklenen `BAŞARISIZ` logları ise suite sonucunu bozmadığı sürece regression sinyali olarak yorumlanmamalı. Topology health gate `required_status=HEALTHY` eşiğini görünür kılmalı ancak `enforced=false` kalmalı; gerçek bloklama `TopologyValidator` başarısızlıklarında oluşmalı. Run-bağımlı provenance/ölçüm gürültüsü ile çekirdek sözleşme farkı net ayrıştırılmalı.
- Ölçülebilir çıktı:
  - `python -m unittest backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1` sonucu **Ran 19 tests ... OK** olmalı.
  - `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1` sonucu **Ran 83 tests ... OK** olmalı.

## 3. Bu Oturumda Yapılan Son İş
- Son değişiklik özeti: `backend/run_regression_tests.py` içinde topology health gate semantiği netleştirildi. `_evaluate_topology_health_gate(...)` artık `required_status=HEALTHY` eşiğini yalnız görünürlük amaçlı raporluyor; `_enforce_topology_health_gate(...)` legacy shim olarak aynı özeti döndürüyor; gerçek bloklama `TopologyValidator.validate(...)` invariant'larında kalıyor.
- Son dokunulan dosyalar: `backend/run_regression_tests.py`, `docs/CURRENT_FOCUS.md`, `docs/LATEST_HANDOFF.md`
- Son doğrulama komutları:
  - `python -m unittest backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
- Son doğrulama sonucu:
  - Manifest / metrics / topology-report regression doğrulaması: **Ran 19 tests in 0.066s — OK**
  - WARNING topology health özeti regression raporunda görünür kaldı; bloklayıcı hata ise yalnız validator FAIL olduğunda `Topology validation failed: ...` biçiminde gözlendi.
  - PowerShell sarmalayıcı stderr/log satırları nedeniyle üst seviyede `NativeCommandError` benzeri gürültü üretse de unittest özeti net olarak `OK` kapandı.

## 4. Hemen Sonraki Adım
- İlk okunacak dosya: `backend/run_regression_tests.py`, `backend/output_manifest.py`, `backend/output_metrics.py`, `backend/tests/test_regression_topology_report_path.py`
- İlk çalıştırılacak test/komut:
  - değişiklik sonrası daha geniş güvence istenirse `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
- Yapılacak minimal değişiklik: regression runner ve golden manifest/metrics katmanında deterministik çekirdek sözleşme ile run-bağımlı provenance/ölçüm alanlarının sınırını daha açık ve tekrar kullanılabilir hale getirmek; ayrıca beklenen negatif senaryo loglarını suite sonucundan görsel olarak daha iyi ayırmak. Amaç genel refactor değil; Geometry/Topology/Canonical BIM Model doğruluğunu etkileyen gerçek mismatch sinyallerini gürültüden ayırmak.
- Not: Parser-backed pipeline determinism için önceki geniş regression tabanı yeşil durumda. Bu oturumdaki değişiklik logging/gözlemlenebilirlik odaklıdır; yeni runner değişikliklerinden sonra geniş suite yeniden koşturulmalıdır.

## 5. Yasak / Ertelenmiş Alanlar
- Bu oturumda dokunulmayacak alanlar: Blender builder, IFC exporter, UI marketing/placeholder işleri
- Bilerek ertelenen işler: core determinism ile doğrudan ilişkili olmayan genel refactor ve stil temizlikleri; provenance dışı olmayan küçük çıktı kozmetiklerini düzeltme; Blender preview için consumer-side geometri düzeltmeleri
- İlgisiz refactor notu: test yardımcılarını veya rapor formatını sadece estetik amaçla yeniden düzenleme, çekirdek determinism/fidelity metriği üretmiyorsa ertelenmeli

## 6. Sapma Kontrol Soruları
- Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model doğruluğunu artırıyor mu?
- Bu adım mevcut aktif hedefe doğrudan hizmet ediyor mu?
- Bu adım testsiz veya kanıtsız ilerlemeye neden oluyor mu?
- Bu adım `docs/STRATEGIC_ROADMAP.md` içindeki aktif program fazı ile uyumlu mu?
