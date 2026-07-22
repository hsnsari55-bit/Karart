# Integration tests for Room Detection Engine with normalization pipeline

import unittest
import json
from pathlib import Path
from backend.room_detector_engine import RoomDetectorEngine

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = RoomDetectorEngine()
        # Sample normalized wall data with known room
        self.sample_walls = [
            {
                "id": 1,
                "type": "LINE",
                "start": [0, 0],
                "end": [10, 0]
            },
            {
                "id": 2,
                "type": "LINE",
                "start": [10, 0],
                "end": [10, 10]
            },
            {
                "id": 3,
                "type": "LINE",
                "start": [10, 10],
                "end": [0, 10]
            },
            {
                "id": 4,
                "type": "LINE",
                "start": [0, 10],
                "end": [0, 0]
            }
        ]

    def test_integration_with_normalization(self):
        # Load normalized walls
        self.engine.load_walls = lambda: self.sample_walls
        rooms = self.engine.detect_rooms()
        # Should detect 1 room with correct properties
        self.assertEqual(len(rooms), 1)
        room = rooms[0]
        self.assertEqual(room['area'], 100.0)
        self.assertEqual(room['centroid'], [5.0, 5.0])
        # Check if normalization was applied correctly
        for wall in self.sample_walls:
            self.assertTrue(all(isinstance(coord, (int, float)) for coord in wall['start'] + wall['end']))

if __name__ == "__main__":
    unittest.main()