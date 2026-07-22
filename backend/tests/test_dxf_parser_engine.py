import os
import unittest
import ezdxf
from ezdxf.layouts import Modelspace

from backend.dxf_parser import DXFParser

class TestDXFParserEngine(unittest.TestCase):
    def setUp(self):
        self.parser = DXFParser()
        self.test_dir = "backend/tests/fixtures"
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_dxf_path = os.path.join(self.test_dir, "test_basic.dxf")
        self.create_test_dxf(self.test_dxf_path)

    def create_test_dxf(self, filepath):
        doc = ezdxf.new(dxfversion='R2010')
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

    def tearDown(self):
        if os.path.exists(self.test_dxf_path):
            os.remove(self.test_dxf_path)

if __name__ == '__main__':
    unittest.main()
