import random
import sys

from core.metrics.sicounter import SecurityIndex
from core.metrics.sicounter import count_security_index_modified_version3


class EdgeStrategy(object):
    RANDOM = 0
    MIN_BA_RATIO = 13

    def __init__(self, gutil):
        self.gutil = gutil
        self.sicounter = SecurityIndex(self.gutil.graph, self.gutil.parts)

    def add_edge(self, edge_sum, mode, ini_edges=None):
        edges = list()

        for i in range(edge_sum):
            if ini_edges:
                edge = ini_edges[i]
            else:
                if mode == EdgeStrategy.RANDOM:
                    edge = self.add_random_edge()
                elif mode == EdgeStrategy.MIN_BA_RATIO:
                    edge = self.add_isi_edge()
                else:
                    raise Exception("mode out of bound.")

            edges.append(edge)
            self.gutil.update(edge)
            self.sicounter.update(edge)

        assert len(edges) == len(set(edges)) == edge_sum

        return edges

    def add_random_edge(self):
        while True:
            src = random.randint(0, self.gutil.graph.vcount() - 1)
            tar = random.randint(0, self.gutil.graph.vcount() - 1)

            if src != tar and not self.gutil.has_edge((src, tar)):
                add_edge = (src, tar)
                break

        return add_edge

    def add_isi_edge(self):
        available_edges = set()
        for si, s_order in enumerate(self.gutil.sorted_parts_degree):
            if not s_order:
                continue

            for ti, t_order in enumerate(self.gutil.sorted_parts_degree):
                s_order = self.gutil.sorted_parts_degree[si]
                if not t_order:
                    continue

                if si == ti:
                    continue

                u, du = s_order[0]
                v, dv = t_order[0]

                if du > dv:
                    u, v = v, u
                    du, dv = dv, du
                    s_order, t_order = t_order, s_order

                u_neighbors = set(self.gutil.graph.neighbors(u))

                for i, di in t_order:
                    if i not in u_neighbors:
                        v, dv = i, di
                        break
                else:
                    u, v = v, u
                    du, dv = dv, du
                    s_order, t_order = t_order, s_order
                    u_neighbors = set(self.gutil.graph.neighbors(u))

                    for i, di in t_order:
                        if i not in u_neighbors:
                            v, dv = i, di
                            break

                upper_bound = du + dv
                available_edges.add((u, v))

                for i, di in t_order:
                    if di >= dv:
                        edge = (u, v) if u < v else (v, u)
                        if not self.gutil.has_edge(edge):
                            available_edges.add(edge)
                            break

                    else:
                        i_neighbors = set(self.gutil.graph.neighbors(i))

                        for j, dj in s_order:
                            if j not in i_neighbors:
                                break

                        if di + dj < upper_bound:
                            edge = (i, j) if i < j else (j, i)
                            if not self.gutil.has_edge(edge):
                                available_edges.add(edge)

        min_si, min_edge = sys.maxsize, None
        for edge in available_edges:
            self.gutil.graph.add_edge(*edge)
            si = count_security_index_modified_version3(self.gutil.graph, self.gutil.parts)
            self.gutil.graph.delete_edges([edge, ])

            if si < min_si:
                min_si, min_edge = si, edge

        assert self.gutil.membership[min_edge[0]] != self.gutil.membership[min_edge[1]]
        assert min_edge is not None

        return min_edge

    def rollback(self, edges):
        for edge in edges:
            self.gutil.update(edge, flag=False)
            self.sicounter.update(edge, flag=False)

    def update_parts(self, parts):
        self.gutil.update_membership(parts.membership)
        self.sicounter.update_parts(parts)


def _sort_data_according_parts(data, parts, membership):
    data_values: list = [list() for _ in parts]

    for node, part_index in enumerate(membership):
        data_values[part_index].append((node, data[node],))

    for data_part in data_values:
        data_part.sort(key=lambda x: x[1])

    return data_values
