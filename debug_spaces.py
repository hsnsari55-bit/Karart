import json

with open('outputs/bim_model.json', 'r') as f:
    model = json.load(f)

walls = model.get('walls', [])
s_counts = {}
for w in walls:
    l = len(w.get('related_spaces', []))
    s_counts[l] = s_counts.get(l, 0) + 1

print("Wall related spaces counts:", s_counts)
