#!/usr/bin/env python3
"""
Validate detection quality by analyzing the outputs programmatically.
"""

import json
import ezdxf
from pathlib import Path
from collections import defaultdict

def load_json(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_dxf_structure(dxf_path):
    """Analyze the DXF file structure to understand what should be detected."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    layer_stats = defaultdict(lambda: {'lines': 0, 'polylines': 0, 'inserts': 0, 'other': 0})
    
    for entity in msp:
        layer = entity.dxf.layer
        if entity.dxftype() == 'LINE':
            layer_stats[layer]['lines'] += 1
        elif entity.dxftype() == 'LWPOLYLINE':
            layer_stats[layer]['polylines'] += 1
        elif entity.dxftype() == 'INSERT':
            layer_stats[layer]['inserts'] += 1
        else:
            layer_stats[layer]['other'] += 1
    
    return dict(layer_stats)

def validate_walls(walls, dxf_path):
    """Validate wall detection."""
    print("\n=== WALL DETECTION VALIDATION ===")
    print(f"Total walls detected: {len(walls)}")
    
    if len(walls) == 0:
        return "FAIL", "No walls detected"
    
    # Check wall lengths
    lengths = [((w['end'][0] - w['start'][0])**2 + (w['end'][1] - w['start'][1])**2)**0.5 for w in walls]
    avg_length = sum(lengths) / len(lengths)
    
    print(f"Average wall length: {avg_length:.2f}")
    print(f"Shortest wall: {min(lengths):.2f}")
    print(f"Longest wall: {max(lengths):.2f}")
    
    # Walls should exist and have reasonable lengths
    if len(walls) > 100 and avg_length > 100:
        return "PASS", f"{len(walls)} walls detected with avg length {avg_length:.2f}"
    else:
        return "FAIL", f"Insufficient walls or unrealistic lengths"

def validate_doors(doors, door_report):
    """Validate door detection."""
    print("\n=== DOOR DETECTION VALIDATION ===")
    print(f"Total door geometries found: {len(doors)}")
    print(f"Classified doors: {door_report.get('total doors', 0)}")
    print(f"Ignored candidates: {door_report.get('ignored candidates', 0)}")
    
    # Check if doors were found but not classified
    if len(doors) > 0 and door_report.get('total doors', 0) == 0:
        return "FAIL", f"Found {len(doors)} door geometries but 0 classified as doors - classification logic issue"
    elif door_report.get('total doors', 0) > 0:
        return "PASS", f"{door_report['total doors']} doors properly classified"
    else:
        return "FAIL", "No doors detected at all"

def validate_windows(windows):
    """Validate window detection."""
    print("\n=== WINDOW DETECTION VALIDATION ===")
    print(f"Total windows detected: {len(windows)}")
    
    if len(windows) == 0:
        return "FAIL", "No windows detected"
    
    # Windows should exist
    if len(windows) > 10:
        return "PASS", f"{len(windows)} windows detected"
    else:
        return "WARN", f"Only {len(windows)} windows detected - may be incomplete"

def validate_rooms(room_report):
    """Validate room detection."""
    print("\n=== ROOM DETECTION VALIDATION ===")
    
    if not room_report:
        return "FAIL", "No room report found - room detection not run or failed"
    
    total_rooms = room_report.get('total_rooms', 0)
    print(f"Total rooms detected: {total_rooms}")
    
    if 'error' in room_report:
        return "FAIL", f"Room detection error: {room_report['error']}"
    elif total_rooms == 0:
        return "FAIL", "No rooms detected - wall topology incomplete"
    elif total_rooms > 0:
        return "PASS", f"{total_rooms} rooms detected"
    else:
        return "FAIL", "Room detection incomplete"

def main():
    """Main validation function."""
    print("=" * 60)
    print("SPRINT 1 VALIDATION - REAL PROJECT")
    print("=" * 60)
    
    # Load data
    dxf_path = Path("data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf")
    walls = load_json("outputs/walls.json")
    doors = load_json("outputs/doors.json")
    windows = load_json("outputs/windows.json")
    wall_report = load_json("outputs/wall_report.json")
    door_report = load_json("outputs/door_report.json")
    
    try:
        room_report = load_json("outputs/room_report.json")
    except FileNotFoundError:
        room_report = None
    
    # Analyze DXF structure
    print("\n=== DXF STRUCTURE ANALYSIS ===")
    layer_stats = analyze_dxf_structure(dxf_path)
    for layer, stats in sorted(layer_stats.items()):
        total = sum(stats.values())
        if total > 10:  # Only show significant layers
            print(f"Layer '{layer}': {stats}")
    
    # Validate each component
    results = {}
    
    wall_status, wall_msg = validate_walls(walls, dxf_path)
    results['Wall Detection'] = (wall_status, wall_msg)
    
    door_status, door_msg = validate_doors(doors, door_report)
    results['Door Detection'] = (door_status, door_msg)
    
    window_status, window_msg = validate_windows(windows)
    results['Window Detection'] = (window_status, window_msg)
    
    room_status, room_msg = validate_rooms(room_report)
    results['Room Detection'] = (room_status, room_msg)
    
    # Print final results
    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    for component, (status, message) in results.items():
        print(f"\n{component}: {status}")
        print(f"  -> {message}")
    
    # Identify blockers
    print("\n" + "=" * 60)
    print("BLOCKERS AND NEXT STEPS")
    print("=" * 60)
    
    if door_status == "FAIL" and len(doors) > 0:
        print("\n[BLOCKER] Door classification logic is broken")
        print("   - Door geometries are detected (197 found)")
        print("   - But classification reports 0 doors")
        print("   - Fix: Review door_detector.py classification criteria")
    
    if room_status == "FAIL":
        print("\n[BLOCKER] Room detection failed")
        if room_report and 'error' in room_report:
            print(f"   - Error: {room_report['error']}")
        else:
            print("   - Likely cause: Incomplete wall topology")
            print("   - Walls may not form closed loops")
            print("   - Check wall connectivity and gaps")

if __name__ == "__main__":
    main()
