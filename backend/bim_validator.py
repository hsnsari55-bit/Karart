import json
import os
import sys
from collections import Counter

# Ensure project root is in sys.path for robust imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.path_manager import PathManager

pm = PathManager()
JSON_FILE = pm.get_path("outputs", "bim_clean.json")
if not os.path.exists(JSON_FILE):
    JSON_FILE = pm.get_path("outputs", "bim.json")

if not os.path.exists(JSON_FILE):
    print(f"Hata: Doğrulama dosyası bulunamadı: {JSON_FILE}")
    sys.exit(1)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    objects = json.load(f)

print("===================================")
print("       KaRar BIM Validator")
print("===================================")

print("\nToplam Obje :", len(objects))

categories = Counter()
entities = Counter()

line_count = 0
polyline_count = 0
closed_polyline = 0

for obj in objects:

    categories[obj["category"]] += 1
    entities[obj["entity"]] += 1

    if obj["entity"] == "LINE":
        line_count += 1

    elif obj["entity"] == "LWPOLYLINE":
        polyline_count += 1

        if obj.get("closed", False):
            closed_polyline += 1

print("\n===== KATEGORİLER =====\n")

for k, v in sorted(categories.items()):
    print(f"{k:<15} : {v}")

print("\n===== ENTITYLER =====\n")

for k, v in sorted(entities.items()):
    print(f"{k:<15} : {v}")

print("\n===== GEOMETRİ =====\n")

print("LINE            :", line_count)
print("LWPOLYLINE      :", polyline_count)
print("Kapalı Polyline :", closed_polyline)

print("\n===================================")
print("Validator Tamamlandı")
print("===================================")