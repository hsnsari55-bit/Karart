"""
Test script for semantic floor classification.

This script tests the enhanced floor identification system to ensure
"Unknown Floor" classifications are eliminated.
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.drawing_segmentation import DrawingSegmentation
from backend.config import DXF, OUTPUT_DIR


def main():
    """Test semantic floor classification"""
    print("=" * 80)
    print("SEMANTIC FLOOR CLASSIFICATION TEST")
    print("=" * 80)
    print(f"\nDXF File: {DXF}")
    print(f"Output Directory: {OUTPUT_DIR}")
    
    # Initialize segmentation with enhanced semantic classifier
    print("\n[1/3] Initializing drawing segmentation with semantic classifier...")
    segmenter = DrawingSegmentation(str(DXF), proximity_threshold=200.0)
    
    # Perform segmentation
    print("\n[2/3] Performing segmentation and floor classification...")
    regions = segmenter.segment()
    
    print(f"\n✓ Detected {len(regions)} drawing regions")
    
    # Save reports
    print("\n[3/3] Generating reports...")
    output_path = OUTPUT_DIR / "drawing_segmentation.json"
    validation_path = OUTPUT_DIR / "floor_classification_validation.json"
    segmenter.save_report(str(output_path), str(validation_path))
    
    # Analyze results
    print("\n" + "=" * 80)
    print("CLASSIFICATION RESULTS")
    print("=" * 80)
    
    floor_plans = segmenter.get_floor_plan_regions()
    
    if not floor_plans:
        print("\n⚠️  No floor plans detected!")
        return
    
    print(f"\nTotal Floor Plans: {len(floor_plans)}")
    
    unknown_count = 0
    low_confidence_count = 0
    
    for i, region in enumerate(floor_plans, 1):
        floor_level = region.get('floor_level', 'Unknown')
        confidence = region.get('confidence', 0.0)
        reasoning = region.get('classification_reasoning', [])
        
        # Check for unknown or low confidence
        if 'Unknown' in floor_level:
            unknown_count += 1
            status = "❌ UNKNOWN"
        elif confidence < 0.5:
            low_confidence_count += 1
            status = "⚠️  LOW CONFIDENCE"
        else:
            status = "✓ OK"
        
        print(f"\n{status} Floor Plan {i}:")
        print(f"  Classification: {floor_level}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Size: {region['width']:.0f} x {region['height']:.0f}")
        print(f"  Entities: {region['entity_count']}")
        
        if reasoning:
            print(f"  Reasoning ({len(reasoning)} factors):")
            for j, reason in enumerate(reasoning[:5], 1):  # Show top 5 reasons
                print(f"    {j}. {reason}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = len(floor_plans) - unknown_count - low_confidence_count
    
    print(f"\nTotal Floor Plans: {len(floor_plans)}")
    print(f"  ✓ Successfully Classified: {success_count}")
    print(f"  ⚠️  Low Confidence (<50%): {low_confidence_count}")
    print(f"  ❌ Unknown Floor: {unknown_count}")
    
    if unknown_count == 0:
        print("\n🎉 SUCCESS! All floor plans successfully classified!")
        print("   Goal achieved: 'Unknown Floor' eliminated!")
    else:
        print(f"\n⚠️  WARNING: {unknown_count} floor plan(s) still classified as 'Unknown'")
        print("   Review the validation report for details.")
    
    print(f"\n📄 Reports saved:")
    print(f"   - Segmentation: {output_path}")
    print(f"   - Validation: {validation_path}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
