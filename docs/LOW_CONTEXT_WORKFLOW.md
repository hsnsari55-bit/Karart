# KaRar Düşük Bağlam Maliyetli Çalışma Protokolü

Amaç: algoritma geliştirme sırasında **gereksiz API isteğini**, **token tüketimini** ve **oturumlar arası bağlam kaybını** azaltmak.

## Temel Kurallar

1. **Önce kanıt, sonra yorum**
   - Önce ilgili test, ilgili modül, ilgili çıktı okunur.
   - Tüm repo bağlamı yüklenmez.

2. **Önce yerel doğrulama**
   - LLM yardımı istemeden önce hedefli test/komut çalıştırılır.

3. **Tek değişiklik - tek kanıt zinciri**
   - Her değişiklik şu zincirle izlenir:
   - Gereksinim → Dosya → Test → Çıktı → Risk

4. **Geniş okuma yerine hedefli okuma**
   - Önce arama
   - Sonra ilgili dosya bölümü
   - Sonra hedefli düzenleme

5. **Çekirdek öncelik filtresi**
   - Her görev şu soruyu geçmeli:
   - “Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir artırıyor mu?”

## Önerilen Oturum Akışı

1. `npm run preflight`
2. hedef modül kartını oku
3. uygun hard-mode komutunu çalıştır (`npm run hard:topology` gibi)
4. sadece ilgili dosyayı düzenle
5. aynı hard-mode komutunu tekrar çalıştır
6. gerekiyorsa `npm run release:gate` ile strict HEALTHY kapısını doğrula
7. kısa handoff notu bırak

## Profesyonel Tek-Komut Kısayolları

- `npm run preflight`
  - `doctor` + `context:guard`
  - LOW risk bağlamı zorunlu kılar

- `npm run verify:p0`
  - `topology:health` + `manifest:verify` + `metrics:verify`
  - P0 ölçüm ve güvence zincirini tek çıktıda görünür kılar

- `npm run release:gate`
  - strict doğrulama akışı
  - `topology health = HEALTHY` bekler

- `npm run hard:topology`
  - `preflight` + topology hedef testi + `verify:p0`

- `npm run hard:geometry`
  - `preflight` + geometry hedef testi + `verify:p0`

- `npm run hard:pipeline`
  - `preflight` + pipeline hedef testi + `verify:p0`

## Kalıcı Hafıza Dosyaları

- `docs/STRATEGIC_ROADMAP.md`
  - Projenin uzun ömürlü yönünü sabitler.
  - Hangi işlerin önce, hangilerinin sonra yapılacağını unutmamayı sağlar.

- `docs/CURRENT_FOCUS.md`
  - Şu anda neye odaklanıldığını sabitler.
  - Yeni oturum açıldığında ilk okunacak dosyalardan biridir.

- `docs/DECISIONS_LOG.md`
  - Daha önce alınmış teknik kararları saklar.
  - Aynı tartışmanın tekrar açılmasını azaltır.

- `docs/HANDOFF_TEMPLATE.md`
  - Oturum kapanışında doldurulur.
  - Bir sonraki ajan/oturum için düşük maliyetli devir sağlar.

- `docs/AGENT_CONTINUITY.md`
  - Ürün yönünü, aktif yorum çerçevesini ve kısa/orta vadeli süreklilik bilgisini sabitler.
  - Yeni ajanların yanlış ürün varsayımıyla başlamasını engeller.

## Yeni Oturum Başlangıç Rutini

1. `docs/STRATEGIC_ROADMAP.md` oku
2. `docs/CURRENT_FOCUS.md` oku
3. ilgili `docs/algorithm-state/*.md` modül kartını oku
4. `docs/DECISIONS_LOG.md` içinde ilgili karar var mı kontrol et
5. `npm run preflight` çalıştır
6. hedef hard-mode komutunu veya hedef testi çalıştır
7. yalnızca kanıtlanan problemi çöz
8. varsa `docs/LATEST_HANDOFF.md` dosyasını okuyup doğrudan oradaki "Sonraki En Doğru Adım" ile başla

## Oturum Kapanış Rutini

1. `docs/CURRENT_FOCUS.md` güncelle
2. gerekiyorsa `docs/DECISIONS_LOG.md` kaydı ekle
3. `docs/HANDOFF_TEMPLATE.md` üzerinden kısa devir notu bırak
4. geçen test ve kalan riski açık yaz
5. `docs/LATEST_HANDOFF.md` dosyasını gerçek son durumla güncelle

## Zorunlu Okuma Sırası

Yeni bir oturumda tam repo okuması yapmadan önce şu sıra izlenmeli:

1. `docs/STRATEGIC_ROADMAP.md`
2. `docs/CURRENT_FOCUS.md`
3. `docs/LATEST_HANDOFF.md`
4. `docs/AGENT_CONTINUITY.md`
5. ilgili `docs/algorithm-state/<modul>.md`
6. `docs/DECISIONS_LOG.md`
7. `npm run context:guard`
8. ilgili test dosyası

Bu sıradan çıkmak için elde somut gerekçe olmalı.

## Gereksiz Token Harcamasını Azaltan Pratikler

- Tüm dosyaları tekrar tekrar okutma
- Aynı hata için uzun serbest anlatım yerine test çıktısını kullan
- “kodun tamamını açıkla” yerine “şu fonksiyon + şu test” yaklaşımı kullan
- Her iş sonunda durum kartını güncelle

## Sapma Önleyici Mini Kontrol Listesi

- Aktif hedef tek cümlede yazılabiliyor mu?
- Elimde bu hedef için somut kanıt var mı?
- Yapacağım değişiklik minimum gerekli değişiklik mi?
- Test veya doğrulama komutu hazır mı?
- Bu iş daha önce çözülmüş bir konuyu yanlışlıkla geri açıyor olabilir mi?

## Context Guard Yorumu

`npm run context:guard` çıktısı şu amaçla okunur:

- `Risk seviyesi: LOW`
  - aktif bağlam büyük ölçüde tutarlı
  - doğrudan hedef teste geçilebilir
- `Risk seviyesi: MEDIUM`
  - aktif hedefte belirsizlik veya bağlam dışı değişiklik var
  - önce önerilen adımlar uygulanmalı, sonra kod değişikliğine geçilmeli
- `Risk seviyesi: HIGH`
  - odak dosyaları, handoff veya doğrulama komutu eksik
  - çözüm üretmeden önce bağlam kaydı düzeltilmeli

Komut ayrıca şu gerçek veri kaynaklarına bakar:

- `docs/STRATEGIC_ROADMAP.md`
- `docs/CURRENT_FOCUS.md`
- `docs/LATEST_HANDOFF.md`
- `docs/DECISIONS_LOG.md`
- `git status --short`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse --short HEAD`

`npm run preflight`, bu çıktıyı doğrudan kullanır ve risk seviyesi `LOW` değilse hard-mode akışını durdurur.
