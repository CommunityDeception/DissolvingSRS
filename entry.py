from igraph import Graph
from loguru import logger

from core.runner.adapt_runner import AdaptRunner
from core.runner.static_pro_runner import StaticProRunner

logger.remove(0)

repeat = 100
init_iter_num = 10000
iter_num = 1000
available_action = 10
edge_sum = 500
one_time_edge_num = 5

graph_names = [
    # ('gaussian', '6_50_1_20_0.9'),
    # ('gaussian', '11_28_1_5_0.9'),
    ('real', 'dblp_202'),
    # ('lfr', '500_2.5_1.5_0.1_5_40'),
    # ('gaussian', '10_50_1_10_0.9'),
    # ('gaussian', '4_50_1_10_0.9'),
    # ('lfr', '200_2.5_1.5_0.2_5_30')
]
for data_dir, graph_name in graph_names:
    graph = Graph.Read_GML(f"data/{data_dir}/{graph_name}.gml")

    for i in range(repeat):
        copy_graph = graph.copy()
        copy_graph.name = f"{graph_name}_{one_time_edge_num}"
        runner = AdaptRunner(
            graph=copy_graph,
            iter_num=iter_num,
            init_iter_num=init_iter_num,
            available_action=available_action,
            edge_sum=edge_sum,
            mode=13,
            one_time_edge_num=one_time_edge_num,
            init_with_membership=False
        )
        runner.run()
