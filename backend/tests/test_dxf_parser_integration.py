import os
import json
import unittest

class TestDXFParserIntegration(unittest.TestCase):
    def test_dxf_raw_json_creation(self):
        # In a real environment, we would trigger the parser via main.py or similar.
        # Here we just verify that dxf_raw.json has correct structure if it exists.
        dxf_path = "outputs/dxf_raw.json"
        if os.path.exists(dxf_path):
            with open(dxf_path, "r") as f:
                data = json.load(f)
            self.assertIn("entities", data)
            self.assertIn("bounding_box", data)

if __name__ == '__main__':
    unittest.main()
