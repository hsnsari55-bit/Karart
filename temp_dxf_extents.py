import ezdxf

doc = ezdxf.readfile('datasets/twin_villa/dxf/kaRar.dxf')
msp = doc.modelspace()
lwpolylines = [e for e in msp if e.dxftype() == 'LWPOLYLINE']

xmin, ymin, xmax, ymax = float('inf'), float('inf'), float('-inf'), float('-inf')

for polyline in lwpolylines:
    vertices = list(polyline.vertices())
    for vertex in vertices:
        xmin = min(xmin, vertex[0])
        ymin = min(ymin, vertex[1])
        xmax = max(xmax, vertex[0])
        ymax = max(ymax, vertex[1])

if not (xmin == float('inf') and ymin == float('inf')):
    print(f'Bounding Box: {xmin}, {ymin} to {xmax}, {ymax}')
else:
    print('No bounding box found')