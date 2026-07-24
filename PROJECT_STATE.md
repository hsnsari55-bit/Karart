# KaRar Project State

## Governance & Documentation Hierarchy
KaRar is structured with the following 5-tier governance hierarchy:
1. **Manifesto**: Product vision (immutable).
2. **Architecture Contract**: Core architecture (rarely changes).
3. **Pipeline Contract**: Inter-module data flow.
4. **Engineering Invariants**: Invariant engineering rules.
5. **10-Year CTO Vision (`KARAR_10_YEAR_CTO_RESEARCH.md`)**: Long-term technology, academic references, and R&D direction.

## CTO Working Model (3-Track Management)
1. **Production Track**: Daily development and test suite for core engines (Geometry, Topology, Canonical BIM, Benchmark).
2. **Research Track**: Advanced algorithms and academic studies under the 10-year CTO vision (OpenCASCADE, Shewchuk predicates, TCC).
3. **Validation Track**: Rigorous proof via real DXF datasets, benchmarks, and regression tests before any algorithm graduation.

## Mandatory Quality Gates (Quality Gates & Verification Framework)
After every major development milestone or core algorithmic change, the following 5 automated verification reports must be generated and verified prior to release approval:
1. **Repository Verification Report**: Tracks modified files, diffs, and git commits.
2. **Regression Report**: Documents passed/failed unit tests and integration test suites.
3. **Benchmark Report**: Measures real DXF processing success rates, execution time (ms/MB), and memory consumption (MB).
4. **Canonical BIM Validation Report**: Verifies SSoT JSON schema compliance, topological watertightness, and relational entity integrity.
5. **Architecture Compliance Report**: Verifies architectural boundary invariants (e.g. Geometry Engine makes no semantic decisions, Topology Engine does not alter raw geometry, Canonical BIM remains the sole SSoT).

### Engineering Evidence Rule
Every "completed" feature or architectural improvement must be proven by 4 distinct pieces of evidence:
1. **Code Evidence**: Git commit and modified files list.
2. **Test Evidence**: Regression and benchmark test results.
3. **Architectural Evidence**: Architecture Compliance report.
4. **Data Evidence**: Real-world DXF dataset execution outputs.

### Traceability Rule
Every technical modification must be end-to-end traceable along this exact chain:
`Requirement ──► Architecture Decision ──► Implementation ──► Commit ──► Tests ──► Benchmark ──► Release`

### Release Approval Pipeline
```
Code Change ──► Repo Verification ──► Regression Tests ──► Benchmark Tests ──► BIM Validation ──► Architecture Compliance ──► Release Approval
```

## Production Readiness Challenge & Stress Test (`PRODUCTION_READINESS_CHALLENGE.md`)
- **CTO Stress Test Completed**: Evaluated KaRar’s locked architecture from the perspective of Autodesk, OpenCASCADE, CGAL, IfcOpenShell, and BlenderBIM chief architects.
- **Top 20 Production Blockers & 10 Failure Categories Analyzed**: Documented degenerate geometry, room leaks, floating-point precision issues, multi-vendor DXF incompatibilities, performance bottlenecks ($O(N^2)$), and mandatory validation rules.
- **v1.0 Stability Gate**: Established non-negotiable prerequisites (Shewchuk predicates, adaptive epsilon, STRtree spatial indexing, SHA-256 SSoT GUID hashing, Euler-Poincare topology validation, and golden master regression test suite).

## Benchmark, Accuracy & Telemetry Framework (`BENCHMARK_AND_QUALITY_FRAMEWORK.md`)
- **1000+ Real-World DXF Benchmark Suite**: Vendor-balanced dataset (AutoCAD, BricsCAD, ZWCAD, DraftSight, LibreCAD) with difficulty classification (Class A-D).
- **Quantitative Accuracy Metrics**: Wall $F_1$-score ($\ge 0.985$), Room Closure Rate ($\ge 99.0\%$), Opening Ownership Accuracy ($\ge 99.5\%$), Schema & Topological Consistency ($100\%$).
- **Deterministic Regression Infrastructure**: SHA-256 cryptographic SSoT state locking, execution time limit ($\le 150\text{ ms/MB}$), peak memory limit ($\le 256\text{ MB}$).
- **Privacy-Preserving Production Telemetry**: Zero-knowledge structural telemetry (no raw geometry or IP transmitted) logging repair pattern frequencies and execution bottlenecks.

## Current Status
- **Phase 0 (Public API Freeze & Golden Dataset Baseline Lock)**: **Tamamlandı ve Doğrulandı**. Public Python API (`backend/main.py`), CLI arayüzü ve `outputs/bim_model.json` veri sözleşmesi kilitlendi. 7 gruptan oluşan resmi Golden Dataset sınıflandırması tanımlandı.
- **Phase 1 (Repository Refactoring & Layer Isolation)**: **Koşullu Onay Alındı / Operasyonel Doğrulama Aşamasında**. Domain-oriented dizin yapısı (`geometry/`, `semantics/`, `bim/`, `validation/`, `exporters/`, `cli/`, `common/`, `tests/`) ve tek yönlü bağımlılık kuralı ($\text{common} \leftarrow \text{geometry} \leftarrow \text{semantics} \leftarrow \text{bim} \leftarrow \text{validation}$) tanımlandı. `.github/workflows/quality.yml` CI otomasyonu devreye alındı.
- Tüm linters ve TypeScript tip kontrolleri sıfır hata ile geçmektedir (`npm run lint` & `tsc --noEmit` -> PASS).

## Progress Summary (Aktif Geliştirme Alanları)
1. **Geometry Engine (Aktif / Geliştiriliyor)**:
   - AutoCAD koordinatlarının ortak orijine normalizasyonu, gürültü temizliği ve kısa çizgilerin elenmesi (Repair).
   - Gerçek DXF analizi kapsamında: toplam okunan 102.191 grup kodu çiftinden 633 adet normalize edilmiş geometri segmenti.
2. **Topology Engine (Aktif / Geliştiriliyor)**:
   - Duvar çizgileri arasında kenetleme (Snapping) ve kapalı oda poligonlarının tespiti.
   - Topolojik ağ yapısının kurulması (94 Düğüm, 321 Kenar).
3. **Semantic Enrichment (Planlandı / Geliştiriliyor)**:
   - Geometrik ve topolojik verilere göre kapı, pencere, kolon ayrımı ve oda işlevlerinin etiketlenmesi.
4. **Canonical BIM Model (Aktif / Geliştiriliyor)**:
   - Blender, IFC ve arayüzün besleneceği tek doğruluk kaynağı olan resmi JSON Şeması sözleşmesi.
5. **Pipeline Contract & Test Strategy (Aktif / Geliştiriliyor)**:
   - Katmanlar arası otomatik geçişlerin birim (Unit) ve entegrasyon testleriyle doğrulanması.

## Next Steps
- Geometri ve topoloji algoritmalarındaki kenetleme (snapping) hassasiyetini ve kapalı poligon bulma determinizmini artırmak.
- Canonical BIM JSON model şemasını sıkılaştırmak ve TypeScript arayüz tipleri ile korumak.
- Blender 3D Builder ve IFC Export modüllerini, ancak Canonical BIM Model tamamen kararlı hale geldikten sonra bu ortak sözleşme üzerinden inşa etmek.
- UI ve bulut özelliklerini, çekirdek motor tamamen olgunlaşana dek salt görselleştirme katmanı olarak tutmak.

## Resolved & Archived Technical Debts
- **[RESOLVED & ARCHIVED] Sabit Windows Yolları (Hardcoded C:\ Paths)**: `backend/bim_validator.py`, `backend/geometry_validator.py` ve `backend/geometry_core.py` içindeki Windows odaklı mutlak dosya yolları kaldırıldı. Dinamik, çoklu platform uyumlu `PathManager` entegrasyonu sağlandı.
- **[RESOLVED & ARCHIVED] Kırık Birim Testleri (Broken Unit Tests & Imports)**: `backend/window_detector.py` içindeki eksik `config` kütüphanesi ve `DXF` import hatası nedeniyle çöken test süiti tamamen onarıldı. `python3 -m unittest` komutuyla 31 adet birim testinin tamamı başarıyla yeşile döndürüldü (`OK`).
- **[RESOLVED & ARCHIVED] CTO Architectural Audit & Determinism Gate Approval**:
  - ✅ **Entity Order Invariance**: Verified via canonical byte sorting & SSoT SHA-256 state locking.
  - ✅ **Multi-Directional UTM Test Suite**: Verified 100% topological isomorphism across all 4 coordinate quadrants & $10^9\text{mm}$ diagonal offset.
  - ✅ **Tolerance Policy**: Replaced hardcoded magic numbers with `ToleranceManager` (adaptive unit scaling for $INSUNITS & bounding box).
  - ✅ **Ground Truth Accuracy Engine**: Implemented `GroundTruthEngine` evaluating Wall $F_1$, Room IoU, and Opening Association Accuracy.

- **[RESOLVED & ARCHIVED] KaRar v1.x Architecture Freeze & Engineering Governance Contract**:
  - ✅ **Architecture Freeze**: Core reference pipeline (Parser ──► Geometry ──► Topology ──► Constraint Solver ──► Canonical BIM SSoT ──► Validator ──► Consumers) is strictly locked. No new architectural layers or core engines will be introduced for v1.x.
  - ✅ **Single Source of Truth (SSoT)**: `bim_model.json` remains the sole, inviolable canonical engineering model contract.
  - ✅ **Validation Before Export**: Mandatory quality gate enforced before any Blender 3D or IFC generation.
  - ✅ **Evidence-Driven Engineering**: Development complete only with Code + Test + Architecture + Data evidence.
  - ✅ **End-to-End Traceability**: Requirement ──► Architecture Decision ──► Implementation ──► Commit ──► Tests ──► Benchmark ──► Release chain active.
  - ✅ **P1-P6 Technical Focus**: Continuous maturation on real DXF benchmark suite, Ground Truth accuracy, heterogeneous CAD compatibility, curved geometry (ARC/SPLINE/ELLIPSE), performance profiling, and Canonical BIM schema versioning.

1. **P1 — Real-World DXF Benchmark Pool Expansion**: Scaling dataset to 100+ multi-vendor drawings (AutoCAD, BricsCAD, ZWCAD, DraftSight, LibreCAD) including non-standard and dirty drawings.
2. **P2 — Ground Truth Accuracy Engine**: Continuous evaluation of Precision, Recall, $F_1$, and Room IoU across diverse architectural floor plans.
3. **P3 — Curved Geometry Support**: Deterministic handling of `ARC`, `SPLINE`, and `ELLIPSE` primitives in Geometry Engine and Topology Engine.
4. **P4 — Large-Scale Drawing Performance**: Optimization of R-Tree spatial index ($O(N \log N)$), memory profiling, and execution time under $150\text{ ms/MB}$ for $100,000+$ entity plans.
5. **P5 — Canonical BIM Schema Versioning**: Long-term backward compatibility and schema evolution contract management for downstream IFC and 3D generators.



