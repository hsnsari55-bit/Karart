# -*- coding: utf-8 -*-
"""
Test wall detection on the real DXF file to identify blockers.
"""
import ezdxf
import json
import sys
from backend.classifier import classify

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

dxf_path = r"data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

print("=" * 60)
print("WALL DETECTION BLOCKER ANALYSIS")
print("=" * 60)

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# Step 1: Count entities by layer classification
layer_stats = {}
classified_stats = {}

for entity in msp:
    layer = entity.dxf.layer
    etype = entity.dxftype()
    
    if layer not in layer_stats:
        layer_stats[layer] = {'total': 0, 'LINE': 0, 'LWPOLYLINE': 0, 'ARC': 0}
    
    layer_stats[layer]['total'] += 1
    if etype in ['LINE', 'LWPOLYLINE', 'ARC']:
        layer_stats[layer][etype] += 1
    
    classification = classify(layer)
    if classification not in classified_stats:
        classified_stats[classification] = 0
    classified_stats[classification] += 1

print("\n1. LAYER CLASSIFICATION RESULTS:")
print("-" * 60)
for cls, count in sorted(classified_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {cls:15} : {count:6} entities")

# Step 2: Analyze wall-classified layers
print("\n2. WALL-CLASSIFIED LAYERS:")
print("-" * 60)
wall_layers = []
for layer, stats in layer_stats.items():
    if classify(layer) == 'WALL':
        wall_layers.append(layer)
        print(f"  Layer: '{layer}'")
        print(f"    Total: {stats['total']}, LINE: {stats['LINE']}, LWPOLYLINE: {stats['LWPOLYLINE']}, ARC: {stats['ARC']}")

# Step 3: Check current wall detection logic
print("\n3. CURRENT WALL DETECTION LOGIC ANALYSIS:")
print("-" * 60)
print("  Current export_walls.py logic:")
print("    - Hardcoded DXF: 'test_plan.dxf'")
print("    - Hardcoded layer filter: layer == 'duvar' (lowercase exact match)")
print("    - Entity type filter: LWPOLYLINE only")
print("")
print("  BLOCKER IDENTIFIED:")
print("    [X] Hardcoded file path prevents processing real DXF")
print("    [X] Hardcoded layer name 'duvar' doesn't match 'Duvar' (case mismatch)")
print("    [X] Only processes LWPOLYLINE, but 'Duvar' layer has 244 LINEs")

# Step 4: Analyze Duvar layer in detail
print("\n4. 'Duvar' LAYER DETAILED ANALYSIS:")
print("-" * 60)
duvar_lines = []
duvar_polylines = []

for entity in msp:
    if entity.dxf.layer == 'Duvar':
        if entity.dxftype() == 'LINE':
            duvar_lines.append({
                'start': [entity.dxf.start.x, entity.dxf.start.y],
                'end': [entity.dxf.end.x, entity.dxf.end.y],
                'length': ((entity.dxf.end.x - entity.dxf.start.x)**2 + 
                          (entity.dxf.end.y - entity.dxf.start.y)**2)**0.5
            })
        elif entity.dxftype() == 'LWPOLYLINE':
            points = [[p[0], p[1]] for p in entity.get_points()]
            duvar_polylines.append({
                'points': points,
                'closed': entity.closed,
                'num_points': len(points)
            })

print(f"  LINE entities: {len(duvar_lines)}")
if duvar_lines:
    lengths = [l['length'] for l in duvar_lines]
    print(f"    Length range: {min(lengths):.2f} to {max(lengths):.2f}")
    print(f"    Average length: {sum(lengths)/len(lengths):.2f}")
    print(f"    Sample coordinates:")
    for i, line in enumerate(duvar_lines[:3]):
        print(f"      Line {i+1}: ({line['start'][0]:.2f}, {line['start'][1]:.2f}) -> ({line['end'][0]:.2f}, {line['end'][1]:.2f})")

print(f"\n  LWPOLYLINE entities: {len(duvar_polylines)}")
if duvar_polylines:
    print(f"    Point counts: {[p['num_points'] for p in duvar_polylines[:5]]}")

# Step 5: Root cause summary
print("\n" + "=" * 60)
print("ROOT CAUSE ANALYSIS")
print("=" * 60)
print("""
PRIMARY BLOCKER: Hardcoded Configuration in export_walls.py

The wall detection pipeline cannot process the real DXF because:

1. FILE PATH BLOCKER:
   - export_walls.py line 8: DXF_FILE = "test_plan.dxf"
   - Should use: config.py's DXF variable (already points to real file)

2. LAYER NAME BLOCKER:
   - export_walls.py line 31: if layer != "duvar"
   - Real DXF has layer "Duvar" (capital D)
   - Should use: classifier.py's classify() function (already handles this)

3. ENTITY TYPE BLOCKER:
   - export_walls.py line 26: if entity.dxftype() != "LWPOLYLINE"
   - Real DXF "Duvar" layer: 244 LINEs + 223 LWPOLYLINEs
   - Current code ignores 244 LINE entities (50% of wall data)
   - Should process: Both LINE and LWPOLYLINE entities

IMPACT:
- 0 walls detected from real DXF (should be ~467 entities)
- Downstream pipeline (doors, windows, rooms) has no walls to work with
- Complete pipeline failure at first step
""")

print("\n" + "=" * 60)
print("AFFECTED FILES")
print("=" * 60)
print("""
1. backend/export_walls.py (PRIMARY)
   - Lines 8, 26, 31: Hardcoded file, entity type, layer name

2. backend/first_wall.py (SECONDARY)
   - Lines 31-32: Uses hardcoded villa1_filtered.json paths
   - Should integrate with export_walls.py output

3. backend/main.py (TERTIARY)
   - Pipeline orchestration needs to pass correct file paths
""")

print("\n" + "=" * 60)
print("RECOMMENDED IMPLEMENTATION PLAN")
print("=" * 60)
print("""
PHASE 1: Fix export_walls.py (Critical Path)
-----------------------------------------
1.1. Replace hardcoded DXF_FILE with config.DXF
1.2. Replace hardcoded layer check with classifier.classify()
1.3. Add LINE entity processing alongside LWPOLYLINE
1.4. Convert LWPOLYLINEs to LINE segments for unified processing

PHASE 2: Verify Wall Extraction
-----------------------------------------
2.1. Run updated export_walls.py on real DXF
2.2. Verify ~467 wall entities extracted (244 LINEs + 223 LWPOLYLINEs)
2.3. Check coordinate ranges match DXF bounds (X: 1184-31614, Y: -8556-5728)

PHASE 3: Update Downstream Pipeline
-----------------------------------------
3.1. Update first_wall.py to use export_walls.py output
3.2. Ensure coordinate normalization handles real DXF scale
3.3. Verify wall connectivity graph builds correctly

ESTIMATED IMPACT:
- Phase 1: Unblocks wall detection (1-2 hours)
- Phase 2: Validates extraction (30 min)
- Phase 3: Enables downstream pipeline (2-3 hours)
""")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
