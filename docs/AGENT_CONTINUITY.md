# KaRar Agent Continuity Board

Bu dosya, **benim veya başka bir ajanın** projeyi kaldığı yerden devam ettirebilmesi için tutulur.

Amaç:
- yapılan işi unutmamak,
- ürün yönünü sabitlemek,
- bir sonraki doğru işi net görmek,
- aynı tartışmayı tekrar tekrar açmamak,
- bağlam kaybı yüzünden başa dönmemek.

> Kullanım kuralı: Yeni oturum başında bu dosya yalnız okunmaz; `docs/STRATEGIC_ROADMAP.md`, `docs/CURRENT_FOCUS.md` ve `docs/LATEST_HANDOFF.md` ile birlikte değerlendirilir.

---

## 1. Ürün Yönü Sabiti

- KaRar'ın ana hedefi, **2D CAD/mimari projeyi deterministik biçimde anlayıp güvenilir bir yapı modeline dönüştürmek**.
- Nihai kullanıcı değeri, bu modelden **3D sahne üretmek** ve mimarın bunu görselleştirme akışında kullanabilmesini sağlamaktır.
- KaRar, şu anki yönüyle **Blender veya 3ds Max'in birebir alternatifi** olarak konumlanmaz.
- Daha doğru tanım şudur:
  - **KaRar = 2D planı anlayan çekirdek mühendislik motoru + güvenilir model üretici + 3D sahne hazırlayıcı**
  - **Blender = downstream sahne, malzeme, ışık, render ortamı**
- Beklenen ürün akışı:
  1. DXF/2D plan yüklenir
  2. Parser + Geometry + Topology çalışır
  3. Canonical BIM Model oluşur
  4. 3D sahne üretilir
  5. Blender gibi araçlarda malzeme / renk / render aşamasına geçilir
- Kendi uygulama tarafında preview olabilir; ancak çekirdek değer, **doğru model üretmek**tir.

---

## 2. Şu Anda Nerede Olduğumuz

- Aktif program fazı: **P0 — Ölçüm ve Güvence Katmanı**
- Şu anki ana hedef: **çekirdek determinizm ve doğruluk yüzeyini güçlendirmek**
- Özellikle aktif odak:
  - `backend/dxf_parser.py`
  - parser instance reuse determinism
- Bunun anlamı:
  - Aynı plan tekrar işlendiğinde aynı sonucun çıkması
  - Önceki parse çağrısının state'inin sonraki parse'a sızmaması
  - Geometry/Topology katmanına kirli veri gitmemesi

---

## 3. Son Tamamlanan İşler

- `DXFParser` çağrılar arası state sızıntısı için düzeltme yapıldı.
- Güvenceye alınan alanlar:
  - `skipped_entities`
  - `entities`
  - `bounding_box`
- Eklenen regression testleri:
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_skipped_entities_between_runs`
  - `backend/tests/test_dxf_parser_engine.py::TestDXFParserEngine::test_parse_resets_entities_and_bounds_between_runs`
- Dokümantasyon güncellendi:
  - `docs/CURRENT_FOCUS.md`
  - `docs/LATEST_HANDOFF.md`

---

## 4. Şu An Yapılmaması Gereken Yanlış Yorumlar

- Bu proje şu anda **tam bağımsız bir render uygulaması** haline getirilmiyor.
- Bu proje şu anda **Blender/3ds Max alternatifi bir DCC aracı** haline getirilmiyor.
- UI'nin amacı şu aşamada marketing/placeholder ekranı üretmek değil; **mühendislik doğrulama ekranı** olmaktır.
- Blender Builder, IFC Export ve UI katmanları; çekirdek doğruluk sabitlenmeden “tamamlandı” diye etiketlenmemelidir.

---

## 5. Sıradaki En Doğru İşler

Öncelik sırasıyla:

1. `DXFParser` instance-reuse regression yüzeyini genişlet
   - block promotion metadata
   - repair/recover akışları
   - `INSERT/BLOCK`, `HATCH`, gerçek plan export fixture'ları

2. Parser determinizm yüzeyi yeterince sabitlenince
   - Geometry Engine doğruluk/sağlamlık kanıtını artır
   - Topology Engine loop/room extraction güvenilirliğini derinleştir

3. Ancak bundan sonra aşağı akış katmanlarında ilerle
   - Canonical BIM Model zenginleştirme
   - Semantic Enrichment
   - Blender Builder üzerinden güvenilir 3D sahne üretimi

---

## 6. Bittiğinde Uygulama Nasıl Çalışacak?

Hedef çalışma şekli:

1. Kullanıcı 2D planı yükler
2. Sistem planı okur ve normalize eder
3. Duvar / oda / kapı / pencere / topoloji çıkarılır
4. Canonical BIM Model oluşturulur
5. 3D sahne üretilir
6. Kullanıcı preview görür veya Blender tarafına geçer
7. Malzeme, renk, ışık ve render downstream araçta uygulanır

Önemli not:
- KaRar'ın asıl değeri “güzel görünen ama yanlış” model üretmek değil,
- **teknik olarak doğru bir 3D sahne temeli üretmek**tir.

---

## 7. Yeni Ajan İçin Hızlı Başlangıç Rutini

Yeni gelen ajan şu sırayı izlemeli:

1. `docs/STRATEGIC_ROADMAP.md`
2. `docs/CURRENT_FOCUS.md`
3. `docs/LATEST_HANDOFF.md`
4. `docs/AGENT_CONTINUITY.md`
5. ilgili `docs/algorithm-state/<modul>.md`
6. ilgili test dosyası

Sonra şu soruyu cevaplamalı:

> “Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model doğruluğunu, determinizmini, sağlamlığını ya da performansını ölçülebilir artırıyor mu?”

Hayır ise iş ertelenmeli veya yeniden çerçevelenmelidir.

---

## 8. Tek Bakışta Durum

### Yapıldı
- Parser reuse determinism için ilk kritik açık kapatıldı
- Regression kanıtı eklendi
- Handoff/focus belgeleri güncellendi

### Yapılıyor
- Parser state izolasyonunu daha geniş fixture yüzeyine yayma hazırlığı

### Sonraki
- block promotion metadata regression'ları
- repair/recover akış regression'ları
- daha gerçekçi DXF fixture'ları

### Riskler
- Tüm mutable parser state henüz kapsanmış değil
- Gerçek saha DXF çeşitliliği henüz tam temsil edilmiyor
- Çekirdek stabilize olmadan downstream 3D/preview işlerine erken kayma riski var
