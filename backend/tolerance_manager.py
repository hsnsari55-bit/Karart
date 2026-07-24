"""
KaRar CAD-to-BIM Engine - Dynamic Tolerance Manager
Provides adaptive, unit-aware, and scale-aware geometrical tolerances
across Geometry Engine, Topology Engine, and Space Engine while preserving
100% cross-platform floating-point determinism.
"""

import math
import logging

logger = logging.getLogger("ToleranceManager")

class ToleranceManager:
    """
    Centralized, scale-aware tolerance policy manager.
    Eliminates fixed magic numbers and provides adaptive tolerances based on
    drawing bounds, DXF header $INSUNITS, and domain constraints.
    """
    
    # Standard DXF $INSUNITS mappings
    UNIT_SCALE_TO_MM = {
        0: 1.0,      # Unspecified -> default mm
        1: 25.4,     # Inches
        2: 304.8,    # Feet
        4: 1.0,      # Millimeters
        5: 10.0,     # Centimeters
        6: 1000.0,   # Meters
    }

    def __init__(self, insunits: int = 4, bounding_box_max_dim_mm: float = 50000.0):
        self.insunits = insunits
        self.unit_scale = self.UNIT_SCALE_TO_MM.get(insunits, 1.0)
        self.bounding_box_max_dim_mm = bounding_box_max_dim_mm
        self._compute_tolerances()

    def _compute_tolerances(self):
        """
        Dynamically computes scale-adaptive tolerances based on unit scale and drawing size.
        """
        # Determine scale factor relative to standard 50m building footprint
        scale_factor = max(0.1, min(10.0, self.bounding_box_max_dim_mm / 50000.0))
        
        # 1. Collinear line merge distance tolerance
        self.collinear_distance_mm = round(10.0 * scale_factor, 3)
        self.collinear_angle_deg = 0.5  # 0.5 degrees threshold
        
        # 2. Node snapping tolerance (for topological noding)
        self.node_snap_tolerance_mm = round(5.0 * scale_factor, 3)
        
        # 3. T-Junction snap distance
        self.t_junction_snap_mm = round(20.0 * scale_factor, 3)
        
        # 4. Space gap closure threshold (SpaceEngine iterative search limit)
        self.gap_closure_threshold_mm = round(400.0 * scale_factor, 3)
        
        # 5. Coordinate precision decimals (for canonical byte alignment)
        if self.unit_scale >= 1000.0:  # Meters
            self.coordinate_precision_decimals = 4
        elif self.unit_scale <= 1.0:   # Millimeters
            self.coordinate_precision_decimals = 2
        else:                          # Centimeters / Inches
            self.coordinate_precision_decimals = 3
            
        logger.info(
            f"ToleranceManager Initialized: Units=$INSUNITS({self.insunits}), Scale={self.unit_scale}mm/unit. "
            f"CollinearDist={self.collinear_distance_mm}mm, NodeSnap={self.node_snap_tolerance_mm}mm, "
            f"GapClosure={self.gap_closure_threshold_mm}mm, PrecisionDecimals={self.coordinate_precision_decimals}"
        )

    def snap_coordinate(self, val: float) -> float:
        """Determinisitically rounds coordinate according to canonical precision policy."""
        return round(float(val), self.coordinate_precision_decimals)

    def snap_point(self, pt: tuple) -> tuple:
        """Determinisitically rounds (x, y) point tuple."""
        return (self.snap_coordinate(pt[0]), self.snap_coordinate(pt[1]))

    def to_dict(self) -> dict:
        """Exports tolerance policy parameters as a dictionary contract."""
        return {
            "insunits": self.insunits,
            "unit_scale_to_mm": self.unit_scale,
            "bounding_box_max_dim_mm": self.bounding_box_max_dim_mm,
            "collinear_distance_mm": self.collinear_distance_mm,
            "collinear_angle_deg": self.collinear_angle_deg,
            "node_snap_tolerance_mm": self.node_snap_tolerance_mm,
            "t_junction_snap_mm": self.t_junction_snap_mm,
            "gap_closure_threshold_mm": self.gap_closure_threshold_mm,
            "coordinate_precision_decimals": self.coordinate_precision_decimals,
        }
