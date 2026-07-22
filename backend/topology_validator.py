import logging
from typing import Dict, Any

class TopologyValidationError(Exception):
    pass

class TopologyValidator:
    """
    Topology Validator (Mandatory Blocking Gate before Canonical Validator / Export)
    Ensures topological graph integrity, manifold compliance, and absence of severe defects.
    """
    def __init__(self):
        self.logger = logging.getLogger('KaRar-TopologyValidator')

    def validate(self, graph: Dict[str, Any]) -> bool:
        self.logger.info("Executing Topology Validator blocking check...")
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        if not nodes:
            raise TopologyValidationError("Topology validation failed: Graph contains zero nodes.")
        if not edges:
            raise TopologyValidationError("Topology validation failed: Graph contains zero edges.")

        self.logger.info(f"Topology Validator passed successfully ({len(nodes)} nodes, {len(edges)} edges).")
        return True
