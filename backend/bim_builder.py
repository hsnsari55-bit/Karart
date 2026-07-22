import json

WALLS = r"C:\KaRar\outputs\walls_thickness.json"
DOORS = r"C:\KaRar\outputs\doors_matched.json"
WINDOWS = r"C:\KaRar\outputs\windows_matched.json"
COLUMNS = r"C:\KaRar\outputs\columns_matched.json"
ROOMS = r"C:\KaRar\outputs\rooms.json"

OUTPUT = r"C:\KaRar\outputs\bim_model.json"

with open(WALLS, "r", encoding="utf-8") as f:
    walls = json.load(f)

with open(DOORS, "r", encoding="utf-8") as f:
    doors = json.load(f)

with open(WINDOWS, "r", encoding="utf-8") as f:
    windows = json.load(f)

with open(COLUMNS, "r", encoding="utf-8") as f:
    columns = json.load(f)

with open(ROOMS, "r", encoding="utf-8") as f:
    rooms = json.load(f)

bim = {
    "walls": walls,
    "doors": doors,
    "windows": windows,
    "columns": columns,
    "rooms": rooms,
    "statistics": {
        "wall_count": len(walls),
        "door_count": len(doors),
        "window_count": len(windows),
        "column_count": len(columns),
        "room_count": len(rooms)
    }
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(bim, f, indent=4, ensure_ascii=False)

print("====================================")
print("         BIM BUILDER")
print("====================================")
print("Walls   :", len(walls))
print("Doors   :", len(doors))
print("Windows :", len(windows))
print("Columns :", len(columns))
print("Rooms   :", len(rooms))
print("------------------------------------")
print("Kaydedildi :", OUTPUT)
print("====================================")