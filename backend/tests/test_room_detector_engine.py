import unittest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add backend directory to path so we can import the detector
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.room_detector_engine import RoomDetectorEngine, get_project_path


class TestRoomDetectorEngine(unittest.TestCase):
    """Comprehensive unit tests for Room Detection Engine"""
    
    def setUp(self):
        """Set up test fixtures with sample wall data"""
        self.sample_walls = [
            {
                "id": 1,
                "type": "LINE",
                "start": [0, 0],
                "end": [10, 0],
                "length": 10.0,
                "angle": 0.0
            },
            {
                "id": 2,
                "type": "LINE",
                "start": [10, 0],
                "end": [10, 10],
                "length": 10.0,
                "angle": 90.0
            },
            {
                "id": 3,
                "type": "LINE",
                "start": [10, 10],
                "end": [0, 10],
                "length": 10.0,
                "angle": 180.0
            },
            {
                "id": 4,
                "type": "LINE",
                "start": [0, 10],
                "end": [0, 0],
                "length": 10.0,
                "angle": 270.0
            }
        ]
        
        # Create a second room (adjacent)
        self.sample_walls.extend([
            {
                "id": 5,
                "type": "LINE",
                "start": [10, 0],
                "end": [20, 0],
                "length": 10.0,
                "angle": 0.0
            },
            {
                "id": 6,
                "type": "LINE",
                "start": [20, 0],
                "end": [20, 10],
                "length": 10.0,
                "angle": 90.0
            },
            {
                "id": 7,
                "type": "LINE",
                "start": [20, 10],
                "end": [10, 10],
                "length": 10.0,
                "angle": 180.0
            }
            # Note: wall id 2 already connects [10,0] to [10,10] and wall id 3 connects [10,10] to [0,10]
            # This creates two adjacent rooms sharing the wall [10,0]-[10,10]
        ])
        
        # Create engine instance with test data
        self.engine = RoomDetectorEngine()
    
    def test_prepare_wall_lines(self):
        """Test wall line preparation and lookup creation"""
        lines, wall_lookup = self.engine.prepare_wall_lines(self.sample_walls)
        
        # Should have 7 lines (all LINE type)
        self.assertEqual(len(lines), 7)
        
        # Check lookup contains both directions
        self.assertIn(((0, 0), (10, 0)), wall_lookup)
        self.assertIn(((10, 0), (0, 0)), wall_lookup)
        self.assertEqual(wall_lookup[((0, 0), (10, 0))], 1)
        self.assertEqual(wall_lookup[((10, 0), (0, 0))], 1)
    
    def test_detect_rooms_basic(self):
        """Test basic room detection with simple square"""
        # Use only the first 4 walls (single square room)
        single_room_walls = self.sample_walls[:4]
        lines, wall_lookup = self.engine.prepare_wall_lines(single_room_walls)
        
        # Temporarily replace load_walls method
        self.engine.load_walls = lambda: single_room_walls
        rooms = self.engine.detect_rooms()
        
        # Should detect exactly 1 room
        self.assertEqual(len(rooms), 1)
        
        room = rooms[0]
        # Check room properties
        self.assertEqual(room['id'], 'room_1')
        self.assertEqual(room['area'], 100.0)  # 10x10 square
        self.assertEqual(room['perimeter'], 40.0)  # 4 sides of 10
        self.assertEqual(room['centroid'], [5.0, 5.0])
        self.assertIn(1, room['wall_ids'])
        self.assertIn(2, room['wall_ids'])
        self.assertIn(3, room['wall_ids'])
        self.assertIn(4, room['wall_ids'])
    
    def test_detect_rooms_multiple(self):
        """Test detection of multiple adjacent rooms"""
        self.engine.load_walls = lambda: self.sample_walls
        rooms = self.engine.detect_rooms()
        
        # Should detect 2 rooms (two adjacent 10x10 squares)
        self.assertEqual(len(rooms), 2)
        
        # Both should have area 100
        for room in rooms:
            self.assertEqual(room['area'], 100.0)
    
    def test_confidence_score(self):
        """Test confidence score calculation"""
        self.engine.load_walls = lambda: self.sample_walls[:4]  # Single square
        rooms = self.engine.detect_rooms()
        
        # For a perfect square, circularity = (4*pi*100)/(40^2) = 1256.6/1600 ≈ 0.785
        expected_circularity = (4 * 3.141592653589793 * 100.0) / (40.0 * 40.0)
        self.assertAlmostEqual(rooms[0]['confidence_score'], round(expected_circularity, 3), places=2)
    
    def test_generate_report(self):
        """Test report generation"""
        self.engine.load_walls = lambda: self.sample_walls
        rooms = self.engine.detect_rooms()
        report = self.engine.generate_report(rooms)
        
        self.assertEqual(report['total_rooms'], 2)
        self.assertEqual(len(report['room_areas']), 2)
        self.assertEqual(report['average_area'], 100.0)
        self.assertIsNotNone(report['largest_room'])
        self.assertIsNotNone(report['smallest_room'])
        self.assertIn('confidence_stats', report)
    
    def test_empty_walls(self):
        """Test handling of empty wall list"""
        self.engine.load_walls = lambda: []
        rooms = self.engine.detect_rooms()
        self.assertEqual(len(rooms), 0)
        
        report = self.engine.generate_report(rooms)
        self.assertEqual(report['total_rooms'], 0)
        self.assertEqual(report['average_area'], 0.0)
    
    def test_export_rooms(self):
        """Test room export to JSON file"""
        # Create temporary directory for test output
        with tempfile.TemporaryDirectory() as tmpdir:
            test_rooms_path = os.path.join(tmpdir, "test_rooms.json")
            test_report_path = os.path.join(tmpdir, "test_report.json")
            
            # Create engine with test paths
            test_engine = RoomDetectorEngine(
                walls_input="outputs/walls_normalized.json",
                rooms_output=test_rooms_path,
                report_output=test_report_path
            )
            test_engine.load_walls = lambda: self.sample_walls
            rooms = test_engine.detect_rooms()
            test_engine.export_rooms(rooms)
            
            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(test_rooms_path))
            with open(test_rooms_path, 'r', encoding='utf-8') as f:
                exported_rooms = json.load(f)
            self.assertEqual(len(exported_rooms), 2)
    
    def test_export_report(self):
        """Test report export to JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_rooms_path = os.path.join(tmpdir, "test_rooms.json")
            test_report_path = os.path.join(tmpdir, "test_report.json")
            
            test_engine = RoomDetectorEngine(
                walls_input="outputs/walls_normalized.json",
                rooms_output=test_rooms_path,
                report_output=test_report_path
            )
            test_engine.load_walls = lambda: self.sample_walls
            rooms = test_engine.detect_rooms()
            report = test_engine.generate_report(rooms)
            test_engine.export_report(report)
            
            # Verify file was created and contains valid JSON
            self.assertTrue(os.path.exists(test_report_path))
            with open(test_report_path, 'r', encoding='utf-8') as f:
                exported_report = json.load(f)
            self.assertEqual(exported_report['total_rooms'], 2)
    
    def test_get_project_path(self):
        """Test project path resolution"""
        path = get_project_path()
        self.assertTrue(isinstance(path, Path))
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()