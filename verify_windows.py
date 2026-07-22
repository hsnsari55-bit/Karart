import json

with open('outputs/dxf_raw.json', 'r') as f:
    data = json.load(f)

windows = [ent for ent in data.get('entities', []) if ent.get('type') == 'LWPOLYLINE' and 'pencere' in ent.get('layer', '').lower()]
print(f"Total LWPOLYLINE windows: {len(windows)}")

def analyze_geometry(ent):
    vertices = ent.get('vertices', [])
    if len(vertices) < 2:
        return "Not enough vertices"
    
    xs = [v['x'] for v in vertices]
    ys = [v['y'] for v in vertices]
    
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    
    is_closed = ent.get('flag_70', 0) & 1 == 1 or (len(vertices) > 2 and abs(vertices[0]['x'] - vertices[-1]['x']) < 1e-3 and abs(vertices[0]['y'] - vertices[-1]['y']) < 1e-3)
    
    return f"Vertices: {len(vertices)}, Closed: {is_closed}, Size: {width:.2f} x {height:.2f}"

for i, win in enumerate(windows[:10]):
    print(f"Window {i+1}: {analyze_geometry(win)}")

