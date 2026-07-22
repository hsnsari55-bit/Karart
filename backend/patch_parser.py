import re

with open("backend/dxf_parser.py", "r") as f:
    content = f.read()

patch = """        try:
            # First try standard read
            doc = ezdxf.readfile(filepath)
        except Exception as e:
            self.logger.warning(f"Standard DXF read failed: {e}. Trying recover mode...")
            try:
                from ezdxf import recover
                doc, auditor = recover.readfile(filepath)
                if auditor.has_errors:
                    self.logger.warning(f"Recovered with {len(auditor.errors)} errors.")
            except Exception as e2:
                self.logger.error(f"Failed to read DXF file even with recover: {e2}")
                return {"error": str(e2), "entities": []}"""

content = re.sub(r'        try:\n            doc = ezdxf\.readfile\(filepath\)\n        except Exception as e:\n            self\.logger\.error\(f"Failed to read DXF file: \{e\}"\)\n            return \{"error": str\(e\), "entities": \[\]\}', patch, content)

with open("backend/dxf_parser.py", "w") as f:
    f.write(content)
