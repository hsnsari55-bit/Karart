import subprocess
import sys
import os
import shutil

print("=" * 50)
print("           KaRar AI v0.2")
print("=" * 50)

# 1. Aşama: Veri analizi ve JSON çıktısı üreten standart Python adımları
steps = [
    "export_walls.py",
    "export_doors.py",
    "export_windows.py",
    "room_detector.py",
    "analyzer.py",
    "save_clusters.py"
]

for step in steps:
    print(f"\n>>> Çalışıyor: {step}")

    result = subprocess.run(
        [sys.executable, f"backend/{step}"]
    )

    if result.returncode != 0:
        print(f"\nHATA: {step} çalışmadı.")
        sys.exit(1)


# 2. Aşama: Üretilen JSON verilerini alıp 3D modeli ören Blender Motoru
print("\n>>> Çalışıyor: blender_builder.py (Blender 3D İnşa Motoru)")

# NOT: Bilgisayarındaki Blender sürümüne göre klasör yolunu (Blender 4.0, Blender 4.2 vb.) kontrol etmen gerekebilir.
blender_yolu = r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
if not os.path.exists(blender_yolu):
    blender_yolu = shutil.which("blender") or "blender"

print(f"Kullanılan Blender yolu: {blender_yolu}")

blender_result = subprocess.run([
    blender_yolu,
    "--python", 
    "backend/blender_builder.py"
])

if blender_result.returncode != 0:
    print("\nHATA: Blender motoru çalışmadı veya json verisini bulamadı.")
    sys.exit(1)


print("\n==========================================")
print("KaRar AI başarıyla tamamlandı.")
print("==========================================")
