import sys
with open('backend/dxf_parser.py', 'r') as f:
    content = f.read()

content = content.replace("res = parser.parse(filename)", "block_f = sys.argv[2] if len(sys.argv) > 2 else None\n        res = parser.parse(filename, block_f)")

with open('backend/dxf_parser.py', 'w') as f:
    f.write(content)
