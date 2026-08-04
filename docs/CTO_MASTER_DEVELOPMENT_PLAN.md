# KaRar CTO Resmî Kilit Kararı

KaRar v1.x için mimari yön arama ve yeni çekirdek katman önerme dönemi kapanmıştır.

KaRar’ın resmî amacı:

> Gerçek mimari 2B çizimleri deterministik biçimde işleyerek mühendislik açısından geçerli, sürümlü ve doğrulanabilir bir Canonical BIM Model üretmek; bütün 3B ve dış format çıktılarını yalnızca bu modelden türetmek.

Referans mimari:

Parser
→ Geometry Engine
→ Topology Engine
→ Constraint Solver
→ Canonical BIM Builder
→ Canonical Validator
→ Consumers

SemanticEngine ve SpaceEngine korunacaktır; ancak ayrı üst seviye mimari katman sayılmayacak, Canonical BIM Builder’a veri hazırlayan deterministik iç bileşenler olarak yönetilecektir.

Değişmez kurallar:

1. Geometry, Topology ve Canonical BIM kararları deterministik olacaktır.
2. Sistemde yalnızca bir resmî mühendislik modeli bulunacaktır.
3. Canonical Validator geçmeden Blender, IFC veya başka çıktı üretilmeyecektir.
4. CLI, web sunucusu, testler ve CI aynı resmî pipeline’ı kullanacaktır.
5. Consumer katmanları kendi geometri veya mimari yorumlarını üretmeyecektir.
6. Kod, test, mimari ve gerçek veri kanıtı olmadan hiçbir görev tamamlanmış sayılmayacaktır.
7. Belirsiz durumda sistem yanlış model üretmek yerine kontrollü olarak duracaktır.
8. Baseline, golden manifest veya metrikler yalnızca bilinçli teknik onayla değiştirilecektir.
9. Yeni özellikler, çekirdek doğruluk kanıtlanmadan öncelik alamayacaktır.
10. Her değişiklik gereksinimden release’e kadar izlenebilir olacaktır.

Aktif geliştirme fazı:

> Faz 0 — Reproducible Baseline & Repository Consolidation

Faz 0 tamamlanmadan Geometry, Topology, Blender veya IFC üzerinde yeni ana geliştirme başlatılmayacaktır.

Faz 0’ın çıkış şartları:

- temiz makinede kilitli bağımlılık kurulumu,
- bütün çekirdek testlerin çalışması,
- tek resmî execution path planının doğrulanması,
- aktif ve legacy kodun ayrılması,
- gerçek CI architecture gate,
- Windows ve Linux tekrar üretilebilirlik kanıtı,
- rollback yapılabilecek referans commit.

KaRar’ın ilerlemesi takvim veya özellik sayısıyla değil kalite kapılarıyla ölçülecektir.

Nihai geliştirme sırası:

Reproducible repository
→ Single official pipeline
→ Real quality gates
→ Independent Ground Truth
→ Geometry hardening
→ Topology and Constraint hardening
→ Canonical BIM contract and validator
→ Canonical-only Blender
→ Validated IFC
→ Controlled pilot
→ v1.0 Stable
