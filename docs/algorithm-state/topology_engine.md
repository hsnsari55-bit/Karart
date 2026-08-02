# Topology Engine Durum Kartı

## Amaç
Temiz segmentlerden düğüm/kenar ağı oluşturmak, noding yapmak ve kapalı yüz/oda adaylarını deterministik biçimde çıkarmak.

## Giriş / Çıkış
- Giriş: Geometry Engine temiz segment çıktısı
- Çıkış: graph, planar edge ağı, room/face adayları

## Mevcut Deterministik Davranış
- Kaynak segmentler `tolerances.min_segment_length_mm` eşiğinin altındaysa topolojiye alınmaz.
- `unary_union` sonrası oluşan mikro/near-degenerate planar kenarlar da aynı minimum uzunluk sözleşmesiyle elenir.
- Node/edge/loop kanonikleştirmesi ile çıktı sırası deterministik tutulur ve SHA-256 ile kilitlenir.
- T-junction snap yalnızca segment iç projeksiyonlarında (`0 < t < 1`) uygulanır; uç nokta yapışmaları engellenir.
- Topology health diagnostics component bazında deterministik üretilir; aynı graph için component üyelikleri, boyut dağılımı ve issue-context alanları sabit sırada raporlanır.

## İnvariant'lar
- Ham geometriyi değiştirmez
- Semantik etiketleme yapmaz
- Ağ kuralları deterministik olmalıdır
- Near-degenerate drafting noise graph node/edge sayısını yapay olarak artırmamalıdır

## Bilinen Riskler
- Kapalı poligon bulma, küçük açıklıklarda hassas olabilir
- Unary union / noding davranışı tolerans yönetimine bağımlı olabilir
- `min_segment_length_mm` çok agresif yükseltilirse gerçek kısa geometri de elenebilir

## Gözlemlenebilir QA Sinyalleri
- `initial_segments`
- `filtered_short_segments`
- `t_junctions_snapped`
- `final_nodes`
- `final_edges`
- `closed_loops_found`
- `connected_components`
- `component_sizes`
- `component_size_histogram`
- `dangling_nodes`
- `dangling_node_component_indexes`
- `isolated_nodes`
- `isolated_node_component_indexes`

## Topology Health Report Hizalaması
- `backend/topology_health_report.py`, validator'ın bloklayıcı kurallarını non-blocking health görünürlüğüne taşırken component bağlamını da raporlar.
- Health report graph metrikleri artık yalnızca toplam sayaç değil, aşağıdaki deterministik teşhis alanlarını da içerir:
  - `component_node_groups`
  - `component_sizes`
  - `component_size_histogram`
  - `dangling_node_components`
  - `isolated_node_components`
- `DANGLING_NODES`, `ISOLATED_NODES`, `DISCONNECTED_COMPONENTS` diagnostic kodları issue'nin hangi connected component içinde oluştuğunu açıkça verir.
- `backend/run_regression_tests.py` health gate mesajı, regression başarısızlığında kök neden analizini hızlandırmak için `component_sizes`, `dangling_components` ve `isolated_components` özetini üretir.

## Ölçüm ve Güvence Etkisi
- Bu görünürlük artışı P0 Ölçüm ve Güvence Katmanı hedefiyle uyumludur.
- Amaç, validator ↔ health report kapsama farklarını kapatırken topolojik bozulmaların component düzeyinde izlenmesini sağlamaktır.
- Bu değişiklik downstream üreticilere değil, doğrudan çekirdek topology determinism ve regression risk reduction alanına hizmet eder.

## Önce Okunacak Dosyalar
- `backend/topology_engine.py`
- `backend/topology_validator.py`
- `backend/topology_health_report.py`
- `backend/tests/test_topology_validator.py`
- `backend/tests/test_topology_engine_determinism.py`

## Önce Çalıştırılacak Komut
- `python -m unittest backend.tests.test_topology_engine_determinism backend.tests.test_topology_validator backend.tests.test_topology_health_report backend.tests.test_modern_pipeline`
