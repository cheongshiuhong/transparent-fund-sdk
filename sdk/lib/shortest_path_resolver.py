# Types
from typing import Optional, Iterable

# Libraries
from collections import defaultdict, deque


class ShortestPathResolver:
    """
    Simple unweighted-edge undirected graph BFS for shortest path.
    """

    def __init__(self, edges: Iterable[tuple[str, str]]):
        self.shortest_paths: dict[tuple[str, str], list[str]] = {}
        self.__resolve(edges)

    def get(self, src: str, dst: str) -> Optional[list[str]]:
        """
        Looks up the resolved shortest paths dictionary and returns if exists.

        Args:
            src: The source node.
            dst: The destination node.

        Returns:
            The list of nodes representing the path if exists, otherwise None.
        """
        if (src, dst) in self.shortest_paths.keys():
            return self.shortest_paths[(src, dst)]

        if (dst, src) in self.shortest_paths.keys():
            return self.shortest_paths[(dst, src)]

        return None

    def __resolve(self, edges: Iterable[tuple[str, str]]) -> None:
        """
        Finds all possible shortest paths based on the input edges
        by first constructing the adjacency list and doing a BFS.

        Args:
            edges: The list of edges (tuples) to use.
        """
        # Record the set of nodes and build the adjacency list dictionary
        nodes = set[str]()
        adj_list = defaultdict[str, set[str]](set)

        for edge in edges:
            nodes.add(edge[0])
            nodes.add(edge[1])
            adj_list[edge[0]].add(edge[1])
            adj_list[edge[1]].add(edge[0])

        # BFS and find the shortest paths
        queue = deque([[src] for src in nodes])

        while queue:
            current_path = queue.popleft()

            # Go through directly reachable nodes from the path's last node
            for dst in adj_list[current_path[-1]]:
                # Use each of the node in the currrent path as starting point
                for i, src in enumerate(current_path):
                    # Skip if round trip
                    if src == dst:
                        continue

                    # Skip if already found
                    if self.get(src, dst) is not None:
                        continue

                    # Record if not shortest path found yet
                    path_found = [*current_path[i:], dst]
                    self.shortest_paths[(src, dst)] = path_found

                    # Also add it to be visited (only once needed)
                    if i == 0:
                        queue.append(path_found)
