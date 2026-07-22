import ezdxf

doc = ezdxf.readfile('datasets/twin_villa/dxf/kaRar.dxf')
msp = doc.modelspace()

min_x, max_x, min_y, max_y = float('inf'), -float('inf'), float('inf'), -float('inf')

for entity in msp:
    if hasattr(entity, 'insert'):
        insert_point = entity.insert
        min_x, max_x = min(min_x, insert_point[0]), max(max_x, insert_point[0])
        min_y, max_y = min(min_y, insert_point[1]), max(max_y, insert_point[1])

    if hasattr(entity, 'start') and hasattr(entity, 'end'):
        start_point = entity.start
        end_point = entity.end
        
        min_x, max_x = min(min_x, start_point[0], end_point[0]), max(max_x, start_point[0], end_point[0])
        min_y, max_y = min(min_y, start_point[1], end_point[1]), max(max_y, start_point[1], end_point[1])

print(f'Drawing Extents: MinX={min_x}, MaxX={max_x}, MinY={min_y}, MaxY={max_y}')