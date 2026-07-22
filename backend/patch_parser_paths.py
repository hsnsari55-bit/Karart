import re

with open("backend/dxf_parser.py", "r") as f:
    content = f.read()

# Replace project_root with workspace_root handling
patch = """        if filename.startswith("/"):
            filepath = filename
        else:
            filepath = os.path.join(self.path_manager.workspace_root, filename)"""

content = re.sub(r"        filepath = self\.path_manager\.get_path\('project_root', filename\).*?filename\)", patch, content, flags=re.DOTALL)

with open("backend/dxf_parser.py", "w") as f:
    f.write(content)
