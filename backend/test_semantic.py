import json
with open('outputs/dxf_raw.json', 'r') as f:
    raw = json.load(f)
    print(f"Total raw entities: {len(raw.get('entities', []))}")
    if raw.get('entities'):
        print("Sample entity:", raw['entities'][0])
