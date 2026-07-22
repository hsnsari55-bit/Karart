import json

with open('outputs/dxf_raw.json', 'r') as f:
    data = json.load(f)

entities = data.get('entities', [])

stats = {}
for ent in entities:
    # the parser already filtered by block_filter="467-3 A BLOK A-A" when creating dxf_raw.json
    layer = ent.get('layer', 'UNKNOWN')
    etype = ent.get('type', 'UNKNOWN')
    key = (layer, etype)
    stats[key] = stats.get(key, 0) + 1

print("| Layer (Katman) | Entity Türü | Adet |")
print("|---|---|---|")
for (layer, etype), count in sorted(stats.items()):
    print(f"| {layer} | {etype} | {count} |")

