import re

with open('server.ts', 'r') as f:
    content = f.read()

content = content.replace(
    'spaces: "PYTHONPATH=. python3 backend/space_engine.py",',
    'spaces: "PYTHONPATH=. python3 backend/space_engine.py",\n    core: "PYTHONPATH=. python3 backend/bim_core.py",'
)

with open('server.ts', 'w') as f:
    f.write(content)
