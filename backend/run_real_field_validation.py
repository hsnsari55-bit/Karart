import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_regression_tests import RegressionTester

def main():
    tester = RegressionTester()
    tester.run_on_file('datasets/twin_villa/dxf/kaRar.dxf')
    print("REAL FIELD DXF VALIDATION SUCCESSFUL")

if __name__ == '__main__':
    main()
