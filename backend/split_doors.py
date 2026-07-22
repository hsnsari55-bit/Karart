import json

MID_X = 30371.6308271139

with open(
    r"C:\KaRar\outputs\doors.json",
    "r",
    encoding="utf-8"
) as f:
    doors = json.load(f)

villa1 = []
villa2 = []

for door in doors:

    if door["type"] == "LINE":

        x = (door["start"][0] + door["end"][0]) / 2

    else:

        xs = [p[0] for p in door["points"]]
        x = sum(xs) / len(xs)

    if x < MID_X:
        villa1.append(door)
    else:
        villa2.append(door)

with open(
    r"C:\KaRar\outputs\villa1_doors.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(villa1, f, indent=4, ensure_ascii=False)

with open(
    r"C:\KaRar\outputs\villa2_doors.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(villa2, f, indent=4, ensure_ascii=False)

print("Villa 1 Kapıları :", len(villa1))
print("Villa 2 Kapıları :", len(villa2))
print("villa1_doors.json oluşturuldu")
print("villa2_doors.json oluşturuldu")