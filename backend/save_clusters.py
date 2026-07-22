import json
import os
from sklearn.cluster import DBSCAN
from config import OUTPUT_DIR

print("==========================================")
print("     KaRar Villa Kümeleme Motoru Devrede")
print("==========================================")

# Giriş dosyası (Artık doğrudan bizim ana duvar dosyamızı okuyor)
INPUT_FILE = OUTPUT_DIR / "walls.json"

if not os.path.exists(INPUT_FILE):
    print(f"❌ HATA: {INPUT_FILE} bulunamadı. Önce duvarları çıkarmalısın.")
    exit(1)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    walls = json.load(f)

points = []

# Duvarların orta noktalarını bul
for wall in walls:
    if "start" in wall and "end" in wall:
        x = (wall["start"][0] + wall["end"][0]) / 2
        y = (wall["start"][1] + wall["end"][1]) / 2
        points.append([x, y])
    else:
        continue

if len(points) < 10:
    print(f"⚠️  Uyarı: Yalnızca {len(points)} duvar bulundu (DBSCAN için 10+ gerekli)")
else:
    # DBSCAN: 1.5 metre (1500mm) tolerans ile binaları birbirinden ayırır
    model = DBSCAN(eps=1500, min_samples=10)
    labels = model.fit_predict(points)
    
    villa1 = []
    villa2 = []
    
    for i, label in enumerate(labels):
        if label == 0:
            villa1.append(walls[i])
        elif label == 1:
            villa2.append(walls[i])
    
    # Villa 1 Kaydı
    villa1_path = OUTPUT_DIR / "villa1.json"
    with open(villa1_path, "w", encoding="utf-8") as f:
        json.dump(villa1, f, indent=4, ensure_ascii=False)
    
    # Villa 2 Kaydı
    villa2_path = OUTPUT_DIR / "villa2.json"
    with open(villa2_path, "w", encoding="utf-8") as f:
        json.dump(villa2, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Villa 1 : {len(villa1)} duvar bulundu ({villa1_path})")
    print(f"✅ Villa 2 : {len(villa2)} duvar bulundu ({villa2_path})")

print("==========================================")
