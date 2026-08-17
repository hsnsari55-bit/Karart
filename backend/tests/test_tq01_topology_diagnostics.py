import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from backend.tq01_topology_diagnostics import (
    CATEGORIES,
    FORBIDDEN_DOWNSTREAM,
    candidate_measurements,
    run_diagnostics,
)


class TestTQ01TopologyDiagnostics(unittest.TestCase):
    def test_candidate_measurements_excludes_incident_endpoint(self):
        graph = {
            "nodes": [
                {"id": 0, "x": 0.0, "y": 0.0},
                {"id": 1, "x": 100.0, "y": 0.0},
                {"id": 2, "x": 4.0, "y": 0.0},
                {"id": 3, "x": 4.0, "y": 20.0},
            ],
            "edges": [
                {"id": 0, "from": 0, "to": 1, "from_x": 0.0,
                 "from_y": 0.0, "to_x": 100.0, "to_y": 0.0},
                {"id": 1, "from": 2, "to": 3, "from_x": 4.0,
                 "from_y": 0.0, "to_x": 4.0, "to_y": 20.0},
            ],
        }
        result = candidate_measurements(graph, graph["nodes"][0], 0)
        self.assertEqual(2, result["nearest_endpoint_node_id"])
        self.assertEqual(4.0, result["nearest_endpoint_distance_mm"])
        self.assertEqual(1, result["endpoint_candidate_count_at_production_tolerance"])

    def test_generates_deterministic_blocked_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.dxf"
            source.write_bytes(b"0\r\nSECTION\r\n2\r\nBLOCKS\r\n0\r\nLWPO")
            walls = root / "walls_clean.json"
            walls.write_text(json.dumps([
                {"type": "LINE", "layer": "WALL", "block_name": "PLAN",
                 "points": [[0, 0], [100, 0]]},
                {"type": "LINE", "layer": "WALL", "block_name": "PLAN",
                 "points": [[110, 0], [210, 0]]},
            ]), encoding="utf-8")
            raw = root / "dxf_raw.json"
            raw.write_text(json.dumps({
                "source_file": "source.dxf",
                "bounding_box": {"min_x": 0, "min_y": 0,
                                 "max_x": 210, "max_y": 0},
                "metadata": {"promoted_block": "PLAN",
                             "promotion_reason": "heuristic_score"},
                "entities": [{"type": "LINE", "layer": "WALL",
                              "block_name": "PLAN"}],
            }), encoding="utf-8")
            output = root / "result"

            manifest = run_diagnostics(source, walls, raw, output)

            self.assertEqual("TQ-01 QUALIFIED_BLOCKED_NO_SAFE_FIX",
                             manifest["status"])
            self.assertTrue(manifest["determinism"]["equal"])
            self.assertEqual(4, manifest["counts"]["dangling"])
            self.assertEqual(2, manifest["counts"]["components"])
            self.assertTrue(all(
                not (output / name).exists() for name in FORBIDDEN_DOWNSTREAM
            ))
            for name, metadata in manifest["artifacts"].items():
                artifact = output / name
                self.assertEqual(artifact.stat().st_size, metadata["size_bytes"])
                self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(),
                                 metadata["sha256"])

            dangling = json.loads((output / "dangling_nodes.json").read_text())
            self.assertEqual(list(CATEGORIES), dangling["categories"])
            self.assertTrue(all(
                node["provenance"]["entity_id"] == "UNKNOWN"
                for node in dangling["nodes"]
            ))
            report = (output / "TQ01_ENGINEERING_REPORT.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual([
                "# Kanıt", "# Risk Analizi", "# Önerilen Çözüm",
                "# Uygulanan Değişiklik", "# Doğrulama", "# Kalan Riskler",
            ], [line for line in report.splitlines() if line.startswith("# ")])
            self.assertIn(
                "Bu değişiklik Geometry Engine, Topology Engine veya Canonical BIM Model’in",
                report,
            )
            overview = (output / "topology_overview.svg").read_text(
                encoding="utf-8"
            )
            self.assertIn("Legend", overview)
            self.assertIn("closed-loop boundary", overview)


if __name__ == "__main__":
    unittest.main()