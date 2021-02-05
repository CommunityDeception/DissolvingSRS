from math import log
from typing import List

from igraph import Graph
from igraph.clustering import VertexClustering


def _count_position_entropy(graph):
    total_degree = 2 * len(graph.es)
    position_entropy = 0

    for vertex in graph.vs:
        var = vertex.degree() / total_degree
        position_entropy -= var * log(var, 2)

    return position_entropy


def _count_resistance(graph, parts):
    total_degree = 2 * graph.ecount()
    resistance = 0

    for part in parts:
        if not part:
            continue

        part_volume = sum(graph.degree(part))
        subgraph = graph.subgraph(part)
        subgraph_degree = 2 * subgraph.ecount()

        resistance -= subgraph_degree / total_degree * log(part_volume / total_degree, 2)

    return resistance


def count_security_index(graph, parts):
    position_entropy = _count_position_entropy(graph)
    resistance = _count_resistance(graph, parts)
    security_index = resistance / position_entropy

    return security_index


def count_security_index_modified(graph, parts):
    security_index, E = 0, graph.ecount()

    for part in parts:
        if not part: continue
        vj = sum(graph.degree(part))
        gj = vj - 2 * graph.subgraph(part).ecount()

        part_a = (vj - gj) / (2 * E) * log(2 * E / vj, 2) if vj else 0
        part_b = gj / (2 * E) * log(2 * E / (2 * E - vj), 2) if 2 * E > vj else 0

        security_index = security_index + part_a + part_b

    return security_index / _count_position_entropy(graph)


def count_security_index_modified_version2(graph, parts):
    security_index, E = 0, graph.ecount()

    for part in parts:
        if not part: continue
        vj = sum(graph.degree(part))
        gj = vj - 2 * graph.subgraph(part).ecount()

        part_a = (vj - 2 * gj) / (2 * E) * log(2 * E / vj, 2) if vj else 0

        security_index = security_index + part_a

    return security_index / _count_position_entropy(graph)


def count_security_index_modified_version3(graph, parts):
    security_index, E = 0, graph.ecount()

    for part in parts:
        if not part: continue
        vj = sum(graph.degree(part))
        # gj = vj - 2 * graph.subgraph(part).ecount()

        part_a = vj / (2 * E) * log(2 * E / vj, 2) if vj else 0
        # part_b = gj / (2 * E) * log(2 * E / (2 * E - vj), 2) if 2 * E > vj else 0

        security_index = security_index + part_a

    return security_index / _count_position_entropy(graph)


class SecurityIndex(object):
    def __init__(self, graph, parts):
        self._graph: Graph = graph
        self._parts: VertexClustering = parts

        self._parts_degree: List[int] = list()
        self._parts_volume: List[int] = list()
        self._degree_distribute = self._graph.degree(self._graph.vs)

        self._pre_position_entropy = None
        self._pre_resistance = None

        self._pre_process()

    def update_parts(self, parts):
        self._parts = parts
        self._pre_process()

    def _pre_process(self):
        self._parts_degree: List[int] = list()
        self._parts_volume: List[int] = list()

        for index, part in enumerate(self._parts):
            subgraph: Graph = self._parts.subgraph(index)
            self._parts_degree.append(2 * subgraph.ecount())
            self._parts_volume.append(sum(self._graph.degree(part)))

    @staticmethod
    def normal_count(graph, parts):
        return count_security_index(graph, parts)

    def pre_count(self, flag=True):
        if flag:
            delta = 2
        else:
            delta = -2

        total_degree_aft = 2 * self._graph.ecount() + delta
        self._pre_position_entropy = 0
        self._pre_resistance = 0

        for node in self._graph.vs:
            var = self._graph.degree(node) / total_degree_aft
            self._pre_position_entropy -= var * log(var, 2)

        for index, part in enumerate(self._parts):
            if not part:
                continue

            part_volume = self._parts_volume[index]
            part_degree = self._parts_degree[index]

            self._pre_resistance -= part_degree / total_degree_aft * log(part_volume / total_degree_aft, 2)

    @staticmethod
    def __inner_count(value):
        if not value:
            return 0
        else:
            return value * log(value, 2)

    def count_by_pre(self, edge, flag=True):
        if flag:
            delta = 2
            add = 1
        else:
            delta = -2
            add = -1

        total_degree_aft = 2 * self._graph.ecount() + delta
        degree_distribute = self._degree_distribute

        src, des = edge
        src_now = (degree_distribute[src] + add) / total_degree_aft
        src_now = self.__inner_count(src_now)
        src_pre = degree_distribute[src] / total_degree_aft
        src_pre = self.__inner_count(src_pre)

        des_now = (degree_distribute[des] + add) / total_degree_aft
        des_now = self.__inner_count(des_now)
        des_pre = degree_distribute[des] / total_degree_aft
        des_pre = self.__inner_count(des_pre)

        position_entropy = self._pre_position_entropy + (src_pre + des_pre) - (des_now + src_now)

        src_com, des_com = self._parts.membership[src], self._parts.membership[des]

        if src_com == des_com:
            vs = self._parts_volume[src_com]
            gs = vs - self._parts_degree[src_com]
            differ = 0 - (vs - gs + delta) / total_degree_aft * log(((vs + delta) / total_degree_aft), 2) + (
                    vs - gs) / total_degree_aft * log(vs / total_degree_aft, 2)

        else:
            src_volume = self._parts_volume[src_com] + add
            des_volume = self._parts_volume[des_com] + add

            src_degree = self._parts_degree[src_com]
            des_degree = self._parts_degree[des_com]

            src_pre = src_degree / total_degree_aft * log((src_volume - add) / total_degree_aft, 2)
            des_pre = des_degree / total_degree_aft * log((des_volume - add) / total_degree_aft, 2)

            src_now = src_degree / total_degree_aft * log(src_volume / total_degree_aft, 2)
            des_now = des_degree / total_degree_aft * log(des_volume / total_degree_aft, 2)

            differ = src_pre + des_pre - src_now - des_now

        resistance = self._pre_resistance + differ

        return resistance / position_entropy

    def update(self, edge, flag=True):
        src, des = edge
        src_com, des_com = self._parts.membership[src], self._parts.membership[des]

        if flag:
            add = 1
        else:
            add = -1

        if src_com == des_com:
            self._parts_degree[src_com] += 2 * add

        self._parts_volume[src_com] += add
        self._parts_volume[des_com] += add
        self._degree_distribute[src] += add
        self._degree_distribute[des] += add
