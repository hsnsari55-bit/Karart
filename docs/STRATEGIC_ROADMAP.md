# KaRar Stratejik Yol Haritası

Bu dosya, projenin yönünü oturumlar arasında sabitlemek ve kısa vadeli görevlerin uzun vadeli teknik amaca bağlı kalmasını sağlamak için tutulur.

## 1. Kuzey Yıldızı Kararı
- Program tipi: **kanıt-güdümlü deterministik çekirdek programı**
- Ana amaç: Geometry Engine, Topology Engine ve Canonical BIM Model doğruluğunu, determinizmini, sağlamlığını ve performansını ölçülebilir biçimde artırmak
- Karar kuralı: Bir iş maddesi bu çekirdek metriklerden en az birini ölçülebilir artırmıyorsa ertelenir, reddedilir veya ayrı track’e alınır

## 2. Zorunlu Öncelik Sırası

### P0 — Ölçüm ve Güvence Katmanı
- topology validator ↔ topology health report kapsama hizalaması
- output manifest / output metrics doğrulama akışları
- golden manifest / golden metrics / regression hash kilidi
- context guard + handoff + decisions log + current focus entegrasyonu
- Faz çıkış kapısı: aynı referans veri setinde `topology-health`, `manifest verify` ve `metrics verify` sonuçları birlikte yorumlanabilir ve regression ile korunur olmalı
- Amaç: Her çekirdek değişikliğin kanıt zinciriyle doğrulanması

### P1 — Geometry Numerik Sağlamlaştırma
- adaptive epsilon politikası
- duplicate overlay removal
- micro-gap bridging
- spatial indexing / STRtree benzeri hızlandırma
- Amaç: kirli DXF ve büyük koordinat ofsetlerinde deterministik geometri üretmek

### P2 — Topology Determinism Hardening
- deterministic noding ve graph bütünlük kontrolleri
- room leak tespiti
- closed loop / tiny loop / disconnected component kapsama genişletme
- watertightness ve Euler-Poincare doğrulama hazırlığı
- Amaç: oda/yüz üretimini kanıtlanabilir ve stabil hale getirmek

### P3 — Canonical BIM Contract Hardening
- opening ownership regression zinciri
- parent wall ilişki doğrulaması
- sorted serialization ve stable hash
- schema versioning / backward compatibility kuralları
- Amaç: downstream sistemler için kırılmaz SSoT üretmek

### P4 — Semantik Zenginleştirme
- kapı / pencere / kolon / oda işlevleri
- Önkoşul: P0-P3 metriği güvenilir hale gelmiş olmalı

### P5 — Downstream Consumers
- IFC exporter
- Blender builder
- dashboard / UI
- Kural: Bu katmanlar yalnızca Canonical BIM Model okur; bağımsız geometri üretmez

## 3. Çalışma Modeli
- Track 1: **Core Algorithm Track**
- Track 2: **Verification Track**
- Track 3: **Research Track**
- Track 4: **Consumer Track**

Her görev şu filtreyi geçmelidir:
> Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir artırıyor mu?

## 4. Zorunlu Karar Matrisi
Her öneri şu başlıklarda puanlanır:
- Determinism impact
- Accuracy impact
- Performance impact
- Regression risk reduction
- Implementation cost

Yorum kuralı:
- yüksek determinism + accuracy + regression reduction veren düşük maliyetli işler önce alınır
- çekirdeğe etkisi olmayan refactor ve görsel işler ayrı backlog’da tutulur

## 5. Şu Anki Program Fazı
- Aktif faz: **P0 — Ölçüm ve Güvence Katmanı**
- Aktif alt hedef: `topology-health` komutundaki `WARNING` sonucunu manifest/metrics PASS baseline ile birlikte çelişkisiz açıklayan release-gate zincirini kurmak
- Mevcut başarı komutu: `node scripts/dev-tools.mjs topology-health`
- Tamamlayıcı doğrulama komutları: `node scripts/dev-tools.mjs manifest verify`, `node scripts/dev-tools.mjs metrics verify`
- Bir sonraki profesyonel genişleme: topology health WARNING nedenini tek regression + minimal kod değişikliği ile sınıflandırıp validator/health report/metrics hattını tek kanıt zincirinde birleştirmek

## 6. Sapma Yasakları
- çekirdek metriklere kanıtlı katkı yoksa genel refactor yapılmaz
- Blender / IFC / UI işleri çekirdek stabil olmadan öncelik alamaz
- testsiz veya benchmark’sız “tamamlandı” denmez
- decisions log’da resolved olan konu yeni teknik kanıt yoksa geri açılmaz

## 7. Yeni Oturumda Zorunlu Hatırlatma
Yeni bir oturum başlarken şu sıra korunur:
1. `docs/STRATEGIC_ROADMAP.md`
2. `docs/CURRENT_FOCUS.md`
3. `docs/LATEST_HANDOFF.md`
4. ilgili `docs/algorithm-state/*.md`
5. `docs/DECISIONS_LOG.md`
6. `npm run context:guard`
7. hedef test

## 8. Bu Dosya Ne Zaman Güncellenir?
- stratejik öncelik sırası değişirse
- aktif program fazı değişirse
- yeni release gate zorunlu hale gelirse
- çekirdeğin doğruluk / determinism / performance stratejisini etkileyen yeni kanıt oluşursa