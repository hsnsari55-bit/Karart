import json
import os
import sys
import tempfile
import time
import unittest
import hashlib


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.bim_core import BIMCoreEngine
from backend.semantic_engine import SemanticEngine
from backend.space_engine import SpaceEngine


class _StubPathManager:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def get_path(self, category: str, filename: str) -> str:
        return os.path.join(self.root_dir, filename)


class _StubSemanticPathManager(_StubPathManager):
    pass


def _canonical_sha256(data) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


DOMAIN_HASH_SPEC_VERSION = "1.0"


def _domain_hash_v1(bim_model) -> str:
    payload = {
        "domain_hash_spec": DOMAIN_HASH_SPEC_VERSION,
        "spaces": bim_model.get("spaces", []),
        "walls": bim_model.get("walls", []),
        "windows": bim_model.get("windows", []),
        "columns": bim_model.get("columns", []),
        "doors": bim_model.get("doors", []),
    }
    json_bytes = json.dumps(payload, indent=4, sort_keys=True).replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(json_bytes).hexdigest()


def _strip_volatile_provenance_fields(model):
    clone = json.loads(json.dumps(model))
    provenance = clone.get("provenance", {})
    for key in ("generated_at", "python_version", "shapely_version", "input_hashes", "canonical_bim_sha256"):
        provenance.pop(key, None)
    return clone


class TestRegressionBIMCoreOpeningParentWall(unittest.TestCase):
    def test_legacy_wall_id_is_normalized_to_parent_wall_uuid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "element_id": "wall_1",
                                "wall_id": 101,
                                "type": "Wall",
                                "points": [[0.0, 0.0], [10.0, 0.0]],
                                "thickness": 250.0,
                            },
                            {
                                "element_id": "door_1",
                                "type": "Door",
                                "points": [[2.0, 0.0], [3.0, 0.0]],
                                "width": 900.0,
                                "wall_id": 101,
                            },
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "spaces": [
                            {
                                "space_id": "space_1",
                                "name": "Salon",
                                "area": 100.0,
                                "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]],
                                "edge_indices": [0],
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [
                            {"id": 0, "x": 0.0, "y": 0.0},
                            {"id": 1, "x": 10.0, "y": 0.0},
                        ],
                        "edges": [{"id": 1, "from": 0, "to": 1}],
                    },
                    f,
                    indent=2,
                )

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            canonical_model = engine.run()

            self.assertEqual(len(canonical_model["walls"]), 1)
            self.assertEqual(len(canonical_model["doors"]), 1)

            wall_uuid = canonical_model["walls"][0]["uuid"]
            door = canonical_model["doors"][0]
            space = canonical_model["spaces"][0]

            self.assertEqual(door["parent_wall"], wall_uuid)
            self.assertIn(door["uuid"], space["related_doors"])

    def test_semantic_geometry_contract_and_block_trace_resolve_to_parent_wall_uuid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "uuid": "wall-semantic-1",
                                "type": "Wall",
                                "geometry": {
                                    "points": [[0.0, 0.0], [10.0, 0.0]],
                                    "length": 10.0,
                                },
                                "edge_id": 1,
                                "source_block_name": "ROOM_BLOCK_A",
                            },
                            {
                                "uuid": "door-semantic-1",
                                "type": "Door",
                                "geometry": {
                                    "points": [[2.0, 0.0], [3.0, 0.0]],
                                    "length": 1.0,
                                },
                                "nearest_wall_edge_id": 1,
                                "source_block_name": "ROOM_BLOCK_A",
                            },
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "spaces": [
                            {
                                "space_id": "space_1",
                                "name": "Salon",
                                "area": 100.0,
                                "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]],
                                "edge_indices": [0],
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [
                            {"id": 0, "x": 0.0, "y": 0.0},
                            {"id": 1, "x": 10.0, "y": 0.0},
                        ],
                        "edges": [{"id": 1, "from": 0, "to": 1}],
                    },
                    f,
                    indent=2,
                )

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            canonical_model = engine.run()

            self.assertEqual(len(canonical_model["walls"]), 1)
            self.assertEqual(len(canonical_model["doors"]), 1)

            wall = canonical_model["walls"][0]
            door = canonical_model["doors"][0]
            space = canonical_model["spaces"][0]

            self.assertEqual(door["parent_wall"], wall["uuid"])
            self.assertEqual(door["source_block_name"], "ROOM_BLOCK_A")
            self.assertEqual(wall["source_block_name"], "ROOM_BLOCK_A")
            self.assertIn(door["uuid"], space["related_doors"])

    def test_space_bounded_by_walls_falls_back_to_related_wall_uuids_when_edge_indices_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "uuid": "wall-semantic-1",
                                "type": "Wall",
                                "geometry": {
                                    "points": [[0.0, 0.0], [10.0, 0.0]],
                                    "length": 10.0,
                                },
                            },
                            {
                                "uuid": "wall-semantic-2",
                                "type": "Wall",
                                "geometry": {
                                    "points": [[10.0, 0.0], [10.0, 10.0]],
                                    "length": 10.0,
                                },
                            },
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "spaces": [
                            {
                                "space_id": "space_1",
                                "name": "Salon",
                                "area": 100.0,
                                "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]],
                                "bounded_by_walls": ["wall-semantic-1", "wall-semantic-2"],
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [],
                        "edges": [],
                        "loops": [],
                    },
                    f,
                    indent=2,
                )

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            canonical_model = engine.run()

            self.assertEqual(len(canonical_model["walls"]), 2)
            space = canonical_model["spaces"][0]

            self.assertEqual(
                sorted(space["related_walls"]),
                ["wall-semantic-1", "wall-semantic-2"],
            )
            for wall in canonical_model["walls"]:
                self.assertEqual(wall["related_spaces"], [space["uuid"]])

    def test_curved_opening_from_flattened_arc_keeps_wall_trace_and_is_classified(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = os.path.join(temp_dir, "dxf_raw.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "entities": [
                            {
                                "type": "LWPOLYLINE",
                                "source_entity_type": "ARC",
                                "layer": "kapı",
                                "block_name": "CURVED_DOOR_BLOCK",
                                "closed": False,
                                "vertices": [
                                    {"x": 200.0, "y": 0.0},
                                    {"x": 225.0, "y": 20.0},
                                    {"x": 250.0, "y": 0.0}
                                ]
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [
                            {"id": 0, "x": 0.0, "y": 0.0},
                            {"id": 1, "x": 1000.0, "y": 0.0},
                        ],
                        "edges": [
                            {"id": 7, "from": 0, "to": 1, "length": 1000.0}
                        ],
                        "loops": [],
                    },
                    f,
                    indent=2,
                )

            engine = SemanticEngine()
            engine.path_manager = _StubSemanticPathManager(temp_dir)

            semantics = engine.run()

            self.assertTrue(semantics["elements"])
            wall = next(el for el in semantics["elements"] if el["type"] == "Wall")
            door = next(el for el in semantics["elements"] if el["type"] == "Door")

            self.assertEqual(wall["edge_id"], 7)
            self.assertEqual(door["nearest_wall_edge_id"], 7)
            self.assertEqual(door["source_entity_type"], "ARC")
            self.assertEqual(door["source_block_name"], "CURVED_DOOR_BLOCK")
            self.assertEqual(door["geometry"]["points"][0], [200.0, 0.0])

    def test_semantic_explicit_graph_handoff_overrides_raw_geometry_graph_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_path = os.path.join(temp_dir, "dxf_raw.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "entities": [
                            {
                                "type": "LWPOLYLINE",
                                "source_entity_type": "ARC",
                                "layer": "kapı",
                                "block_name": "CURVED_DOOR_BLOCK",
                                "closed": False,
                                "vertices": [
                                    {"x": 200.0, "y": 0.0},
                                    {"x": 225.0, "y": 20.0},
                                    {"x": 250.0, "y": 0.0}
                                ]
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [
                            {"id": 0, "x": 0.0, "y": 0.0},
                            {"id": 1, "x": 1000.0, "y": 0.0},
                        ],
                        "edges": [
                            {"id": 7, "from": 0, "to": 1, "length": 1000.0}
                        ],
                        "loops": [],
                    },
                    f,
                    indent=2,
                )

            resolved_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0},
                    {"id": 1, "x": 1000.0, "y": 0.0},
                ],
                "edges": [
                    {"id": 42, "from": 0, "to": 1, "length": 1000.0}
                ],
                "loops": [],
            }

            engine = SemanticEngine()
            engine.path_manager = _StubSemanticPathManager(temp_dir)

            semantics = engine.run(graph_data=resolved_graph)

            wall = next(el for el in semantics["elements"] if el["type"] == "Wall")
            door = next(el for el in semantics["elements"] if el["type"] == "Door")

            self.assertEqual(wall["edge_id"], 42)
            self.assertEqual(door["nearest_wall_edge_id"], 42)
            self.assertNotEqual(door["nearest_wall_edge_id"], 7)

    def test_space_engine_explicit_graph_handoff_changes_virtual_boundary_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "uuid": "wall-bottom",
                                "type": "Wall",
                                "geometry": {"points": [[0.0, 0.0], [100.0, 0.0]], "length": 100.0},
                            },
                            {
                                "uuid": "wall-right",
                                "type": "Wall",
                                "geometry": {"points": [[100.0, 0.0], [100.0, 100.0]], "length": 100.0},
                            },
                            {
                                "uuid": "wall-top",
                                "type": "Wall",
                                "geometry": {"points": [[100.0, 100.0], [0.0, 100.0]], "length": 100.0},
                            },
                        ]
                    },
                    f,
                    indent=2,
                )

            raw_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
                    {"id": 1, "x": 100.0, "y": 0.0, "degree": 2},
                    {"id": 2, "x": 100.0, "y": 100.0, "degree": 2},
                    {"id": 3, "x": 0.0, "y": 100.0, "degree": 2},
                ],
                "edges": [
                    {"id": 0, "from": 0, "to": 1, "length": 100.0},
                    {"id": 1, "from": 1, "to": 2, "length": 100.0},
                    {"id": 2, "from": 2, "to": 3, "length": 100.0},
                ],
                "loops": [],
            }
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(raw_graph, f, indent=2)

            resolved_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0, "degree": 1},
                    {"id": 1, "x": 100.0, "y": 0.0, "degree": 2},
                    {"id": 2, "x": 100.0, "y": 100.0, "degree": 2},
                    {"id": 3, "x": 0.0, "y": 100.0, "degree": 1},
                ],
                "edges": raw_graph["edges"],
                "loops": [],
            }

            raw_engine = SpaceEngine()
            raw_engine.path_manager = _StubPathManager(temp_dir)
            raw_output = raw_engine.run()

            resolved_engine = SpaceEngine()
            resolved_engine.path_manager = _StubPathManager(temp_dir)
            resolved_output = resolved_engine.run(graph_data=resolved_graph)

            self.assertEqual(len(raw_output["spaces"]), 0)
            self.assertEqual(raw_output["stats"]["Virtual Boundaries"], 0)
            self.assertEqual(len(resolved_output["spaces"]), 1)
            self.assertEqual(resolved_output["stats"]["Virtual Boundaries"], 1)
            self.assertEqual(len(resolved_output["spaces"][0]["bounded_by_walls"]), 3)

    def test_bim_core_explicit_graph_handoff_updates_provenance_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "uuid": "wall-semantic-1",
                                "type": "Wall",
                                "geometry": {
                                    "points": [[0.0, 0.0], [10.0, 0.0]],
                                    "length": 10.0,
                                },
                                "edge_id": 1,
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump({"spaces": []}, f, indent=2)

            raw_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0},
                    {"id": 1, "x": 10.0, "y": 0.0},
                ],
                "edges": [{"id": 1, "from": 0, "to": 1}],
            }
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(raw_graph, f, indent=2)

            resolved_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0},
                    {"id": 1, "x": 10.0, "y": 0.0},
                ],
                "edges": [{"id": 99, "from": 0, "to": 1}],
            }

            with open(graph_path, "rb") as f:
                raw_graph_sha256 = hashlib.sha256(f.read()).hexdigest()

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            canonical_model = engine.run(graph_data=resolved_graph)

            self.assertEqual(
                canonical_model["provenance"]["input_hashes"]["geometry_graph_sha256"],
                _canonical_sha256(resolved_graph),
            )
            self.assertNotEqual(
                canonical_model["provenance"]["input_hashes"]["geometry_graph_sha256"],
                raw_graph_sha256,
            )

    def test_domain_hash_excludes_volatile_provenance_and_registers_spec_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")
            graph_path = os.path.join(temp_dir, "geometry_graph.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "element_id": "wall_1",
                                "wall_id": 101,
                                "type": "Wall",
                                "points": [[0.0, 0.0], [10.0, 0.0]],
                                "thickness": 250.0,
                            },
                            {
                                "element_id": "door_1",
                                "type": "Door",
                                "points": [[2.0, 0.0], [3.0, 0.0]],
                                "width": 900.0,
                                "wall_id": 101,
                            },
                            {
                                "element_id": "window_1",
                                "type": "Window",
                                "points": [[6.0, 0.0], [7.0, 0.0]],
                                "width": 1200.0,
                                "wall_id": 101,
                            },
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "spaces": [
                            {
                                "space_id": "space_1",
                                "name": "Salon",
                                "area": 100.0,
                                "boundary": [[0, 0], [10, 0], [10, 10], [0, 10]],
                                "edge_indices": [0],
                                "element_indices": [],
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "nodes": [
                            {"id": 0, "x": 0.0, "y": 0.0},
                            {"id": 1, "x": 10.0, "y": 0.0},
                        ],
                        "edges": [{"id": 1, "from": 0, "to": 1}],
                        "loops": [],
                    },
                    f,
                    indent=2,
                )

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            first_model = engine.run()
            time.sleep(1.1)
            second_model = engine.run()

            self.assertNotEqual(first_model["provenance"]["generated_at"], second_model["provenance"]["generated_at"])
            self.assertEqual(first_model["provenance"]["domain_hash_spec"], DOMAIN_HASH_SPEC_VERSION)
            self.assertEqual(second_model["provenance"]["domain_hash_spec"], DOMAIN_HASH_SPEC_VERSION)
            self.assertEqual(
                first_model["provenance"]["canonical_bim_sha256"],
                second_model["provenance"]["canonical_bim_sha256"],
            )
            self.assertEqual(first_model["provenance"]["canonical_bim_sha256"], _domain_hash_v1(first_model))
            self.assertEqual(second_model["provenance"]["canonical_bim_sha256"], _domain_hash_v1(second_model))
            self.assertEqual(
                _strip_volatile_provenance_fields(first_model),
                _strip_volatile_provenance_fields(second_model),
            )

    def test_transient_logical_connectors_are_excluded_from_canonical_bim_and_domain_hash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            semantics_path = os.path.join(temp_dir, "bim_semantics.json")
            spaces_path = os.path.join(temp_dir, "spaces.json")

            with open(semantics_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "elements": [
                            {
                                "uuid": "wall-semantic-1",
                                "type": "Wall",
                                "geometry": {
                                    "points": [[0.0, 0.0], [10.0, 0.0]],
                                    "length": 10.0,
                                },
                                "edge_id": 1,
                            }
                        ]
                    },
                    f,
                    indent=2,
                )

            with open(spaces_path, "w", encoding="utf-8") as f:
                json.dump({"spaces": []}, f, indent=2)

            physical_graph = {
                "nodes": [
                    {"id": 0, "x": 0.0, "y": 0.0},
                    {"id": 1, "x": 10.0, "y": 0.0},
                ],
                "edges": [{"id": 1, "from": 0, "to": 1}],
                "loops": [],
            }
            candidate_graph = json.loads(json.dumps(physical_graph))
            candidate_graph["logical_connectors"] = [
                {
                    "id": "transient-connector-must-not-persist",
                    "type": "door",
                    "from": 0,
                    "to": 1,
                    "physical": False,
                }
            ]

            engine = BIMCoreEngine()
            engine.path_manager = _StubPathManager(temp_dir)

            baseline_model = engine.run(graph_data=physical_graph)
            candidate_model = engine.run(graph_data=candidate_graph)

            domain_keys = ("spaces", "walls", "windows", "columns", "doors")
            self.assertEqual(
                {key: baseline_model[key] for key in domain_keys},
                {key: candidate_model[key] for key in domain_keys},
            )
            self.assertEqual(
                baseline_model["provenance"]["canonical_bim_sha256"],
                candidate_model["provenance"]["canonical_bim_sha256"],
            )
            self.assertEqual(
                candidate_model["provenance"]["canonical_bim_sha256"],
                _domain_hash_v1(candidate_model),
            )
            self.assertNotEqual(
                baseline_model["provenance"]["input_hashes"]["geometry_graph_sha256"],
                candidate_model["provenance"]["input_hashes"]["geometry_graph_sha256"],
            )
            self.assertNotIn("logical_connectors", candidate_model)
            self.assertNotIn(
                "transient-connector-must-not-persist",
                json.dumps(candidate_model, sort_keys=True),
            )


if __name__ == "__main__":
    unittest.main()