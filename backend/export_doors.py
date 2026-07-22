import ezdxf
import json
import math
from config import DXF, OUTPUT_DIR

doc = ezdxf.readfile(DXF)
msp = doc.modelspace()

doors = []
door_report = {
    "total doors": 0,
    "single doors": 0,
    "double doors": 0,
    "average width": 0,
    "ignored candidates": 0
}

# Door layer names (case-insensitive)
DOOR_LAYERS = [
    "kapı", "kapi", "kapi___pencere", "kapi ve pencereler",
    "kapı ve pencereler", "kap�", "KAPI VE PENCERELER"
]

# Door validation parameters (in DXF units, not mm)
MIN_DOOR_WIDTH = 1.0   # Minimum ~30mm in DXF units
MAX_DOOR_WIDTH = 50.0  # Maximum ~1600mm in DXF units
MIN_ARC_RADIUS = 1.0
MAX_ARC_RADIUS = 50.0
MIN_ARC_SWEEP = 30     # degrees
MAX_ARC_SWEEP = 180    # degrees

ignored = 0

for entity in msp:
    # Case-insensitive layer matching
    layer_lower = entity.dxf.layer.lower()
    if not any(dl.lower() == layer_lower for dl in DOOR_LAYERS):
        continue

    door_data = None
    
    if entity.dxftype() == "LINE":
        start = entity.dxf.start
        end = entity.dxf.end
        width = math.dist([start.x, start.y], [end.x, end.y])
        
        # Validate width
        if width < MIN_DOOR_WIDTH or width > MAX_DOOR_WIDTH:
            ignored += 1
            continue
            
        door_data = {
            "layer": entity.dxf.layer,
            "type": "LINE",
            "start": [start.x, start.y],
            "end": [end.x, end.y],
            "width": width,
            "door_type": "Single"
        }

    elif entity.dxftype() == "LWPOLYLINE":
        points = [[p[0], p[1]] for p in entity.get_points()]
        if len(points) < 2:
            ignored += 1
            continue
            
        # Calculate bounding box width
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        width = max(max(xs) - min(xs), max(ys) - min(ys))
        
        # Validate width
        if width < MIN_DOOR_WIDTH or width > MAX_DOOR_WIDTH:
            ignored += 1
            continue
            
        door_data = {
            "layer": entity.dxf.layer,
            "type": "LWPOLYLINE",
            "points": points,
            "width": width,
            "door_type": "Single"
        }
    
    elif entity.dxftype() == "ARC":
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle % 360
        end_angle = entity.dxf.end_angle % 360
        
        # Calculate sweep angle
        sweep = abs(end_angle - start_angle)
        if sweep > 180:
            sweep = 360 - sweep
        
        # Validate radius and sweep
        if radius < MIN_ARC_RADIUS or radius > MAX_ARC_RADIUS:
            ignored += 1
            continue
        if sweep < MIN_ARC_SWEEP or sweep > MAX_ARC_SWEEP:
            ignored += 1
            continue
            
        # Classify door type based on sweep
        door_type = "Single"
        if 80 <= sweep <= 100:
            door_type = "Single"
        elif 170 <= sweep <= 190:
            door_type = "Double"
            
        door_data = {
            "layer": entity.dxf.layer,
            "type": "ARC",
            "center": [entity.dxf.center.x, entity.dxf.center.y],
            "radius": radius,
            "start_angle": start_angle,
            "end_angle": end_angle,
            "sweep_angle": sweep,
            "width": radius,
            "door_type": door_type
        }
    
    if door_data:
        doors.append(door_data)

# Generate report
door_report["total doors"] = len(doors)
door_report["single doors"] = sum(1 for d in doors if d.get("door_type") == "Single")
door_report["double doors"] = sum(1 for d in doors if d.get("door_type") == "Double")
door_report["average width"] = round(sum(d.get("width", 0) for d in doors) / len(doors), 2) if doors else 0
door_report["ignored candidates"] = ignored

# Save doors
with open(OUTPUT_DIR / "doors.json", "w", encoding="utf-8") as f:
    json.dump(doors, f, indent=4, ensure_ascii=False)

# Save report
with open(OUTPUT_DIR / "door_report.json", "w", encoding="utf-8") as f:
    json.dump(door_report, f, indent=4, ensure_ascii=False)

print(f"Detected {len(doors)} doors (ignored {ignored} candidates)")
print(f"Single: {door_report['single doors']}, Double: {door_report['double doors']}")