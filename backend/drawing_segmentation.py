"""
Drawing Segmentation Module

Automatically detects and classifies drawing regions in a DXF file using
connected components analysis instead of fixed grid partitioning.

Classifies drawings into:
- Floor Plan (with second-stage subdivision for individual floors)
- Roof Plan
- Elevation
- Section
- Detail

This ensures room detection only runs on floor plans.

Second-stage subdivision separates individual floor drawings within
a Floor Plan region using whitespace analysis, alignment detection,
and text-based floor identification.

Enhanced with SemanticFloorClassifier to eliminate "Unknown Floor" classifications.
"""

import ezdxf
import json
import math
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import numpy as np
from backend.semantic_floor_classifier import SemanticFloorClassifier, generate_validation_report


class DrawingSegmentation:
    """Detects and classifies drawing regions using connected components"""
    
    # Classification keywords for layer names
    FLOOR_PLAN_KEYWORDS = [
        'kat', 'plan', 'zemin', 'floor', 'ground', 'story', 'level',
        'duvar', 'wall', 'kapi', 'kapı', 'door', 'pencere', 'window'
    ]
    
    ROOF_PLAN_KEYWORDS = [
        'çatı', 'cati', 'roof', 'üst', 'ust', 'top'
    ]
    
    ELEVATION_KEYWORDS = [
        'görünüş', 'gorunus', 'görünü', 'gorunu', 'elevation', 'facade',
        'cephe', 'view', 'gor', 'gör'
    ]
    
    SECTION_KEYWORDS = [
        'kesit', 'section', 'cut'
    ]
    
    DETAIL_KEYWORDS = [
        'detay', 'detail', 'node', 'junction'
    ]
    
    # Floor level identification keywords
    GROUND_FLOOR_KEYWORDS = [
        'zemin', 'ground', 'gf', 'g.f', 'kat 0', 'kat0', 'level 0', 'level0'
    ]
    
    FIRST_FLOOR_KEYWORDS = [
        '1. kat', '1.kat', 'birinci', 'first', '1st', 'kat 1', 'kat1', 'level 1', 'level1'
    ]
    
    SECOND_FLOOR_KEYWORDS = [
        '2. kat', '2.kat', 'ikinci', 'second', '2nd', 'kat 2', 'kat2', 'level 2', 'level2'
    ]
    
    THIRD_FLOOR_KEYWORDS = [
        '3. kat', '3.kat', 'üçüncü', 'ucuncu', 'third', '3rd', 'kat 3', 'kat3', 'level 3', 'level3'
    ]
    
    def __init__(self, dxf_path: str, proximity_threshold: float = 200.0):
        """
        Initialize the segmentation engine.
        
        Args:
            dxf_path: Path to the DXF file
            proximity_threshold: Maximum distance for entities to be considered connected
        """
        self.dxf_path = dxf_path
        self.proximity_threshold = proximity_threshold
        self.doc = None
        self.entities = []
        self.regions = []
        self.text_entities = []  # Store text entities separately
        self.semantic_classifier = SemanticFloorClassifier()  # Enhanced classifier
        self.classification_details = []  # Store detailed classification info
        
    def load_dxf(self) -> None:
        """Load DXF file and extract entities"""
        self.doc = ezdxf.readfile(self.dxf_path)
        msp = self.doc.modelspace()
        
        # Extract relevant entities with geometry
        for entity in msp:
            e_type = entity.dxftype()
            
            # Extract text entities separately for floor identification
            if e_type in ("TEXT", "MTEXT"):
                try:
                    text_data = {
                        'type': e_type,
                        'text': entity.dxf.text if e_type == "TEXT" else entity.text,
                        'layer': entity.dxf.layer,
                        'position': {
                            'x': entity.dxf.insert.x if e_type == "TEXT" else entity.dxf.insert.x,
                            'y': entity.dxf.insert.y if e_type == "TEXT" else entity.dxf.insert.y
                        },
                        'height': entity.dxf.height if hasattr(entity.dxf, 'height') else 0
                    }
                    self.text_entities.append(text_data)
                except:
                    pass
                continue
            
            # Skip other non-geometric entities
            if e_type in ("HATCH", "DIMENSION", "LEADER", "MLEADER"):
                continue
                
            if e_type not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE"):
                continue
            
            # Extract entity data
            entity_data = {
                'type': e_type,
                'layer': entity.dxf.layer,
                'handle': entity.dxf.handle
            }
            
            # Extract bounding box
            try:
                if e_type == "LINE":
                    entity_data['bounds'] = self._get_line_bounds(entity)
                elif e_type in ("LWPOLYLINE", "POLYLINE"):
                    entity_data['bounds'] = self._get_polyline_bounds(entity)
                elif e_type == "ARC":
                    entity_data['bounds'] = self._get_arc_bounds(entity)
                elif e_type == "CIRCLE":
                    entity_data['bounds'] = self._get_circle_bounds(entity)
                else:
                    continue
                    
                self.entities.append(entity_data)
            except:
                # Skip entities with invalid geometry
                continue
    
    def _get_line_bounds(self, entity) -> Dict[str, float]:
        """Get bounding box for LINE entity"""
        return {
            'min_x': min(entity.dxf.start.x, entity.dxf.end.x),
            'max_x': max(entity.dxf.start.x, entity.dxf.end.x),
            'min_y': min(entity.dxf.start.y, entity.dxf.end.y),
            'max_y': max(entity.dxf.start.y, entity.dxf.end.y)
        }
    
    def _get_polyline_bounds(self, entity) -> Dict[str, float]:
        """Get bounding box for POLYLINE entity"""
        points = list(entity.get_points())
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return {
            'min_x': min(xs),
            'max_x': max(xs),
            'min_y': min(ys),
            'max_y': max(ys)
        }
    
    def _get_arc_bounds(self, entity) -> Dict[str, float]:
        """Get bounding box for ARC entity"""
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        return {
            'min_x': cx - r,
            'max_x': cx + r,
            'min_y': cy - r,
            'max_y': cy + r
        }
    
    def _get_circle_bounds(self, entity) -> Dict[str, float]:
        """Get bounding box for CIRCLE entity"""
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        return {
            'min_x': cx - r,
            'max_x': cx + r,
            'min_y': cy - r,
            'max_y': cy + r
        }
    
    def _bounds_distance(self, bounds1: Dict[str, float], bounds2: Dict[str, float]) -> float:
        """
        Calculate minimum distance between two bounding boxes.
        Returns 0 if they overlap or touch.
        
        Args:
            bounds1: First bounding box
            bounds2: Second bounding box
            
        Returns:
            Minimum distance between the boxes
        """
        # Check for overlap or adjacency
        x_overlap = not (bounds1['max_x'] < bounds2['min_x'] or bounds2['max_x'] < bounds1['min_x'])
        y_overlap = not (bounds1['max_y'] < bounds2['min_y'] or bounds2['max_y'] < bounds1['min_y'])
        
        if x_overlap and y_overlap:
            return 0.0  # Overlapping
        
        # Calculate minimum distance
        if x_overlap:
            # Vertically separated
            return min(
                abs(bounds1['min_y'] - bounds2['max_y']),
                abs(bounds2['min_y'] - bounds1['max_y'])
            )
        elif y_overlap:
            # Horizontally separated
            return min(
                abs(bounds1['min_x'] - bounds2['max_x']),
                abs(bounds2['min_x'] - bounds1['max_x'])
            )
        else:
            # Diagonally separated - use corner-to-corner distance
            dx = max(
                bounds1['min_x'] - bounds2['max_x'],
                bounds2['min_x'] - bounds1['max_x'],
                0
            )
            dy = max(
                bounds1['min_y'] - bounds2['max_y'],
                bounds2['min_y'] - bounds1['max_y'],
                0
            )
            return math.sqrt(dx * dx + dy * dy)
    
    def _connected_components(self) -> List[List[int]]:
        """
        Find connected components using proximity-based clustering.
        Entities are connected if their bounding boxes are within proximity_threshold.
        
        Returns:
            List of components, where each component is a list of entity indices
        """
        n = len(self.entities)
        if n == 0:
            return []
        
        # Build adjacency list
        adjacency = defaultdict(set)
        
        # Check all pairs for proximity
        for i in range(n):
            for j in range(i + 1, n):
                distance = self._bounds_distance(
                    self.entities[i]['bounds'],
                    self.entities[j]['bounds']
                )
                
                if distance <= self.proximity_threshold:
                    adjacency[i].add(j)
                    adjacency[j].add(i)
        
        # Find connected components using iterative DFS (to avoid stack overflow)
        visited = set()
        components = []
        
        # Process all nodes
        for i in range(n):
            if i not in visited:
                # Iterative DFS using a stack
                component = []
                stack = [i]
                
                while stack:
                    node = stack.pop()
                    
                    if node in visited:
                        continue
                    
                    visited.add(node)
                    component.append(node)
                    
                    # Add unvisited neighbors to stack
                    for neighbor in adjacency[node]:
                        if neighbor not in visited:
                            stack.append(neighbor)
                
                components.append(component)
        
        return components
    
    def _merge_bounds(self, entity_indices: List[int]) -> Dict[str, float]:
        """
        Compute the bounding box that encompasses all entities in the list.
        
        Args:
            entity_indices: List of entity indices
            
        Returns:
            Merged bounding box
        """
        if not entity_indices:
            return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        
        bounds_list = [self.entities[i]['bounds'] for i in entity_indices]
        
        return {
            'min_x': min(b['min_x'] for b in bounds_list),
            'max_x': max(b['max_x'] for b in bounds_list),
            'min_y': min(b['min_y'] for b in bounds_list),
            'max_y': max(b['max_y'] for b in bounds_list)
        }
    
    def _classify_by_layer(self, layer_name: str) -> Optional[str]:
        """
        Classify drawing type based on layer name.
        
        Returns:
            Drawing type or None if uncertain
        """
        layer_lower = layer_name.lower()
        
        # Check each category (order matters - more specific first)
        if any(kw in layer_lower for kw in self.ROOF_PLAN_KEYWORDS):
            return "Roof Plan"
        
        if any(kw in layer_lower for kw in self.ELEVATION_KEYWORDS):
            return "Elevation"
        
        if any(kw in layer_lower for kw in self.SECTION_KEYWORDS):
            return "Section"
        
        if any(kw in layer_lower for kw in self.DETAIL_KEYWORDS):
            return "Detail"
        
        if any(kw in layer_lower for kw in self.FLOOR_PLAN_KEYWORDS):
            return "Floor Plan"
        
        return None
    
    def _classify_region(self, entity_indices: List[int], bounds: Dict[str, float]) -> str:
        """
        Classify a drawing region based on its characteristics.
        
        Args:
            entity_indices: Indices of entities in this region
            bounds: Bounding box of the region
            
        Returns:
            Drawing type classification
        """
        entities = [self.entities[i] for i in entity_indices]
        
        # Count specific architectural elements by layer
        wall_count = 0
        door_count = 0
        window_count = 0
        column_count = 0
        stair_count = 0
        roof_count = 0
        elevation_count = 0
        section_count = 0
        
        for entity in entities:
            layer_lower = entity['layer'].lower()
            
            # Floor plan indicators
            if any(kw in layer_lower for kw in ['duvar', 'wall']):
                wall_count += 1
            if any(kw in layer_lower for kw in ['kapi', 'kapı', 'door']):
                door_count += 1
            if any(kw in layer_lower for kw in ['pencere', 'window']):
                window_count += 1
            if any(kw in layer_lower for kw in ['kolon', 'column']):
                column_count += 1
            if any(kw in layer_lower for kw in ['merdiven', 'stair', 'stairs']):
                stair_count += 1
            
            # Other drawing type indicators
            if any(kw in layer_lower for kw in ['çatı', 'cati', 'roof']):
                roof_count += 1
            if any(kw in layer_lower for kw in ['görünüş', 'gorunus', 'görünü', 'gorunu', 'elevation', 'cephe', 'gor', 'gör']):
                elevation_count += 1
            if any(kw in layer_lower for kw in ['kesit', 'section']):
                section_count += 1
        
        # Calculate ratios
        total = len(entities)
        floor_plan_score = (wall_count + door_count + window_count + column_count + stair_count) / total if total > 0 else 0
        
        # Strong floor plan indicators (walls, doors, windows, columns, stairs)
        if floor_plan_score > 0.15:  # At least 15% of entities are floor plan elements
            return "Floor Plan"
        
        # Explicit layer classification
        if elevation_count > total * 0.2:
            return "Elevation"
        
        if section_count > total * 0.2:
            return "Section"
        
        if roof_count > total * 0.2:
            return "Roof Plan"
        
        # Geometric heuristics as fallback
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        aspect_ratio = width / height if height > 0 else 1.0
        area = width * height
        
        # Detail: small region
        if area < 1000000:
            return "Detail"
        
        # Section: typically taller than wide (vertical cut)
        if aspect_ratio < 0.5:
            return "Section"
        
        # Elevation: very wide horizontal view with few floor plan elements
        if aspect_ratio > 4.0 and floor_plan_score < 0.05:
            return "Elevation"
        
        # Check for roof indicators (simpler geometry, fewer walls)
        if wall_count < total * 0.05 and area > 500000:  # Very few walls but substantial area
            return "Roof Plan"
        
        # Default to Floor Plan (most common for architectural drawings)
        return "Floor Plan"
    
    def segment(self, min_entities: int = 10) -> List[Dict[str, Any]]:
        """
        Perform drawing segmentation using connected components.
        
        Args:
            min_entities: Minimum number of entities for a valid region
            
        Returns:
            List of classified regions
        """
        # Load DXF if not already loaded
        if not self.entities:
            self.load_dxf()
        
        print(f"Loaded {len(self.entities)} entities")
        
        # Find connected components
        components = self._connected_components()
        print(f"Found {len(components)} connected components")
        
        # Filter and classify each component
        classified_regions = []
        
        for component in components:
            # Skip small components (noise)
            if len(component) < min_entities:
                continue
            
            # Compute bounding box for this drawing
            bounds = self._merge_bounds(component)
            width = bounds['max_x'] - bounds['min_x']
            height = bounds['max_y'] - bounds['min_y']
            
            # Skip degenerate regions
            if width < 10 or height < 10:
                continue
            
            # Classify the region
            classification = self._classify_region(component, bounds)
            
            classified_region = {
                'type': classification,
                'bounds': bounds,
                'width': width,
                'height': height,
                'entity_count': len(component),
                'entity_indices': component,
                'center': {
                    'x': (bounds['min_x'] + bounds['max_x']) / 2,
                    'y': (bounds['min_y'] + bounds['max_y']) / 2
                }
            }
            
            classified_regions.append(classified_region)
        
        # Sort regions by area (largest first)
        classified_regions.sort(key=lambda r: r['width'] * r['height'], reverse=True)
        
        self.regions = classified_regions
        print(f"Detected {len(classified_regions)} valid drawing regions")
        
        # Apply second-stage subdivision to Floor Plan regions
        self._subdivide_floor_plans()
        
        return classified_regions
    
    def _subdivide_floor_plans(self) -> None:
        """
        Apply second-stage subdivision to Floor Plan regions to separate
        individual floor drawings (Ground Floor, First Floor, etc.)
        """
        new_regions = []
        
        for region in self.regions:
            if region['type'] == 'Floor Plan':
                # Subdivide this floor plan region
                subdivisions = self._detect_individual_floors(region)
                
                if subdivisions and len(subdivisions) > 1:
                    print(f"  Subdivided Floor Plan into {len(subdivisions)} individual floors")
                    new_regions.extend(subdivisions)
                else:
                    # Keep original if subdivision didn't work
                    new_regions.append(region)
            else:
                # Keep non-floor-plan regions as-is
                new_regions.append(region)
        
        self.regions = new_regions
    
    def _detect_individual_floors(self, region: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect individual floor drawings within a Floor Plan region.
        
        Uses:
        - Whitespace analysis (vertical gaps between drawings)
        - Horizontal alignment detection
        - Entity density analysis
        - Text-based floor identification
        
        Args:
            region: Floor Plan region to subdivide
            
        Returns:
            List of individual floor drawing regions
        """
        entity_indices = region['entity_indices']
        entities = [self.entities[i] for i in entity_indices]
        bounds = region['bounds']
        
        # Determine primary layout direction by aspect ratio
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        
        # If width >> height, drawings are arranged horizontally
        # If height >> width, drawings are arranged vertically
        horizontal_layout = width > height * 1.5
        
        if horizontal_layout:
            return self._subdivide_horizontal(region, entities, entity_indices)
        else:
            return self._subdivide_vertical(region, entities, entity_indices)
    
    def _subdivide_horizontal(self, region: Dict[str, Any], entities: List[Dict],
                              entity_indices: List[int]) -> List[Dict[str, Any]]:
        """
        Subdivide horizontally-arranged floor drawings using vertical whitespace analysis.
        
        Strategy:
        1. Project entity density onto X-axis
        2. Find vertical whitespace gaps (low density regions)
        3. Split at gaps to separate individual drawings
        4. Identify floor level from text labels
        """
        bounds = region['bounds']
        min_x, max_x = bounds['min_x'], bounds['max_x']
        
        # Create density histogram along X-axis
        bin_width = 100.0  # 100 units per bin
        num_bins = int((max_x - min_x) / bin_width) + 1
        density = np.zeros(num_bins)
        
        # Count entities in each bin
        for entity in entities:
            e_bounds = entity['bounds']
            center_x = (e_bounds['min_x'] + e_bounds['max_x']) / 2
            bin_idx = int((center_x - min_x) / bin_width)
            if 0 <= bin_idx < num_bins:
                density[bin_idx] += 1
        
        # Smooth density to reduce noise
        if len(density) > 5:
            kernel_size = 5
            kernel = np.ones(kernel_size) / kernel_size
            density = np.convolve(density, kernel, mode='same')
        
        # Find gaps (low density regions)
        threshold = np.mean(density) * 0.2  # 20% of mean density
        gaps = []
        
        in_gap = False
        gap_start = 0
        
        for i, d in enumerate(density):
            if d < threshold and not in_gap:
                gap_start = i
                in_gap = True
            elif d >= threshold and in_gap:
                gap_end = i
                # Only consider significant gaps (at least 3 bins wide)
                if gap_end - gap_start >= 3:
                    gap_x = min_x + (gap_start + gap_end) / 2 * bin_width
                    gaps.append(gap_x)
                in_gap = False
        
        # If no significant gaps found, return original region
        if not gaps:
            return [region]
        
        # Split entities at gaps
        split_points = [min_x] + gaps + [max_x]
        subdivisions = []
        
        for i in range(len(split_points) - 1):
            x_start = split_points[i]
            x_end = split_points[i + 1]
            
            # Collect entities in this range
            sub_entity_indices = []
            for idx, entity in zip(entity_indices, entities):
                e_bounds = entity['bounds']
                center_x = (e_bounds['min_x'] + e_bounds['max_x']) / 2
                if x_start <= center_x < x_end:
                    sub_entity_indices.append(idx)
            
            # Skip if too few entities
            if len(sub_entity_indices) < 10:
                continue
            
            # Compute bounds for this subdivision
            sub_bounds = self._merge_bounds(sub_entity_indices)
            sub_width = sub_bounds['max_x'] - sub_bounds['min_x']
            sub_height = sub_bounds['max_y'] - sub_bounds['min_y']
            
            # Identify floor level from text with enhanced semantic classification
            relative_pos = {
                'total_drawings': len(split_points) - 1,
                'position_index': i,
                'layout': 'horizontal'
            }
            floor_label, confidence, reasoning = self._identify_floor_level(
                sub_bounds,
                sub_entity_indices,
                relative_pos
            )
            
            subdivision = {
                'type': 'Floor Plan',
                'floor_level': floor_label,
                'confidence': confidence,
                'classification_reasoning': reasoning,
                'bounds': sub_bounds,
                'width': sub_width,
                'height': sub_height,
                'entity_count': len(sub_entity_indices),
                'entity_indices': sub_entity_indices,
                'center': {
                    'x': (sub_bounds['min_x'] + sub_bounds['max_x']) / 2,
                    'y': (sub_bounds['min_y'] + sub_bounds['max_y']) / 2
                }
            }
            
            subdivisions.append(subdivision)
            
            # Store classification details for validation report
            self.classification_details.append({
                'classification': floor_label,
                'confidence': confidence,
                'reasoning': reasoning,
                'bounds': sub_bounds,
                'text_samples': [t['text'] for t in self.text_entities
                               if sub_bounds['min_x'] - 500 <= t['position']['x'] <= sub_bounds['max_x'] + 500
                               and sub_bounds['min_y'] - 500 <= t['position']['y'] <= sub_bounds['max_y'] + 500][:10],
                'layer_samples': list(set([self.entities[idx]['layer'] for idx in sub_entity_indices]))[:10]
            })
        
        return subdivisions if subdivisions else [region]
    
    def _subdivide_vertical(self, region: Dict[str, Any], entities: List[Dict],
                           entity_indices: List[int]) -> List[Dict[str, Any]]:
        """
        Subdivide vertically-arranged floor drawings using horizontal whitespace analysis.
        
        Similar to horizontal subdivision but operates on Y-axis.
        """
        bounds = region['bounds']
        min_y, max_y = bounds['min_y'], bounds['max_y']
        
        # Create density histogram along Y-axis
        bin_height = 100.0
        num_bins = int((max_y - min_y) / bin_height) + 1
        density = np.zeros(num_bins)
        
        # Count entities in each bin
        for entity in entities:
            e_bounds = entity['bounds']
            center_y = (e_bounds['min_y'] + e_bounds['max_y']) / 2
            bin_idx = int((center_y - min_y) / bin_height)
            if 0 <= bin_idx < num_bins:
                density[bin_idx] += 1
        
        # Smooth density
        if len(density) > 5:
            kernel_size = 5
            kernel = np.ones(kernel_size) / kernel_size
            density = np.convolve(density, kernel, mode='same')
        
        # Find gaps
        threshold = np.mean(density) * 0.2
        gaps = []
        
        in_gap = False
        gap_start = 0
        
        for i, d in enumerate(density):
            if d < threshold and not in_gap:
                gap_start = i
                in_gap = True
            elif d >= threshold and in_gap:
                gap_end = i
                if gap_end - gap_start >= 3:
                    gap_y = min_y + (gap_start + gap_end) / 2 * bin_height
                    gaps.append(gap_y)
                in_gap = False
        
        if not gaps:
            return [region]
        
        # Split entities at gaps
        split_points = [min_y] + gaps + [max_y]
        subdivisions = []
        
        for i in range(len(split_points) - 1):
            y_start = split_points[i]
            y_end = split_points[i + 1]
            
            sub_entity_indices = []
            for idx, entity in zip(entity_indices, entities):
                e_bounds = entity['bounds']
                center_y = (e_bounds['min_y'] + e_bounds['max_y']) / 2
                if y_start <= center_y < y_end:
                    sub_entity_indices.append(idx)
            
            if len(sub_entity_indices) < 10:
                continue
            
            sub_bounds = self._merge_bounds(sub_entity_indices)
            sub_width = sub_bounds['max_x'] - sub_bounds['min_x']
            sub_height = sub_bounds['max_y'] - sub_bounds['min_y']
            
            # Identify floor level with enhanced semantic classification
            relative_pos = {
                'total_drawings': len(split_points) - 1,
                'position_index': i,
                'layout': 'vertical'
            }
            floor_label, confidence, reasoning = self._identify_floor_level(
                sub_bounds,
                sub_entity_indices,
                relative_pos
            )
            
            subdivision = {
                'type': 'Floor Plan',
                'floor_level': floor_label,
                'confidence': confidence,
                'classification_reasoning': reasoning,
                'bounds': sub_bounds,
                'width': sub_width,
                'height': sub_height,
                'entity_count': len(sub_entity_indices),
                'entity_indices': sub_entity_indices,
                'center': {
                    'x': (sub_bounds['min_x'] + sub_bounds['max_x']) / 2,
                    'y': (sub_bounds['min_y'] + sub_bounds['max_y']) / 2
                }
            }
            
            subdivisions.append(subdivision)
            
            # Store classification details for validation report
            self.classification_details.append({
                'classification': floor_label,
                'confidence': confidence,
                'reasoning': reasoning,
                'bounds': sub_bounds,
                'text_samples': [t['text'] for t in self.text_entities
                               if sub_bounds['min_x'] - 500 <= t['position']['x'] <= sub_bounds['max_x'] + 500
                               and sub_bounds['min_y'] - 500 <= t['position']['y'] <= sub_bounds['max_y'] + 500][:10],
                'layer_samples': list(set([self.entities[idx]['layer'] for idx in sub_entity_indices]))[:10]
            })
        
        return subdivisions if subdivisions else [region]
    
    def _identify_floor_level(self, bounds: Dict[str, float],
                             entity_indices: List[int] = None,
                             relative_position: Optional[Dict[str, Any]] = None) -> Tuple[str, float, List[str]]:
        """
        Identify floor level using enhanced semantic classification.
        
        Args:
            bounds: Bounding box of the floor drawing
            entity_indices: Indices of entities in this region
            relative_position: Optional position info relative to other drawings
            
        Returns:
            Tuple of (floor_level, confidence, reasoning)
        """
        # Expand bounds slightly to catch nearby labels
        margin = 500.0
        search_bounds = {
            'min_x': bounds['min_x'] - margin,
            'max_x': bounds['max_x'] + margin,
            'min_y': bounds['min_y'] - margin,
            'max_y': bounds['max_y'] + margin
        }
        
        # Find text entities within search bounds
        relevant_text_entities = []
        for text_entity in self.text_entities:
            pos = text_entity['position']
            if (search_bounds['min_x'] <= pos['x'] <= search_bounds['max_x'] and
                search_bounds['min_y'] <= pos['y'] <= search_bounds['max_y']):
                relevant_text_entities.append(text_entity)
        
        # Collect layer names from entities in this region
        layer_names = []
        if entity_indices:
            layer_names = list(set([self.entities[i]['layer'] for i in entity_indices]))
        
        # Use semantic classifier
        classification, confidence, reasoning = self.semantic_classifier.classify_floor(
            text_entities=relevant_text_entities,
            bounds=bounds,
            layer_names=layer_names,
            entity_count=len(entity_indices) if entity_indices else 0,
            relative_position=relative_position
        )
        
        # Normalize classification to human-readable label
        floor_label = self.semantic_classifier.normalize_classification(classification)
        
        return floor_label, confidence, reasoning
    
    def get_floor_plan_regions(self) -> List[Dict[str, Any]]:
        """
        Get only the floor plan regions.
        
        Returns:
            List of floor plan regions
        """
        if not self.regions:
            self.segment()
        
        return [r for r in self.regions if r['type'] == 'Floor Plan']
    
    def filter_entities_by_type(self, drawing_type: str) -> List[Dict[str, Any]]:
        """
        Filter entities that belong to a specific drawing type.
        
        Args:
            drawing_type: Type of drawing to filter for
            
        Returns:
            List of entities in that drawing type
        """
        if not self.regions:
            self.segment()
        
        # Get regions of the specified type
        target_regions = [r for r in self.regions if r['type'] == drawing_type]
        
        # Collect all entity indices from these regions
        entity_indices = set()
        for region in target_regions:
            entity_indices.update(region['entity_indices'])
        
        # Return the actual entities
        return [self.entities[i] for i in entity_indices]
    
    def save_report(self, output_path: str, validation_report_path: Optional[str] = None) -> None:
        """
        Save segmentation report to JSON file.
        
        Args:
            output_path: Path to save the report
            validation_report_path: Optional path to save detailed validation report
        """
        if not self.regions:
            self.segment()
        
        # Count regions by type
        type_counts = Counter(r['type'] for r in self.regions)
        
        # Count floor plan regions by floor level
        floor_level_counts = Counter()
        unknown_count = 0
        for r in self.regions:
            if r['type'] == 'Floor Plan' and 'floor_level' in r:
                floor_level_counts[r['floor_level']] += 1
                if 'Unknown' in r['floor_level']:
                    unknown_count += 1
        
        # Prepare regions for JSON (remove entity_indices for cleaner output)
        regions_for_json = []
        for region in self.regions:
            region_copy = region.copy()
            region_copy.pop('entity_indices', None)  # Remove large list
            regions_for_json.append(region_copy)
        
        report = {
            'total_entities': len(self.entities),
            'total_text_entities': len(self.text_entities),
            'total_regions': len(self.regions),
            'proximity_threshold': self.proximity_threshold,
            'region_types': dict(type_counts),
            'floor_levels': dict(floor_level_counts),
            'unknown_floor_count': unknown_count,
            'regions': regions_for_json
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nSegmentation report saved to {output_path}")
        print(f"\nRegion Summary:")
        for drawing_type, count in type_counts.items():
            print(f"  {drawing_type}: {count} region(s)")
        
        if floor_level_counts:
            print(f"\nFloor Plan Breakdown:")
            for floor_level, count in floor_level_counts.items():
                confidence_info = ""
                # Find average confidence for this floor level
                confidences = [r.get('confidence', 0) for r in self.regions
                             if r.get('floor_level') == floor_level]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    confidence_info = f" (avg confidence: {avg_confidence:.2f})"
                print(f"  {floor_level}: {count} region(s){confidence_info}")
            
            if unknown_count > 0:
                print(f"\n⚠️  WARNING: {unknown_count} 'Unknown Floor' classification(s) found!")
            else:
                print(f"\n✓ SUCCESS: All floor plans successfully classified!")
        
        # Generate detailed validation report if requested
        if validation_report_path and self.classification_details:
            generate_validation_report(self.classification_details, validation_report_path)
            print(f"\nDetailed validation report saved to {validation_report_path}")


def main():
    """Test the drawing segmentation module with enhanced semantic classification"""
    from config import DXF, OUTPUT_DIR
    
    # Initialize segmentation with proximity threshold
    segmenter = DrawingSegmentation(str(DXF), proximity_threshold=200.0)
    
    # Perform segmentation
    print("Performing drawing segmentation using connected components...")
    print("Enhanced with semantic floor classification...")
    regions = segmenter.segment()
    
    # Save report with validation
    output_path = OUTPUT_DIR / "drawing_segmentation.json"
    validation_path = OUTPUT_DIR / "floor_classification_validation.json"
    segmenter.save_report(str(output_path), str(validation_path))
    
    # Show floor plan regions
    floor_plans = segmenter.get_floor_plan_regions()
    print(f"\nFound {len(floor_plans)} floor plan region(s)")
    
    for i, region in enumerate(floor_plans, 1):
        floor_level = region.get('floor_level', 'Unknown')
        confidence = region.get('confidence', 0.0)
        print(f"\nFloor Plan {i}: {floor_level} (confidence: {confidence:.2f})")
        print(f"  Bounds: X[{region['bounds']['min_x']:.2f}, {region['bounds']['max_x']:.2f}]")
        print(f"  Bounds: Y[{region['bounds']['min_y']:.2f}, {region['bounds']['max_y']:.2f}]")
        print(f"  Size: {region['width']:.2f} x {region['height']:.2f}")
        print(f"  Entities: {region['entity_count']}")
        
        # Show classification reasoning (first 3 reasons)
        reasoning = region.get('classification_reasoning', [])
        if reasoning:
            print(f"  Classification reasoning:")
            for reason in reasoning[:3]:
                print(f"    - {reason}")


if __name__ == "__main__":
    main()
