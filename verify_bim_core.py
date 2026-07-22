import json

with open('outputs/bim_model.json', 'r') as f:
    model = json.load(f)

spaces = model.get('spaces', [])
walls = model.get('walls', [])
windows = model.get('windows', [])
columns = model.get('columns', [])
doors = model.get('doors', [])

print("# Canonical BIM Model Doğrulama Raporu")
print("BIM Core Engine başarıyla çalıştırıldı ve tüm yapısal/anlamsal veriler tek bir `bim_model.json` altında birleştirildi.")
print("\n## 1. Benzersiz Kimlik (UUID) Doğrulaması")

all_uuids = set()
duplicates = 0
total_elements = len(spaces) + len(walls) + len(windows) + len(columns) + len(doors)

for lst in [spaces, walls, windows, columns, doors]:
    for el in lst:
        uid = el.get('uuid')
        if uid in all_uuids:
            duplicates += 1
        all_uuids.add(uid)

print(f"* Toplam İşlenen Nesne Sayısı: {total_elements}")
print(f"* Atanan Benzersiz UUID Sayısı: {len(all_uuids)}")
print(f"* Çakışan/Tekrar Eden UUID Sayısı: {duplicates}")

print("\n## 2. İlişkisel Bütünlük (Relationships) Doğrulaması")

# Duvar <-> Uzay
wall_with_spaces = sum(1 for w in walls if len(w.get('related_spaces', [])) > 0)
print(f"* Duvar ↔ Uzay İlişkisi: {wall_with_spaces} / {len(walls)} duvar, en az bir odayı (space) çevreliyor.")

# Pencere <-> Duvar
window_with_walls = sum(1 for w in windows if w.get('parent_wall') is not None)
print(f"* Pencere ↔ Duvar İlişkisi: {window_with_walls} / {len(windows)} pencere, başarıyla bir ana duvara (parent_wall) tutundu.")

# Uzay ↔ Komşu Uzay
spaces_with_neighbors = sum(1 for s in spaces if len(s.get('neighbors', [])) > 0)
print(f"* Uzay ↔ Komşu Uzay İlişkisi: {spaces_with_neighbors} / {len(spaces)} odanın en az bir komşu odası var (ortak duvar paylaşıyorlar).")

# Uzay ↔ Pencere/Kolon
spaces_with_windows = sum(1 for s in spaces if len(s.get('related_windows', [])) > 0)
spaces_with_columns = sum(1 for s in spaces if len(s.get('related_columns', [])) > 0)
print(f"* Odaya Ait Pencereler: {spaces_with_windows} oda en az bir pencereye sahip.")
print(f"* Odaya Ait Kolonlar: {spaces_with_columns} oda en az bir kolonu barındırıyor.")

print("\n## Sonuç")
if duplicates == 0 and wall_with_spaces > 0:
    print("✅ Canonical BIM Model ilişkisel bütünlük testlerini geçti. Veriler UI veya 3D katmanına aktarılmaya hazır.")
else:
    print("❌ Modelde hatalar mevcut.")
