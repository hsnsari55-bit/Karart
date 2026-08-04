# KaRar Latest Handoff

Bu handoff, bir sonraki oturumun ek bağlam istemeden başlayabilmesi için son teknik durumu **6 başlıklı zorunlu formatta** özetler.

## 1. Kanıt
- Aktif hedef / kapsam: `backend/run_regression_tests.py`, `backend/output_manifest.py`, `backend/output_metrics.py` ve golden dataset sözleşmesinde çekirdek deterministik çıktı ile run-bağımlı gürültü sınırını netleştirmek; parser-backed determinism zinciri ise koruyucu regression olarak yeşil tutuluyor. Bu oturumda özel olarak topology health gate'in beklenen negatif senaryolarında traceback gürültüsü azaltıldı.
- İlgili dosyalar:
  - `backend/run_regression_tests.py`
  - `backend/output_manifest.py`
  - `backend/output_metrics.py`
  - `backend/tests/test_output_manifest.py`
  - `backend/tests/test_output_metrics.py`
  - `backend/tests/test_regression_topology_report_path.py`
  - `backend/tests/test_modern_pipeline.py`
  - `docs/CURRENT_FOCUS.md`
  - `docs/LATEST_HANDOFF.md`
- İlgili testler:
  - `backend/tests/test_output_manifest.py`
  - `backend/tests/test_output_metrics.py`
  - `backend/tests/test_regression_topology_report_path.py`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic`
  - `backend/tests/test_modern_pipeline.py::TestModernPipeline::test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic`
- Kod kanıtı:
  - `backend/tests/test_output_manifest.py` ve `backend/tests/test_output_metrics.py`, hem başarılı hem de bilinçli başarısız senaryolarda golden sözleşmenin beklenen şekilde raporlandığını doğruluyor; bu yüzden konsolda görülen `Manifest doğrulaması BAŞARISIZ` / `Metrik doğrulaması BAŞARISIZ` satırları tek başına suite başarısızlığı anlamına gelmiyor.
  - `backend/tests/test_regression_topology_report_path.py`, `RegressionTester` içindeki topology health / topology validation rapor yolu, özet yükleme ve gate davranışını proje-başına/relative-path sözleşmesi ile kilitliyor.
  - `backend/run_regression_tests.py` içindeki en dış hata yakalama bloğu artık `TopologyHealthGateError` için `exc_info=True` kullanmıyor; beklenen gate düşüşleri tek satırlık yüksek sinyalli log olarak kalırken beklenmeyen istisnalarda traceback görünürlüğü korunuyor.
  - `backend/tests/test_modern_pipeline.py` içindeki `normalize_canonical_model(...)` yardımcı fonksiyonu `provenance.generated_at`, `provenance.canonical_bim_sha256` ve `provenance.input_hashes.{bim_semantics_sha256, spaces_sha256, geometry_graph_sha256}` alanlarını normalize ederek Canonical BIM yapısal determinizmini run-bağımlı metadata'dan ayırıyor.
  - Bu oturumda çalıştırılan hedefli doğrulama komutu (`19` test), output manifest/metrics ve topology report path regression yüzeyinde yeni logging davranışının suite sonucunu bozmadığını kanıtladı.
- Son komut çıktıları:
  - `python -m unittest backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
- Sonuç:
  - Golden manifest / metrics / topology-report regression doğrulaması: **Ran 19 tests in 0.066s — OK**
  - Beklenen topology health gate düşüşü tek satırlık log ile gözlendi: `Pipeline failed on sample_plan.dxf: Topology health gate failed: expected HEALTHY but got WARNING ...`
  - PowerShell sarmalayıcı, stderr/log satırları nedeniyle `NativeCommandError` benzeri bir üst seviye çıktı verdi; ancak unittest özeti net olarak `OK` kapandı. Bu, test başarısızlığı değil komut sarmalayıcı gürültüsü.

## 2. Risk Analizi
- Parser-backed determinism şimdi parser/geometry/topology/health ile birlikte semantic/space/BIM core yapısına kadar regression ile kapsanıyor; ancak golden manifest / metrics / runner katmanında run-bağımlı provenance veya ölçüm gürültüsü ile gerçek sözleşme sapmasının sınırı hâlâ daha net ayrıştırılmalı.
- Negatif senaryoların beklenen stderr/log çıktıları, özellikle PowerShell sarmalayıcı üzerinden okunduğunda yanlış başarısızlık izlenimi verebiliyor. `TopologyHealthGateError` için traceback gürültüsü azaltılmış olsa da diğer beklenen negatif akışlarda benzer sinyal ayrımı henüz tam standart değil.
- Daha temsilî gerçek plan export'ları, çok daha karmaşık multi-room / multi-opening vakaları ve recover sonrası çoklu promotion dallarının semantic/space/BIM core etkileri için kanıt yüzeyi hâlâ sınırlı.

## 3. Önerilen Çözüm
- `test_02f` ile gelen canonical model normalizasyon yaklaşımı korunmalı; determinism testleri çekirdek sözleşmeyi kıyaslamalı, run-bağımlı provenance alanlarını değil.
- Aynı ayrım regression runner / golden manifest / metrics doğrulama katmanında daha açık hale getirilmeli; mümkünse raporlanan failure mesajları ile suite sonucu arasındaki sınır kod ve dokümantasyon seviyesinde netleştirilmeli. Topology health gate için uygulanan düşük-gürültülü logging deseni, yalnız beklenen negatif akışlara kontrollü biçimde genişletilerek kullanılmalı.
- Fixture ailesi, çok odalı / çok açıklıklı / daha temsilî gerçek plan export'ları ve recover sonrası çoklu promotion dalları ile genişletilmeli.

## 4. Uygulanan Değişiklik
- `backend/run_regression_tests.py` içinde en dış hata yakalama bloğu güncellendi.
- Beklenen `TopologyHealthGateError` durumlarında `self.logger.error(..., exc_info=False)` davranışı uygulanarak traceback seli kaldırıldı; beklenmeyen istisnalarda ise `exc_info=True` korunuyor.
- Hedefli golden manifest / metrics / topology-report regression paketi çalıştırıldı; **19 test OK** ile bu logging değişikliğinin regression sözleşmesini bozmadığı kanıtlandı.
- `docs/CURRENT_FOCUS.md` ve `docs/LATEST_HANDOFF.md` bu product-code değişikliği ve doğrulama çıktısı ile senkronize edildi.

## 5. Doğrulama
- Hedefli doğrulama komutları:
  - `python -m unittest backend.tests.test_output_manifest backend.tests.test_output_metrics backend.tests.test_regression_topology_report_path 2>&1`
    - Sonuç: **Ran 19 tests in 0.066s — OK**
- Doğrulanan davranışlar:
  - Golden manifest/metrics/topology-report katmanı yeni doğrulama turunda yeşil kaldı.
  - Beklenen topology health gate başarısızlığı suite sonucunu bozmadı ve artık traceback yerine tek satırlık yüksek-sinyalli hata mesajı olarak raporlandı.
  - PowerShell üst seviye sarmalayıcı gürültüsüne rağmen gerçek unittest sonucu `OK` olarak ayrıştı.

## 6. Kalan Riskler
- P0 çıkış kapısı hâlâ kapalı; çünkü determinism kanıtı temsilî fixture'larda güçlü olsa da gerçek plan export'ları ve daha büyük çok-oda / çok-opening senaryoları için kapsam sınırlı.
- Provenance / manifest / metrics katmanında run-bağımlı alanlarla çekirdek sözleşme sapmasının sınırı tüm araçlarda tam standartlaştırılmış değil.
- Beklenen negatif akışların tümünde düşük-gürültülü logging deseni henüz genelleştirilmedi.
- Sonraki en doğru adım: regression runner ve golden output katmanında bu ayrımı netleştirmek; ardından daha temsilî plan fixture'larıyla semantic/space/BIM core determinism yüzeyini büyütmek.