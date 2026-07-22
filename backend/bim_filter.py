import json

INPUT = r"C:\KaRar\outputs\bim.json"
OUTPUT = r"C:\KaRar\outputs\bim_clean.json"

KEEP = {
    "WALL",
    "DOOR",
    "WINDOW",
    "COLUMN",
    "STAIR"
}

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

clean = []

for obj in objects:

    if obj["category"] in KEEP:
        clean.append(obj)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(clean, f, indent=4, ensure_ascii=False)

print("--------------------------------")
print("İlk Obje :", len(objects))
print("Temiz Obje :", len(clean))
print("Silinen :", len(objects) - len(clean))
print("--------------------------------")