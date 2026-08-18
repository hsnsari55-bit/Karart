# RV-02 Gerçek Proje Dikey Dilim Mühendislik Raporu

## 1. Kanıt

- Koruma ön koşulu tamamlandı: `wip/pre-rv02-local-changes-20260818` branch'indeki `7b12b13c4e94ca3c377436a6d7c37d63575cee9b` commit'i yalnız önceden belirlenen dört tracked kullanıcı değişikliğini içeriyor. RV-02 branch'i temiz `main` tabanı `22b82f642bc3baa5a2095f93b239de972edc1192` üzerinden oluşturuldu.
- Yetkili ve stage edilmemiş kaynaklar:
  - `data/proje.dwg`: SHA-256 `572461cb97d06a7296eed03205f09303d7fa3b560db348d0812f47c40bd00c20`
  - `data/proje.dxf`: SHA-256 `289b586570f0d915cae1707ccb234b84bd0527bd1412189b5b238811aa9a721c`
- Feature branch oluşturulmadan önce `data/proje.dxf` için fiziksel EOF, standart `ezdxf.readfile`, `doc.audit()` ve birim kapıları geçti: DXF sürümü `AC1027`, `$INSUNITS=4` (milimetre), audit sonucu `0` hata / `0` düzeltme. `Layout1` ve `Layout2` boş; `Model` modelspace 13.665 entity içeriyor. Bu nedenle authoritative seçim tüm `Model` modelspace, `block_filter=None`, repair/promotion olmadan yapıldı.
- `backend/run_real_field_validation.py`, yasaklı `datasets/twin_villa/**` hard-code'u yerine zorunlu positional `source_path` alıyor ve bunu değiştirmeden `RegressionTester.run_on_file(source_path)` metoduna aktarıyor. `backend/tests/test_run_real_field_validation.py` hem başarısız hem başarılı sonuç sözleşmesinde exact path aktarımını doğruluyor.
- Gerçek komut `python backend\run_real_field_validation.py data\proje.dxf` exit code `1` ile, yanlış başarı beyan etmeden mandatory validation kapısında durdu.
- Aynı gerçek koşudaki deterministik çekirdek kanıtı:
  - Geometry: iki çalıştırma eşit, SHA-256 `d3153dc7f613c5d58e4bbda82fb2c3056f01c806eb76a7d696e24e89568bf9c3`; 1.809 başlangıç entity'si, 2.088 segment çıkışı, 29 zero-length kaldırma, 339 overlap merge, 36 sliver filtreleme ve 989 snapped point.
  - Topology: iki çalıştırma eşit, SHA-256 `3f09f1892886a43f94c17cc325142b8b6c2918a11fa7804ebc84fde3e7187aba`; 2.782 node, 2.602 edge, 298 closed loop, 510 snapped T-junction ve 63 filtered short segment.
- `outputs/topology_validation_proje.json:4-18` mandatory `TopologyValidator` sonucunu `FAIL` olarak kaydediyor. `outputs/topology_health_proje.json` 478 connected component gösteriyor ve şu kontroller `false`: `single_connected_component`, `no_dangling_nodes`, `no_tiny_loops`, `no_tiny_sliver_faces`. Tiny loop kimlikleri `[0, 1, 2]`.
- Odaklı regresyon komutu `python -m pytest backend/tests/test_run_real_field_validation.py backend/tests/test_topology_validator.py backend/tests/test_topology_engine_determinism.py -q` sonucu: `44 passed, 7 subtests passed in 1.91s`.
- `outputs/` içinde `proje` adına bağlı yalnız `topology_health_proje.json` ve `topology_validation_proje.json` bulunuyor. RV-02'ye özgü Canonical BIM, P2, Blender, GLB, OBJ veya render artifact'i üretilmedi.

## 2. Risk Analizi

- Topoloji grafiğinin 478 ayrı bileşene ayrılması ve çok sayıdaki dangling node, tek ve doğrulanabilir bina topolojisi varsayımını ihlal ediyor. Bu veri Canonical BIM'e geçirilirse odalar, duvar ilişkileri ve açıklık ebeveynlikleri güvenilir olmaz.
- Tiny loop ve tiny sliver face kontrollerinin başarısız olması, yanlış oda/yüz üretimi ve tolerans kaynaklı sahte geometriler riski taşıyor.
- Parser sırasında görülen `DIMASSOC` virtual-copy uyarıları kaynak audit'inde bozulma kanıtı değildir; ancak INSERT içeriğinin sanal açılımında ezdxf yardımcı kopyalama sınırlaması olarak izlenmelidir. Bu uyarılar smart repair veya legacy snapshot kullanımını haklı çıkarmaz.
- Global `outputs/` dizininde önceden mevcut legacy/generic artifact'ler bulunduğundan, downstream yokluğu yalnız genel dosya yokluğuyla kanıtlanamaz. Kanıt RV-02'ye özgü adlandırma, temiz Git durumu ve mandatory validator exception'ından sonraki runner kontrol akışına dayanır.

## 3. Önerilen Çözüm

- Mandatory TopologyValidator kapısını bypass etmeden, 478 bileşenin katman/entity türü ve uzamsal cluster bazında kaynağını izole eden ayrı bir topology investigation yürütülmelidir.
- Dangling endpoint dağılımı ile Geometry Engine snapping/short-segment kararları karşılaştırılmalı; yalnız ölçülebilir ground-truth veya regression fixture kanıtı bulunan tolerans/algoritma değişiklikleri önerilmelidir.
- Tiny loop `[0, 1, 2]` ve sliver yüzler, kaynak entity lineage'ı korunarak minimal reproducer'lara indirgenmelidir. Çözüm Parser → Geometry → Topology sınırlarını ve Canonical BIM SSoT sözleşmesini korumalıdır.
- Canonical BIM/P2 ve tüm 3D consumer'lar ancak aynı yetkili kaynakla mandatory topology validation `PASS` olduktan sonra çalıştırılmalıdır.
- Öncelik sorusunun yanıtı **EVET**: explicit source injection, yasaklı fixture'ın yanlışlıkla seçilmesini engelleyerek gerçek kaynak doğrulamasının tekrarlanabilirliğini ve traceability'sini ölçülebilir biçimde artırıyor; focused test exact path aktarımını kanıtlıyor. Bu değişiklik topoloji kusurlarını çözmez ve öyle sunulmamaktadır.

## 4. Uygulanan Değişiklik

- `backend/run_real_field_validation.py` içine `argparse` tabanlı zorunlu DXF source path injection eklendi; hard-coded `datasets/twin_villa/dxf/kaRar.dxf` kaldırıldı.
- `main(source_path)` sonucu mevcut başarı/başarısızlık exit-code sözleşmesini koruyarak JSON çıktısını üretmeye devam ediyor.
- `backend/tests/test_run_real_field_validation.py`, her iki sonuç yolunda `run_on_file` çağrısının tam olarak `data/proje.dxf` ile yapıldığını doğrulayacak şekilde güncellendi.
- Parser, Geometry Engine, Topology Engine, Constraint Solver, Canonical BIM, Blender script'i veya export consumer'larında değişiklik yapılmadı.
- Yetkili `data/proje.dwg` ve `data/proje.dxf` dosyaları değiştirilmedi ve stage edilmedi. Smart repair, repaired snapshot ve yasaklı reference/twin-villa girdileri kullanılmadı.

## 5. Doğrulama

- Preflight source gates: fiziksel EOF `PASS`; standard read `PASS`; audit `PASS`; millimetre units `PASS`; tüm dolu `Model` modelspace seçimi `PASS`.
- Focused tests: `44 passed, 7 subtests passed`.
- `git diff --check`: whitespace hatası yok; yalnız Windows çalışma ağacı için LF→CRLF bilgilendirme uyarıları var.
- Gerçek pipeline: Parser `SUCCESS`; Geometry `SUCCESS` ve deterministic; Topology `SUCCESS` ve deterministic; mandatory TopologyValidator `FAIL`.
- Pipeline, Semantic/Space/Canonical BIM/P2 adımlarından önce durdu. Blender/GLB/OBJ/render komutu çalıştırılmadı.
- RV-02 durumu **BLOCKED_RV02_TOPOLOGY_VALIDATION** olarak raporlanır; modül tamamlandı, production-ready veya yüzde yüz başarılı olarak işaretlenmez.

## 6. Kalan Riskler

- 478 connected component ve dangling node kümesinin kök nedeni henüz entity lineage ile sınıflandırılmadı.
- Tiny loop ve sliver face üretiminin kaynak çizim niyeti mi, Geometry Engine toleransı mı, yoksa Topology Engine yüz çıkarımı mı olduğu henüz ayrıştırılmadı.
- Canonical BIM schema/P2 validation bu koşuda çalıştırılmadığı için gerçek proje için canonical contract uygunluğu hakkında olumlu sonuç yoktur.
- Downstream 3D/IFC sonuçları bilinçli olarak üretilmedi; topology gate geçmeden kalite veya doğruluk iddiasında bulunulamaz.
- `DIMASSOC` virtual-copy uyarılarının etkisi, yalnız reproducer ve entity lineage kanıtı elde edilirse ayrı bir teknik borç olarak ele alınmalıdır.