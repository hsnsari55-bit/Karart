import json
from collections import defaultdict

INPUT = r"C:\KaRar\outputs\bim_clean.json"
OUTPUT = r"C:\KaRar\outputs\bim_index.json"

with open(INPUT, "r", encoding="utf-8") as f:
    objects = json.load(f)

index = {
    "by_category": defaultdict(list),
    "by_layer": defaultdict(list),
    "by_entity": defaultdict(list)
}

for i, obj in enumerate(objects):

    index["by_category"][obj["category"]].append(i)
    index["by_layer"][obj["layer"]].append(i)
    index["by_entity"][obj["entity"]].append(i)

index["by_category"] = dict(index["by_category"])
index["by_layer"] = dict(index["by_layer"])
index["by_entity"] = dict(index["by_entity"])

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(index, f, indent=4, ensure_ascii=False)

print("--------------------------------")
print("Toplam Obje :", len(objects))
print("Kategori Sayısı :", len(index["by_category"]))
print("Layer Sayısı :", len(index["by_layer"]))
print("Entity Sayısı :", len(index["by_entity"]))
print("Index Kaydedildi :", OUTPUT)
print("--------------------------------")