import os
import sys
import unittest
import json
import logging
import tempfile
import types
from typing import Dict, Any
import ezdxf

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.path_manager import PathManager
from backend.dxf_parser import DXFParser
from backend.geometry_engine import GeometryEngine
from backend.topology_engine import TopologyEngine
from backend.topology_health_report import TopologyHealthReporter
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
        """Initialize logger only; each test uses an isolated temp workspace."""
        cls.logger = logging.getLogger("TestModernPipeline")

    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir = self._temp_dir.name
        self.outputs_dir = os.path.join(self.temp_dir, "outputs")
        os.makedirs(self.outputs_dir, exist_ok=True)

        self.path_manager = types.SimpleNamespace(
            get_path=lambda *parts: os.path.join(self.temp_dir, *parts),
            get_relative_path=lambda path: path,
        )

        self.test_outputs = {
            "dxf_raw": self.path_manager.get_path("outputs", "dxf_raw.json"),
            "walls_clean": self.path_manager.get_path("outputs", "walls_clean.json"),
            "geometry_graph": self.path_manager.get_path("outputs", "geometry_graph.json"),
            "bim_semantics": self.path_manager.get_path("outputs", "bim_semantics.json"),
            "spaces": self.path_manager.get_path("outputs", "spaces.json"),
            "bim_model": self.path_manager.get_path("outputs", "bim_model.json"),
        }

    def tearDown(self):
        self._temp_dir.cleanup()

    def _bind_engine(self, engine):
        engine.path_manager = self.path_manager
        return engine

    def test_01_geometry_engine_collinear_merge(self):
        """Overlapping collinear lines should collapse into one exact wall segment."""
        engine = self._bind_engine(GeometryEngine())
        
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
            
        expected_wall = {
            "type": "LWPOLYLINE",
            "layer": "duvar",
            "block_name": "default",
            "closed": False,
            "points": [[0.0, 0.0], [10.0, 0.0]],
        }

        # Run GeometryEngine
        merged_walls = engine.run()
        self.assertEqual(merged_walls, [expected_wall])
        self.assertEqual(len(merged_walls), 1)
        
        # Verify clean walls output file exists and persisted contract matches memory output
        self.assertTrue(os.path.exists(self.test_outputs["walls_clean"]))
        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            clean_data = json.load(f)

        self.assertEqual(clean_data, [expected_wall])
        self.assertEqual(clean_data, merged_walls)

    def test_01a_geometry_engine_removes_duplicate_segments(self):
        """Identical and reversed duplicate wall segments should collapse to one exact output segment."""
        engine = self._bind_engine(GeometryEngine())

        dummy_raw_payload = {
            "project": "Duplicate Segment Fixture",
            "source_file": "duplicate_segments.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 1.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.0, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.0, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 10.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 0.0, "y": 0.0, "z": 0.0}
                }
            ]
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        expected_wall = {
            "type": "LWPOLYLINE",
            "layer": "duvar",
            "block_name": "default",
            "closed": False,
            "points": [[0.0, 0.0], [10.0, 0.0]],
        }

        clean_walls = engine.run()

        self.assertEqual(clean_walls, [expected_wall])
        self.assertEqual(len(clean_walls), 1)

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(persisted_clean_walls, [expected_wall])
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["total_segments_out"], 1)

    def test_01b_geometry_engine_removes_zero_length_and_below_min_length_segments(self):
        """Zero-length and below-min-length wall inputs should be dropped, preserving only valid exact segments."""
        engine = self._bind_engine(GeometryEngine())

        original_get = engine.config.get
        engine.config = types.SimpleNamespace(
            get=lambda key, default=None: (
                0.1 if key == "tolerances.snapping_distance_mm" else original_get(key, default)
            ),
            get_layer_mapping=engine.config.get_layer_mapping,
        )
        engine.snap_tolerance = 0.1

        dummy_raw_payload = {
            "project": "Zero Length Cleanup Fixture",
            "source_file": "zero_length_cleanup.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 30.0, "max_y": 1.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 0.0, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 10.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.5, "y": 0.0, "z": 0.0}
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 20.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 30.0, "y": 0.0, "z": 0.0}
                }
            ]
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        expected_wall = {
            "type": "LWPOLYLINE",
            "layer": "duvar",
            "block_name": "default",
            "closed": False,
            "points": [[20.0, 0.0], [30.0, 0.0]],
        }

        clean_walls = engine.run()

        self.assertEqual(clean_walls, [expected_wall])
        self.assertEqual(len(clean_walls), 1)

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(persisted_clean_walls, [expected_wall])
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["zero_length_removed"], 2)
        self.assertEqual(engine.stats["total_segments_out"], 1)

    def test_01c_geometry_engine_segments_open_polyline_into_exact_walls(self):
        """Open wall polylines should segment into the exact expected ordered wall edges."""
        engine = self._bind_engine(GeometryEngine())

        dummy_raw_payload = {
            "project": "Open Polyline Segmentation Fixture",
            "source_file": "open_polyline_segmentation.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "closed": False,
                    "vertices": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 5.0, "y": 0.0},
                        {"x": 5.0, "y": 5.0},
                    ],
                }
            ]
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [5.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[5.0, 0.0], [5.0, 5.0]],
            },
        ]

        clean_walls = engine.run()

        self.assertEqual(clean_walls, expected_walls)
        self.assertEqual(len(clean_walls), 2)

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(persisted_clean_walls, expected_walls)
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["total_segments_out"], 2)

    def test_01d_geometry_engine_segments_closed_polyline_into_exact_walls(self):
        """Closed wall polylines should segment into the exact expected ordered wall edges including closure."""
        engine = self._bind_engine(GeometryEngine())

        dummy_raw_payload = {
            "project": "Closed Polyline Segmentation Fixture",
            "source_file": "closed_polyline_segmentation.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "closed": True,
                    "vertices": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 10.0, "y": 0.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 0.0, "y": 10.0},
                    ],
                }
            ]
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 10.0], [0.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [10.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[10.0, 10.0], [0.0, 10.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[10.0, 0.0], [10.0, 10.0]],
            },
        ]

        clean_walls = engine.run()

        self.assertEqual(clean_walls, expected_walls)
        self.assertEqual(len(clean_walls), 4)

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(persisted_clean_walls, expected_walls)
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["total_segments_out"], 4)

    def test_01e_geometry_engine_snapping_is_deterministic_across_entity_permutations(self):
        """Near-coincident wall endpoints should snap to the same observable geometry regardless of entity order."""

        def run_geometry_once(entities):
            engine = self._bind_engine(GeometryEngine())
            original_get = engine.config.get
            engine.config = types.SimpleNamespace(
                get=lambda key, default=None: (
                    0.1 if key == "tolerances.snapping_distance_mm" else original_get(key, default)
                ),
                get_layer_mapping=engine.config.get_layer_mapping,
            )
            engine.snap_tolerance = 0.1

            raw_payload = {
                "project": "Snapping Determinism Fixture",
                "source_file": "snapping_determinism.dxf",
                "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.04, "max_y": 5.0},
                "entities": entities,
            }

            with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
                json.dump(raw_payload, f, indent=4)

            clean_walls = engine.run()

            with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
                persisted_clean_walls = json.load(f)

            return {
                "clean_walls": clean_walls,
                "persisted_clean_walls": persisted_clean_walls,
                "points_snapped_count": engine.stats["points_snapped_count"],
                "avg_snap_distance_mm": engine.stats["avg_snap_distance_mm"],
                "max_snap_distance_mm": engine.stats["max_snap_distance_mm"],
                "total_segments_out": engine.stats["total_segments_out"],
                "geometry_sha256": engine.stats["geometry_sha256"],
            }

        left = {
            "type": "LINE",
            "layer": "duvar",
            "block_name": "default",
            "start": {"x": 0.0, "y": 0.0, "z": 0.0},
            "end": {"x": 10.0, "y": 0.0, "z": 0.0},
        }
        right = {
            "type": "LINE",
            "layer": "duvar",
            "block_name": "default",
            "start": {"x": 10.04, "y": 0.0, "z": 0.0},
            "end": {"x": 10.04, "y": 5.0, "z": 0.0},
        }

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [10.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[10.0, 0.0], [10.04, 5.0]],
            },
        ]

        first_run = run_geometry_once([left, right])
        second_run = run_geometry_once([right, left])

        for run in (first_run, second_run):
            self.assertEqual(run["clean_walls"], expected_walls)
            self.assertEqual(run["persisted_clean_walls"], expected_walls)
            self.assertEqual(run["persisted_clean_walls"], run["clean_walls"])
            self.assertEqual(run["points_snapped_count"], 1)
            self.assertAlmostEqual(run["avg_snap_distance_mm"], 0.04, places=6)
            self.assertAlmostEqual(run["max_snap_distance_mm"], 0.04, places=6)
            self.assertEqual(run["total_segments_out"], 2)
            self.assertEqual(
                run["geometry_sha256"],
                "6244f2878c6cd39d4b7d9a37b2e9e23ec838d27d68d0da3db898197999c98b45",
            )

        self.assertEqual(first_run["clean_walls"], second_run["clean_walls"])
        self.assertEqual(first_run["persisted_clean_walls"], second_run["persisted_clean_walls"])
        self.assertEqual(first_run["geometry_sha256"], second_run["geometry_sha256"])

    def test_01eaa_geometry_engine_does_not_snap_when_distance_equals_tolerance(self):
        """Binary-exact equality to snap tolerance should not snap because the contract is strict `<`."""
        engine = self._bind_engine(GeometryEngine())
        original_get = engine.config.get
        engine.config = types.SimpleNamespace(
            get=lambda key, default=None: (
                0.125 if key == "tolerances.snapping_distance_mm" else original_get(key, default)
            ),
            get_layer_mapping=engine.config.get_layer_mapping,
        )
        engine.snap_tolerance = 0.125

        raw_payload = {
            "project": "Snap Equality Boundary Fixture",
            "source_file": "snap_equality_boundary.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 1.125, "max_y": 1.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 1.0, "y": 0.0, "z": 0.0},
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 1.125, "y": 0.0, "z": 0.0},
                    "end": {"x": 1.125, "y": 1.0, "z": 0.0},
                },
            ],
        }

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [1.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[1.125, 0.0], [1.125, 1.0]],
            },
        ]

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(raw_payload, f, indent=4)

        clean_walls = engine.run()

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(clean_walls, expected_walls)
        self.assertEqual(persisted_clean_walls, expected_walls)
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["points_snapped_count"], 0)
        self.assertEqual(engine.stats["avg_snap_distance_mm"], 0.0)
        self.assertEqual(engine.stats["max_snap_distance_mm"], 0.0)
        self.assertEqual(engine.stats["overlapping_merged"], 0)
        self.assertEqual(engine.stats["total_segments_out"], 2)
        self.assertEqual(
            engine.stats["geometry_sha256"],
            "1054cf5e9000551a3b3de83961bfd430e5eb7f249919d6026e71db847a67e831",
        )

    def test_01ea_geometry_engine_reuse_resets_stats_between_runs(self):
        """Reusing the same GeometryEngine instance should not accumulate QA stats across identical runs."""
        engine = self._bind_engine(GeometryEngine())
        original_get = engine.config.get
        engine.config = types.SimpleNamespace(
            get=lambda key, default=None: (
                0.1 if key == "tolerances.snapping_distance_mm" else original_get(key, default)
            ),
            get_layer_mapping=engine.config.get_layer_mapping,
        )
        engine.snap_tolerance = 0.1

        raw_payload = {
            "project": "Snapping Reuse Fixture",
            "source_file": "snapping_reuse_fixture.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.04, "max_y": 5.0},
            "entities": [
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.0, "y": 0.0, "z": 0.0},
                },
                {
                    "type": "LINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "start": {"x": 10.04, "y": 0.0, "z": 0.0},
                    "end": {"x": 10.04, "y": 5.0, "z": 0.0},
                },
            ],
        }

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [10.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[10.0, 0.0], [10.04, 5.0]],
            },
        ]

        expected_stats = {
            "initial_entities": 2,
            "zero_length_removed": 0,
            "points_snapped_count": 1,
            "avg_snap_distance_mm": 0.04,
            "max_snap_distance_mm": 0.04,
            "overlapping_merged": 0,
            "total_segments_out": 2,
            "geometry_sha256": "6244f2878c6cd39d4b7d9a37b2e9e23ec838d27d68d0da3db898197999c98b45",
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(raw_payload, f, indent=4)

        first_clean_walls = engine.run()

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            first_persisted_clean_walls = json.load(f)

        first_stats = {key: engine.stats[key] for key in expected_stats}

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(raw_payload, f, indent=4)

        second_clean_walls = engine.run()

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            second_persisted_clean_walls = json.load(f)

        second_stats = {key: engine.stats[key] for key in expected_stats}

        self.assertEqual(first_clean_walls, expected_walls)
        self.assertEqual(first_persisted_clean_walls, expected_walls)
        self.assertEqual(first_persisted_clean_walls, first_clean_walls)
        self.assertEqual(first_stats, expected_stats)

        self.assertEqual(second_clean_walls, expected_walls)
        self.assertEqual(second_persisted_clean_walls, expected_walls)
        self.assertEqual(second_persisted_clean_walls, second_clean_walls)
        self.assertEqual(second_stats, expected_stats)

        self.assertEqual(first_clean_walls, second_clean_walls)
        self.assertEqual(first_persisted_clean_walls, second_persisted_clean_walls)
        self.assertEqual(first_stats, second_stats)

    def test_01f_geometry_engine_repairs_self_intersecting_closed_polygon_into_deterministic_segments(self):
        """Self-intersecting closed wall polylines should repair into the exact observed deterministic segment set."""
        engine = self._bind_engine(GeometryEngine())

        dummy_raw_payload = {
            "project": "Polygon Repair Fixture",
            "source_file": "polygon_repair.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "closed": True,
                    "vertices": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 0.0, "y": 10.0},
                        {"x": 10.0, "y": 0.0},
                    ],
                }
            ],
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        expected_walls = [
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 0.0], [10.0, 10.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[0.0, 10.0], [10.0, 0.0]],
            },
            {
                "type": "LWPOLYLINE",
                "layer": "duvar",
                "block_name": "default",
                "closed": False,
                "points": [[10.0, 10.0], [0.0, 10.0]],
            },
        ]

        clean_walls = engine.run()

        self.assertEqual(clean_walls, expected_walls)
        self.assertEqual(len(clean_walls), 3)

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(persisted_clean_walls, expected_walls)
        self.assertEqual(persisted_clean_walls, clean_walls)
        self.assertEqual(engine.stats["self_intersections_repaired"], 2)
        self.assertEqual(engine.stats["slivers_filtered"], 2)
        self.assertEqual(engine.stats["invalid_polygons_dropped"], 0)
        self.assertEqual(engine.stats["total_segments_out"], 3)
        self.assertEqual(
            engine.stats["geometry_sha256"],
            "c6c89eec7b0d50320c08b5266c7104b0cd340770f6e4363fc993d9b8307958b5",
        )

    def test_02_topology_engine_network(self):
        """Test TopologyEngine node-edge graph extraction"""
        engine = self._bind_engine(TopologyEngine())
        
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

    def test_02b_closed_wall_polyline_drives_healthy_geometry_topology_health_chain(self):
        """Closed wall polyline should produce a healthy loop across Geometry -> Topology -> Health."""
        geometry_engine = self._bind_engine(GeometryEngine())
        topology_engine = self._bind_engine(TopologyEngine())

        dummy_raw_payload = {
            "project": "Closed Loop Fixture",
            "source_file": "closed_loop_fixture.dxf",
            "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 10.0},
            "entities": [
                {
                    "type": "LWPOLYLINE",
                    "layer": "duvar",
                    "block_name": "default",
                    "closed": True,
                    "vertices": [
                        {"x": 0.0, "y": 0.0},
                        {"x": 10.0, "y": 0.0},
                        {"x": 10.0, "y": 10.0},
                        {"x": 0.0, "y": 10.0}
                    ]
                }
            ]
        }

        with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
            json.dump(dummy_raw_payload, f, indent=4)

        clean_walls = geometry_engine.run()

        self.assertEqual(len(clean_walls), 4)
        self.assertTrue(os.path.exists(self.test_outputs["walls_clean"]))

        with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
            persisted_clean_walls = json.load(f)

        self.assertEqual(len(persisted_clean_walls), 4)

        graph = topology_engine.run()

        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(len(graph["edges"]), 4)
        self.assertEqual(len(graph["loops"]), 1)

        reporter = TopologyHealthReporter(
            report_output_path=self.path_manager.get_path("outputs", "topology_health_report.json")
        )
        report = reporter.generate(graph)

        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["counts"], {"nodes": 4, "edges": 4, "loops": 1})
        self.assertEqual(report["diagnostics"], [])
        self.assertTrue(report["checks"]["has_loops"])
        self.assertTrue(report["checks"]["closed_loops"])
        self.assertTrue(report["checks"]["no_dangling_nodes"])
        self.assertTrue(report["checks"]["degree_metadata_consistency"])

    def test_02ba_polyline_vertices_contract_keeps_geometry_output_deterministic_across_entity_permutations(self):
        """Equivalent LWPOLYLINE vertex payload permutations should keep Geometry output identical."""

        def run_geometry_once(entities):
            geometry_engine = self._bind_engine(GeometryEngine())
            raw_payload = {
                "project": "Polyline Contract Fixture",
                "source_file": "polyline_contract_fixture.dxf",
                "bounding_box": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 1.0},
                "entities": entities,
            }

            with open(self.test_outputs["dxf_raw"], "w", encoding="utf-8") as f:
                json.dump(raw_payload, f, indent=4)

            clean_walls = geometry_engine.run()

            with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
                persisted_clean_walls = json.load(f)

            return {
                "clean_walls": clean_walls,
                "persisted_clean_walls": persisted_clean_walls,
                "geometry_sha256": geometry_engine.stats["geometry_sha256"],
            }

        left_to_right = {
            "type": "LWPOLYLINE",
            "layer": "duvar",
            "block_name": "default",
            "closed": False,
            "vertices": [
                {"x": 0.0, "y": 0.0},
                {"x": 5.0, "y": 0.0},
            ],
        }
        right_to_left = {
            "type": "LWPOLYLINE",
            "layer": "duvar",
            "block_name": "default",
            "closed": False,
            "vertices": [
                {"x": 10.0, "y": 0.0},
                {"x": 5.0, "y": 0.0},
            ],
        }

        first_run = run_geometry_once([left_to_right, right_to_left])
        second_run = run_geometry_once([right_to_left, left_to_right])

        self.assertEqual(len(first_run["clean_walls"]), 1)
        self.assertEqual(len(second_run["clean_walls"]), 1)
        self.assertEqual(first_run["clean_walls"], second_run["clean_walls"])
        self.assertEqual(first_run["persisted_clean_walls"], second_run["persisted_clean_walls"])
        self.assertEqual(
            first_run["clean_walls"][0]["points"],
            second_run["clean_walls"][0]["points"],
        )
        self.assertEqual(first_run["geometry_sha256"], second_run["geometry_sha256"])

    def test_02c_parser_backed_closed_loop_dxf_drives_healthy_geometry_topology_health_chain(self):
        """Real DXF parse output should preserve a closed wall loop through Geometry -> Topology -> Health."""
        fixtures_dir = os.path.join(self.temp_dir, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        fixture_name = "closed_loop_fixture.dxf"
        fixture_path = os.path.join(fixtures_dir, fixture_name)

        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 4  # millimeters
        msp = doc.modelspace()
        msp.add_lwpolyline(
            [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
            close=True,
            dxfattribs={"layer": "duvar"},
        )
        doc.saveas(fixture_path)

        parser = DXFParser()
        parser.path_manager = types.SimpleNamespace(
            workspace_root=self.temp_dir,
            get_path=self.path_manager.get_path,
            get_relative_path=self.path_manager.get_relative_path,
        )
        geometry_engine = self._bind_engine(GeometryEngine())
        topology_engine = self._bind_engine(TopologyEngine())

        raw_payload = parser.parse(os.path.join("fixtures", fixture_name))

        self.assertEqual(raw_payload["source_file"], os.path.join("fixtures", fixture_name))
        self.assertEqual(len(raw_payload["entities"]), 1)
        self.assertEqual(raw_payload["entities"][0]["type"], "LWPOLYLINE")
        self.assertTrue(raw_payload["entities"][0]["closed"])
        self.assertTrue(os.path.exists(self.test_outputs["dxf_raw"]))

        clean_walls = geometry_engine.run()

        self.assertEqual(len(clean_walls), 4)
        self.assertTrue(os.path.exists(self.test_outputs["walls_clean"]))

        graph = topology_engine.run()

        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(len(graph["edges"]), 4)
        self.assertEqual(len(graph["loops"]), 1)

        reporter = TopologyHealthReporter(
            report_output_path=self.path_manager.get_path("outputs", "topology_health_report.json")
        )
        report = reporter.generate(graph)

        self.assertEqual(report["status"], "HEALTHY")
        self.assertEqual(report["counts"], {"nodes": 4, "edges": 4, "loops": 1})
        self.assertEqual(report["diagnostics"], [])
        self.assertTrue(report["checks"]["has_loops"])
        self.assertTrue(report["checks"]["all_loops_closed"])
        self.assertTrue(report["checks"]["closed_loops"])
        self.assertTrue(report["checks"]["no_dangling_nodes"])

    def test_02d_parser_reuse_keeps_closed_loop_pipeline_outputs_deterministic(self):
        """Reusing the same parser instance should keep raw/geometry/topology/health outputs stable."""
        fixtures_dir = os.path.join(self.temp_dir, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        fixture_name = "closed_loop_fixture_reuse.dxf"
        fixture_path = os.path.join(fixtures_dir, fixture_name)

        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 4  # millimeters
        msp = doc.modelspace()
        msp.add_lwpolyline(
            [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
            close=True,
            dxfattribs={"layer": "duvar"},
        )
        doc.saveas(fixture_path)

        parser = DXFParser()
        parser.path_manager = types.SimpleNamespace(
            workspace_root=self.temp_dir,
            get_path=self.path_manager.get_path,
            get_relative_path=self.path_manager.get_relative_path,
        )

        def run_pipeline_once():
            geometry_engine = self._bind_engine(GeometryEngine())
            topology_engine = self._bind_engine(TopologyEngine())

            raw_payload = parser.parse(os.path.join("fixtures", fixture_name))
            with open(self.test_outputs["dxf_raw"], "r", encoding="utf-8") as f:
                persisted_raw = json.load(f)

            clean_walls = geometry_engine.run()
            with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
                persisted_clean_walls = json.load(f)

            graph = topology_engine.run()
            with open(self.test_outputs["geometry_graph"], "r", encoding="utf-8") as f:
                persisted_graph = json.load(f)

            reporter = TopologyHealthReporter(
                report_output_path=self.path_manager.get_path("outputs", "topology_health_report.json")
            )
            report = reporter.generate(graph)

            return {
                "raw_payload": raw_payload,
                "persisted_raw": persisted_raw,
                "clean_walls": clean_walls,
                "persisted_clean_walls": persisted_clean_walls,
                "graph": graph,
                "persisted_graph": persisted_graph,
                "report": report,
            }

        first_run = run_pipeline_once()
        second_run = run_pipeline_once()

        for run in (first_run, second_run):
            self.assertEqual(run["raw_payload"]["source_file"], os.path.join("fixtures", fixture_name))
            self.assertEqual(run["raw_payload"]["bounding_box"], {
                "min_x": 0.0,
                "min_y": 0.0,
                "max_x": 4000.0,
                "max_y": 3000.0,
            })
            self.assertEqual(len(run["raw_payload"]["entities"]), 1)
            self.assertEqual(run["raw_payload"]["entities"][0]["type"], "LWPOLYLINE")
            self.assertTrue(run["raw_payload"]["entities"][0]["closed"])
            self.assertEqual(run["raw_payload"].get("promoted_block"), None)
            self.assertEqual(run["raw_payload"].get("promotion_reason"), None)
            self.assertEqual(len(run["clean_walls"]), 4)
            self.assertEqual(len(run["graph"]["nodes"]), 4)
            self.assertEqual(len(run["graph"]["edges"]), 4)
            self.assertEqual(len(run["graph"]["loops"]), 1)
            self.assertEqual(run["report"]["status"], "HEALTHY")
            self.assertEqual(run["report"]["counts"], {"nodes": 4, "edges": 4, "loops": 1})
            self.assertEqual(run["report"]["diagnostics"], [])
            self.assertTrue(run["report"]["checks"]["has_loops"])
            self.assertTrue(run["report"]["checks"]["all_loops_closed"])
            self.assertTrue(run["report"]["checks"]["closed_loops"])
            self.assertTrue(run["report"]["checks"]["no_dangling_nodes"])

        self.assertEqual(first_run["raw_payload"], second_run["raw_payload"])
        self.assertEqual(first_run["persisted_raw"], second_run["persisted_raw"])
        self.assertEqual(first_run["clean_walls"], second_run["clean_walls"])
        self.assertEqual(first_run["persisted_clean_walls"], second_run["persisted_clean_walls"])
        self.assertEqual(first_run["graph"], second_run["graph"])
        self.assertEqual(first_run["persisted_graph"], second_run["persisted_graph"])
        first_report = {key: value for key, value in first_run["report"].items() if key != "timestamp"}
        second_report = {key: value for key, value in second_run["report"].items() if key != "timestamp"}
        self.assertEqual(first_report, second_report)

    def test_02e_parser_reuse_keeps_truncated_recover_pipeline_outputs_deterministic(self):
        """Reusing the same parser instance should keep truncated-DXF recover outputs stable through Topology health."""
        fixtures_dir = os.path.join(self.temp_dir, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        fixture_name = "truncated_recoverable_fixture_reuse.dxf"
        fixture_path = os.path.join(fixtures_dir, fixture_name)

        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 4  # millimeters
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "Walls"})
        doc.saveas(fixture_path)

        with open(fixture_path, "r", encoding="latin-1") as f:
            content = f.read()

        with open(fixture_path, "w", encoding="latin-1") as f:
            f.write(content[:-40])

        parser = DXFParser()
        parser.path_manager = types.SimpleNamespace(
            workspace_root=self.temp_dir,
            get_path=self.path_manager.get_path,
            get_relative_path=self.path_manager.get_relative_path,
        )

        def run_pipeline_once():
            geometry_engine = self._bind_engine(GeometryEngine())
            topology_engine = self._bind_engine(TopologyEngine())

            raw_payload = parser.parse(os.path.join("fixtures", fixture_name))
            with open(self.test_outputs["dxf_raw"], "r", encoding="utf-8") as f:
                persisted_raw = json.load(f)

            clean_walls = geometry_engine.run()
            with open(self.test_outputs["walls_clean"], "r", encoding="utf-8") as f:
                persisted_clean_walls = json.load(f)

            graph = topology_engine.run()
            with open(self.test_outputs["geometry_graph"], "r", encoding="utf-8") as f:
                persisted_graph = json.load(f)

            reporter = TopologyHealthReporter(
                report_output_path=self.path_manager.get_path("outputs", "topology_health_report.json")
            )
            report = reporter.generate(graph)

            return {
                "raw_payload": raw_payload,
                "persisted_raw": persisted_raw,
                "clean_walls": clean_walls,
                "persisted_clean_walls": persisted_clean_walls,
                "graph": graph,
                "persisted_graph": persisted_graph,
                "report": report,
            }

        first_run = run_pipeline_once()
        second_run = run_pipeline_once()

        for run in (first_run, second_run):
            self.assertEqual(run["raw_payload"]["source_file"], os.path.join("fixtures", fixture_name))
            self.assertEqual(run["raw_payload"]["bounding_box"], {
                "min_x": 0.0,
                "min_y": 0.0,
                "max_x": 100.0,
                "max_y": 0.0,
            })
            self.assertEqual(run["raw_payload"]["metadata"]["promoted_block"], None)
            self.assertEqual(run["raw_payload"]["metadata"]["promotion_reason"], None)
            self.assertEqual(run["raw_payload"]["metadata"]["skipped_entities"], 0)
            self.assertEqual(len(run["raw_payload"]["entities"]), 1)
            self.assertEqual(run["raw_payload"]["entities"][0]["type"], "LINE")
            self.assertEqual(len(run["clean_walls"]), 1)
            self.assertEqual(len(run["graph"]["nodes"]), 2)
            self.assertEqual(len(run["graph"]["edges"]), 1)
            self.assertEqual(len(run["graph"]["loops"]), 0)
            self.assertEqual(run["report"]["status"], "WARNING")
            self.assertEqual(run["report"]["counts"], {"nodes": 2, "edges": 1, "loops": 0})
            self.assertFalse(run["report"]["checks"]["has_loops"])
            self.assertFalse(run["report"]["checks"]["no_dangling_nodes"])
            self.assertTrue(run["report"]["checks"]["all_loops_closed"])
            self.assertTrue(run["report"]["checks"]["closed_loops"])

        self.assertEqual(first_run["raw_payload"], second_run["raw_payload"])
        self.assertEqual(first_run["persisted_raw"], second_run["persisted_raw"])
        self.assertEqual(first_run["clean_walls"], second_run["clean_walls"])
        self.assertEqual(first_run["persisted_clean_walls"], second_run["persisted_clean_walls"])
        self.assertEqual(first_run["graph"], second_run["graph"])
        self.assertEqual(first_run["persisted_graph"], second_run["persisted_graph"])
        first_report = {key: value for key, value in first_run["report"].items() if key != "timestamp"}
        second_report = {key: value for key, value in second_run["report"].items() if key != "timestamp"}
        self.assertEqual(first_report, second_report)

    def test_02f_parser_reuse_keeps_semantic_space_bim_outputs_deterministic(self):
        """Reusing the same parser instance should keep Semantic -> Space -> BIM Core outputs stable."""
        fixtures_dir = os.path.join(self.temp_dir, "fixtures")
        os.makedirs(fixtures_dir, exist_ok=True)
        fixture_name = "closed_loop_semantic_space_bim_fixture.dxf"
        fixture_path = os.path.join(fixtures_dir, fixture_name)

        doc = ezdxf.new(dxfversion="R2010")
        doc.header["$INSUNITS"] = 4  # millimeters
        msp = doc.modelspace()
        msp.add_lwpolyline(
            [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
            close=True,
            dxfattribs={"layer": "duvar"},
        )
        msp.add_line((2000, 0), (2000, 120), dxfattribs={"layer": "kapı"})
        doc.saveas(fixture_path)

        parser = DXFParser()
        parser.path_manager = types.SimpleNamespace(
            workspace_root=self.temp_dir,
            get_path=self.path_manager.get_path,
            get_relative_path=self.path_manager.get_relative_path,
        )

        def normalize_semantics(payload):
            normalized = json.loads(json.dumps(payload))
            normalized.setdefault("stats", {})["processing_time_ms"] = 0
            normalized["elements"].sort(key=lambda el: (el.get("type", ""), el.get("uuid", "")))
            return normalized

        def normalize_spaces(payload):
            normalized = json.loads(json.dumps(payload))
            normalized.setdefault("stats", {})["processing_time_ms"] = 0
            normalized["spaces"].sort(key=lambda sp: sp.get("uuid", ""))
            for sp in normalized["spaces"]:
                sp["bounded_by_walls"] = sorted(sp.get("bounded_by_walls", []))
            return normalized

        def normalize_canonical_model(payload):
            normalized = json.loads(json.dumps(payload))
            provenance = normalized.setdefault("provenance", {})
            provenance["generated_at"] = "<normalized>"
            provenance["canonical_bim_sha256"] = "<normalized>"
            input_hashes = provenance.setdefault("input_hashes", {})
            input_hashes["bim_semantics_sha256"] = "<normalized>"
            input_hashes["spaces_sha256"] = "<normalized>"
            input_hashes["geometry_graph_sha256"] = "<normalized>"

            for collection in ("spaces", "walls", "windows", "columns", "doors"):
                normalized[collection].sort(key=lambda el: el.get("uuid", ""))

            for sp in normalized["spaces"]:
                sp["related_walls"] = sorted(sp.get("related_walls", []))
                sp["related_windows"] = sorted(sp.get("related_windows", []))
                sp["related_columns"] = sorted(sp.get("related_columns", []))
                sp["related_doors"] = sorted(sp.get("related_doors", []))
                sp["neighbors"] = sorted(sp.get("neighbors", []))

            for wall in normalized["walls"]:
                if "related_spaces" in wall:
                    wall["related_spaces"] = sorted(wall["related_spaces"])

            for column in normalized["columns"]:
                if "parent_spaces" in column:
                    column["parent_spaces"] = sorted(column["parent_spaces"])

            return normalized

        def run_pipeline_once():
            geometry_engine = self._bind_engine(GeometryEngine())
            topology_engine = self._bind_engine(TopologyEngine())
            semantic_engine = self._bind_engine(SemanticEngine())
            space_engine = self._bind_engine(SpaceEngine())
            bim_core_engine = self._bind_engine(BIMCoreEngine())

            raw_payload = parser.parse(os.path.join("fixtures", fixture_name))
            clean_walls = geometry_engine.run()
            graph = topology_engine.run()

            semantics = semantic_engine.run()
            with open(self.test_outputs["bim_semantics"], "r", encoding="utf-8") as f:
                persisted_semantics = json.load(f)

            spaces = space_engine.run()
            with open(self.test_outputs["spaces"], "r", encoding="utf-8") as f:
                persisted_spaces = json.load(f)

            canonical_model = bim_core_engine.run()
            with open(self.test_outputs["bim_model"], "r", encoding="utf-8") as f:
                persisted_bim_model = json.load(f)

            return {
                "raw_payload": raw_payload,
                "clean_walls": clean_walls,
                "graph": graph,
                "semantics": semantics,
                "persisted_semantics": persisted_semantics,
                "spaces": spaces,
                "persisted_spaces": persisted_spaces,
                "canonical_model": canonical_model,
                "persisted_bim_model": persisted_bim_model,
            }

        first_run = run_pipeline_once()
        second_run = run_pipeline_once()

        for run in (first_run, second_run):
            semantic_types = [el["type"] for el in run["semantics"]["elements"]]

            self.assertEqual(run["raw_payload"]["source_file"], os.path.join("fixtures", fixture_name))
            self.assertEqual(len(run["clean_walls"]), 4)
            self.assertEqual(len(run["graph"]["nodes"]), 4)
            self.assertEqual(len(run["graph"]["edges"]), 4)
            self.assertEqual(len(run["graph"]["loops"]), 1)
            self.assertEqual(semantic_types.count("Wall"), 4)
            self.assertIn("Space", semantic_types)
            self.assertIn("Door", semantic_types)
            self.assertEqual(len(run["spaces"]["spaces"]), 1)
            self.assertEqual(len(run["spaces"]["spaces"][0]["bounded_by_walls"]), 4)
            self.assertEqual(len(run["canonical_model"]["spaces"]), 1)
            self.assertEqual(len(run["canonical_model"]["walls"]), 4)
            self.assertEqual(len(run["canonical_model"]["doors"]), 1)
            self.assertEqual(
                sorted(run["canonical_model"]["spaces"][0]["related_walls"]),
                sorted(run["spaces"]["spaces"][0]["bounded_by_walls"]),
            )
            self.assertEqual(
                sorted(run["persisted_bim_model"]["spaces"][0]["related_walls"]),
                sorted(run["persisted_spaces"]["spaces"][0]["bounded_by_walls"]),
            )

            door = run["canonical_model"]["doors"][0]
            self.assertIsNotNone(door.get("parent_wall"))

            self.assertEqual(
                normalize_semantics(run["semantics"]),
                normalize_semantics(run["persisted_semantics"]),
            )
            self.assertEqual(
                normalize_spaces(run["spaces"]),
                normalize_spaces(run["persisted_spaces"]),
            )
            self.assertEqual(
                normalize_canonical_model(run["canonical_model"]),
                normalize_canonical_model(run["persisted_bim_model"]),
            )

        self.assertEqual(
            normalize_semantics(first_run["semantics"]),
            normalize_semantics(second_run["semantics"]),
        )
        self.assertEqual(
            normalize_semantics(first_run["persisted_semantics"]),
            normalize_semantics(second_run["persisted_semantics"]),
        )
        self.assertEqual(
            normalize_spaces(first_run["spaces"]),
            normalize_spaces(second_run["spaces"]),
        )
        self.assertEqual(
            normalize_spaces(first_run["persisted_spaces"]),
            normalize_spaces(second_run["persisted_spaces"]),
        )
        self.assertEqual(
            normalize_canonical_model(first_run["canonical_model"]),
            normalize_canonical_model(second_run["canonical_model"]),
        )
        self.assertEqual(
            normalize_canonical_model(first_run["persisted_bim_model"]),
            normalize_canonical_model(second_run["persisted_bim_model"]),
        )

    def test_03_semantic_classification(self):
        """Test SemanticEngine classification of WALLS, COLUMNS, DOORS, WINDOWS"""
        engine = self._bind_engine(SemanticEngine())

        mock_graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0},
                {"id": 1, "x": 10.0, "y": 0.0}
            ],
            "edges": [
                {"id": 1, "from": 0, "to": 1}
            ],
            "loops": [
                {
                    "id": 10,
                    "area": 100.0,
                    "edges": [],
                    "boundary": [
                        {"x": 5.0, "y": 5.0},
                        {"x": 15.0, "y": 5.0},
                        {"x": 15.0, "y": 15.0},
                        {"x": 5.0, "y": 15.0}
                    ]
                }
            ]
        }
        
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
        with open(self.test_outputs["geometry_graph"], "w", encoding="utf-8") as f:
            json.dump(mock_graph, f, indent=4)
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
        engine = self._bind_engine(SpaceEngine())
        
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
        engine = self._bind_engine(BIMCoreEngine())
        
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

    def test_06_bim_core_normalizes_legacy_opening_wall_id_to_parent_wall_uuid(self):
        """Legacy opening wall refs should be normalized to canonical parent_wall UUID."""
        engine = self._bind_engine(BIMCoreEngine())

        mock_semantics = {
            "elements": [
                {
                    "element_id": "wall_1",
                    "wall_id": 101,
                    "type": "Wall",
                    "points": [[0.0, 0.0], [10.0, 0.0]],
                    "thickness": 250.0
                },
                {
                    "element_id": "door_1",
                    "type": "Door",
                    "points": [[2.0, 0.0], [3.0, 0.0]],
                    "width": 900.0,
                    "wall_id": 101
                }
            ]
        }
        mock_spaces = {
            "spaces": [
                {
                    "space_id": "space_1",
                    "name": "Salon",
                    "area": 100.0,
                    "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]],
                    "edge_indices": [0]
                }
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

        canonical_model = engine.run()

        self.assertEqual(len(canonical_model["walls"]), 1)
        self.assertEqual(len(canonical_model["doors"]), 1)

        wall_uuid = canonical_model["walls"][0]["uuid"]
        door = canonical_model["doors"][0]

        self.assertEqual(door["parent_wall"], wall_uuid)
        self.assertIn(door["uuid"], canonical_model["spaces"][0]["related_doors"])

if __name__ == '__main__':
    unittest.main()
