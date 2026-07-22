"""
Test script for Drawing Segmentation module

Verifies that the segmentation correctly classifies drawing regions
and filters entities by drawing type.
"""

from backend.drawing_segmentation import DrawingSegmentation
from backend.config import DXF
import json


def test_segmentation():
    """Test the drawing segmentation functionality"""
    
    print("="*60)
    print("DRAWING SEGMENTATION TEST")
    print("="*60)
    
    # Initialize segmentation
    segmenter = DrawingSegmentation(str(DXF))
    
    # Perform segmentation
    print("\n1. Performing segmentation...")
    regions = segmenter.segment()
    
    print(f"   Total regions detected: {len(regions)}")
    
    # Count by type
    type_counts = {}
    for region in regions:
        region_type = region['type']
        type_counts[region_type] = type_counts.get(region_type, 0) + 1
    
    print("\n2. Region classification:")
    for drawing_type, count in sorted(type_counts.items()):
        print(f"   - {drawing_type}: {count} region(s)")
    
    # Test floor plan filtering
    print("\n3. Testing floor plan filtering...")
    floor_plans = segmenter.get_floor_plan_regions()
    print(f"   Floor plan regions: {len(floor_plans)}")
    
    for i, region in enumerate(floor_plans, 1):
        print(f"\n   Floor Plan {i}:")
        print(f"      Bounds: X[{region['bounds']['min_x']:.2f}, {region['bounds']['max_x']:.2f}]")
        print(f"      Bounds: Y[{region['bounds']['min_y']:.2f}, {region['bounds']['max_y']:.2f}]")
        print(f"      Size: {region['width']:.2f} x {region['height']:.2f}")
        print(f"      Entities: {region['entity_count']}")
    
    # Test entity filtering by type
    print("\n4. Testing entity filtering by drawing type...")
    
    for drawing_type in ['Floor Plan', 'Elevation', 'Roof Plan', 'Section']:
        entities = segmenter.filter_entities_by_type(drawing_type)
        print(f"   {drawing_type}: {len(entities)} entities")
    
    # Verify floor plans have walls
    print("\n5. Verifying floor plans contain wall entities...")
    floor_plan_entities = segmenter.filter_entities_by_type('Floor Plan')
    
    wall_layers = ['duvar', 'wall']
    wall_count = sum(1 for e in floor_plan_entities 
                     if any(kw in e['layer'].lower() for kw in wall_layers))
    
    print(f"   Total floor plan entities: {len(floor_plan_entities)}")
    print(f"   Wall entities in floor plans: {wall_count}")
    
    # Verify elevations don't have many walls
    print("\n6. Verifying elevations have fewer walls...")
    elevation_entities = segmenter.filter_entities_by_type('Elevation')
    
    elevation_wall_count = sum(1 for e in elevation_entities 
                               if any(kw in e['layer'].lower() for kw in wall_layers))
    
    print(f"   Total elevation entities: {len(elevation_entities)}")
    print(f"   Wall entities in elevations: {elevation_wall_count}")
    
    # Calculate filtering effectiveness
    print("\n7. Segmentation effectiveness:")
    total_entities = len(segmenter.entities)
    floor_plan_percentage = (len(floor_plan_entities) / total_entities * 100) if total_entities > 0 else 0
    
    print(f"   Total entities in DXF: {total_entities}")
    print(f"   Floor plan entities: {len(floor_plan_entities)} ({floor_plan_percentage:.1f}%)")
    print(f"   Non-floor plan entities filtered: {total_entities - len(floor_plan_entities)}")
    
    # Test result
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    success = True
    
    # Check 1: Multiple drawing types detected
    if len(type_counts) < 2:
        print("[FAIL] Expected multiple drawing types, found only", len(type_counts))
        success = False
    else:
        print(f"[PASS] Detected {len(type_counts)} different drawing types")
    
    # Check 2: Floor plans detected
    if 'Floor Plan' not in type_counts:
        print("[FAIL] No floor plans detected")
        success = False
    else:
        print(f"[PASS] Detected {type_counts['Floor Plan']} floor plan region(s)")
    
    # Check 3: Floor plans contain walls
    if wall_count == 0:
        print("[FAIL] No walls found in floor plan regions")
        success = False
    else:
        print(f"[PASS] Found {wall_count} wall entities in floor plans")
    
    # Check 4: Filtering reduces entity count
    if len(floor_plan_entities) >= total_entities:
        print("[FAIL] Filtering did not reduce entity count")
        success = False
    else:
        reduction = total_entities - len(floor_plan_entities)
        print(f"[PASS] Filtered out {reduction} non-floor plan entities")
    
    print("="*60)
    
    if success:
        print("[SUCCESS] ALL TESTS PASSED")
        print("\nDrawing segmentation is working correctly!")
        print("Room detection will now only process floor plan regions.")
    else:
        print("[FAILED] SOME TESTS FAILED")
        print("\nPlease review the segmentation logic.")
    
    print("="*60)
    
    return success


if __name__ == "__main__":
    test_segmentation()
