import datetime
import os

import networkx as nx
from igraph import Graph

from core.strategy.edge import EdgeStrategy
from core.gutil import GUtil


def networkx2igraph(nx_graph: nx.Graph):
    igraph_graph = Graph(
        n=nx_graph.number_of_nodes(),
        edges=list(nx_graph.edges()),
        directed=False,
    )

    blocks = list(i[1] for i in nx_graph.nodes(data="block"))
    add_part_to_graph(igraph_graph, blocks)

    return igraph_graph


def add_part_to_graph(graph: Graph, membership: list, part_name="part", inplace=True):
    if inplace:
        graph.vs[part_name] = membership
        return None

    else:
        temp_graph = graph.copy()
        temp_graph.vs[part_name] = membership
        return temp_graph


def get_file_name_without_suffix(path):
    return os.path.splitext(os.path.basename(path))[0]


def args_join_with_sep(*args, sep="_"):
    return sep.join([str(i) for i in args])


def seconds2datetime(seconds):
    return str(datetime.timedelta(seconds=round(seconds, 2)))


def line_contain_word(word="", char="=", line_length=60):
    mark = (line_length - len(word)) // 2
    line = char * mark
    line += word
    mark = line_length - len(line)
    line += char * mark

    return line


def data_format(data, width=6, precision=4):
    if isinstance(data, float):
        return f"{data: {width}.{precision}}"

    if isinstance(data, int):
        return f"{data: {width}}"

    if isinstance(data, str):
        return data
