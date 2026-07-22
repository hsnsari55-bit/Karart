import json
import os
import math

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def analyze_villas():
    bim_path = "outputs/bim_clean.json"
    if not os.path.exists(bim_path):
        print("BIM file not found!")
        return

    with open(bim_path, "r", encoding="utf-8") as f:
        elements = json.load(f)

    # Prepare elements
    valid_elements = []
    for idx, elem in enumerate(elements):
        if "points" not in elem or not elem["points"]:
            continue
        pts = elem["points"]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        
        valid_elements.append({
            "idx": idx,
            "center": (cx, cy),
            "points": pts,
            "category": elem.get("category", "UNKNOWN"),
            "type": elem.get("type", "Unknown")
        })

    if not valid_elements:
        print("No elements with geometric points found.")
        return

    # Pure Python distance-based clustering (single-linkage style)
    # If distance between any two elements' centers is <= 120 units, they belong to the same block
    eps = 120.0
    clusters = []
    visited = set()

    for i, elem in enumerate(valid_elements):
        if i in visited:
            continue
        
        # Start a new cluster
        cluster = [elem]
        visited.add(i)
        
        # Breadth-first search for connected neighbors
        queue = [elem]
        while queue:
            curr = queue.pop(0)
            for j, other in enumerate(valid_elements):
                if j in visited:
                    continue
                if distance(curr["center"], other["center"]) <= eps:
                    visited.add(j)
                    cluster.append(other)
                    queue.append(other)
        
        clusters.append(cluster)

    # Sort clusters by their X center coordinate
    def get_cluster_x_center(c):
        all_x = [e["center"][0] for e in c]
        return sum(all_x) / len(all_x)

    clusters.sort(key=get_cluster_x_center)

    print("==================================================")
    print("      VILLA BLOCK / CLUSTER DIAGNOSTICS (PURE PYTHON)")
    print("==================================================")
    print(f"Total classified elements loaded: {len(elements)}")
    print(f"Clustering detected {len(clusters)} distinct spatial groups.")

    for idx, cluster in enumerate(clusters):
        all_xs = []
        all_ys = []
        for elem in cluster:
            for pt in elem["points"]:
                all_xs.append(pt[0])
                all_ys.append(pt[1])
        
        min_x, max_x = min(all_xs), max(all_xs)
        min_y, max_y = min(all_ys), max(all_ys)
        
        categories = {}
        for elem in cluster:
            cat = elem["category"]
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\nBlock Group {idx + 1} (Potential Block {chr(65 + idx)}):")
        print(f"  Element Count : {len(cluster)}")
        print(f"  Bounds X      : [{min_x:.2f} to {max_x:.2f}] (width: {max_x - min_x:.2f})")
        print(f"  Bounds Y      : [{min_y:.2f} to {max_y:.2f}] (height: {max_y - min_y:.2f})")
        print(f"  Center        : ({(min_x + max_x)/2:.2f}, {(min_y + max_y)/2:.2f})")
        print(f"  Categories    : {categories}")

    print("==================================================")

if __name__ == "__main__":
    analyze_villas()
