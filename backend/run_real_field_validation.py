import json
import os
import sys

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPOSITORY_ROOT not in sys.path:
    sys.path.insert(0, REPOSITORY_ROOT)

from backend.run_regression_tests import RegressionTester


def main():
    tester = RegressionTester()
    result = tester.run_on_file('datasets/twin_villa/dxf/kaRar.dxf')
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))

    if result.get("status") == "SUCCESS":
        print("REAL FIELD DXF VALIDATION SUCCESSFUL")
        return 0

    print("REAL FIELD DXF VALIDATION FAILED", file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
