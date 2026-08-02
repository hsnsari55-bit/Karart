# KaRar Current Focus

Bu dosya, oturumlar arasında **anlık önceliği kaybetmemek** ve ajanların/katılımcıların aynı hedefe hizalı kalmasını sağlamak için tutulur.

## 0. Stratejik Çerçeve
- Program modu: **kanıt-güdümlü deterministik çekirdek programı**
- Aktif program fazı: **P0 — Ölçüm ve Güvence Katmanı**
- Kuzey yıldızı dosyası: `docs/STRATEGIC_ROADMAP.md`
- Öncelik filtresi: çekirdek doğruluk / determinizm / sağlamlık / performans etkisi ölçülemeyen işler ertelenir

## 1. Aktif Hedef
- Hedef modül: `backend/tests/test_modern_pipeline.py` içindeki parser-backed determinism regression yüzeyi; odak alanı `DXFParser -> GeometryEngine -> TopologyEngine -> SemanticEngine -> SpaceEngine -> BIMCoreEngine`
- Hedef problem: Aynı `DXFParser` örneği tekrar kullanıldığında parser state sızıntısı büyük ölçüde kapatıldı ve bu kanıt Geometry/Topology/Health zincirine taşındı. Bu oturumda kapsam bir adım daha ileri götürülerek aynı parser örneğiyle üretilen **Semantic / Space / Canonical BIM Model** çıktılarının yapısal olarak deterministik kaldığı regression ile kilitlendi. Son kalan fark, `BIMCoreEngine` provenance alanlarındaki (`generated_at`, `canonical_bim_sha256`, `input_hashes.*`) run-bağımlı metadata idi; test normalizasyonu bu alanları bilinçli şekilde dışarıda bırakarak çekirdek Canonical BIM sözleşmesini kıyaslıyor.
- Neden şimdi: Bu değişiklik doğrudan Canonical BIM Model determinizmini ölçülebilir biçimde güçlendiriyor. Geometry/Topology zinciri downstream modüllerin tek veri kaynağı olduğundan, parser-backed tekrar çağrı davranışının semantics/space/BIM core seviyesine kadar kanıtlanması P0 güvence katmanı için yüksek öncelikliydi. Ayrıca hedefli düzeltmenin geniş regresyon yüzeyinde yeni kırılma üretmediği de doğrulanmalıydı.

## 2. Başarı Kriteri
- Geçmesi gereken parser determinism testleri:
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_skipped_entities_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_entities_and_bounds_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_without_leaking_block_promotion_metadata`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_without_leaking_hatch_output_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_block_filter_on_nested_blocks`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_dxf_recover_fallback`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_nested_block_filter_recover_fallback`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_multi_candidate_heuristic_recover_fallback`
- Geçmesi gereken pipeline determinism testleri:
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic`
- Beklenen deterministik davranış: Aynı parser örneğiyle art arda yapılan çağrılarda parser metadata'sı, promoted geometry, `dxf_raw`, `walls_clean`, `geometry_graph`, topology health çıktıları ve Semantic/Space/BIM Core çıktı sözleşmeleri yapısal olarak birebir aynı kalmalı. `BIMCoreEngine` provenance alanlarındaki run-bağımlı metadata (`generated_at`, `canonical_bim_sha256`, `input_hashes.*`) determinism testinde normalize edilerek çekirdek model yapısından ayrıştırılmalı.
- Ölçülebilir çıktı:
  - `python -m unittest backend.tests.test_modern_pipeline.TestModernPipeline.test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic 2>&1` sonucu **Ran 3 tests ... OK** olmalı.
  - `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1` sonucu **Ran 82 tests ... OK** olmalı.

## 3. Bu Oturumda Yapılan Son İş
- Son değişiklik özeti: `backend/tests/test_modern_pipeline.py` içindeki `test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic` normalizasyonu genişletildi. `normalize_canonical_model(...)` artık `provenance.generated_at`, `provenance.canonical_bim_sha256` ve `provenance.input_hashes.*` alanlarını normalize ediyor; böylece `DXFParser -> Geometry -> Topology -> Semantic -> Space -> BIM Core` zincirinde yapısal determinism, run-bağımlı provenance gürültüsünden ayrıştırılarak doğrulanıyor.
- Son dokunulan dosyalar: `backend/tests/test_modern_pipeline.py`, `docs/CURRENT_FOCUS.md`, `docs/LATEST_HANDOFF.md`
- Son doğrulama komutları:
  - `python -m unittest backend.tests.test_modern_pipeline.TestModernPipeline.test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic 2>&1`
  - `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
- Son doğrulama sonucu:
  - Hedefli determinism doğrulaması: **Ran 3 tests in 0.160s — OK**
  - Genişletilmiş core regression yüzeyi: **Ran 82 tests in 0.439s — OK**

## 4. Hemen Sonraki Adım
- İlk okunacak dosya: `backend/run_regression_tests.py`, `backend/output_manifest.py`, `backend/output_metrics.py`, `datasets/golden_manifests/modern_pipeline_outputs.json`, `datasets/golden_manifests/modern_pipeline_metrics.json`
- İlk çalıştırılacak test/komut:
  - `python -m unittest backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
  - ardından gerekli ise `python backend/run_regression_tests.py ...` ile temsilî örnekler üzerinde topology health gate / manifest / metrics davranışını izole et
- Yapılacak minimal değişiklik: sonraki yüksek değerli iş, regression runner ve golden manifest katmanında deterministik sözleşme ile run-bağımlı provenance/ölçüm alanlarının sınırını netleştirmek. Amaç genel refactor değil; Geometry/Topology/Canonical BIM Model doğruluğunu etkileyen gerçek mismatch sinyallerini gürültüden ayırmak.
- Not: Parser-backed pipeline determinism şu anda yeşil. Bundan sonraki iş, bunu golden output / metrics doğrulama katmanında daha temsilî fixture'larla sürdürmek olmalı.

## 5. Yasak / Ertelenmiş Alanlar
- Bu oturumda dokunulmayacak alanlar: Blender builder, IFC exporter, UI marketing/placeholder işleri
- Bilerek ertelenen işler: core determinism ile doğrudan ilişkili olmayan genel refactor ve stil temizlikleri; provenance dışı olmayan küçük çıktı kozmetiklerini düzeltme; Blender preview için consumer-side geometri düzeltmeleri
- İlgisiz refactor notu: test yardımcılarını veya rapor formatını sadece estetik amaçla yeniden düzenleme, çekirdek determinism/fidelity metriği üretmiyorsa ertelenmeli

## 6. Sapma Kontrol Soruları
- Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model doğruluğunu artırıyor mu?
- Bu adım mevcut aktif hedefe doğrudan hizmet ediyor mu?
- Bu adım testsiz veya kanıtsız ilerlemeye neden oluyor mu?
- Bu adım `docs/STRATEGIC_ROADMAP.md` içindeki aktif program fazı ile uyumlu mu?
