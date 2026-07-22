import ezdxf
import json
import time
import tracemalloc
import logging
from config import DXF, OUTPUT_DIR

"""Parses a DXF file, filters entities, groups by layer, and generates a report.

This module reads a DXF file and processes its entities with the following steps:
1. Skips unwanted entity types (HATCH, TEXT, MTEXT, DIMENSION, LEADER, MLEADER)
2. Retains only LINE, LWPOLYLINE, POLYLINE, ARC, CIRCLE
3. Groups retained entities by their layer attribute
4. Generates a comprehensive report with metrics

The report includes:
- Total entities processed
- Filtered entities count
- Remaining geometry count
- Layer distribution
- Parsing performance metrics

Logging is implemented for errors and performance metrics."""

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def parse_dxf():
    """Main parsing function with safety checks and metrics collection.

Args:
    None

Returns:
    None

Raises:
    None (errors are logged)"""
    try:
        doc = ezdxf.readfile(str(DXF))
    except Exception as e:
        logging.error(f"Failed to read DXF file {DXF}: {e}")
        return

    msp = doc.modelspace()
    total_entities = 0
    ignored_entities = 0
    layer_entities = {}  # layer name -> list of entity dicts

    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()

    for entity in msp:
        total_entities += 1
        e_type = entity.dxftype()
        layer = entity.dxf.layer

        # Filter out unwanted entity types
        if e_type in ("HATCH", "TEXT", "MTEXT", "DIMENSION", "LEADER", "MLEADER"):
            ignored_entities += 1
            continue

        # Process only supported entity types
        if e_type in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE"):
            # Create entity representation
            item = {
                "type": e_type,
                "layer": layer,
                "handle": entity.dxf.handle,
            }
            # Add optional properties
            try:
                item["color"] = entity.dxf.color
            except:
                item["color"] = None
            try:
                item["linetype"] = entity.dxf.linetype
            except:
                item["linetype"] = None

            # Add geometry-specific data
            if e_type == "LINE":
                item["start"] = [entity.dxf.start.x, entity.dxf.start.y]
                item["end"] = [entity.dxf.end.x, entity.dxf.end.y]
            elif e_type == "LWPOLYLINE":
                item["points"] = [[p[0], p[1]] for p in entity.get_points()]
                item["closed"] = entity.closed
            elif e_type == "POLYLINE":
                # 3D polyline handling can be added here
                pass
            elif e_type == "ARC":
                item["center"] = [entity.dxf.center.x, entity.dxf.center.y]
                item["radius"] = entity.dxf.radius
                item["start_angle"] = entity.dxf.start_angle
                item["end_angle"] = entity.dxf.end_angle
            elif e_type == "CIRCLE":
                item["center"] = [entity.dxf.center.x, entity.dxf.center.y]
                item["radius"] = entity.dxf.radius

            # Group by layer
            if layer not in layer_entities:
                layer_entities[layer] = []
            layer_entities[layer].append(item)
        else:
            # Log unknown entity types for debugging
            logging.debug(f"Skipping unsupported entity type: {e_type}")

    # Stop memory tracking
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    parsing_time = time.time() - start_time

    # Generate report
    report = {
        "total_entity_count": total_entities,
        "filtered_entity_count": ignored_entities,
        "remaining_geometry_count": sum(len(entities) for entities in layer_entities.values()),
        "parsing_time": parsing_time,
        "peak_memory_usage_mb": peak / (1024 ** 2),
        "layer_list": list(layer_entities.keys()),
        "entity_count_per_layer": {layer: len(entities) for layer, entities in layer_entities.items()},
        "warnings": []
    }

    # Write report to outputs/report.json
    report_path = OUTPUT_DIR / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    # Log completion metrics
    logging.info(f"Parsing completed in {parsing_time:.4f} seconds with peak memory {peak / (1024**2):.2f} MB")
    logging.info(f"Layer list: {list(layer_entities.keys())}")
    logging.info(f"Entity count per layer: { {layer: len(entities) for layer, entities in layer_entities.items()} }")

if __name__ == "__main__":
    parse_dxf()
