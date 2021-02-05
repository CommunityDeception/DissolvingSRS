from igraph.clustering import VertexClustering


class GUtil(object):
    """
    proxy to manage the variables related with graph
    """
    def __init__(self, graph, membership=None):
        self.graph = graph
        self.membership = membership if membership else [int(i) for i in graph.vs['part']]
        self.parts = VertexClustering(self.graph, self.membership)

        self.neighbors = None
        self.sorted_parts_degree = None

        self._preprocess()

    def _preprocess(self):
        self._set_neighbors()
        self._set_sorted_part_degree()

    def has_edge(self, edge, directed=False):
        return self.graph.get_eid(*edge, directed=directed, error=False) != -1

    def _set_neighbors(self):
        neighbors = dict()
        for node in self.graph.vs:
            node_neighbors = self.graph.neighbors(node)
            neighbors[node.index] = node_neighbors

        self.neighbors = neighbors

    def _update_neighbors(self, edge, flag=True):
        if not self.neighbors:
            return

        src, tar = edge
        if flag:
            self.neighbors[src].append(tar)
            self.neighbors[tar].append(src)
        else:
            self.neighbors[src].remove(tar)
            self.neighbors[tar].remove(src)

    def _set_sorted_part_degree(self):
        parts_degree: list = [list() for _ in self.parts]
        for node, part_index in enumerate(self.membership):
            parts_degree[part_index].append((node, self.graph.degree(node)))

        for part_degree in parts_degree:
            part_degree.sort(key=lambda x: x[1])

        self.sorted_parts_degree = parts_degree

    def _update_sorted_part_degree(self, edge, flag=True):
        flag = 1 if flag else -1

        for node in edge:
            part = self.sorted_parts_degree[self.membership[node]]
            degree = self.graph.degree(node)

            part.remove((node, degree))
            for i, value in enumerate(part):
                if value[1] > degree:
                    part.insert(i, (node, degree + flag))
                    break
            else:
                if not part:
                    i = -1
                part.insert(i + 1, (node, degree + flag))

    def _update_graph(self, edge, flag=True):
        if flag:
            self.graph.add_edge(*edge)
        else:
            self.graph.delete_edges([edge, ])

    def update_membership(self, membership):
        """
        update membership manual
        :param membership: list[int]
        :return:
        """
        self.membership = membership
        self.parts = VertexClustering(self.graph, self.membership)
        self._set_sorted_part_degree()

    def update(self, edge, flag=True):
        self._update_sorted_part_degree(edge, flag)
        self._update_neighbors(edge, flag)
        self._update_graph(edge, flag)
