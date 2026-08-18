import argparse
import json
import os
import sys

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, REPOSITORY_ROOT)

from backend.run_regression_tests import RegressionTester


def main(source_path):
    tester = RegressionTester()
    result = tester.run_on_file(source_path)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))

    if result.get("status") == "SUCCESS":
        print("REAL FIELD DXF VALIDATION SUCCESSFUL")
        return 0

    print("REAL FIELD DXF VALIDATION FAILED", file=sys.stderr)
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the mandatory CAD-to-BIM validation gates.")
    parser.add_argument("source_path", help="DXF source to validate")
    args = parser.parse_args()
    sys.exit(main(args.source_path))
