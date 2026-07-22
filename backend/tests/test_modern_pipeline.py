import os
import sys
import unittest
import json
import logging
from typing import Dict, Any

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.path_manager import PathManager
from backend.dxf_parser import DXFParser
from backend.geometry_engine import GeometryEngine
from backend.topology_engine import TopologyEngine
from backend.semantic_engine import SemanticEngine
from backend.space_engine import SpaceEngine
from backend.bim_core import BIMCoreEngine

class TestModernPipeline(unittest.TestCase):
    """
    Unit and integration tests for the modern KaRar pipeline:
    DXFParser -> GeometryEngine -> TopologyEngine -> SemanticEngine -> SpaceEngine -> BIMCoreEngine
    """

    @classmethod
    def setUpClass(cls):
        """Initialize workspace and test outputs path"""
        cls.path_manager = PathManager()
        cls.logger = logging.getLogger("TestModernPipeline")
        
        # We will work on a clean test outputs space
        cls.test_outputs = {
            "dxf_raw": cls.path_manager.get_path("outputs", "dxf_raw.json"),
            "walls_clean": cls.path_manager.get_path("outputs", "walls_clean.json"),
            "geometry_graph": cls.path_manager.get_path("outputs", "geometry_graph.json"),
            "bim_semantics": cls.path_manager.get_path("outputs", "bim_semantics.json"),
            "spaces": cls.path_manager.get_path("outputs", "spaces.json"),
            "bim_model": cls.path_manager.get_path("outputs", "bim_model.json"),
        }

    def test_01_geometry_engine_collinear_merge(self):
        """Test GeometryEngine collinear walls merging capabilities"""
        engine = GeometryEngine()
        
        # Define two collinear overlapping wall lines
        # Segment 1: (0, 0) to (5, 0)
        # Segment 2: (4, 0) to (10, 0)
        # They should merge into a single segment: (0, 0) to (10, 0)
        dummy_raw_payload = {
            "project": "Test Project",
            "source_file": "dummy.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 5.0, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 4.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.0, "y": 0.0, "z": 0.0}
                }
            ]
        }
        
        # Save mock raw dxf
        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)
            
        # Run GeometryEngine
        merged_walls = engine.run()
        self.assertIsNotNone(merged_walls)
        
        # Verify clean walls output file exists
        self.assertTrue(os.path.exists(self.test_outputs["walls_clean"]))
        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            clean_data = json.load(f)
            
        # The engine collinear logic should merge them or keep them grouped
        self.assertTrue(len(clean_data) > 0)

    def test_02_topology_engine_network(self):
        """Test TopologyEngine node-edge graph extraction"""
        engine = TopologyEngine()
        
        # Mock wall data representing a simple L-junction of walls:
        # Wall 1: (0, 0) to (10, 0)
        # Wall 2: (10, 0) to (10, 10)
        mock_walls = [
            {
                "wall_id": 1,
                "layer": "duvar",
                "points": [[0.0, 0.0], [10.0, 0.0]],
                "thickness": 25.0
            },
            {
                "wall_id": 2,
                "layer": "duvar",
                "points": [[10.0, 0.0], [10.0, 10.0]],
                "thickness": 25.0
            }
        ]
        
        with open(self.test_outputs["walls_clean"], "w", encoding="utf-8") as f:
            json.dump(mock_walls, f, indent=4)
            
        # Run TopologyEngine
        graph = engine.run()
        self.assertIsNotNone(graph)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        
        # It should detect nodes and edges
        self.assertTrue(len(graph["nodes"]) >= 3)
        self.assertTrue(len(graph["edges"]) >= 2)
        
        # Verify output file exists
        self.assertTrue(os.path.exists(self.test_outputs["geometry_graph"]))

    def test_03_semantic_classification(self):
        """Test SemanticEngine classification of WALLS, COLUMNS, DOORS, WINDOWS"""
        engine = SemanticEngine()
        
        # Write dummy raw dxf with secondary elements
        dummy_raw_payload = {
            "project": "Test Project",
            "source_file": "dummy.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.0, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LWPOLYLINE",
                    "layer": "kolon",
                    "closed": True,
                    "vertices": [
                        {"x": 5.0, "y": 5.0},
                        {"x": 15.0, "y": 5.0},
                        {"x": 15.0, "y": 15.0},
                        {"x": 5.0, "y": 15.0}
                    ]
                },
                {
                    "type": "LINE",
                    "layer": "kapı",
                    "block_name": "default",
                    "start": {"x": 2.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 3.0, "y": 0.0, "z": 0.0}
                }
            ]
        }
        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)
            
        # Run SemanticEngine
        semantics = engine.run()
        self.assertIsNotNone(semantics)
        self.assertIn("elements", semantics)
        
        # Classify types
        categories = [el["type"] for el in semantics["elements"]]
        self.assertIn("Wall", categories)
        self.assertIn("Column", categories)
        self.assertIn("Door", categories)
        
        # Verify output file exists
        self.assertTrue(os.path.exists(self.test_outputs["bim_semantics"]))

    def test_04_space_extraction(self):
        """Test SpaceEngine closed-loop room detection"""
        engine = SpaceEngine()
        
        # Mock geometry graph representing a closed square room:
        # Node 0 (0,0), Node 1 (10,0), Node 2 (10,10), Node 3 (0,10)
        mock_graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                {"id": 1, "x": 10.0, "y": 0.0, "degree": 2},
                {"id": 2, "x": 10.0, "y": 10.0, "degree": 2},
                {"id": 3, "x": 0.0, "y": 10.0, "degree": 2}
            ],
            "edges": [
                {"id": 1, "from": 0, "to": 1},
                {"id": 2, "from": 1, "to": 2},
                {"id": 3, "from": 2, "to": 3},
                {"id": 4, "from": 3, "to": 0}
            ],
            "loops": [
                {
                    "id": 0,
                    "area": 100.0,
                    "edges": [1, 2, 3, 4],
                    "boundary": [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}, {"x": 10.0, "y": 10.0}, {"x": 0.0, "y": 10.0}]
                }
            ]
        }
        mock_semantics = {
            "elements": [
                {"id": "w1", "type": "Wall", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 250.0},
                {"id": "w2", "type": "Wall", "points": [[10.0, 0.0], [10.0, 10.0]], "thickness": 250.0},
                {"id": "w3", "type": "Wall", "points": [[10.0, 10.0], [0.0, 10.0]], "thickness": 250.0},
                {"id": "w4", "type": "Wall", "points": [[0.0, 10.0], [0.0, 0.0]], "thickness": 250.0}
            ]
        }
        
        with open(self.test_outputs["geometry_graph"], "w", encoding="utf-8") as f:
            json.dump(mock_graph, f, indent=4)
        with open(self.test_outputs["bim_semantics"], "w", encoding="utf-8") as f:
            json.dump(mock_semantics, f, indent=4)
            
        # Run SpaceEngine
        spaces = engine.run()
        self.assertIsNotNone(spaces)
        
        # Verify output file exists
        self.assertTrue(os.path.exists(self.test_outputs["spaces"]))

    def test_05_bim_core_canonical_export(self):
        """Test BIMCoreEngine canonical BIM structure assembling"""
        engine = BIMCoreEngine()
        
        # Setup mock inputs
        mock_semantics = {
            "elements": [
                {"element_id": "wall_1", "type": "Wall", "points": [[0.0, 0.0], [10.0, 0.0]], "thickness": 250.0},
                {"element_id": "door_1", "type": "Door", "points": [[2.0, 0.0], [3.0, 0.0]], "width": 900.0}
            ]
        }
        mock_spaces = {
            "spaces": [
                {"space_id": "space_1", "name": "Salon", "area": 100.0, "polygon": [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]}
            ]
        }
        mock_graph = {
            "nodes": [{"id": 0, "x": 0.0, "y": 0.0}, {"id": 1, "x": 10.0, "y": 0.0}],
            "edges": [{"id": 1, "from": 0, "to": 1}]
        }
        
        with open(self.test_outputs["bim_semantics"], "w", encoding="utf-8") as f:
            json.dump(mock_semantics, f, indent=4)
        with open(self.test_outputs["spaces"], "w", encoding="utf-8") as f:
            json.dump(mock_spaces, f, indent=4)
        with open(self.test_outputs["geometry_graph"], "w", encoding="utf-8") as f:
            json.dump(mock_graph, f, indent=4)
            
        # Run BIMCoreEngine
        canonical_model = engine.run()
        self.assertIsNotNone(canonical_model)
        self.assertIn("walls", canonical_model)
        self.assertIn("spaces", canonical_model)
        
        # Verify output exists
        self.assertTrue(os.path.exists(self.test_outputs["bim_model"]))

if __name__ == '__main__':
    unittest.main()
