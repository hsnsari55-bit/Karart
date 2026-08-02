# KaRar

KaRar, 2D CAD mimari çizimlerden deterministik bir **Canonical BIM Model** üretmeyi hedefleyen bir mühendislik hattıdır.

## Hızlı Başlangıç

### 1) Ortamı kontrol et

```bash
npm run doctor
```

Bu komut şunları kontrol eder:
- Node.js / npm erişimi
- proje içi `venv` veya `.venv`
- sistem Python erişimi
- temel proje klasörleri

### 1.1) Bağlam sapmasını erken yakala

```bash
npm run context:guard
```

Bu komut şunları gerçek verilerle raporlar:
- `docs/CURRENT_FOCUS.md`, `docs/LATEST_HANDOFF.md`, `docs/DECISIONS_LOG.md` var mı
- aktif hedef modül / problem / doğrulama komutu çıkarılabiliyor mu
- git branch / HEAD bilgisi
- çalışma ağacındaki kirli dosyalar aktif bağlamla hizalı mı
- risk seviyesi (`LOW`, `MEDIUM`, `HIGH`) ve doğrudan önerilen sonraki adım

### 1.2) Tek komutla hard-mode hazır ol

```bash
npm run preflight
```

Bu komut şunları sırasıyla yapar:
- `doctor`
- `context:guard`
- hard-mode algoritma geliştirme için bağlamın **LOW risk** seviyesinde olduğunu doğrular

`MEDIUM` veya `HIGH` risk durumunda akışı bilinçli olarak durdurur.

### 2) Python ortamını hazırla

```bash
npm run setup:python
```

Bu komut:
- proje için `venv` oluşturur
- `pip` günceller
- backend için gerekli Python bağımlılıklarını kurar

### 3) Tüm temel kontrolleri çalıştır

```bash
npm run check
```

Bu komut sırasıyla:
- TypeScript tip kontrolü
- ortam doğrulaması
- Python pipeline testlerini

çalıştırır.

### 4) P0 doğrulama hattını tek komutta çalıştır

```bash
npm run verify:p0
```

Bu komut:
- `topology:health`
- `manifest:verify`
- `metrics:verify`

akışını tek zincirde çalıştırır ve topology health özetini ayrıca görünür biçimde raporlar.

### 5) Hard-mode algoritma döngüsünü başlat

```bash
npm run hard:topology
```

Bu komut:
- `preflight`
- hedefli çekirdek test
- `verify:p0`

adımlarını tek akışta çalıştırır. Böylece P0 çekirdek geliştirme sırasında kanıt zinciri bozulmadan ilerlenir.

## Faydalı Komutlar

```bash
npm run dev           # geliştirme sunucusu
npm run build         # frontend + server build
npm run lint          # TypeScript noEmit kontrolü
npm run doctor        # ortam tanılama
npm run preflight     # doctor + context guard; LOW risk zorunlu
npm run context:guard # bağlam sapması risklerini ve sonraki doğru adımı göster
npm run setup:python  # venv + Python bağımlılık kurulumu
npm run test:python   # modern pipeline unittest
npm run test:geometry # geometry odaklı hedefli test
npm run test:topology # topology odaklı hedefli test
npm run test:pipeline # pipeline odaklı hedefli test
npm run test:bim      # bim core regresyon testi
npm run test:regression # seçili regresyon testi
npm run manifest:update # mevcut outputs için golden manifest üret/güncelle
npm run manifest:verify # outputs hash'lerini golden manifest ile doğrula
npm run metrics:update  # deterministik çıktı metrik snapshot'ını üret/güncelle
npm run metrics:verify  # çıktı metriklerini baseline ile karşılaştır
npm run topology:health # topology graph sağlık raporu üret
npm run verify:p0      # topology-health + manifest verify + metrics verify
npm run release:gate   # strict P0 gate; topology health HEALTHY olmalı
npm run hard:geometry  # preflight + geometry testi + P0 verify
npm run hard:topology  # preflight + topology testi + P0 verify
npm run hard:pipeline  # preflight + pipeline testi + P0 verify
npm run hard:bim       # preflight + BIM regression + P0 verify
npm run hard:regression # preflight + seçili regression + P0 verify
npm run demo          # regresyon/doğrulama akışı
npm run check         # lint + doctor + context guard + Python testleri
```

## Notlar

- Python komutları artık Windows ve Unix-benzeri ortamlarda aynı npm scriptleri üzerinden çalışacak şekilde standardize edilmiştir.
- `test:python` ve `demo`, varsa proje içi `venv` ortamını; yoksa sistem Python yorumlayıcısını kullanmayı dener.
- Deterministik doğrulama odağı gereği ilk öncelik Geometry Engine, Topology Engine ve Canonical BIM Model doğrulama akışıdır.
- `release:gate`, `backend/run_regression_tests.py` içindeki strict release-gate mantığıyla uyumlu olacak şekilde `topology health = HEALTHY` bekler; `verify:p0` ise mevcut baseline'daki `WARNING` durumunu görünür kılar ama manifest/metrics ile birlikte raporlar.

## Sağlıklı Çalışma Ortamı Katmanı

Hafıza kaybını ve gereksiz bağlam yükünü azaltmak için aşağıdaki dosyalar eklendi:

- `docs/HANDOFF_TEMPLATE.md`
- `docs/LOW_CONTEXT_WORKFLOW.md`
- `docs/algorithm-state/geometry_engine.md`
- `docs/algorithm-state/topology_engine.md`
- `docs/algorithm-state/space_engine.md`
- `docs/algorithm-state/bim_core.md`

Önerilen akış:

1. `npm run preflight`
2. ilgili algoritma durum kartını oku
3. hard-mode hedef komutunu çalıştır (`npm run hard:topology` gibi)
4. sadece ilgili dosyayı düzenle
5. aynı hard-mode komutunu yeniden çalıştır
6. gerekirse `npm run release:gate` ile strict HEALTHY kapısını doğrula
7. bilinçli baseline değişikliğinde `npm run manifest:update && npm run metrics:update` çalıştır
8. handoff şablonuna kısa devir notu bırak

Golden manifest dosyası:

- `datasets/golden_manifests/modern_pipeline_outputs.json`

Normalizasyon kuralları:

- `bim_model.json > provenance.generated_at`
- `bim_model.json > provenance.canonical_bim_sha256`

Bu iki alan doğrulamada dışlanır; çünkü biri zaman damgası, diğeri ise dosyanın kendi self-hash alanıdır.

Metrik snapshot dosyası:

- `datasets/golden_manifests/modern_pipeline_metrics.json`

Takip edilen metrikler:

- temiz duvar sayısı
- toplam duvar segment uzunluğu
- topology node / edge sayısı
- semantic element sayısı ve tip dağılımı
- space sayısı ve toplam alan
- canonical BIM içindeki wall / door / window / column / space sayıları

Topology health report dosyası:

- `outputs/topology_health_report.json`

Takip edilen topology sağlık sinyalleri:

- connected component sayısı ve boyutları
- dangling / isolated node sayıları
- self-loop edge tespiti
- invalid edge reference tespiti
- duplicate undirected edge tespiti
- closed/open/tiny loop sayıları
