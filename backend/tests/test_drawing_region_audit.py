import hashlib
import csv
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

import ezdxf

from backend.drawing_region_audit import (
    EXPECTED_AB_VIEWS,
    AuditEntity,
    DrawingRegionAudit,
    _normalize_exact_text,
    _normalize_text,
)


def line(source_id, x1, y1, x2, y2):
    return AuditEntity(
        source_id,
        "LINE",
        "WALL",
        (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)),
        length=((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5,
        render_points=((x1, y1), (x2, y2)),
    )


def rectangle(prefix, x, y, size=1000):
    return [
        line(prefix + "-1", x, y, x + size, y),
        line(prefix + "-2", x + size, y, x + size, y + size),
        line(prefix + "-3", x, y + size, x + size, y + size),
        line(prefix + "-4", x, y, x, y + size),
    ]


def annotation(source_id, x, y, text):
    return AuditEntity(source_id, "TEXT", "NOTES", (x, y, x, y), "annotation", text)


def polyline(source_id, bounds, closed=True, layer="CERCEVE", points=None):
    min_x, min_y, max_x, max_y = bounds
    render_points = points or ((min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y))
    return AuditEntity(source_id, "LWPOLYLINE", layer, bounds, is_closed=closed, render_points=tuple(render_points))


def framed_cell(prefix, x, y, title, pool_second_title=None):
    entities = [
        polyline(f"{prefix}-frame-{inset}", (x + inset, y + inset, x + 2000 - inset, y + 1200 - inset))
        for inset in (0, 10, 20)
    ]
    if pool_second_title is None:
        entities.append(annotation(f"{prefix}-title", x + 1000, y + 1050, title))
        entities.extend(rectangle(f"{prefix}-geometry", x + 200, y + 200, 600))
    else:
        entities.extend([
            annotation(f"{prefix}-title-a", x + 1000, y + 300, title),
            annotation(f"{prefix}-title-b", x + 1000, y + 900, pool_second_title),
            AuditEntity(f"{prefix}-separator", "LINE", "CERCEVE", (x + 100, y + 600, x + 1900, y + 600), length=1800, render_points=((x + 100, y + 600), (x + 1900, y + 600))),
            line(f"{prefix}-geometry-a", x + 200, y + 200, x + 800, y + 200),
            line(f"{prefix}-geometry-b", x + 200, y + 800, x + 800, y + 800),
        ])
    return entities


def complete_source_view_catalog():
    entities = []
    titles = {
        "1.BODRUM KAT PLANI": "1.BODRUM KAT PLANI",
        "ZEMİN KAT PLANI": "ZEMİN KAT PLANI",
        "1.NORMAL KAT PLANI": "1.NORMAL KAT PLANI",
        "Ç.A.P. KAT PLANI": "Ç.A.P. KAT PLANI",
        "ÇATI PLANI": "ÇATI PLANI",
        "A-A KESİT": "A-A KESİT",
        "B-B KESİT": "B-B KESİT",
        "ÖN": "ÖN",
        "SOL YAN": "SOL YAN",
        "ARKA": "ARKA",
        "SAĞ YAN": "SAĞ YAN",
    }
    for scope_index, scope in enumerate(("A", "B")):
        for view_index, (_, view_name, _) in enumerate(EXPECTED_AB_VIEWS[:-1]):
            x = scope_index * 30000 + (view_index % 4) * 3000
            y = (view_index // 4) * 2000
            entities.extend(framed_cell(f"{scope}-{view_index}", x, y, f"{scope} BLOK {titles[view_name]} Ö:1/50"))
    entities.extend(framed_cell("pool", 15000, 7000, "A BLOK HAVUZ PROJESİ Ö:1/50", "B BLOK HAVUZ PROJESİ Ö:1/50"))
    for site_index in range(3):
        x, y = 50000 + site_index * 3000, 0
        entities.extend([
            polyline(f"site-{site_index}-outer", (x, y, x + 2000, y + 1200), closed=False),
            polyline(f"site-{site_index}-inner", (x + 20, y + 20, x + 1980, y + 1180)),
            annotation(f"site-{site_index}-title", x + 1000, y + 1050, "VAZİYET PLANI Ö:1/200"),
            line(f"site-{site_index}-geometry", x + 200, y + 200, x + 800, y + 200),
        ])
    entities.extend([
        line("crossing", 1990, 500, 2010, 500),
        line("unassigned", 90000, 90000, 91000, 90000),
    ])
    return entities


def comparison_fixture():
    entities = []
    views = []
    cases = {
        EXPECTED_AB_VIEWS[0][:2]: ("exact", (0, 0, 100, 100), (0, 0, 100, 100), ((10, 10), (30, 10)), ((10, 10), (30, 10))),
        EXPECTED_AB_VIEWS[1][:2]: ("translation-equivalent", (0, 200, 100, 300), (1000, 200, 1100, 300), ((10, 210), (30, 210)), ((1010, 210), (1030, 210))),
        EXPECTED_AB_VIEWS[2][:2]: ("mirror-candidate", (0, 400, 100, 500), (1000, 400, 1100, 500), ((10, 410), (30, 410)), ((1070, 410), (1090, 410))),
        EXPECTED_AB_VIEWS[3][:2]: ("different", (0, 600, 100, 700), (1000, 600, 1100, 700), ((10, 610), (30, 610)), ((1010, 610), (1040, 610))),
    }
    for ordinal, (drawing_type, view_name, _) in enumerate(EXPECTED_AB_VIEWS):
        case = cases.get((drawing_type, view_name))
        for scope in ("A", "B"):
            assigned = []
            bounds = (ordinal * 200, 1000, ordinal * 200 + 100, 1100)
            if case:
                _, left_bounds, right_bounds, left_points, right_points = case
                bounds = left_bounds if scope == "A" else right_bounds
                source_id = f"comparison-{ordinal}-{scope}"
                points = left_points if scope == "A" else right_points
                entities.append(line(source_id, *points[0], *points[1]))
                assigned = [source_id]
            views.append({
                "scope": scope, "drawing_type": drawing_type, "level_or_view_name": view_name,
                "view_id": f"view-{ordinal}-{scope}",
                "frame_bounds_mm": {"min_x": bounds[0], "min_y": bounds[1], "max_x": bounds[2], "max_y": bounds[3]},
                "assigned_entity_ids": assigned,
            })
    return {"status": "ready_for_review", "views": views}, entities, cases


class TestDrawingRegionAudit(unittest.TestCase):
    def setUp(self):
        self.audit = DrawingRegionAudit(min_structural_entities=4)

    def test_permutation_invariance_and_no_duplicate_assignment(self):
        entities = rectangle("a", 0, 0) + rectangle("b", 10000, 0)
        first, thresholds_a = self.audit.extract_candidates(entities)
        second, thresholds_b = self.audit.extract_candidates(list(reversed(entities)))
        self.assertEqual(thresholds_a, thresholds_b)
        self.assertEqual([[e.source_id for e in c.members] for c in first], [[e.source_id for e in c.members] for c in second])
        assigned = [entity.source_id for candidate in first for entity in candidate.members]
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_annotation_does_not_bridge_structural_regions(self):
        entities = rectangle("a", 0, 0) + rectangle("b", 10000, 0)
        entities.append(AuditEntity("text", "TEXT", "NOTES", (5000, 500, 5000, 500), "annotation", "SALON"))
        candidates, _ = self.audit.extract_candidates(entities)
        self.assertEqual(len(candidates), 2)

    def test_long_closed_frame_is_evidence_not_connectivity_bridge(self):
        entities = rectangle("a", 0, 0) + rectangle("b", 10000, 0)
        entities.append(AuditEntity("frame", "LWPOLYLINE", "ANY", (-1000, -1000, 12000, 2000), length=32000, is_closed=True))
        candidates, thresholds = self.audit.extract_candidates(entities)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(thresholds["bridge_context_entity_count"], 1)
        assigned = {entity.source_id for candidate in candidates for entity in candidate.members}
        self.assertNotIn("frame", assigned)

    def test_conflicting_drawing_labels_abstain(self):
        entities = rectangle("a", 0, 0) + [annotation("floor", 500, 500, "ZEMIN KAT"), annotation("section", 600, 500, "A-A KESIT")]
        candidates, _ = self.audit.extract_candidates(entities)
        result = self.audit._classify(candidates[0])
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual(result["ambiguity_reason"], "conflicting_drawing_type_evidence")

    def test_translation_invariance_of_segmentation_and_classification(self):
        original = rectangle("a", 0, 0) + rectangle("b", 10000, 0) + [annotation("label", 500, 500, "SALON")]
        translated = [
            AuditEntity(entity.source_id, entity.entity_type, entity.layer,
                        tuple(value + (25000 if index % 2 == 0 else -7000) for index, value in enumerate(entity.bounds)),
                        entity.role, entity.text, entity.length, entity.is_closed)
            for entity in original
        ]
        first, first_thresholds = self.audit.extract_candidates(original)
        second, second_thresholds = self.audit.extract_candidates(translated)
        self.assertEqual(first_thresholds, second_thresholds)
        self.assertEqual([len(candidate.members) for candidate in first], [len(candidate.members) for candidate in second])
        self.assertEqual([self.audit._classify(candidate) for candidate in first], [self.audit._classify(candidate) for candidate in second])

    def test_mm_normalized_equivalent_geometry_is_invariant(self):
        millimetres = rectangle("a", 0, 0, 1000) + rectangle("b", 10000, 0, 1000)
        source_centimetres = rectangle("a", 0, 0, 100) + rectangle("b", 1000, 0, 100)
        normalized = [
            AuditEntity(entity.source_id, entity.entity_type, entity.layer,
                        tuple(value * 10 for value in entity.bounds), entity.role, entity.text,
                        entity.length * 10, entity.is_closed)
            for entity in source_centimetres
        ]
        first, first_thresholds = self.audit.extract_candidates(millimetres)
        second, second_thresholds = self.audit.extract_candidates(normalized)
        self.assertEqual(first_thresholds, second_thresholds)
        self.assertEqual([[entity.source_id for entity in candidate.members] for candidate in first], [[entity.source_id for entity in candidate.members] for candidate in second])

    def test_weak_evidence_abstains(self):
        candidate, _ = self.audit.extract_candidates(rectangle("a", 0, 0))
        result = self.audit._classify(candidate[0])
        self.assertEqual(result["status"], "ambiguous")
        self.assertIsNone(result["predicted_type"])

    def test_turkish_normalization_preserves_evidence_and_has_lossy_matching_key(self):
        raw = "  ZEMI\u0307N\n  Ç.A.P.   KAT PLANI  "
        exact = _normalize_exact_text(raw)
        self.assertEqual(exact, "ZEMİN Ç.A.P. KAT PLANI")
        self.assertEqual(_normalize_text(exact), "ZEMIN C A P KAT PLANI")

    def test_complete_catalog_routes_exact_27_views_and_reports_ownership(self):
        entities = complete_source_view_catalog()
        result = self.audit.build_source_views(entities)
        self.assertEqual(result["status"], "ready_for_review")
        self.assertEqual(result["summary"], {
            "view_count": 27,
            "floor_plan_count": 8,
            "routing_type_counts": {"ELEVATION": 8, "FLOOR_PLAN": 8, "POOL_PROJECT": 2, "ROOF_PLAN": 2, "SECTION": 4, "SITE_PLAN": 3},
        })
        self.assertEqual(sum(view["scope"] in {"A", "B"} for view in result["views"]), 24)
        self.assertEqual(sum(view["scope"] == "site" for view in result["views"]), 3)
        self.assertEqual(len({view["view_id"] for view in result["views"]}), 27)
        self.assertEqual(result["assignment"]["multiply_assignable_entity_ids"], [])
        self.assertIn("crossing", result["assignment"]["crossing_entity_ids"])
        self.assertIn("unassigned", result["assignment"]["unassigned_entity_ids"])
        floor_assignments = [source_id for view in result["views"] if view["drawing_type"] == "FLOOR_PLAN" for source_id in view["assigned_entity_ids"]]
        self.assertEqual(len(floor_assignments), len(set(floor_assignments)))

    def test_catalog_missing_duplicate_and_pool_separator_conflicts_fail_closed(self):
        entities = complete_source_view_catalog()
        missing = [entity for entity in entities if entity.source_id != "A-0-title"]
        self.assertEqual(self.audit.build_source_views(missing)["reason"], "title_catalog_mismatch")
        duplicate = entities + [annotation("duplicate", 1000, 1050, "A BLOK 1.BODRUM KAT PLANI Ö:1/50")]
        self.assertEqual(self.audit.build_source_views(duplicate)["reason"], "title_catalog_mismatch")
        no_separator = [entity for entity in entities if entity.source_id != "pool-separator"]
        blocked = self.audit.build_source_views(no_separator)
        self.assertEqual(blocked["reason"], "frame_association_conflict")
        self.assertEqual(blocked["conflicts"][0]["reason"], "pool_separator_missing")

    def test_frame_reconstruction_rejects_unrelated_open_geometry(self):
        entities = complete_source_view_catalog()
        entities.append(polyline("unrelated-open", (70000, 0, 72000, 1200), closed=False))
        frames = self.audit._frame_candidates(entities)
        self.assertEqual(len(frames), 26)
        self.assertNotIn("unrelated-open", {source_id for frame in frames for source_id in frame.source_entity_ids})
        self.assertEqual(sum(frame.evidence == "open_cerceve_outer_with_closed_inset" for frame in frames), 3)

    def test_source_view_ids_are_permutation_and_translation_invariant(self):
        original = complete_source_view_catalog()
        translated = [
            AuditEntity(entity.source_id, entity.entity_type, entity.layer,
                        (entity.bounds[0] + 12345, entity.bounds[1] - 6789, entity.bounds[2] + 12345, entity.bounds[3] - 6789),
                        entity.role, entity.text, entity.length, entity.is_closed,
                        tuple((x + 12345, y - 6789) for x, y in entity.render_points), entity.root_source_id, entity.insert_ancestry)
            for entity in reversed(original)
        ]
        first = self.audit.build_source_views(original)
        second = self.audit.build_source_views(translated)
        self.assertEqual([view["view_id"] for view in first["views"]], [view["view_id"] for view in second["views"]])
        self.assertEqual([view["frame_id"] for view in first["views"]], [view["frame_id"] for view in second["views"]])

    def test_closed_entity_signature_is_start_vertex_and_orientation_invariant(self):
        points = ((0, 0), (10, 0), (10, 5), (0, 5))
        shifted = ((10, 5), (0, 5), (0, 0), (10, 0))
        reversed_shifted = tuple(reversed(shifted))
        entities = [polyline("a", (0, 0, 10, 5), points=variant, layer="WALL") for variant in (points, shifted, reversed_shifted)]
        signatures = [self.audit._entity_signature(entity) for entity in entities]
        self.assertEqual(signatures[0], signatures[1])
        self.assertEqual(signatures[0], signatures[2])

    def test_ab_comparison_classifies_all_allowed_outcomes_without_deduplication(self):
        source_views, entities, cases = comparison_fixture()
        comparisons = self.audit.compare_ab_views(source_views, entities)
        indexed = {(item["drawing_type"], item["level_or_view_name"]): item for item in comparisons}
        for key, (expected, *_unused) in cases.items():
            self.assertEqual(indexed[key]["classification"], expected)
        not_proven_key = EXPECTED_AB_VIEWS[4][:2]
        self.assertEqual(indexed[not_proven_key]["classification"], "not-proven")
        self.assertEqual(len(comparisons), 12)
        self.assertTrue(all(item["deduplication_performed"] is False for item in comparisons))

    def test_nested_insert_transforms_and_cycle_guard_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "nested.dxf"
            doc = ezdxf.new("R2013")
            doc.header["$INSUNITS"] = 4
            inner = doc.blocks.new("INNER")
            inner.add_line((0, 0), (10, 0), dxfattribs={"layer": "WALL"})
            outer = doc.blocks.new("OUTER")
            outer.add_blockref("INNER", (5, 0), dxfattribs={"xscale": 2, "yscale": 2})
            cycle_a = doc.blocks.new("CYCLE_A")
            cycle_b = doc.blocks.new("CYCLE_B")
            cycle_a.add_blockref("CYCLE_B", (0, 0))
            cycle_b.add_blockref("CYCLE_A", (0, 0))
            doc.modelspace().add_blockref("OUTER", (100, 200), dxfattribs={"rotation": 90})
            doc.modelspace().add_blockref("CYCLE_A", (0, 0))
            doc.saveas(source)
            first, first_metadata = self.audit.read_dxf(source)
            second, second_metadata = self.audit.read_dxf(source)
        self.assertEqual(first, second)
        self.assertEqual(first_metadata, second_metadata)
        transformed = next(entity for entity in first if entity.entity_type == "LINE")
        self.assertEqual(transformed.render_points, ((100.0, 205.0), (100.0, 225.0)))
        self.assertEqual(transformed.insert_ancestry, ("OUTER", "INNER"))
        self.assertEqual(first_metadata["ignored_entity_counts"]["INSERT_cycle_guard"], 1)

    def test_sha_guard_and_blocked_source_views_fail_before_artifact_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.dxf"
            output = Path(temporary) / "output"
            source.write_bytes(b"not-the-required-source")
            with mock.patch.object(self.audit, "read_dxf") as read_dxf:
                with self.assertRaisesRegex(RuntimeError, "Source SHA-256 mismatch"):
                    self.audit.run(source, output)
            read_dxf.assert_not_called()
            self.assertFalse(output.exists())

            with mock.patch.object(self.audit, "read_dxf", return_value=([], {"normalized_unit": "mm"})), \
                    mock.patch.object(self.audit, "write_artifacts") as write_artifacts:
                with self.assertRaisesRegex(RuntimeError, "BLOCKED_SOURCE_VIEW_ISOLATION"):
                    self.audit.run(source, output, required_source_sha=None)
            write_artifacts.assert_not_called()
            self.assertFalse(output.exists())

    def test_complete_catalog_qualifies_exactly_eight_isolated_floor_views(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        from backend.topology_validator import TopologyValidator
        original_validate = TopologyValidator.validate
        with mock.patch.object(TopologyValidator, "validate", autospec=True, side_effect=original_validate) as validate:
            qualification = self.audit.qualify_floor_topology(source_views, entities)
        floor_view_ids = {
            view["view_id"] for view in source_views["views"]
            if view["drawing_type"] == "FLOOR_PLAN"
        }
        self.assertEqual(len(qualification), 8)
        self.assertEqual(validate.call_count, 8)
        self.assertEqual({item["view_id"] for item in qualification}, floor_view_ids)
        self.assertTrue(all(item["assigned_source_entity_count"] >= 4 for item in qualification))
        self.assertTrue(all(item["geometry_input_entity_count"] >= 4 for item in qualification))
        self.assertTrue(all(item["input_segment_count"] >= 4 for item in qualification))
        self.assertTrue(all(item["downstream"] == {"executed": False} for item in qualification))
        self.assertTrue(all(set(item["configured_tolerances_unchanged"]) == {"snap_tolerance_mm", "min_segment_length_mm"} for item in qualification))
        self.assertTrue(all(item["status"] in {"VALIDATOR_PASS", "VALIDATOR_FAIL"} for item in qualification))

    def test_floor_qualification_default_preserves_legacy_baseline_shape(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)

        qualification = self.audit.qualify_floor_topology(source_views, entities)

        self.assertEqual(len(qualification), 8)
        self.assertTrue(all("baseline" not in item for item in qualification))
        self.assertTrue(all("candidate" not in item for item in qualification))

    def test_candidate_handoff_uses_exact_assigned_source_entities_and_preserves_physical_graph(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        entity_by_id = {entity.source_id: entity for entity in entities}
        captured_sources = []

        def capture_generation(_graph, sources, tolerance_mm=5.0):
            captured_sources.append(list(sources))
            return {"logical_connectors": [], "rejections": []}

        with mock.patch(
            "backend.transient_boundary_connectors.generate_logical_connectors",
            side_effect=capture_generation,
        ):
            qualification = self.audit.qualify_floor_topology(
                source_views, entities, include_transient_connectors=True
            )

        floor_views = sorted(
            (view for view in source_views["views"] if view["drawing_type"] == "FLOOR_PLAN"),
            key=lambda view: view["view_id"],
        )
        captured_by_ids = sorted(
            ([entity.source_id for entity in sources] for sources in captured_sources)
        )
        expected_by_ids = sorted(
            ([source_id for source_id in view["assigned_entity_ids"] if source_id in entity_by_id]
             for view in floor_views)
        )
        self.assertEqual(captured_by_ids, expected_by_ids)
        self.assertEqual(len(qualification), 8)
        self.assertTrue(all(item["candidate"]["physical_graph_unchanged"] for item in qualification))
        self.assertTrue(all(item["candidate"]["logical_connectors"] == [] for item in qualification))
        self.assertTrue(all("logical_connectors" not in item["baseline"] for item in qualification))

    def test_candidate_qualification_is_source_permutation_deterministic(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)

        first = self.audit.qualify_floor_topology(
            source_views, entities, include_transient_connectors=True
        )
        second = self.audit.qualify_floor_topology(
            source_views, list(reversed(entities)), include_transient_connectors=True
        )

        self.assertEqual(first, second)
        self.assertTrue(all(item["baseline"]["snapshot_sha256"] for item in first))
        self.assertTrue(all(item["candidate"]["snapshot_sha256"] for item in first))

    def test_candidate_qualification_keeps_baseline_physical_and_candidate_effective_health_separate(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        observed_graph_keys = []

        def health_report(graph):
            observed_graph_keys.append(set(graph))
            candidate = "logical_connectors" in graph
            return {
                "timestamp": "ignored",
                "status": "WARNING",
                "counts": {
                    "nodes": 10,
                    "edges": 8,
                    "loops": 0,
                    **({"physical_edges": 8, "logical_connectors": 2, "effective_edges": 10} if candidate else {}),
                },
                "graph_metrics": {
                    "connected_components": 3 if candidate else 4,
                    "dangling_node_count": 2 if candidate else 6,
                },
                "loop_metrics": {},
                "checks": {},
                "issues": [],
                "diagnostics": [],
            }

        with mock.patch(
            "backend.transient_boundary_connectors.generate_logical_connectors",
            return_value={"logical_connectors": [], "rejections": []},
        ), mock.patch(
            "backend.topology_health_report.TopologyHealthReporter.build_report",
            autospec=True,
            side_effect=lambda _reporter, graph: health_report(graph),
        ):
            qualification = self.audit.qualify_floor_topology(
                source_views, entities, include_transient_connectors=True
            )

        self.assertEqual(len(observed_graph_keys), 16)
        self.assertTrue(all("logical_connectors" not in keys for keys in observed_graph_keys[0::2]))
        self.assertTrue(all("logical_connectors" in keys for keys in observed_graph_keys[1::2]))
        self.assertTrue(all(item["baseline"]["health"]["graph_metrics"]["connected_components"] == 4 for item in qualification))
        self.assertTrue(all(item["baseline"]["health"]["graph_metrics"]["dangling_node_count"] == 6 for item in qualification))
        self.assertTrue(all(item["candidate"]["health"]["graph_metrics"]["connected_components"] == 3 for item in qualification))
        self.assertTrue(all(item["candidate"]["health"]["graph_metrics"]["dangling_node_count"] == 2 for item in qualification))
        self.assertTrue(all("timestamp" not in item["candidate"]["health"] for item in qualification))

    def test_build_report_enables_transient_connector_candidate_qualification(self):
        entities = complete_source_view_catalog()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.dxf"
            source.write_bytes(b"read-only-test-source")
            with mock.patch.object(
                self.audit, "qualify_floor_topology", return_value=[]
            ) as qualify:
                self.audit.build_report(source, entities, {"normalized_unit": "mm"})

        source_views = self.audit.build_source_views(entities)
        qualify.assert_called_once_with(
            source_views, entities, include_transient_connectors=True
        )

    def test_geometry_adapter_preserves_actual_assigned_sources_without_fallback(self):
        entities = {
            "actual-line": line("actual-line", 10, 20, 30, 40),
            "unsupported": AuditEntity("unsupported", "CIRCLE", "WALL", (0, 0, 2, 2)),
        }
        view = {
            "assigned_entity_ids": ["actual-line", "unsupported", "missing"],
            "frame_bounds_mm": {"min_x": 0, "min_y": 0, "max_x": 100, "max_y": 100},
        }
        payload, rejected = self.audit._geometry_input(view, entities)
        self.assertEqual([item["source_id"] for item in payload["entities"]], ["actual-line"])
        self.assertEqual(payload["entities"][0]["start"], {"x": 10.0, "y": 20.0})
        self.assertEqual(payload["entities"][0]["end"], {"x": 30.0, "y": 40.0})
        self.assertEqual(rejected, {"missing_source_entity": 1, "unsupported_CIRCLE": 1})

    def test_floor_qualification_is_deterministic_and_does_not_write_global_outputs(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        watched = [Path("outputs") / name for name in ("dxf_raw.json", "walls_clean.json", "topology_graph.json", "topology_validation_report.json")]
        before = {path: path.read_bytes() if path.exists() else None for path in watched}
        first = self.audit.qualify_floor_topology(source_views, entities)
        second = self.audit.qualify_floor_topology(source_views, list(reversed(entities)))
        self.assertEqual(first, second)
        self.assertEqual(before, {path: path.read_bytes() if path.exists() else None for path in watched})

    def test_floor_qualification_reports_validator_failure_without_downstream_execution(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        from backend.topology_validator import TopologyValidationError, TopologyValidator
        with mock.patch.object(TopologyValidator, "validate", side_effect=TopologyValidationError("forced validator failure")) as validate:
            qualification = self.audit.qualify_floor_topology(source_views, entities)
        self.assertEqual(validate.call_count, 8)
        self.assertTrue(all(item["status"] == "VALIDATOR_FAIL" for item in qualification))
        self.assertTrue(all(item["failed_checks"] == ["forced validator failure"] for item in qualification))
        self.assertTrue(all(item["node_count"] > 0 and item["downstream"] == {"executed": False} for item in qualification))

    def test_floor_qualification_reports_not_evaluated_before_validator(self):
        entities = complete_source_view_catalog()
        source_views = self.audit.build_source_views(entities)
        from backend.geometry_engine import GeometryEngine
        from backend.topology_validator import TopologyValidator
        with mock.patch.object(GeometryEngine, "run", side_effect=RuntimeError("forced geometry failure")), \
                mock.patch.object(TopologyValidator, "validate") as validate:
            qualification = self.audit.qualify_floor_topology(source_views, entities)
        validate.assert_not_called()
        self.assertTrue(all(item["status"] == "NOT_EVALUATED" for item in qualification))
        self.assertTrue(all(item["failed_checks"] == ["Pipeline not evaluated: RuntimeError: forced geometry failure"] for item in qualification))
        self.assertTrue(all(item["node_count"] == item["edge_count"] == item["loop_count"] == 0 for item in qualification))
        self.assertTrue(all(item["geometry_sha256"] == "" and item["downstream"] == {"executed": False} for item in qualification))

    def test_source_view_review_svg_contains_geometry_frames_and_exact_metadata(self):
        entities = complete_source_view_catalog()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.dxf"
            source.write_bytes(b"read-only-test-source")
            report = self.audit.build_report(source, entities, {"normalized_unit": "mm"})
        svg = self.audit._source_views_svg(report)
        root = ET.fromstring(svg)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        geometry = root.find("svg:g[@id='source-geometry']", namespace)
        frames = root.find("svg:g[@id='detected-frames']", namespace)
        legend = root.find("svg:g[@id='source-view-legend']", namespace)
        self.assertIsNotNone(geometry)
        self.assertIsNotNone(frames)
        self.assertIsNotNone(legend)
        self.assertGreater(len(list(geometry)), 0)
        self.assertEqual(len(frames.findall("svg:rect", namespace)), 27)
        legend_text = " ".join(node.text or "" for node in legend.findall("svg:text", namespace))
        for view in report["source_views"]["views"]:
            self.assertIn(view["view_id"], legend_text)
            self.assertIn(view["exact_normalized_title"], legend_text)
            self.assertIn(view["drawing_type"], legend_text)
            self.assertIn(view["routing_role"], legend_text)
        self.assertIn('stroke-opacity="0.18"', svg)

    def test_repeated_artifacts_are_byte_identical(self):
        entities = rectangle("a", 0, 0)
        metadata = {"insunits": 4, "normalized_unit": "mm"}
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.dxf"
            source.write_bytes(b"read-only-test-source")
            report = self.audit.build_report(source, entities, metadata)
            output_a, output_b = Path(temporary) / "a", Path(temporary) / "b"
            self.audit.write_artifacts(report, output_a)
            self.audit.write_artifacts(report, output_b)
            artifact_names = ("regions.json", "regions.svg", "region_evidence.csv", "source_views.json", "source_views.csv", "source_views.xml", "source_views.svg", "manifest.json")
            for name in artifact_names:
                digest_a = hashlib.sha256((output_a / name).read_bytes()).hexdigest()
                digest_b = hashlib.sha256((output_b / name).read_bytes()).hexdigest()
                self.assertEqual(digest_a, digest_b, name)
            manifest = json.loads((output_a / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(set(manifest["files"]), set(artifact_names) - {"manifest.json"})
            json.loads((output_a / "source_views.json").read_text(encoding="utf-8"))
            list(csv.reader(io.StringIO((output_a / "source_views.csv").read_text(encoding="utf-8"))))
            ET.parse(output_a / "source_views.xml")
            ET.parse(output_a / "source_views.svg")
            for name, evidence in manifest["files"].items():
                payload = (output_a / name).read_bytes()
                self.assertEqual(evidence["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(evidence["size_bytes"], len(payload))

    def test_svg_renders_geometry_and_keeps_labels_in_legend(self):
        entities = rectangle("a", 0, 0) + [annotation("label", 500, 500, "ZEMIN KAT")]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.dxf"
            source.write_bytes(b"read-only-test-source")
            report = self.audit.build_report(source, entities, {"normalized_unit": "mm"})
            svg = self.audit._svg(report)
            root = ET.fromstring(svg)
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            drawing = root.find("svg:g[@id='drawing-geometry']", namespace)
            legend = root.find("svg:g[@id='region-legend']", namespace)
            self.assertIsNotNone(drawing)
            self.assertIsNotNone(legend)
            self.assertEqual(len(drawing.findall(".//svg:polyline", namespace)), 4)
            self.assertEqual(len(drawing.findall(".//svg:text", namespace)), 0)
            self.assertGreater(len(legend.findall("svg:text", namespace)), 1)


if __name__ == "__main__":
    unittest.main()