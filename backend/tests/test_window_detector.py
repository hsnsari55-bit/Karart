import unittest
import os
import sys
import json
import tempfile
import ezdxf

# Add backend directory to path so we can import the detector
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.window_detector import (
    normalize_point,
    compute_center,
    bounding_box,
    distance_point_to_segment,
    point_in_polygon,
    process_line_entity,
    process_lwpolyline_entity,
    process_polyline_entity,
    process_arc_entity,
    match_to_wall,
    assign_room_to_window,
    WINDOW_LAYERS,
    GEOMETRY_TYPES,
    WINDOW_WIDTH_MIN,
    WINDOW_WIDTH_MAX,
)


class TestGeometryHelpers(unittest.TestCase):
    def test_normalize_point(self):
        x, y = normalize_point(18274.87 + 100, 16346.3 + 200)
        self.assertAlmostEqual(x, 100, places=2)
        self.assertAlmostEqual(y, 200, places=2)

    def test_compute_center(self):
        pts = [(0, 0), (10, 0), (10, 10), (0, 10)]
        cx, cy = compute_center(pts)
        self.assertAlmostEqual(cx, 5.0)
        self.assertAlmostEqual(cy, 5.0)

    def test_bounding_box(self):
        pts = [(0, 0), (10, 0), (10, 20)]
        min_x, min_y, max_x, max_y = bounding_box(pts)
        self.assertEqual((min_x, min_y, max_x, max_y), (0, 0, 10, 20))

    def test_distance_point_to_segment(self):
        # Point directly above midpoint of horizontal segment
        d = distance_point_to_segment((5, 5), (0, 0), (10, 0))
        self.assertAlmostEqual(d, 5.0)
        # Point at endpoint
        d2 = distance_point_to_segment((0, 0), (0, 0), (10, 0))
        self.assertAlmostEqual(d2, 0.0)

    def test_point_in_polygon(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.assertTrue(point_in_polygon((5, 5), square))
        self.assertFalse(point_in_polygon((15, 5), square))


class TestEntityProcessing(unittest.TestCase):
    def _make_line(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        return msp.add_line((0, 0), (1000, 0))

    def _make_lwpolyline(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        return msp.add_lwpolyline([(0, 0), (1000, 0), (1000, 500), (0, 500)])

    def _make_polyline(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        return msp.add_polyline2d([(0, 0), (1000, 0), (1000, 500), (0, 500)])

    def _make_arc(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        return msp.add_arc((500, 500), 500, 0, 90)

    def test_process_line(self):
        ent = self._make_line()
        data = process_line_entity(ent)
        self.assertEqual(data["entity_type"], "LINE")
        self.assertIsNotNone(data["center"])
        self.assertGreater(data["width"], 0)
        self.assertIsNone(data["height"])

    def test_process_lwpolyline(self):
        ent = self._make_lwpolyline()
        data = process_lwpolyline_entity(ent)
        self.assertEqual(data["entity_type"], "LWPOLYLINE")
        self.assertGreater(data["width"], 0)
        self.assertGreater(data["height"], 0)

    def test_process_polyline(self):
        ent = self._make_polyline()
        data = process_polyline_entity(ent)
        self.assertEqual(data["entity_type"], "POLYLINE")
        self.assertGreater(data["width"], 0)
        self.assertGreater(data["height"], 0)

    def test_process_arc(self):
        ent = self._make_arc()
        data = process_arc_entity(ent)
        self.assertEqual(data["entity_type"], "ARC")
        self.assertGreater(data["width"], 0)
        self.assertGreater(data["height"], 0)


class TestMatching(unittest.TestCase):
    def test_match_to_wall(self):
        walls = [
            {"id": 1, "type": "LINE", "start": [0, 0], "end": [100, 0]},
            {"id": 2, "type": "LINE", "start": [0, 100], "end": [100, 100]},
        ]
        wall = match_to_wall((50, 10), walls)
        self.assertIsNotNone(wall)
        self.assertEqual(wall["id"], 1)

    def test_assign_room(self):
        rooms = [
            {"id": "room_1", "polygon": [(0, 0), (100, 0), (100, 100), (0, 100)]},
        ]
        rid = assign_room_to_window((50, 50), rooms)
        self.assertEqual(rid, "room_1")
        rid_none = assign_room_to_window((500, 500), rooms)
        self.assertIsNone(rid_none)


class TestConstants(unittest.TestCase):
    def test_window_layers(self):
        self.assertIn("pencere", WINDOW_LAYERS)
        self.assertIn("cam", WINDOW_LAYERS)

    def test_geometry_types(self):
        for g in ["LINE", "LWPOLYLINE", "POLYLINE", "ARC"]:
            self.assertIn(g, GEOMETRY_TYPES)

    def test_width_range(self):
        self.assertLess(WINDOW_WIDTH_MIN, WINDOW_WIDTH_MAX)


if __name__ == "__main__":
    unittest.main()
