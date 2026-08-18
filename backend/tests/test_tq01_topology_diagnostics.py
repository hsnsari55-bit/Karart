import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import ezdxf

from backend.tq01_topology_diagnostics import (
    CATEGORIES,
    FORBIDDEN_DOWNSTREAM,
    MANAGED_ARTIFACTS,
    candidate_measurements,
    component_inventory,
    dangling_inventory,
    rebuild_graph,
    run_diagnostics,
    source_audit,
    validate_topology_graph,
)


def wall(start, end):
    return {
        "type": "LINE",
        "layer": "WALL",
        "block_name": "PLAN",
        "points": [start, end],
    }


def valid_square_graph():
    nodes = [
        {"id": 10, "x": 0.0, "y": 0.0, "degree": 2, "type": "L_corner"},
        {"id": 20, "x": 10.0, "y": 0.0, "degree": 2, "type": "L_corner"},
        {"id": 30, "x": 10.0, "y": 10.0, "degree": 2, "type": "L_corner"},
        {"id": 40, "x": 0.0, "y": 10.0, "degree": 2, "type": "L_corner"},
    ]
    edges = [
        {"id": 5, "from": 10, "to": 20, "length": 10.0, "angle": 0.0},
        {"id": 6, "from": 20, "to": 30, "length": 10.0, "angle": 90.0},
        {"id": 7, "from": 30, "to": 40, "length": 10.0, "angle": 180.0},
        {"id": 8, "from": 40, "to": 10, "length": 10.0, "angle": -90.0},
    ]
    boundary = [
        {"x": 0.0, "y": 0.0},
        {"x": 10.0, "y": 0.0},
        {"x": 10.0, "y": 10.0},
        {"x": 0.0, "y": 10.0},
        {"x": 0.0, "y": 0.0},
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "loops": [{"id": 3, "area": 100.0, "edges": [5, 6, 7, 8], "boundary": boundary}],
    }


class TestTQ01TopologyDiagnostics(unittest.TestCase):
    def create_dxf(self, path):
        document = ezdxf.new("R2010")
        document.modelspace().add_line((0, 0), (100, 0))
        document.saveas(path)

    def create_inputs(self, root, walls):
        source = root / "source.dxf"
        self.create_dxf(source)
        walls_path = root / "walls_clean.json"
        walls_path.write_text(json.dumps(walls), encoding="utf-8")
        raw_path = root / "dxf_raw.json"
        raw_path.write_text(
            json.dumps(
                {
                    "source_file": "source.dxf",
                    "bounding_box": {"min_x": "0<&", "min_y": 0, "max_x": 100, "max_y": 100},
                    "metadata": {
                        "promoted_block": 'PLAN<&"',
                        "promotion_reason": "heuristic_score",
                    },
                    "entities": [
                        {"type": "LINE", "layer": "WALL", "block_name": 'PLAN<&"'}
                    ],
                }
            ),
            encoding="utf-8",
        )
        return source, walls_path, raw_path

    def test_candidate_types_and_non_contiguous_node_ids(self):
        graph = {
            "nodes": [
                {"id": 10, "x": 0.0, "y": 0.0, "degree": 1},
                {"id": 30, "x": -100.0, "y": 0.0, "degree": 1},
                {"id": 70, "x": 4.0, "y": 0.0, "degree": 1},
                {"id": 90, "x": 3.0, "y": 0.0, "degree": 3},
                {"id": 110, "x": 4.0, "y": -10.0, "degree": 2},
                {"id": 130, "x": 4.0, "y": 10.0, "degree": 2},
            ],
            "edges": [
                {"id": 2, "from": 10, "to": 30, "length": 100.0},
                {"id": 4, "from": 70, "to": 90, "length": 1.0},
                {"id": 8, "from": 110, "to": 130, "length": 20.0},
            ],
            "loops": [],
        }
        result = candidate_measurements(graph, graph["nodes"][0], 2)
        self.assertEqual(70, result["nearest_endpoint_node_id"])
        self.assertEqual(90, result["nearest_junction_node_id"])
        self.assertEqual(8, result["nearest_nonincident_segment_edge_id"])
        self.assertEqual(1, result["endpoint_candidate_count_at_production_tolerance"])
        self.assertEqual(1, result["junction_candidate_count_at_production_tolerance"])
        components, node_to_component = component_inventory(graph)
        records = dangling_inventory(graph, [], node_to_component)
        self.assertEqual(3, len(components))
        self.assertIn(10, {record["node_id"] for record in records})

    def test_source_audit_executes_isolated_valid_and_truncated_probes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, _walls, raw_path = self.create_inputs(root, [])
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            original = source.read_bytes()
            valid_audit = source_audit(source, raw_path, raw)
            self.assertEqual(original, source.read_bytes())
            self.assertFalse(Path(f"{source}.repaired.dxf").exists())
            self.assertFalse((root / "outputs").exists())
            for probe in ("standard_read", "production_smart_repair", "original_recover"):
                self.assertEqual("PASS", valid_audit["source"][probe]["status"])
            self.assertGreater(valid_audit["source"]["standard_read"]["modelspace_entities"], 0)
            parser_probe = valid_audit["source"]["production_smart_repair"]
            self.assertEqual(1, parser_probe["entity_count"])
            self.assertEqual(
                parser_probe["entity_count"],
                sum(parser_probe["block_entity_counts"].values()),
            )
            self.assertEqual(
                parser_probe["block_count"],
                len(parser_probe["block_entity_counts"]),
            )

            truncated = root / "truncated.dxf"
            eof_offset = original.rfind(b"EOF")
            self.assertGreater(eof_offset, 0)
            truncated.write_bytes(original[: max(1, eof_offset - 12)])
            truncated_original = truncated.read_bytes()
            truncated_audit = source_audit(truncated, raw_path, raw)
            statuses = [
                truncated_audit["source"][name]["status"]
                for name in ("standard_read", "production_smart_repair", "original_recover")
            ]
            self.assertNotIn("NOT_EXECUTED", statuses)
            self.assertEqual(truncated_original, truncated.read_bytes())
            self.assertFalse(Path(f"{truncated}.repaired.dxf").exists())
            self.assertEqual(
                "NOT_EVALUATED",
                truncated_audit["historical_snapshot"]["reproduction_equivalence"],
            )
            serialized = json.dumps(truncated_audit, sort_keys=True)
            self.assertNotIn(str(root), serialized)
            self.assertNotIn("karar-tq01-", serialized)

    def test_real_frozen_validator_pass_and_fail_paths(self):
        valid = validate_topology_graph(valid_square_graph())
        self.assertEqual("PASS", valid["topology"])
        self.assertEqual("PASS", valid["validator_report_status"])
        self.assertFalse(valid["no_safe_repair_proven"])

        invalid_graph = valid_square_graph()
        invalid_graph["edges"] = invalid_graph["edges"][:-1]
        invalid_graph["loops"][0]["edges"] = [5, 6, 7]
        invalid_graph["nodes"][0]["degree"] = 1
        invalid_graph["nodes"][3]["degree"] = 1
        invalid = validate_topology_graph(invalid_graph)
        self.assertEqual("FAIL", invalid["topology"])
        self.assertEqual("FAIL", invalid["validator_report_status"])
        self.assertEqual("no_dangling_nodes", invalid["failed_check"])
        self.assertIn("Dangling/open topology", invalid["validator_error"])
        self.assertTrue(invalid["no_safe_repair_proven"])
        self.assertIn("No repair was executed", invalid["safe_repair_evidence"])
        self.assertFalse(invalid["downstream_executed"])

    def test_rebuild_records_frozen_configuration_and_rejects_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            walls_path = Path(temp_dir) / "walls.json"
            walls_path.write_text(json.dumps([wall([0, 0], [10, 0])]), encoding="utf-8")
            _graph, _stats, configured = rebuild_graph(walls_path)
            self.assertEqual(5.0, configured)

            class DriftEngine:
                def __init__(self):
                    self.snap_tolerance = 6.0
                    self.stats = {}

            with patch("backend.tq01_topology_diagnostics.TopologyEngine", DriftEngine):
                with self.assertRaisesRegex(RuntimeError, "configuration-drift"):
                    rebuild_graph(walls_path)

    def test_exact_deterministic_blocked_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, walls_path, raw_path = self.create_inputs(
                root, [wall([0, 0], [100, 0]), wall([110, 0], [210, 0])]
            )
            output_a = root / "tq01-package-a"
            output_a.mkdir()
            (output_a / "stale.txt").write_text("stale", encoding="utf-8")
            (output_a / "stale-dir").mkdir()
            output_b = root / "tq01-package-b"
            manifest = run_diagnostics(source, walls_path, raw_path, output_a)
            manifest_b = run_diagnostics(source, walls_path, raw_path, output_b)

            self.assertEqual("TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX", manifest["status"])
            self.assertEqual("FAIL", manifest["hard_gate"]["topology"])
            self.assertEqual("non_empty_loops", manifest["hard_gate"]["failed_check"])
            self.assertEqual(set(MANAGED_ARTIFACTS), {path.name for path in output_a.iterdir()})
            self.assertEqual(set(MANAGED_ARTIFACTS) - {"manifest.json"}, set(manifest["artifacts"]))
            self.assertEqual(manifest, manifest_b)
            for name in MANAGED_ARTIFACTS:
                self.assertEqual((output_a / name).read_bytes(), (output_b / name).read_bytes())
            for name, metadata in manifest["artifacts"].items():
                artifact = output_a / name
                self.assertEqual(artifact.stat().st_size, metadata["size_bytes"])
                self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), metadata["sha256"])
            self.assertTrue(all(not (output_a / name).exists() for name in FORBIDDEN_DOWNSTREAM))
            ET.parse(output_a / "block_candidates.svg")
            ET.parse(output_a / "topology_overview.svg")

            dangling = json.loads((output_a / "dangling_nodes.json").read_text())
            self.assertEqual(list(CATEGORIES), dangling["categories"])
            report = (output_a / "TQ01_ENGINEERING_REPORT.md").read_text(encoding="utf-8")
            self.assertEqual(
                [
                    "# Kanıt", "# Risk Analizi", "# Önerilen Çözüm",
                    "# Uygulanan Değişiklik", "# Doğrulama", "# Kalan Riskler",
                ],
                [line for line in report.splitlines() if line.startswith("# ")],
            )
            self.assertIn("şekilde artırıyor mu? **HAYIR.**", report)
            for path in output_a.iterdir():
                if path.suffix in {".json", ".csv", ".svg", ".md"}:
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("Ã", text)
                    self.assertNotIn("Â", text)

    def test_unsafe_output_target_is_rejected_and_sentinel_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "tq01-parent"
            root.mkdir()
            source, walls_path, raw_path = self.create_inputs(root, [])
            unsafe_output = root / "ordinary-output"
            unsafe_output.mkdir()
            sentinel = unsafe_output / "sentinel.txt"
            sentinel.write_text("must survive", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "dedicated TQ-01 directory"):
                run_diagnostics(source, walls_path, raw_path, unsafe_output)

            self.assertEqual("must survive", sentinel.read_text(encoding="utf-8"))
            self.assertEqual({"sentinel.txt"}, {path.name for path in unsafe_output.iterdir()})

    def test_closed_walls_package_is_qualified_not_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source, walls_path, raw_path = self.create_inputs(
                root,
                [
                    wall([0, 0], [100, 0]), wall([100, 0], [100, 100]),
                    wall([100, 100], [0, 100]), wall([0, 100], [0, 0]),
                ],
            )
            manifest = run_diagnostics(source, walls_path, raw_path, root / "tq01-result")
            self.assertEqual("TQ-01 QUALIFIED", manifest["status"])
            self.assertEqual("PASS", manifest["hard_gate"]["topology"])
            self.assertIsNone(manifest["hard_gate"]["failed_check"])
            self.assertEqual(5.0, manifest["configuration"]["configured_snap_tolerance_mm"])


if __name__ == "__main__":
    unittest.main()