import re

with open('backend/topology_engine.py', 'r') as f:
    content = f.read()

# Just modify the T-Junction tolerance if there is one, or add a print.
content = content.replace("epsilon = 1.0", "epsilon = 5.0 # T-Junction tolerance increased to handle non-manifold overlapping")
content = content.replace("epsilon = 0.1", "epsilon = 0.5") # if it's 0.1

with open('backend/topology_engine.py', 'w') as f:
    f.write(content)
