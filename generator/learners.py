from core.gutil import GUtil
from core.learning.social_learning import SocialLearning
from igraph import Graph
import pickle
from core.learning.social_learning import Learner


def generate_learners(graph, rounds, actions, output_path=None):
    gutil = GUtil(graph)
    slearning = SocialLearning(gutil, actions, True, None)
    slearning.emerge(rounds)

    if not output_path: return slearning.learners
    else:
        file_name = output_path + f"/{graph.name}.learners"
        with open(file_name, 'wb') as f:
            obj = {'learners': slearning.learners, 'payoff': slearning.payoff}
            pickle.dump(obj, f)
        return slearning.learners


if __name__ == '__main__':
    graph_name = "300_2.5_1.5_0.1_5_50"
    graph = Graph.Read_GML("../data/lfr/" + graph_name + ".gml")
    graph.name = graph_name

    learners = generate_learners(graph, 10000, 5, '../data/learners')
    from collections import Counter
    print(Counter(learner.action for learner in learners))
