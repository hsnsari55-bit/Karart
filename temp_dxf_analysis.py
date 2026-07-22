import ezdxf

doc = ezdxf.readfile('datasets/twin_villa/dxf/kaRar.dxf')
msp = doc.modelspace()
xmin, ymin, xmax, ymax = float('inf'), float('inf'), float('-inf'), float('-inf')

# Handle LWPolyline specially
lwpolylines = [e for e in msp if e.dxftype() == 'LWPOLYLINE']
for lwp in lwpolylines:
    points = list(lwp.vertices())
    xmin, ymin, xmax, ymax = float('inf'), float('inf'), float('-inf'), float('-inf')
    for p in points:
        xmin = min(xmin, p[0])
        ymin = min(ymin, p[1])
        xmax = max(xmax, p[0])
        ymax = max(ymax, p[1])

# Print the result
if not (xmin == float('inf') and ymin == float('inf')):
    print(f'Bounding Box: {xmin}, {ymin} to {xmax}, {ymax}')
else:
    print("No bounding box found")
    if hasattr(entity, 'bbox'):
        bbox = entity.bbox
        if bbox is not None:
            xmin = min(xmin, bbox.min_x)
            ymin = min(ymin, bbox.min_y)
            xmax = max(xmax, bbox.max_x)
            ymax = max(ymax, bbox.max_y)
    else:
for p in getattr(entity, 'points', []):
            xmin = min(xmin, p[0])
            ymin = min(ymin, p[1])
            xmax = max(xmax, p[0])
            ymax = max(ymax, p[1])

# Print the result
if not (xmin == float('inf') and ymin == float('inf')):
    print(f'Bounding Box: {xmin}, {ymin} to {xmax}, {ymax}')
else:
    print("No bounding box found")
