import ezdxf
import json

dxf_path = r"data/GÜZELCE 467 ADA 3 PARSEL .(23.12.2025).dxf"

doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# Analyze potential wall layers
wall_candidates = ['Duvar', 'duvar', 'DUVAR', 'k tarama', 'tarama', '0', 'CERCEVE']

layer_analysis = {}

for layer_name in wall_candidates:
    layer_data = {
        'total': 0,
        'LINE': 0,
        'LWPOLYLINE': 0,
        'ARC': 0,
        'CIRCLE': 0,
        'sample_lines': []
    }
    
    for e in msp:
        if e.dxf.layer == layer_name:
            layer_data['total'] += 1
            etype = e.dxftype()
            
            if etype == 'LINE':
                layer_data['LINE'] += 1
                if len(layer_data['sample_lines']) < 5:
                    layer_data['sample_lines'].append({
                        'start': [e.dxf.start.x, e.dxf.start.y],
                        'end': [e.dxf.end.x, e.dxf.end.y],
                        'length': ((e.dxf.end.x - e.dxf.start.x)**2 + (e.dxf.end.y - e.dxf.start.y)**2)**0.5
                    })
            elif etype == 'LWPOLYLINE':
                layer_data['LWPOLYLINE'] += 1
            elif etype == 'ARC':
                layer_data['ARC'] += 1
            elif etype == 'CIRCLE':
                layer_data['CIRCLE'] += 1
    
    if layer_data['total'] > 0:
        layer_analysis[layer_name] = layer_data

print(json.dumps(layer_analysis, indent=2, ensure_ascii=False))
