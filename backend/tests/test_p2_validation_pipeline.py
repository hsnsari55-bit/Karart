import json
import os
import sys
import tempfile
import unittest
from copy import deepcopy


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from p2_validation_pipeline import P2ValidationPipeline


def _build_valid_canonical_bim():
    wall_uuid = "wall-1"
    door_uuid = "door-1"
    window_uuid = "window-1"
    space_uuid = "space-1"
    return {
        "metadata": {"version": "1.0", "generated_by": "test"},
        "provenance": {"engine": "KaRar BIM Core", "canonical_bim_sha256": "placeholder"},
        "walls": [
            {
                "uuid": wall_uuid,
                "points": [[0.0, 0.0], [100.0, 0.0]],
                "related_spaces": [space_uuid],
            }
        ],
        "doors": [
            {
                "uuid": door_uuid,
                "parent_wall": wall_uuid,
                "points": [[10.0, 0.0], [20.0, 0.0]],
            }
        ],
        "windows": [
            {
                "uuid": window_uuid,
                "parent_wall": wall_uuid,
                "points": [[30.0, 0.0], [40.0, 0.0]],
            }
        ],
        "columns": [],
        "spaces": [
            {
                "uuid": space_uuid,
                "boundary": [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]],
                "area": 10000.0,
                "related_walls": [wall_uuid],
                "related_windows": [window_uuid],
                "related_columns": [],
                "related_doors": [door_uuid],
                "neighbors": [],
            }
        ],
    }


def _run_validation(bim_data):
    pipeline = P2ValidationPipeline()

    with tempfile.TemporaryDirectory() as temp_dir:
        bim_model_path = os.path.join(temp_dir, "bim_model.json")
        output_json_path = os.path.join(temp_dir, "p2_validation_summary.json")
        output_report_path = os.path.join(temp_dir, "P2_Validation_Report.md")

        with open(bim_model_path, "w", encoding="utf-8") as f:
            json.dump(bim_data, f, indent=2)

        summary = pipeline.run_validation(
            bim_model_path=bim_model_path,
            ground_truth_path=None,
            output_json_path=output_json_path,
            output_report_path=output_report_path,
        )

        with open(output_report_path, "r", encoding="utf-8") as f:
            report_text = f.read()

    return summary, report_text


class TestP2ValidationPipeline(unittest.TestCase):
    def test_run_validation_accepts_valid_minimal_canonical_model(self):
        summary, _ = _run_validation(_build_valid_canonical_bim())

        self.assertTrue(summary["summary"]["structural_validation_passed"])
        self.assertTrue(summary["summary"]["validation_passed"])
        self.assertEqual(summary["summary"]["quality_grade"], "CLASS_B_STRUCTURALLY_VALIDATED")

    def test_run_validation_without_ground_truth_uses_structural_mode_and_disclaims_benchmark_evidence(self):
        bim_data = _build_valid_canonical_bim()
        summary, report_text = _run_validation(bim_data)

        self.assertEqual(summary["summary"]["validation_mode"], "STRUCTURAL_AUDIT_ONLY")
        self.assertEqual(
            summary["summary"]["benchmark_evidence"],
            "SELF_REFERENTIAL_INTERNAL_COMPARISON",
        )
        self.assertFalse(summary["summary"]["independent_ground_truth_provided"])
        self.assertFalse(summary["summary"]["benchmark_thresholds_applied"])
        self.assertTrue(summary["summary"]["structural_validation_passed"])
        self.assertIsNone(summary["summary"]["benchmark_validation_passed"])
        self.assertTrue(summary["summary"]["validation_passed"])
        self.assertIn("self-referential contract diagnostics", report_text)
        self.assertIn("bağımsız doğruluk kanıtı olarak yorumlanmamalıdır", report_text)

    def test_run_validation_rejects_duplicate_uuid_entities(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["doors"][0]["uuid"] = bim_data["walls"][0]["uuid"]
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["duplicate_uuids_count"],
            1,
        )
        self.assertFalse(summary["summary"]["structural_validation_passed"])
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_missing_mandatory_root_key(self):
        bim_data = _build_valid_canonical_bim()
        del bim_data["metadata"]
        summary, _ = _run_validation(bim_data)

        self.assertIn("metadata", summary["layer_audits"]["layer1_schema"]["missing_root_keys"])
        self.assertFalse(summary["summary"]["structural_validation_passed"])
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_missing_mandatory_provenance_envelope(self):
        bim_data = _build_valid_canonical_bim()
        del bim_data["provenance"]

        summary, _ = _run_validation(bim_data)

        self.assertFalse(summary["layer_audits"]["layer1_schema"]["has_provenance_envelope"])
        self.assertFalse(summary["layer_audits"]["layer1_schema"]["passed"])
        self.assertFalse(summary["summary"]["structural_validation_passed"])
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_orphan_references(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"][0]["related_walls"] = ["missing-wall"]
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["orphan_references_count"],
            1,
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_opening_parent_wall_reference_to_nonexistent_wall(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["doors"][0]["parent_wall"] = "missing-wall"
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["orphan_references_count"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["orphan_details"][0]["type"],
            "Opening->ParentWall",
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_entity_missing_mandatory_uuid(self):
        bim_data = _build_valid_canonical_bim()
        del bim_data["doors"][0]["uuid"]

        summary, _ = _run_validation(bim_data)

        self.assertFalse(summary["layer_audits"]["layer2_uuids_and_references"]["passed"])
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["missing_entity_uuid_count"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["missing_entity_uuid_details"][0]["category"],
            "doors",
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_space_related_walls_reference_to_door_uuid(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"][0]["related_walls"] = [bim_data["doors"][0]["uuid"]]

        summary, _ = _run_validation(bim_data)

        self.assertFalse(summary["layer_audits"]["layer2_uuids_and_references"]["passed"])
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["type_mismatch_references_count"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["type_mismatch_details"][0]["type"],
            "Space->Wall",
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_door_parent_wall_reference_to_space_uuid(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["doors"][0]["parent_wall"] = bim_data["spaces"][0]["uuid"]

        summary, _ = _run_validation(bim_data)

        self.assertFalse(summary["layer_audits"]["layer2_uuids_and_references"]["passed"])
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["type_mismatch_references_count"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer2_uuids_and_references"]["type_mismatch_details"][0]["type"],
            "Opening->ParentWall",
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_invalid_unbounded_space(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"][0]["boundary"] = [[0.0, 0.0], [100.0, 0.0]]
        bim_data["spaces"][0]["related_walls"] = []
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer3_topology_and_graph"]["open_space_polygons"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer4_semantic_invariants"]["violations_count"],
            1,
        )
        self.assertEqual(
            summary["layer_audits"]["layer4_semantic_invariants"]["violation_details"][0]["type"],
            "UnboundedSpace",
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_degenerate_wall(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["walls"][0]["points"] = [[0.0, 0.0], [0.0, 0.0]]
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer3_topology_and_graph"]["degenerate_walls"],
            1,
        )
        self.assertFalse(summary["summary"]["structural_validation_passed"])
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_rejects_non_reciprocal_neighbors(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"][0]["neighbors"] = ["space-2"]
        bim_data["spaces"].append(
            {
                "uuid": "space-2",
                "boundary": [[100.0, 0.0], [200.0, 0.0], [200.0, 100.0], [100.0, 100.0]],
                "area": 10000.0,
                "related_walls": ["wall-1"],
                "related_windows": [],
                "related_columns": [],
                "related_doors": [],
                "neighbors": [],
            }
        )
        summary, _ = _run_validation(bim_data)

        self.assertEqual(
            summary["layer_audits"]["layer4_semantic_invariants"]["violations_count"],
            1,
        )
        self.assertFalse(summary["summary"]["validation_passed"])

    def test_run_validation_accepts_empty_optional_space_reference_collections(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"][0]["related_windows"] = []
        bim_data["spaces"][0]["related_columns"] = []
        bim_data["spaces"][0]["related_doors"] = []
        bim_data["spaces"][0]["neighbors"] = []
        bim_data["doors"] = []
        bim_data["windows"] = []

        summary, report_text = _run_validation(bim_data)

        self.assertTrue(summary["summary"]["validation_passed"])
        self.assertEqual(summary["opening_metrics"]["total_openings"], 0)
        self.assertIn("**Total Openings (Doors + Windows):** 0", report_text)

    def test_run_validation_accepts_zero_openings_and_generates_report_metrics(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["doors"] = []
        bim_data["windows"] = []
        bim_data["spaces"][0]["related_doors"] = []
        bim_data["spaces"][0]["related_windows"] = []

        summary, report_text = _run_validation(bim_data)

        self.assertTrue(summary["summary"]["validation_passed"])
        self.assertEqual(summary["opening_metrics"]["total_openings"], 0)
        self.assertEqual(summary["opening_metrics"]["correctly_associated"], 0)
        self.assertEqual(summary["opening_metrics"]["association_accuracy"], 1.0)
        self.assertIn("**Total Openings (Doors + Windows):** 0", report_text)

    def test_run_validation_accepts_zero_spaces_and_generates_report_metrics(self):
        bim_data = _build_valid_canonical_bim()
        bim_data["spaces"] = []
        bim_data["walls"][0]["related_spaces"] = []

        summary, report_text = _run_validation(bim_data)

        self.assertTrue(summary["summary"]["validation_passed"])
        self.assertEqual(summary["space_metrics"]["extracted_spaces_count"], 0)
        self.assertEqual(summary["space_metrics"]["ground_truth_spaces_count"], 0)
        self.assertEqual(summary["space_metrics"]["closure_rate"], 1.0)
        self.assertEqual(summary["space_metrics"]["mean_iou"], 1.0)
        self.assertIn("**Extracted Spaces:** 0", report_text)

    def test_run_validation_is_deterministic_for_identical_canonical_input(self):
        bim_data = _build_valid_canonical_bim()

        with tempfile.TemporaryDirectory() as temp_dir:
            bim_model_path = os.path.join(temp_dir, "bim_model.json")
            with open(bim_model_path, "w", encoding="utf-8") as f:
                json.dump(bim_data, f, indent=2)

            pipeline = P2ValidationPipeline()
            summary_a = pipeline.run_validation(
                bim_model_path=bim_model_path,
                output_json_path=os.path.join(temp_dir, "summary_a.json"),
                output_report_path=os.path.join(temp_dir, "report_a.md"),
            )
            summary_b = pipeline.run_validation(
                bim_model_path=bim_model_path,
                output_json_path=os.path.join(temp_dir, "summary_b.json"),
                output_report_path=os.path.join(temp_dir, "report_b.md"),
            )

        self.assertEqual(summary_a["ssot_input_sha256"], summary_b["ssot_input_sha256"])
        self.assertEqual(summary_a["validation_seal_sha256"], summary_b["validation_seal_sha256"])
        self.assertEqual(summary_a["summary"], summary_b["summary"])


if __name__ == "__main__":
    unittest.main()