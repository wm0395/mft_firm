from __future__ import annotations
from project.common.models import utc_now_iso
from project.lineage.models import LineageNode, SignalLineage

class LineageTracker:
    def __init__(self):
        self._nodes: dict[str, LineageNode] = {}

    def record_node(
        self, 
        name: str, 
        node_type: str, 
        dependencies: tuple[str, ...], 
        metadata: dict = None
    ) -> str:
        node_id = f"node:{name}:{utc_now_iso()}"
        node = LineageNode(
            node_id=node_id,
            name=name,
            type=node_type,
            timestamp=utc_now_iso(),
            dependencies=dependencies,
            metadata=metadata or {}
        )
        self._nodes[node_id] = node
        return node_id

    def get_lineage(self, signal_id: str, final_node_id: str, final_value: float) -> SignalLineage:
        path = []
        visited = set()
        
        def traverse(node_id: str):
            if node_id in visited or node_id not in self._nodes:
                return
            visited.add(node_id)
            node = self._nodes[node_id]
            for dep in node.dependencies:
                traverse(dep)
            path.append(node)

        traverse(final_node_id)
        return SignalLineage(
            signal_id=signal_id,
            lineage_path=tuple(path),
            final_value=final_value
        )
