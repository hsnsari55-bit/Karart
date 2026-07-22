import json
from backend.geometry_engine import GeometryEngine

engine = GeometryEngine()
walls = engine.run()
print(f"Total wall segments before collinear merge: {len(walls)}")
