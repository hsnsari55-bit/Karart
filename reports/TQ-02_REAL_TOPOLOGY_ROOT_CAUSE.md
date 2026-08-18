# Kanıt

- Yetkili baseline `main@5f5baf23322dc19633440ff611135557eaf6b2e4` ve DXF SHA-256 `289b586570f0d915cae1707ccb234b84bd0527bd1412189b5b238811aa9a721c` olarak kilitlenmiştir.
- İki bağımsız izole Phase 1 koşusu aynı Geometry SHA-256 `d3153dc7f613c5d58e4bbda82fb2c3056f01c806eb76a7d696e24e89568bf9c3` ve Topology SHA-256 `3f09f1892886a43f94c17cc325142b8b6c2918a11fa7804ebc84fde3e7187aba` üretmiştir.
- Baseline 2782 node, 2602 edge, 298 loop, 478 component, 1090 dangling node ve 3 tiny loop üretmiştir. Constraint Solver graph core'u değiştirmemiştir.
- 1090 dangling kaydın 9'u yalnız `candidate_endpoint_to_segment`, 1081'i `unresolved_no_candidate_within_5mm` olarak sınıflandırılmıştır; bu etiketler düzeltme önerisi değil, bounded aday kanıtıdır.
- Geometrik provenance 132 kaydı `inferred_unique_tuple`, 958 kaydı `ambiguous_or_unavailable` olarak ölçmüştür. Atfedilen layer dağılımı `DUVAR_0.30_gkhn=21`, `Duvar=111`, `UNKNOWN=958` olup exact DXF entity lineage mevcut değildir.
- Selection envanterinde 2088 duvar `DUVAR_0.30_gkhn=291`, `Duvar=1743`, `k duvar=54` dağılımındadır. Source/modelspace içeriği gözlenen girdi ve aday katkıdır; tek başına nedensellik veya root cause kanıtı değildir.

# Risk Analizi

- Topology graph DXF entity kimliğini taşımadığından exact edge-to-entity provenance mevcut değildir; geometrik attribution kanıt-sınırlıdır.
- Mimari ground truth olmadan open topology'nin legitimate opening, yanlış selection veya eksik source content olma oranı ölçülemez.
- Raw layer yoğunlukları (`0=5600`, `k yazi=3079`, `agac=2967`, `tarama=2364`, `pencere=1748`, `Duvar=1631`) source içeriğinin heterojenliğini gösterir; hangi entity'nin mimari olarak doğru duvar olması gerektiğini kanıtlamaz.

# Önerilen Çözüm

- Önce local deterministic artifact paketindeki layer/block/entity yoğunlukları insan-onaylı ground truth ile karşılaştırılmalıdır.
- Frozen Topology Engine ancak bağımsız, permutation/translation invariant minimal reproducer matematiksel defect gösterirse ADR ile değiştirilmelidir.

# Uygulanan Değişiklik

- `backend/tq02_topology_root_cause.py` exact-source read-only pipeline, attribution, tolerance ablation, conditional core-fix gate ve atomik local publisher sağlar.
- `backend/tests/test_tq02_topology_root_cause.py` ambiguity, constraint karşılaştırma, gate denial, path safety, exact artifact set ve byte determinism sözleşmelerini doğrular.
- `provenance_inventory.json` yalnız lineage/attribution güven özetini, `selection_experiments.json` yalnız raw ve seçilmiş entity/layer/block envanterlerini taşır; iki artifact farklı deterministik sözleşmelere sahiptir.
- Frozen Geometry/Topology/Canonical/P2 dosyaları değiştirilmemiştir.

# Doğrulama

- Production tolerance 5.0 mm değişmez; 2.5/4/5/6/7.5/10 mm koşuları aynı production Geometry çıktısı üzerinde topology-only ablation olarak etiketlenir.
- Tolerance sonuçları sırasıyla `(components/dangling)` olarak 2.5 mm `507/1117`, 4.0 mm `486/1101`, 5.0 mm `478/1090`, 6.0 mm `475/1079`, 7.5 mm `469/1057`, 10.0 mm `467/1047` üretmiştir. Her bant kendi tekrar hash'iyle deterministiktir; ground truth olmadığından azalan dangling sayısı accuracy artışı sayılmaz.
- Validator bypass edilmez ve topology FAIL olduğunda Semantic/Canonical/P2/Blender/IFC/consumer çalıştırılmaz.
- Conditional core-fix gate'in exact source, locked baseline, iki deterministik koşu, validator reproduksiyonu ve Constraint dışlama kontrolleri geçmiştir; topology izolasyonu, minimal reproducer, permutation/translation invariance ve tartışmasız matematiksel beklenen sonuç kontrolleri geçmemiştir. Karar `NO_CORE_FIX_INSUFFICIENT_PROOF` ve `frozen_core_edited=false` olmuştur.
- Yerel coordinate-bearing SVG'ler `outputs/tq02/proje/topology_overview.svg` ve `outputs/tq02/proje/dangling_candidates.svg` altında ignored tutulur; iki bağımsız 13-artifact paketinin exact set, manifest hash/size ve raw-byte eşitliği Phase 6'da PASS almıştır.
- Phase 6 doğrulaması py_compile, focused topology/validator/constraint matrisi (`79 passed, 7 subtests passed`), declared regression (`14 tests`), full pytest (`182 passed, 7 subtests passed`), domain-hash ile izole manifest/metrics testleri (`16 passed`) ve TypeScript `tsc --noEmit` için PASS almıştır.
- Repo-wide `manifest:verify` ve `metrics:verify`, TQ-02'nin ayrı `outputs/tq02` paketi nedeniyle değil, çalışma alanındaki git-ignored broad `outputs/*.json` içeriği tracked golden fixture ile uyuşmadığı için FAIL vermiştir. Broad outputs ve golden dosyalar değiştirilmemiştir.

# Kalan Riskler

- Nihai kanıt sınıfı `mixed_source_selection_geometry_insufficient_intent`; Topology Engine defect kanıtlanmamıştır ve core fix gate kapalıdır.
- Entity lineage kontratı olmadan attribution kesinleştirilemez; artifact paketi ground truth değildir ve accuracy metriği içermez.