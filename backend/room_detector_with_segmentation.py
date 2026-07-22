"""
Room Detector with Drawing Segmentation Integration

This module integrates drawing segmentation with room detection,
ensuring room detection only runs on floor plan regions.
"""

import json
import math
import ezdxf
from pathlib import Path
from typing import List, Dict, Any, Tuple
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize
from drawing_segmentation import DrawingSegmentation


def get_project_path() -> Path:
    return Path(__file__).parent.parent


class RoomDetectorWithSegmentation:
    """Room Detection with automatic drawing type filtering"""
    
    def __init__(self, 
                 dxf_path: str,
                 rooms_output: str = "outputs/rooms_segmented.json",
                 report_output: str = "outputs/room_report_segmented.json",
                 snap_tolerance: float = 5.0):
        """
        Initialize the Room Detection Engine with Segmentation.
        
        Args:
            dxf_path: Path to DXF file
            rooms_output: Path for rooms output JSON file
            report_output: Path for room report JSON file
            snap_tolerance: Tolerance for snapping wall endpoints
        """
        self.project_path = get_project_path()
        self.dxf_path = dxf_path
        self.rooms_output = rooms_output
        self.report_output = report_output
        self.snap_tolerance = snap_tolerance
        self.segmenter = None
        self.floor_plan_regions = []
        
    def load_segmentation(self) -> None:
        """Load drawing segmentation to identify floor plan regions."""
        print("Loading drawing segmentation...")
        self.segmenter = DrawingSegmentation(self.dxf_path)
        self.floor_plan_regions = self.segmenter.get_floor_plan_regions()
        print(f"Found {len(self.floor_plan_regions)} floor plan region(s)")
    
    def extract_walls_from_dxf(self) -> List[Dict[str, Any]]:
        """
        Extract wall entities from DXF file, filtered to floor plan regions.
        
        Returns:
            List of wall dictionaries with start/end coordinates
        """
        doc = ezdxf.readfile(self.dxf_path)
        msp = doc.modelspace()
        
        walls = []
        wall_layers = ['duvar', 'wall', 'walls']
        
        for entity in msp:
            e_type = entity.dxftype()
            layer = entity.dxf.layer.lower()
            
            # Filter for wall layers
            if not any(kw in layer for kw in wall_layers):
                continue
            
            # Extract LINE entities
            if e_type == "LINE":
                start = [entity.dxf.start.x, entity.dxf.start.y]
                end = [entity.dxf.end.x, entity.dxf.end.y]
                
                # Check if wall is in floor plan region
                if self.is_in_floor_plan(start, end):
                    walls.append({
                        'type': 'LINE',
                        'start': start,
                        'end': end,
                        'layer': entity.dxf.layer,
                        'handle': entity.dxf.handle
                    })
        
        return walls
    
    def is_in_floor_plan(self, start: List[float], end: List[float]) -> bool:
        """
        Check if a wall segment is within any floor plan region.
        
        Args:
            start: Start coordinates [x, y]
            end: End coordinates [x, y]
            
        Returns:
            True if wall is in a floor plan region
        """
        if not self.floor_plan_regions:
            return True  # If no segmentation, include all
        
        # Check center point of wall
        center_x = (start[0] + end[0]) / 2
        center_y = (start[1] + end[1]) / 2
        
        for region in self.floor_plan_regions:
            bounds = region['bounds']
            if (bounds['min_x'] <= center_x <= bounds['max_x'] and
                bounds['min_y'] <= center_y <= bounds['max_y']):
                return True
        
        return False
    
    def snap_walls(self, walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Snap wall endpoints to create connected topology.
        
        Args:
            walls: List of wall dictionaries
            
        Returns:
            List of snapped walls
        """
        # Collect all endpoints
        endpoints = []
        for wall in walls:
            endpoints.append(tuple(wall["start"]))
            endpoints.append(tuple(wall["end"]))
        
        # Cluster nearby points
        clusters = []
        used = set()
        
        for i, point in enumerate(endpoints):
            if i in used:
                continue
            
            # Start a new cluster
            cluster = [point]
            used.add(i)
            
            # Find all points within tolerance
            for j, other_point in enumerate(endpoints):
                if j in used:
                    continue
                dist = math.sqrt((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)
                if dist <= self.snap_tolerance:
                    cluster.append(other_point)
                    used.add(j)
            
            clusters.append(cluster)
        
        # Build snap dictionary
        snap_dict = {}
        for cluster in clusters:
            # Calculate cluster center
            center_x = sum(p[0] for p in cluster) / len(cluster)
            center_y = sum(p[1] for p in cluster) / len(cluster)
            center = (center_x, center_y)
            
            for point in cluster:
                snap_dict[point] = center
        
        # Apply snapping to walls
        snapped_walls = []
        for wall in walls:
            start = tuple(wall["start"])
            end = tuple(wall["end"])
            
            snapped_start = snap_dict.get(start, start)
            snapped_end = snap_dict.get(end, end)
            
            # Skip degenerate walls
            if snapped_start == snapped_end:
                continue
            
            snapped_wall = wall.copy()
            snapped_wall["start"] = list(snapped_start)
            snapped_wall["end"] = list(snapped_end)
            snapped_walls.append(snapped_wall)
        
        return snapped_walls
    
    def detect_rooms(self, walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect enclosed rooms using wall topology.
        
        Args:
            walls: List of wall dictionaries
            
        Returns:
            List of room dictionaries
        """
        # Create LineString objects
        lines = []
        for wall in walls:
            start = tuple(wall["start"])
            end = tuple(wall["end"])
            line = LineString([start, end])
            lines.append(line)
        
        # Generate polygons
        polygons = list(polygonize(lines))
        rooms = []
        
        for i, poly in enumerate(polygons):
            # Calculate properties
            area = poly.area
            perimeter = poly.length
            centroid = poly.centroid
            
            # Get boundary coordinates
            polygon_coords = list(poly.exterior.coords)
            
            # Calculate confidence score
            if perimeter > 0:
                circularity = (4 * math.pi * area) / (perimeter * perimeter)
                confidence_score = round(circularity, 3)
            else:
                confidence_score = 0.0
            
            # Create room representation
            room = {
                'id': f'room_{i+1}',
                'polygon': polygon_coords,
                'area': round(area, 2),
                'perimeter': round(perimeter, 2),
                'centroid': [round(centroid.x, 2), round(centroid.y, 2)],
                'confidence_score': confidence_score
            }
            rooms.append(room)
        
        return rooms
    
    def generate_report(self, rooms: List[Dict[str, Any]], walls_count: int) -> Dict[str, Any]:
        """
        Generate comprehensive room report.
        
        Args:
            rooms: List of detected rooms
            walls_count: Number of walls processed
            
        Returns:
            Report dictionary
        """
        if not rooms:
            return {
                'segmentation_enabled': True,
                'floor_plan_regions': len(self.floor_plan_regions),
                'walls_processed': walls_count,
                'total_rooms': 0,
                'room_areas': [],
                'largest_room': None,
                'smallest_room': None,
                'average_area': 0.0
            }
        
        # Calculate statistics
        areas = [room['area'] for room in rooms]
        largest_room = max(rooms, key=lambda x: x['area'])
        smallest_room = min(rooms, key=lambda x: x['area'])
        average_area = sum(areas) / len(rooms)
        
        report = {
            'segmentation_enabled': True,
            'floor_plan_regions': len(self.floor_plan_regions),
            'walls_processed': walls_count,
            'total_rooms': len(rooms),
            'room_areas': areas,
            'largest_room': largest_room,
            'smallest_room': smallest_room,
            'average_area': round(average_area, 2)
        }
        
        return report
    
    def export_rooms(self, rooms: List[Dict[str, Any]]) -> None:
        """Export detected rooms to JSON file."""
        output_path = self.project_path / self.rooms_output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rooms, f, indent=2)
        print(f"Rooms exported to {output_path}")
    
    def export_report(self, report: Dict[str, Any]) -> None:
        """Export room report to JSON file."""
        output_path = self.project_path / self.report_output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Report exported to {output_path}")
    
    def run_detection(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute the complete room detection pipeline with segmentation.
        
        Returns:
            Tuple of (rooms, report)
        """
        print("Starting Room Detection with Drawing Segmentation...")
        
        # Load segmentation
        self.load_segmentation()
        
        # Extract walls from floor plan regions only
        print("Extracting walls from floor plan regions...")
        walls = self.extract_walls_from_dxf()
        print(f"Extracted {len(walls)} walls from floor plans")
        
        if len(walls) == 0:
            print("Warning: No walls found in floor plan regions")
            return [], {}
        
        # Snap walls
        print("Snapping wall endpoints...")
        snapped_walls = self.snap_walls(walls)
        print(f"Snapped walls: {len(walls)} -> {len(snapped_walls)}")
        
        # Detect rooms
        print("Detecting rooms...")
        rooms = self.detect_rooms(snapped_walls)
        print(f"Detected {len(rooms)} rooms")
        
        # Export results
        self.export_rooms(rooms)
        
        # Generate and export report
        report = self.generate_report(rooms, len(snapped_walls))
        self.export_report(report)
        
        print("Room Detection with Segmentation completed successfully")
        return rooms, report


def main():
    """Test the room detector with segmentation"""
    from config import DXF
    
    # Initialize detector
    detector = RoomDetectorWithSegmentation(str(DXF))
    
    # Run detection
    rooms, report = detector.run_detection()
    
    # Display summary
    print("\n" + "="*50)
    print("DETECTION SUMMARY")
    print("="*50)
    print(f"Floor Plan Regions: {report.get('floor_plan_regions', 0)}")
    print(f"Walls Processed: {report.get('walls_processed', 0)}")
    print(f"Rooms Detected: {report.get('total_rooms', 0)}")
    if report.get('total_rooms', 0) > 0:
        print(f"Average Room Area: {report.get('average_area', 0):.2f}")
        print(f"Largest Room: {report.get('largest_room', {}).get('area', 0):.2f}")
        print(f"Smallest Room: {report.get('smallest_room', {}).get('area', 0):.2f}")
    print("="*50)


if __name__ == "__main__":
    main()
