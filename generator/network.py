import networkx as nx

from utils.convert import networkx2igraph
from collections import defaultdict


def __gaussian_random_partition_graph(l, s, v, k, sigma):
    k = k / 2
    z_in = k * sigma
    z_out = k - z_in
    n = s * l

    p_in = z_in / (s - 1)
    p_out = z_out / (n - s)

    if v:
        v = s / (v ** 2)
    else:
        v = float('inf')

    return nx.generators.gaussian_random_partition_graph(n, s, v, p_in, p_out).to_undirected()


def __check_graph(nx_graph, ig_graph, l, s, v, k, sigma):
    assert not ig_graph.is_directed()
    assert not any(ig_graph.is_multiple())
    assert ig_graph.is_connected()
    assert ig_graph.vcount() == nx_graph.number_of_nodes()
    assert ig_graph.ecount() == nx_graph.number_of_edges()
    assert ig_graph.vcount() == l * s
    assert len(set(ig_graph.vs['part'])) == l


def gaussian_random_partition_graph(l, s, v, k, sigma, output_path=None):
    """
    :param l: number of communities
    :param s: average community size
    :param v: standard deviation of community size
    :param k: average degree of any node
    :param sigma: separation degree
    :param output_path: gml file output path
    :return: igraph.Graph
    """
    try_count = 0

    while True:
        if not try_count % 10:
            print(f"try {try_count + 1} to generate {l}_{s}_{v}_{k}_{sigma}")

        graph: nx.Graph = __gaussian_random_partition_graph(l, s, v, k, sigma)
        new_graph = networkx2igraph(graph)

        try:
            __check_graph(graph, new_graph, l, s, v, k, sigma)
        except AssertionError:
            try_count += 1
            continue
        except Exception as e:
            print(e)
        else:
            print(f"Total try {try_count + 1} times to generate {l}_{s}_{v}_{k}_{sigma}")
            break

    if not output_path:
        return new_graph
    else:
        file_name = f"{l}_{s}_{v}_{k}_{sigma}.gml"
        with open(output_path + "/" + file_name, "wb") as file:
            new_graph.write_gml(file)

    return new_graph


def lfr_benchmark_graph(n, tau1, tau2, mu, average_degree, min_community, output_path=None):
    nx_graph = nx.generators.LFR_benchmark_graph(n, tau1, tau2, mu, average_degree=average_degree, min_community=min_community)
    communities = {frozenset(nx_graph.nodes[v]['community']) for v in nx_graph}
    membership = [0] * nx_graph.number_of_nodes()

    for index, part in enumerate(communities):
        for v in part:
            membership[v] = index

    ig_graph = networkx2igraph(nx_graph)
    ig_graph.vs['part'] = membership

    assert not ig_graph.is_directed()
    assert not any(ig_graph.is_multiple())
    assert ig_graph.is_connected()
    assert ig_graph.vcount() == nx_graph.number_of_nodes()
    assert ig_graph.ecount() == nx_graph.number_of_edges()

    if not output_path:
        return ig_graph
    else:
        file_name = output_path + f"/{n}_{tau1}_{tau2}_{mu}_{average_degree}_{min_community}.gml"
        with open(file_name, "wb") as file:
            ig_graph.write_gml(file)

    return ig_graph


def planted_partition_graph(l, k, p_in, p_out, directed=False, output_path=None):
    nx_graph = nx.generators.planted_partition_graph(l, k, p_in, p_out, directed=directed)
    communities = defaultdict(list)
    for v in nx_graph: communities[nx_graph.nodes[v]['block']].append(v)
    membership = [0] * nx_graph.number_of_nodes()

    for index, part in enumerate(communities.values()):
        for v in part:
            membership[v] = index

    ig_graph = networkx2igraph(nx_graph)
    ig_graph.vs['part'] = membership

    assert not ig_graph.is_directed()
    assert not any(ig_graph.is_multiple())
    assert ig_graph.is_connected()
    assert ig_graph.vcount() == nx_graph.number_of_nodes()
    assert ig_graph.ecount() == nx_graph.number_of_edges()

    if not output_path:
        return ig_graph
    else:
        file_name = output_path + f"/ppg_{l}_{k}_{p_in}_{p_out}.gml"
        with open(file_name, "wb") as file:
            ig_graph.write_gml(file)

    return ig_graph


if __name__ == '__main__':
    # graph = gaussian_random_partition_graph(10, 50, 1, 20, 0.5, "../data/gaussian")
    for i in range(10):
        try:
            graph = lfr_benchmark_graph(500, 2.5, 1.5, 0.3, 5, 30, "../data/lfr")

        except nx.exception.ExceededMaxIterations:
            print(i)
            continue
        else:
            break

    # graph = planted_partition_graph(2, 200, 0.05, 0.01, output_path='../data/ppg')
    from utils.graph import desc

    desc(graph)
