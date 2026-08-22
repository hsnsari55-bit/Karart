# KaRar Decisions Log

Bu dosya, tekrar aynı tartışmaları yapmamak ve daha önce alınmış teknik kararları unutup geri açmamak için tutulur.

## Kullanım Kuralı
- Her kayıt kısa ve kanıt odaklı olmalı.
- Karar, ilgili dosya/test/çıktı ile bağlanmalı.
- “Resolved” olmuş konu, yeni teknik kanıt yoksa geri açılmamalı.

---

## Karar Kaydı Şablonu

### [Tarih] Kısa Başlık
- Durum: Proposed / Accepted / Rejected / Superseded
- Bağlam:
- Karar:
- Gerekçe:
- Kanıt:
- Etkilenen dosyalar:
- İlgili test/komut:
- Takip notu:

---

### [2026-07-28] Validator-health-report hizalaması regression ile korunacak
- Durum: Accepted
- Bağlam: TopologyHealthReporter bazı bütünlük kontrollerini non-blocking raporda gösterirken TopologyValidator bunları blocking davranışla uyguluyor; aradaki farklar ileride dashboard/rapor yorumlarını zayıflatabilir.
- Karar: Davranış farkları veya şema boşlukları büyük refactor ile değil, tek tek regression test + minimal kod değişikliği yaklaşımıyla kapatılacak.
- Gerekçe: Determinizm korunurken yeni yan etki riski düşer ve hangi farkın ne zaman kapatıldığı açık kalır.
- Kanıt: `backend/tests/test_topology_validator.py`, `backend/tests/test_topology_health_report.py`, `backend/topology_validator.py`
- Etkilenen dosyalar: `backend/topology_validator.py`, `backend/tests/test_topology_validator.py`
- İlgili test/komut: `python -m pytest backend/tests/test_topology_validator.py backend/tests/test_topology_health_report.py -q`
- Takip notu: sonraki oturumda `closed_loops` / `all_loops_closed` ve `no_tiny_sliver_faces` / `no_tiny_loops` semantik farkları öncelik filtresinden geçirilerek değerlendirilmeli.

### [2026-07-29] Program yönü kanıt-güdümlü deterministik çekirdek olarak kilitlendi
- Durum: Accepted
- Bağlam: Projede aynı anda çok sayıda modül ve yardımcı iş akışı bulunduğu için odak dağılması, erken consumer geliştirme ve kanıtsız ilerleme riski yükseliyor.
- Karar: KaRar bundan sonra bir özellik projesi gibi değil, kanıt-güdümlü deterministik çekirdek programı olarak yürütülecek; öncelik sırası P0 ölçüm/güvence → P1 geometry hardening → P2 topology hardening → P3 canonical BIM contract → P4 semantics → P5 consumers olacak.
- Gerekçe: Bu yön, çekirdek doğruluk, determinizm, sağlamlık ve performans artışını ölçülebilir hale getirir; UI/IFC/Blender gibi downstream alanların çekirdek olgunlaşmadan odağı bozmasını önler.
- Kanıt: `PROJECT_STATE.md`, `PRODUCTION_READINESS_CHALLENGE.md`, `BENCHMARK_AND_QUALITY_FRAMEWORK.md`, `KARAR_10_YEAR_CTO_RESEARCH.md`, `docs/STRATEGIC_ROADMAP.md`
- Etkilenen dosyalar: `docs/STRATEGIC_ROADMAP.md`, `docs/CURRENT_FOCUS.md`, `docs/LATEST_HANDOFF.md`, `docs/LOW_CONTEXT_WORKFLOW.md`, `scripts/dev-tools.mjs`
- İlgili test/komut: `npm run context:guard`
- Takip notu: aktif teknik iş yine topology validator / health report hizalamasıdır; stratejik karar, aktif işi değiştirmez ama sonraki önceliklendirme sırasını sabitler.

### [2026-07-29] Topology health diagnostics component-bazlı ve deterministik raporlanacak
- Durum: Accepted
- Bağlam: Topology health raporu toplam sayaçlar veriyordu ancak dangling / isolated node sorunlarının hangi connected component içinde oluştuğu açık görünmüyordu; bu da regression gate başarısızlıklarında kök neden analizini yavaşlatıyordu.
- Karar: `TopologyHealthReport` graph metrikleri component üyeliği, component boyut dağılımı ve issue-component eşleşmesini deterministik alanlar olarak üretecek; regression gate mesajı da bu component özetlerini taşıyacak.
- Gerekçe: Bu görünürlük artışı P0 Ölçüm ve Güvence Katmanı içinde doğrudan determinism ve regression risk reduction faydası sağlar; büyük refactor yapmadan teşhis kalitesini artırır.
- Kanıt: `backend/topology_health_report.py`, `backend/run_regression_tests.py`, `backend/tests/test_topology_health_report.py`, `backend/tests/test_regression_topology_report_path.py`, `docs/algorithm-state/topology_engine.md`
- Etkilenen dosyalar: `backend/topology_health_report.py`, `backend/run_regression_tests.py`, `backend/tests/test_topology_health_report.py`, `backend/tests/test_regression_topology_report_path.py`, `docs/algorithm-state/topology_engine.md`
- İlgili test/komut: `python -m unittest backend.tests.test_topology_health_report backend.tests.test_regression_topology_report_path`
- Takip notu: sonraki oturumda validator ile health report arasındaki bir sonraki kapsama farkı yine tek regression test + minimal değişiklik yaklaşımıyla seçilmeli.

### [2026-08-22] AG-04 boundary connector'ları transient ve non-physical kalacak
- Durum: Accepted
- Bağlam: Kapı/pencere açıklıkları fiziksel duvar edge'i üretmeden topology sürekliliğine katkı sağlamalı; aksi halde wall/loop/mesh ve Canonical BIM sözleşmesi bozulur.
- Karar: Typed boundary connector'ları ayrı `logical_connectors` koleksiyonunda, `physical: false` ve fail-closed üretim/doğrulama ile tutulacak; yalnız effective degree/component/dangling hesabına katılacak, fiziksel `nodes/edges/loops`, Canonical BIM ve Domain Hash v1 dışında kalacak.
- Gerekçe: Fiziksel geometriyi değiştirmeden ölçülebilir topology sürekliliği sağlar ve downstream consumer'ların tek gerçek kaynağı olan Canonical BIM'i transient audit kanıtından ayırır.
- Kanıt: `backend/transient_boundary_connectors.py`, `backend/drawing_region_audit.py`, `DOMAIN_HASH_SPEC.md`
- Etkilenen dosyalar: `backend/constraint_solver.py`, `backend/topology_health_report.py`, `backend/topology_validator.py`, `backend/drawing_region_audit.py`
- İlgili test/komut: `python -m unittest backend.tests.test_transient_boundary_connectors backend.tests.test_constraint_solver backend.tests.test_topology_health_report backend.tests.test_topology_validator backend.tests.test_drawing_region_audit backend.tests.test_regression_bim_core_opening_parent_wall`
- Takip notu: Connector'ların physical topology veya Canonical BIM'e persist edilmesi ya da Domain Hash v1 payload'ına eklenmesi sözleşme ihlalidir; yeni BIM entity ihtiyacı ayrı schema/hash spec kararı gerektirir.
