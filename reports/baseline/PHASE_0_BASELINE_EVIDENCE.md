# KaRar Phase 0 Baseline Evidence

> This document records the historical pre-checkpoint repository state captured at commit
> `0a3b519d9a654d06eecafef0cb97eedfc91f5e78`.
> Values in this report must not be interpreted as the current branch state.

## Scope and Safety Constraints

- Task: **KaRar Phase 0 — Task 1: Baseline Evidence Snapshot**
- Goal: Consolidation, dependency, cleanup, pipeline, CI, or architecture changes başlamadan önce mevcut repository durumunun kanıt tabanlı snapshot'ını almak.
- Allowed changes:
  - `reports/baseline/` dizinini oluşturmak
  - yalnız `reports/baseline/PHASE_0_BASELINE_EVIDENCE.md` dosyasını oluşturmak/güncellemek
- Explicitly avoided during this task:
  - install / update / setup / bootstrap / cleanup / archive / delete / move / rename / format
  - commit / checkout / reset / push
  - `package.json`, `package-lock.json`, `bun.lock`, backend kaynak dosyaları, testler, workflows, manifests, metrics, docs veya golden dosyalarını değiştirmek
  - golden manifest / metrics update etmek
- Baseline evidence yalnız read-only inceleme ve koddan doğrulanmış non-mutating komutlarla toplanmıştır.

## Repository Identity

- `cwd`: `<REPOSITORY_ROOT>`
- Branch: `main`
- HEAD (full): `0a3b519d9a654d06eecafef0cb97eedfc91f5e78`
- HEAD (short): `0a3b519`

`git status --branch --short` snapshot (baseline raporu oluşturulmadan önce):

```text
## main...origin/main
 M backend/output_manifest.py
 M backend/output_metrics.py
 M backend/run_regression_tests.py
 M backend/tests/test_output_manifest.py
 M backend/tests/test_output_metrics.py
 M backend/tests/test_regression_topology_report_path.py
 M datasets/golden_manifests/modern_pipeline_metrics.json
 M docs/CURRENT_FOCUS.md
 M docs/LATEST_HANDOFF.md
?? docs/CTO_MASTER_DEVELOPMENT_PLAN.md
```

## Working Tree State

Bu bölüm, baseline raporu oluşturulmadan önceki **pre-existing** çalışma ağacını aynen kaydeder.

Modified:

- `backend/output_manifest.py`
- `backend/output_metrics.py`
- `backend/run_regression_tests.py`
- `backend/tests/test_output_manifest.py`
- `backend/tests/test_output_metrics.py`
- `backend/tests/test_regression_topology_report_path.py`
- `datasets/golden_manifests/modern_pipeline_metrics.json`
- `docs/CURRENT_FOCUS.md`
- `docs/LATEST_HANDOFF.md`

Untracked:

- `docs/CTO_MASTER_DEVELOPMENT_PLAN.md`

Not: Bu snapshot alınırken `reports/baseline/PHASE_0_BASELINE_EVIDENCE.md` henüz mevcut değildi; bu dosya yalnız bu görev kapsamında eklenmiştir.

## Toolchain Versions

```text
WINDOWS=Microsoft Windows NT 10.0.26200.0
POWERSHELL=5.1.26100.8875
PYTHON=Python 3.10.11
NODE=v24.18.0
NPM=11.16.0
GIT=git version 2.54.0.windows.1
UV=NOT INSTALLED
```

## Repository Inventory

```text
REPO_SIZE_BYTES=7272620783
TRACKED_FILES=3795
PYTHON_FILES=5326
TEST_FILES=1001
PRESENT:package.json
PRESENT:package-lock.json
PRESENT:bun.lock
ABSENT:pyproject.toml
ABSENT:uv.lock
ABSENT:requirements.txt
ABSENT:requirements-dev.txt
ABSENT:requirements/base.txt
ABSENT:requirements/base.in
ABSENT:requirements/base-dev.txt
ABSENT:requirements/base-dev.in
ABSENT:requirements-prod.txt
ABSENT:requirements.prod.txt
PRESENT:backend.zip
PRESENT:backend.rar
PRESENT:outputs
```

Inventory notu: `PYTHON_FILES` ve `TEST_FILES` değerleri ham recursive sayımdır; vendored/generated/cache/workspace içerikleri dahil olabilir. Bu nedenle bu sayılar baseline inventory göstergesi olarak saklanmış, semantic source-of-truth olarak yorumlanmamıştır.

Sanitization notu: Makineye özgü ve kalıcı olmayan local cache/build/runtime artifact envanteri bu kopyada detay seviyesinde korunmamıştır. Baseline capture anında bu tür artifact'lerin mevcut olduğu teknik muhakemesi, aşağıdaki komut yüzeyi ve reproducibility değerlendirmesinde zaten korunmuştur.

## Dependency and Lockfile State

- Node dependency surface:
  - `package.json`: present
  - `package-lock.json`: present
  - `bun.lock`: present
- Python dependency manifest surface:
  - `pyproject.toml`: absent
  - `uv.lock`: absent
  - `requirements*.txt` / `requirements*.in`: absent
- `uv`: **NOT INSTALLED**
- Bu görev sırasında hiçbir install/bootstrap/setup/update komutu çalıştırılmamıştır.

## Entry Points and Command Surfaces

### `package.json`

Başlıca script yüzeyleri:

- Environment / guard:
  - `doctor`
  - `preflight`
  - `context:guard`
- Setup / install:
  - `setup:python`
  - `install-all`
- Verification / snapshots:
  - `manifest:update`
  - `manifest:verify`
  - `metrics:update`
  - `metrics:verify`
  - `topology:health`
  - `verify:p0`
- Tests / regression:
  - `test:python`
  - `test:geometry`
  - `test:topology`
  - `test:pipeline`
  - `test:bim`
  - `test:regression`
  - `demo`
  - `release:gate`
  - `hard:*`

### `scripts/dev-tools.mjs`

- `doctor()` ortam, executable ve dosya varlığı denetler; write path kanıtı yok.
- `runContextGuard()` git status ve context dokümanlarını okuyup risk çıktısı verir; write path kanıtı yok.
- `setupPython()` venv oluşturur ve pip install yapar; mutating.
- `bootstrap()` `npm install` + `setupPython()` çağırır; mutating.
- `runManifest("verify")` -> `python -m backend.output_manifest verify`
- `runMetrics("verify")` -> `python -m backend.output_metrics verify`
- `runTopologyHealth()` -> `python -m backend.topology_health_report`
- `runP0Verification()` -> `runTopologyHealth()` + manifest verify + metrics verify

### `backend/output_manifest.py`

- `update_manifest(...)` golden manifest dosyasına yazar.
- `verify_manifest(...)` golden manifest'i okuyup mevcut çıktılarla karşılaştırır; verify yolunda dosya yazımı yok.

### `backend/output_metrics.py`

- `update_metrics(...)` golden metrics snapshot dosyasına yazar.
- `compare_metrics(...)` snapshot'ı okuyup mevcut metric'lerle karşılaştırır; verify yolunda dosya yazımı yok.
- `build_metrics(...)` içinde `TopologyHealthReporter().build_report(graph)` kullanılır; `generate()` çağrılmadığı için topology health report dosyası yazılmaz.

### `backend/topology_health_report.py`

- `generate()` -> `build_report()` + `_write_report()` çağırır.
- CLI `main()` default olarak `outputs/topology_health_report.json` üretir.
- Bu nedenle `npm run topology:health` baseline görevi için non-mutating değildir.

### `backend/run_regression_tests.py`

- Regression ve bazı targeted/test yüzeyleri için ana orchestrator'dır.
- `topology_health_*.json`, `topology_validation_*.json`, `outputs/Production_Validation_Report.md`, `test_report.md`, `pipeline_report.md` ve başka generated output'lar yazabildiği koddan kanıtlanmıştır.
- Bu nedenle regression/test tabanlı komutlar baseline görevinde çalıştırılmamıştır.

### `server.ts`

- Modern Node entry point yüzeyidir.
- `outputs/` dizini oluşturabilir ve gerekli durumda `backend/run_regression_tests.py` çalıştırabilir.
- Baseline görevinde yalnız surface olarak kaydedilmiş, çalıştırılmamıştır.

### `backend/main.py`

- Legacy consumer-first orchestrator yüzeyidir.
- Export ve Blender adımlarını tetikleyebilir.
- Baseline görevinde yalnız surface olarak kaydedilmiş, çalıştırılmamıştır.

### `.github/workflows/quality.yml`

- CI yüzeyi Python dependency install ve regression test koşumu içerir.
- Baseline snapshot sırasında çalıştırılmamıştır; yalnız mevcut surface olarak kaydedilmiştir.

## Golden Manifest Hashes

```text
modern_pipeline_outputs.json SHA256=55396ff47c73b7f7f1b47fc3fa7d3b641af31ea8ebcb539ee5f498893782aec9
modern_pipeline_metrics.json SHA256=a7596bc3073d960c217b56ccfa79982d6d97e8016908f3adb6f2a517155b7518
```

## Verification Commands and Results

### Executed non-mutating commands

1. `npm run doctor 2>&1`
   - Why non-mutating: `scripts/dev-tools.mjs -> doctor()` yalnız environment / executable / file-presence denetliyor.
   - Approval required: `false`
   - Result: **PASS**
   - Output excerpt:

   ```text
   === KaRar Geliştirme Ortamı Doktoru ===
   Çalışma dizini : <REPOSITORY_ROOT>
   Platform       : win32 (10.0.26200)
   Node.js        : v24.18.0
   npm            : 11.16.0
   node_modules/  : mevcut
   tsc            : mevcut
   Python ortamı  : venv bulundu (venv\Scripts\python.exe)
   Venv Python    : Python 3.10.11
   Sistem Python  : py -3 -> Python 3.10.11
   backend/       : mevcut
   package.json   : mevcut
   ```

2. `npm run context:guard 2>&1`
   - Why non-mutating: `scripts/dev-tools.mjs -> runContextGuard()` git durumu ve context dosyalarını okur, risk özeti basar.
   - Approval required: `false`
   - Result: **PASS WITH WARNINGS**
   - Output excerpt:

   ```text
   Branch         : main
   HEAD           : 0a3b519
   Risk seviyesi  : MEDIUM (33/100)
   === Sapma Riskleri ===
   - Aktif hedef için sabit bir doğrulama komutu çıkarılamadı.
   - Aktif bağlam dışında değişmiş dosyalar var: docs/CTO_MASTER_DEVELOPMENT_PLAN.md
   ```

3. `npm run manifest:verify 2>&1`
   - Why non-mutating: `backend/output_manifest.py` içinde yazma yalnız `update_manifest(...)` yolunda; verify yolunda `verify_manifest(...)` snapshot okur ve karşılaştırır.
   - Approval required: `false`
   - Result: **PASS**
   - Output excerpt:

   ```text
   Manifest doğrulaması başarılı
     - dxf_raw.json: a25bbce27262
     - walls_clean.json: 10f5790084f7
     - geometry_graph.json: 2039f7e9fe88
     - bim_semantics.json: 055242345dfb
     - spaces.json: cd4c0fe69e86
     - bim_model.json: b2c596373586
   ```

4. `npm run metrics:verify 2>&1`
   - Why non-mutating: `backend/output_metrics.py` içinde yazma yalnız `update_metrics(...)` yolunda; verify yolunda `compare_metrics(...)` çağrılır. Topology health verisi `build_report()` ile hesaplanır, `_write_report()` çağıran `generate()` kullanılmaz.
   - Approval required: `false`
   - Result: **PASS**
   - Output excerpt:

   ```text
   Metrik doğrulaması başarılı
   {
     "metrics_version": 2,
     "source": "modern_pipeline_outputs",
     "topology_health": {
       "status": "WARNING",
       "diagnostic_codes": [
         "DANGLING_NODES",
         "ZERO_LOOPS"
       ]
     }
   }
   ```

### Explicitly skipped commands

1. `npm run topology:health`
   - Status: **SKIPPED**
   - Exact reason: `backend/topology_health_report.py -> generate()` `_write_report()` çağırır ve default olarak `outputs/topology_health_report.json` yazar.

2. `npm run verify:p0`
   - Status: **SKIPPED**
   - Exact reason: `scripts/dev-tools.mjs -> runP0Verification()` önce `runTopologyHealth()` çağırır; dolayısıyla write side effect taşır.

3. `npm run test:*`, `node scripts/dev-tools.mjs targeted-test ...`, `npm run demo`, `node scripts/dev-tools.mjs regression`, `npm run release:gate`, `npm run hard:*`
   - Status: **SKIPPED**
   - Exact reason: `backend/run_regression_tests.py` birden çok output/report dosyası üretir; baseline görevinde no-mutation kuralını ihlal edebilir.

4. `npm run setup:python`, `npm run install-all`, `npm run manifest:update`, `npm run metrics:update`
   - Status: **SKIPPED**
   - Exact reason: install/bootstrap/update/write semantiği taşıyan mutating komutlardır ve görev kısıtları gereği yasaktır.

## Reproducibility Blockers

- Repository çalışma ağacı baseline alınırken temiz değildir; çoklu pre-existing modified/untracked dosya vardır.
- Node tarafında hem `package-lock.json` hem `bun.lock` mevcuttur; Python tarafında ise `pyproject.toml` / `uv.lock` / `requirements*` manifestleri yoktur.
- `uv` kurulu değildir.
- Verification surface'in bir kısmı write-producing komutlardan oluştuğu için “tam verification set” no-mutation modunda çalıştırılamamıştır.
- `context:guard` çıktısı aktif hedef için sabit bir doğrulama komutunun çıkarılamadığını ve aktif bağlam dışında değişiklikler bulunduğunu raporlamıştır.

## Preserved Pre-existing Changes

Bu görev aşağıdaki pre-existing değişiklikleri **aynen korumuştur**; bu dosyalara hiçbir edit uygulanmamıştır:

- `backend/output_manifest.py`
- `backend/output_metrics.py`
- `backend/run_regression_tests.py`
- `backend/tests/test_output_manifest.py`
- `backend/tests/test_output_metrics.py`
- `backend/tests/test_regression_topology_report_path.py`
- `datasets/golden_manifests/modern_pipeline_metrics.json`
- `docs/CURRENT_FOCUS.md`
- `docs/LATEST_HANDOFF.md`
- `docs/CTO_MASTER_DEVELOPMENT_PLAN.md` (untracked)

Bu görev kapsamında eklenmesi planlanan tek yeni path: `reports/baseline/PHASE_0_BASELINE_EVIDENCE.md`

## Final Verdict

**PARTIALLY REPRODUCIBLE**

Gerekçe:

- Pozitif kanıtlar:
  - `npm run doctor` geçti
  - `npm run context:guard` çalıştı ve mevcut riskleri raporladı
  - `npm run manifest:verify` geçti
  - `npm run metrics:verify` geçti
  - Golden manifest ve golden metrics SHA-256 snapshot'ları sabitlendi
- Sınırlayıcı kanıtlar:
  - çalışma ağacı temiz değil
  - dependency/lockfile hikâyesi tam konsolide değil
  - bazı verification yüzeyleri write side effect nedeniyle no-mutation modunda çalıştırılamıyor

Bu nedenle çekirdek golden doğrulamaları mevcut snapshot'ta başarılı olsa da repository bütünü için “tam temiz ve tek-komutla uçtan uca yeniden üretilebilir” durumu yalnız bu kanıtlarla iddia edilemez.

## Recommended Next Task

**KaRar Phase 0 — Task 2: Reproducibility Contract Consolidation Plan**

Önerilen odak:

1. no-mutation verification surface ile write-producing operational surface'in kesin ayrımı
2. dependency/lockfile contract'ının tekil ve açıklanmış hale getirilmesi
3. clean working tree requirement'ının explicit baseline gate olarak tanımlanması
4. `topology:health` ve regression/report üretim yüzeylerinin verify-only mod ihtiyacının tasarlanması