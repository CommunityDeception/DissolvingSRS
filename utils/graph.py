import pickle
import json

from igraph import Graph
from tqdm import tqdm
from igraph.clustering import VertexClustering
from typing import List

from core.detection.normal import fast_resistance
from core.gutil import GUtil
from core.learning.social_learning import Learner
from core.strategy.edge import EdgeStrategy


def get_edges(graph, mode, func, edge_sum, interval=1, output_path="../data/edges"):
    bar = tqdm(edge_sum // interval)
    edges = list()
    update = edge_sum // interval != 1

    strategy = EdgeStrategy(GUtil(graph))
    for i in range(interval, edge_sum + interval, interval):
        if update:
            parts = func(graph)
            strategy.update_parts(parts)
        edges.extend(strategy.add_edge(interval, mode))
        bar.update(1)

    with open(f"{output_path}/{graph.name}_{mode}_{edge_sum}_{interval}.edges", "wb") as f:
        pickle.dump(edges, f)


def desc(graph: Graph):
    parts = VertexClustering(graph, [int(i) for i in graph.vs['part']])
    print(graph.vcount(), graph.ecount())
    print(f"Part Num: {len(parts)}")
    print(f"Part Size: {[len(part) for part in parts]}")
    print(f"Modularity: {parts.modularity}")
    in_edges = 0
    for subgraph in parts.subgraphs():
        in_edges += subgraph.ecount()

    print(f"fraction: {in_edges / graph.ecount()}")
    print("Degree Distribution: ")
    print(graph.degree_distribution())
    return parts.modularity


def desc_learners(learners: List[Learner]):
    result = list()

    for learner in learners:
        result.append(
            [
                [round(val, 4) for val in learner._rows],
                [round(val, 4) for val in learner._cols],
            ]
        )

    return json.dumps(result)


if __name__ == '__main__':

    graph_name = "4_50_1_10_0.9"
    test_graph = Graph.Read_GML(f"../data/gaussian/{graph_name}.gml")
    desc(test_graph)
    # test_graph.name = graph_name
    #
    # get_edges(test_graph, 1, fast_resistance, 1000, 1000)
