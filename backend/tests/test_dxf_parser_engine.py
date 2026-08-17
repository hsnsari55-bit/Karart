import os
import unittest
from unittest import mock
import ezdxf
from ezdxf.layouts import Modelspace

from backend.dxf_parser import DXFParser

class TestDXFParserEngine(unittest.TestCase):
    def setUp(self):
        self.parser = DXFParser()
        self.test_dir = "backend/tests/fixtures"
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_dxf_path = os.path.join(self.test_dir, "test_basic.dxf")
        self.single_line_dxf_path = os.path.join(self.test_dir, "test_single_line.dxf")
        self.block_only_dxf_path = os.path.join(self.test_dir, "test_block_only.dxf")
        self.nested_block_dxf_path = os.path.join(self.test_dir, "test_nested_block.dxf")
        self.hatch_dxf_path = os.path.join(self.test_dir, "test_hatch.dxf")
        self.truncated_dxf_path = os.path.join(self.test_dir, "test_truncated_recoverable.dxf")
        self.truncated_nested_block_dxf_path = os.path.join(self.test_dir, "test_truncated_nested_block.dxf")
        self.truncated_multi_candidate_dxf_path = os.path.join(self.test_dir, "test_truncated_multi_candidate.dxf")
        self.create_test_dxf(self.test_dxf_path)
        self.create_single_line_dxf(self.single_line_dxf_path)
        self.create_block_only_dxf(self.block_only_dxf_path)
        self.create_nested_block_dxf(self.nested_block_dxf_path)
        self.create_hatch_dxf(self.hatch_dxf_path)
        self.create_truncated_recoverable_dxf(self.truncated_dxf_path)
        self.create_truncated_nested_block_dxf(self.truncated_nested_block_dxf_path)
        self.create_truncated_multi_candidate_dxf(self.truncated_multi_candidate_dxf_path)

    def create_test_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters
        msp = doc.modelspace()
        # Add basic entities
        msp.add_line((0, 0), (10, 10), dxfattribs={'layer': 'Walls'})
        msp.add_circle((5, 5), radius=2, dxfattribs={'layer': 'Columns'})
        
        # Create a block
        block = doc.blocks.new(name="TEST_BLOCK")
        block.add_line((0, 0), (5, 0), dxfattribs={'layer': 'BlockWall'})
        
        # Insert the block, scaled and rotated
        msp.add_blockref("TEST_BLOCK", (10, 10), dxfattribs={
            'xscale': 2, 'yscale': 2, 'rotation': 90
        })
        
        doc.saveas(filepath)

    def create_single_line_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters
        msp = doc.modelspace()
        msp.add_line((100, 200), (110, 220), dxfattribs={'layer': 'Walls'})
        doc.saveas(filepath)

    def create_block_only_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters

        block = doc.blocks.new(name="PLAN_BLOCK")
        block.add_line((0, 0), (2500, 0), dxfattribs={'layer': 'BlockWall'})
        block.add_line((2500, 0), (2500, 1500), dxfattribs={'layer': 'BlockWall'})

        doc.saveas(filepath)

    def create_nested_block_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters

        inner_block = doc.blocks.new(name="INNER_GEOM")
        inner_block.add_line((0, 0), (1000, 0), dxfattribs={'layer': 'InnerWall'})
        inner_block.add_line((1000, 0), (1000, 500), dxfattribs={'layer': 'InnerWall'})

        outer_block = doc.blocks.new(name="FILTER_PLAN")
        outer_block.add_blockref(
            "INNER_GEOM",
            (250, 750),
            dxfattribs={'xscale': 2, 'yscale': 2, 'rotation': 90},
        )

        doc.saveas(filepath)

    def create_hatch_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters
        msp = doc.modelspace()

        hatch = msp.add_hatch(color=7, dxfattribs={'layer': 'Tarama'})
        hatch.paths.add_polyline_path(
            [(0, 0), (2000, 0), (2000, 1000), (0, 1000)],
            is_closed=True,
        )

        doc.saveas(filepath)

    def create_truncated_recoverable_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 0), dxfattribs={'layer': 'Walls'})
        doc.saveas(filepath)

        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()

        with open(filepath, 'w', encoding='latin-1') as f:
            f.write(content[:-40])

    def create_truncated_nested_block_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters

        inner_block = doc.blocks.new(name="INNER_RECOVER_GEOM")
        inner_block.add_line((0, 0), (1000, 0), dxfattribs={'layer': 'InnerWall'})
        inner_block.add_line((1000, 0), (1000, 500), dxfattribs={'layer': 'InnerWall'})

        outer_block = doc.blocks.new(name="RECOVER_FILTER_PLAN")
        outer_block.add_blockref(
            "INNER_RECOVER_GEOM",
            (250, 750),
            dxfattribs={'xscale': 2, 'yscale': 2, 'rotation': 90},
        )

        doc.saveas(filepath)

        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()

        with open(filepath, 'w', encoding='latin-1') as f:
            f.write(content[:-40])

    def create_truncated_multi_candidate_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
        doc.header['$INSUNITS'] = 4  # Millimeters

        decoy_block = doc.blocks.new(name="DETAIL_BLOCK")
        decoy_block.add_line((0, 0), (50, 0), dxfattribs={'layer': 'Decoy'})
        decoy_block.add_line((50, 0), (50, 50), dxfattribs={'layer': 'Decoy'})
        decoy_block.add_line((50, 50), (0, 50), dxfattribs={'layer': 'Decoy'})

        inner_block = doc.blocks.new(name="INNER_HEURISTIC_GEOM")
        inner_block.add_line((0, 0), (1200, 0), dxfattribs={'layer': 'InnerWall'})
        inner_block.add_line((1200, 0), (1200, 400), dxfattribs={'layer': 'InnerWall'})

        winning_block = doc.blocks.new(name="MIMARI_PLAN_MAIN")
        winning_block.add_blockref(
            "INNER_HEURISTIC_GEOM",
            (100, 200),
            dxfattribs={'xscale': 1.5, 'yscale': 1.5, 'rotation': 180},
        )

        doc.saveas(filepath)

        with open(filepath, 'r', encoding='latin-1') as f:
            content = f.read()

        with open(filepath, 'w', encoding='latin-1') as f:
            f.write(content[:-40])

    def assert_parse_results_equal(self, first_result, second_result):
        self.assertEqual(first_result["source_file"], second_result["source_file"])
        self.assertEqual(first_result["metadata"], second_result["metadata"])
        self.assertEqual(first_result["bounding_box"], second_result["bounding_box"])
        self.assertEqual(first_result["entities"], second_result["entities"])

    def test_parser_basic_entities(self):
        res = self.parser.parse(self.test_dxf_path)
        entities = res.get("entities", [])
        
        self.assertTrue(len(entities) > 0)
        
        lines = [e for e in entities if e["type"] == "LINE"]
        self.assertTrue(len(lines) >= 1)
        
        polylines = [e for e in entities if e["type"] == "LWPOLYLINE"]
        self.assertTrue(len(polylines) >= 1) # The circle and the block line (if exploded to polyline? No, block line is LINE)
        
        block_lines = [e for e in lines if e.get("block_name") == "TEST_BLOCK"]
        self.assertEqual(len(block_lines), 1)
        
        # Verify the block line was transformed (scaled by 2, rotated 90, translated to 10,10)
        # Original line: (0,0) to (5,0)
        # Transformed: (10,10) to (10, 20)
        b_line = block_lines[0]
        self.assertAlmostEqual(b_line["start"]["x"], 10.0, places=3)
        self.assertAlmostEqual(b_line["start"]["y"], 10.0, places=3)
        self.assertAlmostEqual(b_line["end"]["x"], 10.0, places=3)
        self.assertAlmostEqual(b_line["end"]["y"], 20.0, places=3)

    def test_parse_resets_skipped_entities_between_runs(self):
        original_process_entity = self.parser._process_entity

        def skip_every_entity(entity, block_name="default", scale_factor=1.0):
            self.parser.skipped_entities += 1

        self.parser._process_entity = skip_every_entity
        first_result = self.parser.parse(self.test_dxf_path)

        self.assertGreater(first_result["metadata"]["skipped_entities"], 0)

        self.parser._process_entity = original_process_entity
        second_result = self.parser.parse(self.test_dxf_path)

        self.assertEqual(second_result["metadata"]["skipped_entities"], 0)
        self.assertGreater(len(second_result.get("entities", [])), 0)

    def test_parse_resets_entities_and_bounds_between_runs(self):
        first_result = self.parser.parse(self.test_dxf_path)
        self.assertGreater(len(first_result.get("entities", [])), 1)

        second_result = self.parser.parse(self.single_line_dxf_path)
        second_entities = second_result.get("entities", [])

        self.assertEqual(len(second_entities), 1)
        self.assertEqual(second_entities[0]["type"], "LINE")
        self.assertAlmostEqual(second_entities[0]["start"]["x"], 100.0, places=3)
        self.assertAlmostEqual(second_entities[0]["start"]["y"], 200.0, places=3)
        self.assertAlmostEqual(second_entities[0]["end"]["x"], 110.0, places=3)
        self.assertAlmostEqual(second_entities[0]["end"]["y"], 220.0, places=3)

        bbox = second_result["bounding_box"]
        self.assertAlmostEqual(bbox["min_x"], 100.0, places=3)
        self.assertAlmostEqual(bbox["min_y"], 200.0, places=3)
        self.assertAlmostEqual(bbox["max_x"], 110.0, places=3)
        self.assertAlmostEqual(bbox["max_y"], 220.0, places=3)
        self.assertEqual(second_result["metadata"]["skipped_entities"], 0)

    def test_parse_reuses_parser_without_leaking_block_promotion_metadata(self):
        self.parser.parse(self.test_dxf_path)

        first_result = self.parser.parse(self.block_only_dxf_path)
        second_result = self.parser.parse(self.block_only_dxf_path)

        self.assertEqual(first_result["metadata"]["promoted_block"], "PLAN_BLOCK")
        self.assertEqual(first_result["metadata"]["promotion_reason"], "heuristic_score")
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertEqual(len(first_result.get("entities", [])), 2)
        self.assertTrue(all(entity.get("block_name") == "PLAN_BLOCK" for entity in first_result["entities"]))
        self.assert_parse_results_equal(first_result, second_result)

    def test_parse_reuses_parser_without_leaking_hatch_output_between_runs(self):
        self.parser.parse(self.single_line_dxf_path)

        first_result = self.parser.parse(self.hatch_dxf_path)
        second_result = self.parser.parse(self.hatch_dxf_path)

        self.assertIsNone(first_result["metadata"]["promoted_block"])
        self.assertIsNone(first_result["metadata"]["promotion_reason"])
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertGreater(len(first_result.get("entities", [])), 0)
        self.assertTrue(
            all(
                entity["type"] == "LWPOLYLINE" and entity.get("closed") is True
                for entity in first_result["entities"]
            )
        )
        self.assert_parse_results_equal(first_result, second_result)

    def test_parse_reuses_parser_with_block_filter_on_nested_blocks(self):
        self.parser.parse(self.test_dxf_path)

        first_result = self.parser.parse(self.nested_block_dxf_path, block_filter="FILTER_PLAN")
        second_result = self.parser.parse(self.nested_block_dxf_path, block_filter="FILTER_PLAN")

        self.assertEqual(first_result["metadata"]["promoted_block"], "FILTER_PLAN")
        self.assertEqual(first_result["metadata"]["promotion_reason"], "filter_match")
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertEqual(len(first_result.get("entities", [])), 2)
        self.assertTrue(all(entity.get("block_name") == "INNER_GEOM" for entity in first_result["entities"]))

        bbox = first_result["bounding_box"]
        self.assertAlmostEqual(bbox["min_x"], -750.0, places=3)
        self.assertAlmostEqual(bbox["min_y"], 750.0, places=3)
        self.assertAlmostEqual(bbox["max_x"], 250.0, places=3)
        self.assertAlmostEqual(bbox["max_y"], 2750.0, places=3)

        self.assert_parse_results_equal(first_result, second_result)

    def test_parse_reuses_parser_with_truncated_dxf_recover_fallback(self):
        self.parser.parse(self.test_dxf_path)

        first_result = self.parser.parse(self.truncated_dxf_path)
        second_result = self.parser.parse(self.truncated_dxf_path)

        self.assertEqual(first_result["metadata"]["promoted_block"], None)
        self.assertEqual(first_result["metadata"]["promotion_reason"], None)
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertEqual(len(first_result.get("entities", [])), 1)

        line = first_result["entities"][0]
        self.assertEqual(line["type"], "LINE")
        self.assertAlmostEqual(line["start"]["x"], 0.0, places=3)
        self.assertAlmostEqual(line["start"]["y"], 0.0, places=3)
        self.assertAlmostEqual(line["end"]["x"], 100.0, places=3)
        self.assertAlmostEqual(line["end"]["y"], 0.0, places=3)

        bbox = first_result["bounding_box"]
        self.assertAlmostEqual(bbox["min_x"], 0.0, places=3)
        self.assertAlmostEqual(bbox["min_y"], 0.0, places=3)
        self.assertAlmostEqual(bbox["max_x"], 100.0, places=3)
        self.assertAlmostEqual(bbox["max_y"], 0.0, places=3)

        self.assert_parse_results_equal(first_result, second_result)

    def test_parse_reuses_parser_with_truncated_nested_block_filter_recover_fallback(self):
        self.parser.parse(self.test_dxf_path)

        first_result = self.parser.parse(
            self.truncated_nested_block_dxf_path,
            block_filter="RECOVER_FILTER_PLAN",
        )
        second_result = self.parser.parse(
            self.truncated_nested_block_dxf_path,
            block_filter="RECOVER_FILTER_PLAN",
        )

        self.assertEqual(first_result["metadata"]["promoted_block"], "RECOVER_FILTER_PLAN")
        self.assertEqual(first_result["metadata"]["promotion_reason"], "filter_match")
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertEqual(len(first_result.get("entities", [])), 2)
        self.assertTrue(
            all(entity.get("block_name") == "INNER_RECOVER_GEOM" for entity in first_result["entities"])
        )

        bbox = first_result["bounding_box"]
        self.assertAlmostEqual(bbox["min_x"], -750.0, places=3)
        self.assertAlmostEqual(bbox["min_y"], 750.0, places=3)
        self.assertAlmostEqual(bbox["max_x"], 250.0, places=3)
        self.assertAlmostEqual(bbox["max_y"], 2750.0, places=3)

        self.assert_parse_results_equal(first_result, second_result)

    def test_parse_reuses_parser_with_truncated_multi_candidate_heuristic_recover_fallback(self):
        self.parser.parse(self.test_dxf_path)

        first_result = self.parser.parse(self.truncated_multi_candidate_dxf_path)
        second_result = self.parser.parse(self.truncated_multi_candidate_dxf_path)

        self.assertEqual(first_result["metadata"]["promoted_block"], "MIMARI_PLAN_MAIN")
        self.assertEqual(first_result["metadata"]["promotion_reason"], "heuristic_score")
        self.assertEqual(first_result["metadata"]["skipped_entities"], 0)
        self.assertEqual(len(first_result.get("entities", [])), 2)
        self.assertTrue(
            all(entity.get("block_name") == "INNER_HEURISTIC_GEOM" for entity in first_result["entities"])
        )

        first_line = first_result["entities"][0]
        second_line = first_result["entities"][1]
        self.assertEqual(first_line["type"], "LINE")
        self.assertEqual(second_line["type"], "LINE")
        self.assertAlmostEqual(first_line["start"]["x"], -1700.0, places=3)
        self.assertAlmostEqual(first_line["start"]["y"], 200.0, places=3)
        self.assertAlmostEqual(first_line["end"]["x"], -1700.0, places=3)
        self.assertAlmostEqual(first_line["end"]["y"], -400.0, places=3)
        self.assertAlmostEqual(second_line["start"]["x"], 100.0, places=3)
        self.assertAlmostEqual(second_line["start"]["y"], 200.0, places=3)
        self.assertAlmostEqual(second_line["end"]["x"], -1700.0, places=3)
        self.assertAlmostEqual(second_line["end"]["y"], 200.0, places=3)

        bbox = first_result["bounding_box"]
        self.assertAlmostEqual(bbox["min_x"], -1700.0, places=3)
        self.assertAlmostEqual(bbox["min_y"], -400.0, places=3)
        self.assertAlmostEqual(bbox["max_x"], 100.0, places=3)
        self.assertAlmostEqual(bbox["max_y"], 200.0, places=3)

        self.assert_parse_results_equal(first_result, second_result)

    def test_truncated_block_repair_is_retained_when_original_recover_has_no_geometry(self):
        empty_recovered_doc = ezdxf.new(dxfversion='R2010')

        with mock.patch(
            "ezdxf.recover.readfile",
            return_value=(empty_recovered_doc, mock.Mock()),
        ):
            first_result = self.parser.parse(
                self.truncated_nested_block_dxf_path,
                block_filter="RECOVER_FILTER_PLAN",
            )
            second_result = self.parser.parse(
                self.truncated_nested_block_dxf_path,
                block_filter="RECOVER_FILTER_PLAN",
            )

        self.assertEqual(first_result["metadata"]["promoted_block"], "RECOVER_FILTER_PLAN")
        self.assertEqual(first_result["metadata"]["promotion_reason"], "filter_match")
        self.assertEqual(len(first_result["entities"]), 2)
        self.assertTrue(
            all(entity.get("block_name") == "INNER_RECOVER_GEOM" for entity in first_result["entities"])
        )
        self.assert_parse_results_equal(first_result, second_result)

    def tearDown(self):
        if os.path.exists(self.test_dxf_path):
            os.remove(self.test_dxf_path)
        if os.path.exists(self.single_line_dxf_path):
            os.remove(self.single_line_dxf_path)
        if os.path.exists(self.block_only_dxf_path):
            os.remove(self.block_only_dxf_path)
        if os.path.exists(self.nested_block_dxf_path):
            os.remove(self.nested_block_dxf_path)
        if os.path.exists(self.hatch_dxf_path):
            os.remove(self.hatch_dxf_path)
        if os.path.exists(self.truncated_dxf_path):
            os.remove(self.truncated_dxf_path)
        if os.path.exists(self.truncated_nested_block_dxf_path):
            os.remove(self.truncated_nested_block_dxf_path)
        if os.path.exists(self.truncated_multi_candidate_dxf_path):
            os.remove(self.truncated_multi_candidate_dxf_path)
        truncated_repaired_path = self.truncated_dxf_path + ".repaired.dxf"
        if os.path.exists(truncated_repaired_path):
            os.remove(truncated_repaired_path)
        truncated_nested_repaired_path = self.truncated_nested_block_dxf_path + ".repaired.dxf"
        if os.path.exists(truncated_nested_repaired_path):
            os.remove(truncated_nested_repaired_path)
        truncated_multi_candidate_repaired_path = self.truncated_multi_candidate_dxf_path + ".repaired.dxf"
        if os.path.exists(truncated_multi_candidate_repaired_path):
            os.remove(truncated_multi_candidate_repaired_path)

if __name__ == '__main__':
    unittest.main()
