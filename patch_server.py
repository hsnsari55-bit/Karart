import re

with open('server.ts', 'r') as f:
    content = f.read()

# Add spaces JSON reading
content = content.replace(
    'const bimCleanPath = path.join(process.cwd(), "outputs", "bim_clean.json");',
    'const bimCleanPath = path.join(process.cwd(), "outputs", "bim_clean.json");\n    const spacesPath = path.join(process.cwd(), "outputs", "spaces.json");'
)

new_spaces_read = """
    if (fs.existsSync(spacesPath)) {
      try {
        response.spaces = JSON.parse(fs.readFileSync(spacesPath, "utf-8"));
      } catch (e) {}
    }
"""

content = content.replace(
    '    if (fs.existsSync(bimCleanPath)) {\n      try {\n        response.bim = JSON.parse(fs.readFileSync(bimCleanPath, "utf-8"));\n      } catch (e) {}\n    }',
    '    if (fs.existsSync(bimCleanPath)) {\n      try {\n        response.bim = JSON.parse(fs.readFileSync(bimCleanPath, "utf-8"));\n      } catch (e) {}\n    }' + new_spaces_read
)

# Add space engine step
content = content.replace(
    'semantic: "PYTHONPATH=. python3 backend/semantic_engine.py",',
    'semantic: "PYTHONPATH=. python3 backend/semantic_engine.py",\n    spaces: "PYTHONPATH=. python3 backend/space_engine.py",'
)

with open('server.ts', 'w') as f:
    f.write(content)
