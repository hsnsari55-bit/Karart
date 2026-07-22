import json

with open('outputs/dxf_raw.json', 'r') as f:
    data = json.load(f)

for ent in data['entities']:
    layer = ent.get('layer', '').lower()
    if 'kap' in layer or 'door' in layer:
        if ent['type'] == 'LINE':
            length = ((ent['start']['x']-ent['end']['x'])**2 + (ent['start']['y']-ent['end']['y'])**2)**0.5
            print(f"Door LINE length: {length:.2f}")
        elif ent['type'] == 'ARC':
            print(f"Door ARC")
