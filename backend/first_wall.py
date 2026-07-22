import json
import math
import os
from collections import defaultdict

# Configuration
MIN_LENGTH = 50
TOLERANCE = 1e-5

def compute_length(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def angle_of_vector(dx, dy):
    return math.degrees(math.atan2(dy, dx))

def round_coord(coord):
    return (round(coord[0], 5), round(coord[1], 5))

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

OUTPUT_DIR = 'C:/KaRar/outputs'

def detect_walls():
    # Paths
    filtered_path = os.path.join(OUTPUT_DIR, 'villa1_filtered.json')
    original_path = os.path.join(OUTPUT_DIR, 'villa1.json')
    walls_path = os.path.join(OUTPUT_DIR, 'walls.json')
    report_path = os.path.join(OUTPUT_DIR, 'wall_report.json')

    # Load filtered geometry
    filtered_data = load_json(filtered_path)
    original_data = load_json(original_path)

    # Build segments
    segments = []
    for obj in filtered_data:
        obj_type = obj.get('type')
        if obj_type == 'LINE':
            start = obj['start']
            end = obj['end']
            length = compute_length(start, end)
            if length >= MIN_LENGTH:
                segments.append({
                    'type': 'LINE',
                    'start': start,
                    'end': end,
                    'length': length
                })
        elif obj_type == 'LWPOLYLINE':
            points = obj['points']
            if len(points) < 2:
                continue
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i+1]
                length = compute_length(start, end)
                if length >= MIN_LENGTH:
                    segments.append({
                        'type': 'LWPOLYLINE',
                        'start': start,
                        'end': end,
                        'length': length
                    })
        # Could handle POLYLINE if present

    # Build start_map and end_map
    start_map = {}
    end_map = {}
    for idx, seg in enumerate(segments):
        s_key = round_coord(seg['start'])
        e_key = round_coord(seg['end'])
        start_map[s_key] = idx
        end_map[e_key] = idx

    # Build adjacency graph
    graph = defaultdict(list)
    for i, seg in enumerate(segments):
        s_key = round_coord(seg['start'])
        e_key = round_coord(seg['end'])
        # Connect to segments that share start/end points
        if s_key in end_map and end_map[s_key] != i:
            graph[i].append(end_map[s_key])
        if e_key in start_map and start_map[e_key] != i:
            graph[i].append(start_map[e_key])

    # Find connected components using DFS
    visited = set()
    walls = []
    wall_id = 1

    for idx in range(len(segments)):
        if idx in visited:
            continue
        # Start new component
        component = []
        stack = [idx]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in graph[current]:
                if neighbor not in visited:
                    stack.append(neighbor)

        # Process component
        merged_walls = []
        for seg_idx in component:
            seg = segments[seg_idx]
            if not merged_walls:
                merged_walls.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'length': seg['length']
                })
            else:
                last = merged_walls[-1]
                # Check collinear
                dx1 = last['end'][0] - last['start'][0]
                dy1 = last['end'][1] - last['start'][1]
                angle1 = angle_of_vector(dx1, dy1)
                dx2 = seg['end'][0] - seg['start'][0]
                dy2 = seg['end'][1] - seg['start'][1]
                angle2 = angle_of_vector(dx2, dy2)
                if abs(angle1 - angle2) < TOLERANCE or abs(abs(angle1 - angle2) - 180) < TOLERANCE:
                    last['end'] = seg['end']
                    last['length'] += seg['length']
                else:
                    merged_walls.append({
                        'start': seg['start'],
                        'end': seg['end'],
                        'length': seg['length']
                    })

        # Create wall entries
        for merged in merged_walls:
            dx = merged['end'][0] - merged['start'][0]
            dy = merged['end'][1] - merged['start'][1]
            angle = angle_of_vector(dx, dy)
            wall_entry = {
                'id': wall_id,
                'layer': 'wall',
                'start': merged['start'],
                'end': merged['end'],
                'length': round(merged['length'], 2),
                'angle': round(angle, 2)
            }
            walls.append(wall_entry)
            wall_id += 1

    # Save walls
    save_json(walls, walls_path)

    # Compute report stats
    total_detected_walls = len(walls)
    lengths = [w['length'] for w in walls]
    avg_length = sum(lengths) / total_detected_walls if total_detected_walls else 0
    longest_wall = max(lengths) if lengths else 0
    shortest_wall = min(lengths) if lengths else 0
    ignored_objects = len(original_data) - len(filtered_data)

    report = {
        'total_detected_walls': total_detected_walls,
        'average_wall_length': round(avg_length, 2),
        'longest_wall': round(longest_wall, 2),
        'shortest_wall': round(shortest_wall, 2),
        'ignored_objects': ignored_objects
    }
    save_json(report, report_path)

    return walls, report

if __name__ == '__main__':
    detect_walls()