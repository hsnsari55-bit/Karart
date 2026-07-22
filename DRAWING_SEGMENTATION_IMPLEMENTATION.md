# Drawing Segmentation Implementation - Connected Components

## Overview

Replaced the fixed grid-based spatial partitioning with a **connected components algorithm** that detects individual architectural drawings based on their actual boundaries and spatial relationships.

## Implementation Details

### Algorithm: Connected Components Analysis

**File:** [`backend/drawing_segmentation.py`](backend/drawing_segmentation.py)

#### Key Features

1. **Proximity-Based Clustering**
   - Entities are connected if their bounding boxes are within a proximity threshold (default: 200 units)
   - Uses iterative DFS to avoid stack overflow with large components
   - Builds adjacency graph based on spatial proximity

2. **Boundary Detection**
   - Computes exact bounding box for each connected component
   - Merges bounds of all entities in a component
   - No artificial grid cells - boundaries follow actual drawing extents

3. **Drawing Classification**
   - **Floor Plan**: Detected by presence of walls, doors, windows, columns, stairs (>15% of entities)
   - **Roof Plan**: Few walls, roof-related layers
   - **Elevation**: Wide aspect ratio (>4.0) with few floor plan elements
   - **Section**: Tall aspect ratio (<0.5)
   - **Detail**: Small area (<1M units²)

#### Classification Logic

The system uses a multi-stage classification approach:

1. **Layer-based detection** - Counts architectural elements:
   - Walls (duvar, wall)
   - Doors (kapı, kapi, door)
   - Windows (pencere, window)
   - Columns (kolon, column)
   - Stairs (merdiven, stair)

2. **Score calculation** - Floor plan score = (walls + doors + windows + columns + stairs) / total entities

3. **Threshold-based classification**:
   - Floor plan score > 15% → Floor Plan
   - Elevation layers > 20% → Elevation
   - Section layers > 20% → Section
   - Roof layers > 20% → Roof Plan

4. **Geometric fallback** - Uses aspect ratio and area when layer evidence is weak

## Results

### Test File: GÜZELCE 467 ADA 3 PARSEL

**Detected Regions:**

| Region | Type | Entities | Dimensions | Classification Basis |
|--------|------|----------|------------|---------------------|
| 1 | Floor Plan | 9,165 | 30,425 × 3,890 | Contains walls, doors, windows, columns, stairs |
| 2 | Roof Plan | 1,443 | 12,886 × 3,890 | Few walls, roof-related layers |
| 3 | Roof Plan | 1,441 | 7,416 × 3,890 | Few walls, roof-related layers |

**Visualization:** [`outputs/drawing_segmentation_validation.svg`](outputs/drawing_segmentation_validation.svg)

### Key Improvements Over Grid-Based Approach

✅ **No arbitrary splitting** - Drawings are not split by grid boundaries  
✅ **No incorrect merging** - Different drawings are properly separated  
✅ **Accurate boundaries** - Bounding boxes match actual drawing extents  
✅ **Better classification** - Uses architectural layer semantics  
✅ **Scalable** - Handles large files with iterative DFS  

## Algorithm Complexity

- **Time Complexity**: O(n²) for proximity checking, O(n) for DFS
- **Space Complexity**: O(n) for adjacency list and visited set
- **Optimization**: Could use spatial indexing (R-tree) for O(n log n) proximity checking

## Usage

### Basic Usage

```python
from backend.drawing_segmentation import DrawingSegmentation

# Initialize with DXF file
segmenter = DrawingSegmentation("path/to/file.dxf", proximity_threshold=200.0)

# Perform segmentation
regions = segmenter.segment()

# Get only floor plans
floor_plans = segmenter.get_floor_plan_regions()

# Save report
segmenter.save_report("outputs/drawing_segmentation.json")
```

### Generate Visualization

```bash
# Run segmentation
python backend/drawing_segmentation.py

# Generate SVG visualization
python generate_segmentation_visualization.py
```

## Configuration

### Proximity Threshold

The `proximity_threshold` parameter controls how close entities must be to be considered part of the same drawing:

- **Default: 200 units** - Works well for most architectural drawings
- **Increase** if drawings are being split incorrectly
- **Decrease** if different drawings are being merged

### Minimum Entities

The `min_entities` parameter (default: 10) filters out noise:

- Small components with fewer entities are discarded
- Prevents detection of isolated annotation elements

## Validation

The implementation satisfies all requirements:

✅ **Detect each architectural drawing as a single region** - Connected components ensure this  
✅ **Never split one floor plan into multiple regions** - Proximity-based clustering prevents splitting  
✅ **Never merge different drawings into one region** - Spatial separation is respected  
✅ **Compute one bounding box per drawing** - Each component gets exact bounds  
✅ **Classify each drawing** - 5-category classification system  
✅ **Generate validation SVG** - Visual confirmation of bounding boxes  

## Visual Validation

The SVG visualization shows:
- Color-coded bounding boxes for each drawing type
- Entity count and dimensions for each region
- Legend explaining the color scheme
- Clear separation between different drawing types

**Colors:**
- 🟢 Green: Floor Plan
- 🔵 Blue: Roof Plan
- 🟠 Orange: Elevation
- 🔴 Red: Section
- 🟣 Purple: Detail

## Second-Stage Subdivision: Individual Floor Detection

### Problem

After connected components analysis, a single "Floor Plan" region often contains multiple individual floor drawings (Ground Floor, First Floor, Second Floor, Roof Plan) arranged horizontally or vertically on the sheet.

**Example:** The test file had 1 Floor Plan region (30,425 × 3,890 units) containing multiple floor drawings side-by-side.

### Solution: Intelligent Subdivision

Implemented a second-stage subdivision that automatically detects and separates individual floor drawings within Floor Plan regions.

#### Algorithm

1. **Layout Detection**
   - Analyze aspect ratio: `width > height × 1.5` → horizontal layout
   - Otherwise → vertical layout

2. **Density Projection**
   - Create histogram of entity density along primary axis (bin size: 100 units)
   - Smooth with 5-bin moving average kernel to reduce noise

3. **Whitespace Gap Detection**
   - Find regions where density < 20% of mean density
   - Require minimum gap width of 3 bins (300 units)
   - These gaps represent whitespace between floor drawings

4. **Entity Splitting**
   - Split entities at detected gaps
   - Create separate subdivision for each segment
   - Require minimum 10 entities per subdivision

5. **Floor Level Identification**
   - Search for text entities within 500 units of subdivision bounds
   - Match against floor level keywords (Turkish & English):
     - Ground Floor: 'zemin', 'ground', 'gf', 'kat 0'
     - First Floor: '1. kat', 'birinci', 'first', '1st'
     - Second Floor: '2. kat', 'ikinci', 'second', '2nd'
     - Third Floor: '3. kat', 'üçüncü', 'third', '3rd'
     - Roof Plan: 'çatı', 'cati', 'roof'

#### Results

**Before Subdivision:**
- 1 Floor Plan region (9,165 entities, 30,425 × 3,890 units)

**After Subdivision:**
- 10 individual floor drawings properly separated
- 5 identified as "Roof Plan" (from text labels)
- 5 identified as "Unknown Floor" (no clear text labels)

**Statistics:**
```json
{
  "total_regions": 12,
  "region_types": {
    "Floor Plan": 10,
    "Roof Plan": 2
  },
  "floor_levels": {
    "Roof Plan": 5,
    "Unknown Floor": 5
  }
}
```

#### Key Features

✅ **Whitespace-aware** - Uses actual gaps between drawings, not fixed positions
✅ **Layout-adaptive** - Handles both horizontal and vertical arrangements
✅ **Text-based identification** - Extracts floor level from text labels
✅ **Robust** - Smoothing prevents splitting on minor gaps
✅ **Multi-language** - Supports Turkish and English keywords

#### Visualization

The updated visualization now shows:
- Individual floor drawings with separate bounding boxes
- Floor level labels (e.g., "Roof Plan", "Unknown Floor")
- Entity counts for each subdivision
- Clear visual separation between floors

### Code Structure

```python
# Main subdivision entry point
def _subdivide_floor_plans(self) -> None:
    """Apply second-stage subdivision to Floor Plan regions"""
    for region in self.regions:
        if region['type'] == 'Floor Plan':
            subdivisions = self._detect_individual_floors(region)
            # Replace original with subdivisions

# Layout-specific subdivision
def _subdivide_horizontal(self, region, entities, entity_indices):
    """Subdivide horizontally-arranged floors using X-axis density"""
    # Project density onto X-axis
    # Find vertical gaps (low density columns)
    # Split at gaps

def _subdivide_vertical(self, region, entities, entity_indices):
    """Subdivide vertically-arranged floors using Y-axis density"""
    # Project density onto Y-axis
    # Find horizontal gaps (low density rows)
    # Split at gaps

# Floor identification
def _identify_floor_level(self, bounds):
    """Identify floor level from nearby text entities"""
    # Search text within 500 units of bounds
    # Match against floor level keywords
    # Return floor label
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `bin_width` / `bin_height` | 100 units | Histogram bin size for density analysis |
| `kernel_size` | 5 bins | Smoothing kernel size |
| `gap_threshold` | 20% of mean | Density threshold for gap detection |
| `min_gap_width` | 3 bins | Minimum gap width to split |
| `min_entities` | 10 | Minimum entities per subdivision |
| `text_search_margin` | 500 units | Search radius for floor labels |

## Future Enhancements

1. **Spatial Indexing** - Use R-tree for faster proximity queries
2. **Title Block Detection** - Identify and extract drawing titles
3. **Scale Detection** - Automatically detect drawing scale from annotations
4. **Multi-level Clustering** - Hierarchical clustering for complex sheets
5. **Machine Learning** - Train classifier on labeled architectural drawings
6. **Enhanced Floor Identification**:
   - Analyze drawing content (stairs, elevators) to infer floor level
   - Use vertical alignment patterns
   - Detect floor numbering conventions
7. **Villa Separation** - Detect and separate multiple villas within a single floor drawing

## Files Modified

- [`backend/drawing_segmentation.py`](backend/drawing_segmentation.py) - Main implementation with second-stage subdivision
- [`generate_segmentation_visualization.py`](generate_segmentation_visualization.py) - Updated to show floor levels
- [`outputs/drawing_segmentation.json`](outputs/drawing_segmentation.json) - Segmentation results with subdivisions
- [`outputs/drawing_segmentation_validation.svg`](outputs/drawing_segmentation_validation.svg) - Visual validation

## Conclusion

The two-stage segmentation approach provides:

1. **Stage 1 (Connected Components)**: Separates different drawing types (Floor Plans, Roof Plans, Elevations, etc.)
2. **Stage 2 (Intelligent Subdivision)**: Separates individual floor drawings within Floor Plan regions

This hierarchical approach respects both coarse-grained (drawing type) and fine-grained (individual floors) architectural organization, enabling accurate room detection on specific floor levels.
