import json
import math

with open('outputs/geometry_graph.json', 'r') as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']

def distance(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def dist_point_to_segment(p, v, w):
    l2 = distance(v, w)**2
    if l2 == 0: return distance(p, v)
    t = max(0, min(1, ((p[0] - v[0]) * (w[0] - v[0]) + (p[1] - v[1]) * (w[1] - v[1])) / l2))
    proj = (v[0] + t * (w[0] - v[0]), v[1] + t * (w[1] - v[1]))
    return distance(p, proj)

t_junctions_found = 0

for node in nodes:
    p = (node['x'], node['y'])
    # Only look at end nodes (degree 1)
    if node['degree'] == 1:
        # Check if it touches any edge's middle
        for edge in edges:
            n1 = nodes[edge['from']]
            n2 = nodes[edge['to']]
            v = (n1['x'], n1['y'])
            w = (n2['x'], n2['y'])
            
            # Skip if node is already part of this edge
            if node['id'] == edge['from'] or node['id'] == edge['to']:
                continue
            
            dist = dist_point_to_segment(p, v, w)
            if 0 < dist < 5.0: # Close to line but not exactly on vertex
                t_junctions_found += 1
                break

print(f"Total nodes: {len(nodes)}")
print(f"Nodes with degree 1: {sum(1 for n in nodes if n['degree'] == 1)}")
print(f"Potential T-Junctions missed (Degree 1 nodes close to edges): {t_junctions_found}")
