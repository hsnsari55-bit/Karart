# KaRar Latest Handoff

Bu handoff, bir sonraki oturumun ek bağlam istemeden başlayabilmesi için son teknik durumu **6 başlıklı zorunlu formatta** özetler.

## 1. Kanıt
- Aktif hedef / kapsam: `backend/tests/test_modern_pipeline.py` içinde aynı `DXFParser` örneğinin art arda çalıştırılmasında deterministikliğin yalnız parser/geometry/topology/health zincirinde değil, `SemanticEngine -> SpaceEngine -> BIMCoreEngine` downstream sözleşmesinde de korunmasını sağlamak.
- İlgili dosyalar:
  - `backend/tests/test_modern_pipeline.py`
  - `backend/bim_core.py`
  - `docs/CURRENT_FOCUS.md`
  - `docs/LATEST_HANDOFF.md`
- İlgili testler:
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_skipped_entities_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_entities_and_bounds_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_without_leaking_block_promotion_metadata`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_without_leaking_hatch_output_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_block_filter_on_nested_blocks`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_dxf_recover_fallback`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_nested_block_filter_recover_fallback`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_reuses_parser_with_truncated_multi_candidate_heuristic_recover_fallback`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic`
- Kod kanıtı:
  - `backend/tests/test_modern_pipeline.py` içindeki `normalize_canonical_model(...)` yardımcı fonksiyonu artık `provenance.generated_at`, `provenance.canonical_bim_sha256` ve `provenance.input_hashes.{bim_semantics_sha256, spaces_sha256, geometry_graph_sha256}` alanlarını normalize ediyor.
  - `backend/bim_core.py:282-312` provenance içine `generated_at`, `input_hashes.*` ve `canonical_bim_sha256` ekliyor; bunlar run-bağımlı olduğu için byte-level output farklılaşabiliyor.
  - `backend/tests/test_modern_pipeline.py` içindeki `test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic` aynı parser örneğiyle aynı fixture'ı iki kez çalıştırıp `semantics`, persisted semantics, `spaces`, persisted spaces, `canonical_model` ve persisted BIM model için yapısal eşitlik doğruluyor.
  - Aynı testte door-parent_wall ilişkisinin korunması, space-wall/door ilişkilerinin sıralı-normalize edilmiş biçimde sabit kalması ve Canonical BIM koleksiyonlarının (`spaces`, `walls`, `windows`, `columns`, `doors`) run'lar arasında aynı içerikle üretildiği doğrulanıyor.
  - Genişletilmiş doğrulama komutu (`82` test) `backend/tests/test_modern_pipeline`, topology health/validator/determinism paketleri, BIM core opening regression, output manifest/metrics ve topology report path regression'larını birlikte çalıştırdı ve tamamı `OK` döndü.
- Son komut çıktıları:
  - `python -m unittest backend.tests.test_modern_pipeline.TestModernPipeline.test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic 2>&1`
  - `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
- Sonuç:
  - Hedefli pipeline determinism doğrulaması: **Ran 3 tests in 0.160s — OK**
  - Genişletilmiş core regression yüzeyi: **Ran 82 tests in 0.439s — OK**
  - `test_02f` sırasında `bim_core.py` loglarında iki koşu için farklı `Canonical BIM Model ... SHA-256` değerleri görüldü; fakat fark yalnız provenance/run-bağımlı alanlarda olduğundan normalize edilmiş Canonical BIM sözleşmesi eşit kaldı ve test geçti.

## 2. Risk Analizi
- Parser-backed determinism şimdi parser/geometry/topology/health ile birlikte semantic/space/BIM core yapısına kadar regression ile kapsanıyor; ancak `BIMCoreEngine` provenance alanları hâlâ run-bağımlı ve byte-level manifest/hash kıyaslarında gürültü oluşturabiliyor.
- `test_02f` yapısal determinismi kilitliyor, fakat golden manifest / metrics katmanında provenance veya ölçüm gürültüsü ile gerçek sözleşme sapmasının sınırı hâlâ daha net ayrıştırılmalı.
- Daha temsilî gerçek plan export'ları, çok daha karmaşık multi-room / multi-opening vakaları ve recover sonrası çoklu promotion dallarının semantic/space/BIM core etkileri için kanıt yüzeyi hâlâ sınırlı.

## 3. Önerilen Çözüm
- `test_02f` ile gelen canonical model normalizasyon yaklaşımı korunmalı; determinism testleri çekirdek sözleşmeyi kıyaslamalı, run-bağımlı provenance alanlarını değil.
- Sonraki adımda aynı ayrım golden manifest / metrics doğrulama katmanına taşınmalı; böylece gerçek core regression sinyalleri ile provenance/ölçüm gürültüsü ayrıştırılabilir.
- Fixture ailesi, çok odalı / çok açıklıklı / daha temsilî gerçek plan export'ları ve recover sonrası çoklu promotion dalları ile genişletilmeli.

## 4. Uygulanan Değişiklik
- `backend/tests/test_modern_pipeline.py` içindeki `normalize_canonical_model(...)` genişletildi ve `provenance.input_hashes.*` alanları da normalize edilmeye başlandı.
- Böylece `test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic` artık Canonical BIM sözleşmesinin yapısal determinizmini, run-bağımlı hash/timestamp gürültüsünden ayrıştırarak doğruluyor.
- Genişletilmiş core regression paketi çalıştırıldı; modern pipeline, topology health/validator/determinism, BIM core opening relation, output manifest/metrics ve topology report path regresyonları birlikte yeşil kaldı.
- `docs/CURRENT_FOCUS.md` ve `docs/LATEST_HANDOFF.md` bu yeni kapsam ve doğrulama yüzeyi ile hizalandı.

## 5. Doğrulama
- Hedefli doğrulama komutları:
  - `python -m unittest backend.tests.test_modern_pipeline.TestModernPipeline.test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic backend.tests.test_modern_pipeline.TestModernPipeline.test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic 2>&1`
    - Sonuç: **Ran 3 tests in 0.160s — OK**
  - `python -m unittest backend.tests.test_modern_pipeline backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_topology_engine_determinism backend.tests.test_regression_bim_core_opening_parent_wall backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
    - Sonuç: **Ran 82 tests in 0.439s — OK**
- Doğrulanan davranışlar:
  - Parser-backed closed-loop ve truncated-recover fixture'larında `dxf_raw`, `walls_clean`, `geometry_graph` ve topology health çıktıları art arda koşularda sabit kalıyor.
  - Semantic/Space/BIM Core zincirinde `elements`, `spaces`, ilişkisel alanlar (`related_walls`, `related_doors`, `neighbors`, `parent_spaces`, `related_spaces`) ve opening-parent_wall bağları yapısal olarak deterministik kalıyor.
  - `BIMCoreEngine` provenance alanlarındaki run-bağımlı hash/timestamp gürültüsü normalize edildiğinde Canonical BIM sözleşmesi iki koşuda da eşit kalıyor.
  - Geniş regression yüzeyi yeni değişiklikle bozulmadı; konsolda görülen bazı manifest/metrik/topology gate başarısızlık mesajları negatif test senaryolarının beklenen çıktısı ve test suite genel sonucu `OK`.

## 6. Kalan Riskler
- P0 çıkış kapısı hâlâ kapalı; çünkü determinism kanıtı temsilî fixture'larda güçlü olsa da gerçek plan export'ları ve daha büyük çok-oda / çok-opening senaryoları için kapsam sınırlı.
- Provenance / manifest / metrics katmanında run-bağımlı alanlarla çekirdek sözleşme sapmasının sınırı tüm araçlarda tam standartlaştırılmış değil.
- Sonraki en doğru adım: regression runner ve golden output katmanında bu ayrımı netleştirmek; ardından daha temsilî plan fixture'larıyla semantic/space/BIM core determinism yüzeyini büyütmek.