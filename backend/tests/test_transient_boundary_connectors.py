import copy
import unittest
from types import SimpleNamespace

from backend.transient_boundary_connectors import (
    effective_edge_pairs,
    generate_logical_connectors,
    validate_logical_connectors,
)


def _graph(offset=(0.0, 0.0)):
    dx, dy = offset
    return {
        "nodes": [
            {"id": 10, "x": 0.0 + dx, "y": 0.0 + dy, "degree": 1},
            {"id": 11, "x": 10.0 + dx, "y": 0.0 + dy, "degree": 1},
            {"id": 20, "x": 0.0 + dx, "y": 10.0 + dy, "degree": 1},
            {"id": 21, "x": 10.0 + dx, "y": 10.0 + dy, "degree": 1},
        ],
        "edges": [
            {"id": "wall-a", "from": 10, "to": 11, "length": 10.0},
            {"id": "wall-b", "from": 20, "to": 21, "length": 10.0},
        ],
        "loops": [],
    }


def _source(layer="kapı", source_id="door-source", offset=(0.0, 0.0), **changes):
    dx, dy = offset
    result = {
        "source_id": source_id,
        "source_handle": "AB12",
        "root_source_id": "AB12",
        "entity_type": "LINE",
        "layer": layer,
        "points": [(10.0 + dx, 0.0 + dy), (10.0 + dx, 10.0 + dy)],
        "closed": False,
        "insert_ancestry": ["DOOR_BLOCK"],
    }
    result.update(changes)
    return result


class TransientBoundaryConnectorTests(unittest.TestCase):
    def test_generates_typed_non_physical_door_without_mutating_graph(self):
        graph = _graph()
        before = copy.deepcopy(graph)
        result = generate_logical_connectors(graph, [_source()])

        self.assertEqual(result["rejections"], [])
        self.assertEqual(len(result["logical_connectors"]), 1)
        connector = result["logical_connectors"][0]
        self.assertEqual(connector["role"], "DOOR_PORTAL")
        self.assertIs(connector["physical"], False)
        self.assertEqual(connector["endpoint_node_ids"], [11, 21])
        self.assertEqual(connector["host_edge_ids"], ["wall-a", "wall-b"])
        self.assertEqual(connector["length_mm"], 10.0)
        self.assertEqual(graph, before)

    def test_generates_window_from_closing_polyline_segment(self):
        source = _source(
            "pencere",
            entity_type="LWPOLYLINE",
            points=[(10.0, 0.0), (15.0, 0.0), (15.0, 10.0), (10.0, 10.0)],
            closed=True,
        )
        connector = generate_logical_connectors(_graph(), [source])["logical_connectors"][0]
        self.assertEqual(connector["role"], "WINDOW_OPENING")
        self.assertEqual(connector["source_layer_normalized"], "pencere")

    def test_closed_audit_entity_with_four_contacts_selects_only_proven_segment(self):
        graph = _graph()
        graph["nodes"].extend([
            {"id": 30, "x": 15.0, "y": 0.0},
            {"id": 31, "x": 15.0, "y": 10.0},
            {"id": 32, "x": 16.0, "y": 0.0},
            {"id": 33, "x": 15.0, "y": -1.0},
            {"id": 34, "x": 16.0, "y": 10.0},
            {"id": 35, "x": 15.0, "y": 11.0},
        ])
        graph["edges"].extend([
            {"id": "extra-a1", "from": 30, "to": 32},
            {"id": "extra-a2", "from": 30, "to": 33},
            {"id": "extra-b1", "from": 31, "to": 34},
            {"id": "extra-b2", "from": 31, "to": 35},
        ])
        source = SimpleNamespace(
            source_id="window-source", source_handle="CD34", root_source_id="CD34",
            entity_type="LWPOLYLINE", layer="pencere", is_closed=True,
            render_points=[(10.0, 0.0), (15.0, 0.0), (15.0, 10.0), (10.0, 10.0)],
            insert_ancestry=(),
        )

        result = generate_logical_connectors(graph, [source])

        self.assertEqual(len(result["logical_connectors"]), 1)
        self.assertEqual(result["logical_connectors"][0]["endpoint_node_ids"], [11, 21])
        self.assertTrue(result["rejections"])
        self.assertEqual(
            {item["reason"] for item in result["rejections"]},
            {"CONTACT_HAS_NON_UNIQUE_PHYSICAL_HOST"},
        )

    def test_accepts_endpoint_overrun_within_unchanged_physical_tolerance(self):
        source = _source(points=[(10.0, 0.0), (10.0, 9.9999)])
        result = generate_logical_connectors(_graph(), [source], tolerance_mm=0.01)
        self.assertEqual(result["rejections"], [])
        self.assertEqual(len(result["logical_connectors"]), 1)

    def test_rejects_unsupported_layer_and_entity_with_explicit_reasons(self):
        layer_result = generate_logical_connectors(_graph(), [_source("kolon")])
        entity_result = generate_logical_connectors(_graph(), [_source(entity_type="ARC")])
        self.assertEqual(layer_result["rejections"][0]["reason"], "UNSUPPORTED_SOURCE_LAYER")
        self.assertEqual(entity_result["rejections"][0]["reason"], "UNSUPPORTED_SOURCE_ENTITY_TYPE")

    def test_rejects_contact_counts_other_than_two(self):
        missing = _source(points=[(5.0, 0.0), (5.0, 10.0)])
        graph = _graph()
        graph["nodes"].append({"id": 22, "x": 10.0, "y": 5.0})
        self.assertEqual(generate_logical_connectors(_graph(), [missing])["rejections"][0]["reason"], "CONTACT_COUNT_NOT_TWO")
        self.assertEqual(generate_logical_connectors(graph, [_source()])["rejections"][0]["reason"], "CONTACT_COUNT_NOT_TWO")

    def test_rejects_non_dangling_or_missing_unique_host(self):
        graph = _graph()
        graph["edges"].append({"id": "third", "from": 11, "to": 20})
        result = generate_logical_connectors(graph, [_source()])
        self.assertEqual(result["rejections"][0]["reason"], "CONTACT_HAS_NON_UNIQUE_PHYSICAL_HOST")

    def test_rejects_shared_host(self):
        graph = _graph()
        graph["edges"] = [{"id": "one", "from": 11, "to": 21}]
        result = generate_logical_connectors(graph, [_source()])
        self.assertEqual(result["rejections"][0]["reason"], "CONTACTS_SHARE_PHYSICAL_HOST")

    def test_rejects_nonparallel_hosts(self):
        graph = _graph()
        graph["nodes"][2].update({"x": 10.0, "y": 20.0})
        result = generate_logical_connectors(graph, [_source()])
        self.assertEqual(result["rejections"][0]["reason"], "HOSTS_NOT_PARALLEL_OR_CONNECTOR_NOT_PERPENDICULAR")

    def test_rejects_nonperpendicular_connector(self):
        source = _source(points=[(10.0, 0.0), (9.0, 10.0)])
        graph = _graph()
        graph["nodes"][2]["x"] = 9.0
        result = generate_logical_connectors(graph, [source])
        self.assertEqual(result["rejections"][0]["reason"], "HOSTS_NOT_PARALLEL_OR_CONNECTOR_NOT_PERPENDICULAR")

    def test_rejects_contacts_not_supported_by_one_finite_span(self):
        source = _source(entity_type="LWPOLYLINE", points=[(10.0, 0.0), (15.0, 5.0), (10.0, 10.0)])
        result = generate_logical_connectors(_graph(), [source])
        self.assertEqual(result["rejections"][0]["reason"], "CONTACTS_NOT_ON_ONE_FINITE_SOURCE_SPAN")

    def test_rejects_ambiguous_duplicate_endpoint_assignment(self):
        result = generate_logical_connectors(_graph(), [_source(source_id="A"), _source(source_id="B")])
        self.assertEqual(result["logical_connectors"], [])
        self.assertEqual([item["reason"] for item in result["rejections"]], [
            "AMBIGUOUS_DUPLICATE_ENDPOINT_ASSIGNMENT",
            "AMBIGUOUS_DUPLICATE_ENDPOINT_ASSIGNMENT",
        ])

    def test_permutation_and_translation_preserve_stable_identity(self):
        expected = generate_logical_connectors(_graph(), [_source()])["logical_connectors"][0]
        permuted = _graph()
        permuted["nodes"].reverse()
        permuted["edges"].reverse()
        actual = generate_logical_connectors(permuted, [_source()])["logical_connectors"][0]
        translated = generate_logical_connectors(_graph((1234.5, -77.0)), [_source(offset=(1234.5, -77.0))])["logical_connectors"][0]
        self.assertEqual(actual, expected)
        self.assertEqual(translated["id"], expected["id"])
        self.assertEqual(translated["length_mm"], expected["length_mm"])

    def test_rounding_within_tolerance_is_deterministic(self):
        source = _source(points=[(10.000001, 0.0), (10.000001, 10.0)])
        first = generate_logical_connectors(_graph(), [source])
        second = generate_logical_connectors(_graph(), [source])
        self.assertEqual(first, second)
        self.assertEqual(len(first["logical_connectors"]), 1)

    def test_validator_projects_only_strict_valid_records(self):
        graph = _graph()
        connector = generate_logical_connectors(graph, [_source()])["logical_connectors"][0]
        malformed = {**connector, "id": "ag04-malformed", "physical": True}
        valid, rejected = validate_logical_connectors(graph["nodes"], graph["edges"], [malformed, connector])
        pairs, projection_rejections = effective_edge_pairs(graph["nodes"], graph["edges"], [connector])
        self.assertEqual(valid, [connector])
        self.assertEqual(rejected[0]["reason"], "CONNECTOR_MUST_BE_NON_PHYSICAL")
        self.assertEqual(pairs, [(11, 21)])
        self.assertEqual(projection_rejections, [])


if __name__ == "__main__":
    unittest.main()