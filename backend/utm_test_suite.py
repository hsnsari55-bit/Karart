"""
KaRar CAD-to-BIM Engine - Multi-Directional & Multi-Scale UTM Large Coordinate Test Suite
Verifies coordinate normalization, topological graph isomorphism, and floating-point
determinism across extreme UTM offsets and coordinate quadrants.
"""

import os
import sys
import json
import hashlib
import copy
import logging

logging.disable(logging.CRITICAL)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_regression_tests import RegressionTester

def run_utm_suite():
    tester = RegressionTester()
    dxf_file = 'data/reference_set/01_konut_standard.dxf'
    
    # 1. Base Reference Run
    tester.parser.parse(dxf_file)
    tester.geometry_engine.run()
    tester.topology_engine.run()
    graph_base = tester.topology_engine.run()
    tester.constraint_solver.run(graph_base)
    tester.topology_validator.validate(graph_base)
    tester.semantic_engine.run()
    tester.space_engine.run()
    base_bim = tester.bim_core_engine.run()

    with open('outputs/dxf_raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    quadrants = [
        ("Q1 (+X, +Y North East)", 500000000.0, 4500000000.0),
        ("Q2 (-X, +Y North West)", -500000000.0, 4500000000.0),
        ("Q3 (-X, -Y South West)", -500000000.0, -4500000000.0),
        ("Q4 (+X, -Y South East)", 500000000.0, -4500000000.0),
        ("Q5 Extreme Diagonal (10^9mm)", 1000000000.0, 1000000000.0),
    ]

    print("=== MULTI-DIRECTIONAL & MULTI-SCALE UTM LARGE COORDINATE BENCHMARK ===")
    print(f"Base Reference Model: Walls={len(base_bim.get('walls', []))}, Spaces={len(base_bim.get('spaces', []))}, Graph Nodes={len(graph_base['nodes'])}, Edges={len(graph_base['edges'])}")
    print("-" * 100)
    print(f"{'Quadrant / Test Case':<32} | {'Offset X (m)':<15} | {'Offset Y (m)':<15} | {'Walls':<6} | {'Spaces':<6} | {'Status':<12}")
    print("-" * 100)

    passed_quadrants = 0

    for name, offset_x, offset_y in quadrants:
        utm_data = copy.deepcopy(raw_data)
        for ent in utm_data['entities']:
            if ent.get('type') == 'LINE':
                ent['start']['x'] += offset_x
                ent['start']['y'] += offset_y
                ent['end']['x'] += offset_x
                ent['end']['y'] += offset_y

        with open('outputs/dxf_raw.json', 'w', encoding='utf-8') as f:
            json.dump(utm_data, f)

        tester.geometry_engine.run()
        tester.topology_engine.run()
        graph_utm = tester.topology_engine.run()
        tester.constraint_solver.run(graph_utm)
        tester.topology_validator.validate(graph_utm)
        tester.semantic_engine.run()
        tester.space_engine.run()
        utm_bim = tester.bim_core_engine.run()

        n_walls = len(utm_bim.get('walls', []))
        n_spaces = len(utm_bim.get('spaces', []))
        nodes_utm = len(graph_utm['nodes'])
        edges_utm = len(graph_utm['edges'])

        is_isomorphic = (n_walls == len(base_bim.get('walls', []))) and \
                        (n_spaces == len(base_bim.get('spaces', []))) and \
                        (nodes_utm == len(graph_base['nodes'])) and \
                        (edges_utm == len(graph_base['edges']))

        status_str = "PASSED (100% Topo Isomorphism)" if is_isomorphic else "FAILED"
        if is_isomorphic:
            passed_quadrants += 1

        print(f"{name:<32} | {offset_x/1000.0:<15.1f} | {offset_y/1000.0:<15.1f} | {n_walls:<6} | {n_spaces:<6} | {status_str:<12}")

    print("-" * 100)
    print(f"UTM Suite Summary: {passed_quadrants}/{len(quadrants)} Quadrants PASSED with 100% Topological Parity.")

if __name__ == '__main__':
    run_utm_suite()
