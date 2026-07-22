import re

with open('server.ts', 'r') as f:
    content = f.read()

content = content.replace(
    'const bimCleanPath = path.join(process.cwd(), "outputs", "bim_clean.json");',
    'const bimCleanPath = path.join(process.cwd(), "outputs", "bim_model.json");'
)

with open('server.ts', 'w') as f:
    f.write(content)
