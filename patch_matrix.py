import re

with open("backend/ifc_exporter.py", "r") as f:
    content = f.read()

def replacer(match):
    return """
                matrix = __import__('numpy').eye(4)
                matrix[0, 3] = loc[0]
                matrix[1, 3] = loc[1]
                matrix[2, 3] = loc[2]
"""

content = re.sub(r'matrix = ifcopenshell\.util\.placement\.get_local_placement\([^)]*\)', 
                 r'''import numpy as np
                matrix = np.eye(4)
                if 'loc' in locals():
                    matrix[0, 3] = loc[0]
                    matrix[1, 3] = loc[1]
                    matrix[2, 3] = loc[2]
                elif 'p0' in locals():
                    matrix[0, 3] = p0[0]
                    matrix[1, 3] = p0[1]
                    matrix[2, 3] = 0.0
                    if 'angle' in locals():
                        c = math.cos(angle)
                        s = math.sin(angle)
                        matrix[0,0] = c
                        matrix[0,1] = -s
                        matrix[1,0] = s
                        matrix[1,1] = c
                if 'sill' in locals() and 'p0' in locals():
                    matrix[2, 3] = sill
''', content)

with open("backend/ifc_exporter.py", "w") as f:
    f.write(content)
