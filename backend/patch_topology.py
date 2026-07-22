import re

with open("backend/topology_engine.py", "r") as f:
    content = f.read()

# We need to build a map of edges by their node pairs to quickly find edge index.
patch = """        # Edge lookup for fast polygon mapping
        edge_lookup = {}
        for edge in edges:
            n0, n1 = edge["from"], edge["to"]
            edge_lookup[(n0, n1)] = edge["id"]
            edge_lookup[(n1, n0)] = edge["id"]
            
        # 5. Extract Closed Loops (Faces)
        self.logger.info("Extracting closed loops (faces)...")
        polygons = list(polygonize(final_lines))
        
        loops = []
        for i, poly in enumerate(polygons):
            boundary_coords = list(poly.exterior.coords)
            poly_edges = set()
            
            # Map boundary coordinates to node IDs, then to Edge IDs
            for c_idx in range(len(boundary_coords) - 1):
                p0 = (round(boundary_coords[c_idx][0], 3), round(boundary_coords[c_idx][1], 3))
                p1 = (round(boundary_coords[c_idx+1][0], 3), round(boundary_coords[c_idx+1][1], 3))
                
                n0 = node_map.get(p0)
                n1 = node_map.get(p1)
                
                if n0 is not None and n1 is not None:
                    edge_id = edge_lookup.get((n0, n1))
                    if edge_id is not None:
                        poly_edges.add(edge_id)
                        
            loops.append({
                "id": i,
                "area": poly.area,
                "edges": list(poly_edges),
                "boundary": [{"x": p[0], "y": p[1]} for p in boundary_coords]
            })"""

content = re.sub(r'        # 5\. Extract Closed Loops \(Faces\).*?            \}\)', patch, content, flags=re.DOTALL)

with open("backend/topology_engine.py", "w") as f:
    f.write(content)

print("Patched.")
