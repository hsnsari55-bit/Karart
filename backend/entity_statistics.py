import json
from collections import Counter

JSON_FILE = r"C:\KaRar\outputs\entities.json"

with open(JSON_FILE, "r", encoding="utf-8") as f:
    entities = json.load(f)

counter = Counter()

for entity in entities:
    counter[entity["category"]] += 1

print("\n========== KaRar Statistics ==========\n")

for name, count in sorted(counter.items()):
    print(f"{name:<15} : {count}")

print("\nToplam :", len(entities))
print("\n======================================")