import json

INPUT = r"C:\KaRar\outputs\bim_clean.json"
OUTPUT = r"C:\KaRar\outputs\bim_no_duplicates.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

seen = set()
clean = []
removed = 0

for obj in objects:

    # Sadece duvar LINE'larını kontrol et
    if obj["category"] == "WALL" and obj["entity"] == "LINE":

        p1 = tuple(round(v, 3) for v in obj["start"])
        p2 = tuple(round(v, 3) for v in obj["end"])

        # A-B ile B-A aynı çizgi kabul edilir
        key = tuple(sorted([p1, p2]))

        if key in seen:
            removed += 1
            continue

        seen.add(key)

    clean.append(obj)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(clean, f, indent=4, ensure_ascii=False)

print("====================================")
print(" Duplicate Line Remover")
print("====================================")
print("İlk Obje      :", len(objects))
print("Kalan         :", len(clean))
print("Silinen Çizgi :", removed)
print("Çıktı         :", OUTPUT)
print("====================================")