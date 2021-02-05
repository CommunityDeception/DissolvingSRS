import json
import sys
import time
from collections import Counter

from igraph import Graph
from igraph.clustering import VertexClustering
from loguru import logger

from core.gutil import GUtil
from core.learning.social_learning import SocialLearning
from core.metrics.cdcounter import count_conformity
from core.metrics.cdcounter import count_diversity
from core.metrics.sicounter import count_security_index
from core.strategy.edge import EdgeStrategy
from utils.convert import args_join_with_sep
from utils.convert import data_format
from utils.convert import line_contain_word
from utils.convert import seconds2datetime


class StaticRunner(object):
    def __init__(self, graph, iter_num, desc_interval, available_action, edge_sum, mode, edges=None, init_with_membership=False):
        self.graph: Graph = graph
        self.gutil: GUtil = GUtil(graph)
        self.learning: SocialLearning = SocialLearning(self.gutil, available_action, init_with_membership=init_with_membership)
        self.strategy: EdgeStrategy = EdgeStrategy(self.gutil)

        self.iter_num = iter_num
        self.edge_sum = edge_sum
        self.available_action = available_action
        self.desc_interval = desc_interval
        self.mode = mode
        self.edges = edges

        self.start_time = time.time()
        self.log_handlers = list()

        self._preprocess()

    def _preprocess(self):
        self._set_log()

    def _set_log(self):
        log_path = args_join_with_sep(
            "logs/" + self.graph.name,
            self.available_action,
            self.iter_num,
            self.edge_sum,
            self.mode,
            "STATIC"
        )
        self.log_handlers.append(logger.add(f"{log_path}.log", rotation="30MB", format="{message}"))
        self.log_handlers.append(logger.add(sys.stderr, format="{message}"))

    def _start(self):
        logger.info(line_contain_word("START"))
        logger.info(
            f"g: {self.graph.name}, "
            f"v: {self.graph.vcount()}, "
            f"e: {self.graph.ecount()}, "
            f"i: {self.iter_num}, "
            f"a: {self.available_action}, "
            f"m: {self.mode}, "
            f"s: {self.edge_sum}"
        )

    def _end(self):
        logger.info(f"t: {seconds2datetime(time.time() - self.start_time)}")
        logger.info(line_contain_word("END"))
        logger.info("\n\n")

        for i in self.log_handlers:
            logger.remove(i)

    def _run(self):
        self.strategy.add_edge(self.edge_sum, self.mode, self.edges)

        logger.info(line_contain_word("RECORD", char="-"))
        for i in range(self.desc_interval, self.iter_num + self.desc_interval, self.desc_interval):
            self.learning.emerge(self.desc_interval)
            self._desc(i)
        logger.info(line_contain_word("RECORD", char="-"))

    def _desc(self, i):
        parts = self.gutil.parts
        learners = self.learning.learners
        vcount = self.graph.vcount()

        actions = [learner.action for learner in learners]
        cls_actions = Counter(actions)
        dis_actions = [round(i / vcount * 100, 2) for i in cls_actions.values()]
        dis_actions.sort(reverse=True)
        clu_actions = VertexClustering(self.graph, membership=actions)

        l_conformity = count_conformity(parts, actions, self.available_action)
        g_conformity = count_security_index(self.graph, clu_actions)
        l_diversity = count_diversity(parts, actions, len(cls_actions))
        g_diversity = count_diversity(parts, actions, self.available_action)
        avg_payoff = sum(self.learning.payoff) / len(self.learning.payoff)
        modularity = clu_actions.modularity

        result = dict()
        result['index'] = data_format(i, width=6)
        result['exist_action'] = data_format(len(cls_actions), width=4)
        result['ldiversity'] = data_format(l_diversity)
        result['gdiversity'] = data_format(g_diversity)
        result['lconformity'] = data_format(l_conformity)
        result['gconformity'] = data_format(g_conformity)
        result['avg_payoff'] = data_format(avg_payoff)
        result['modularity'] = data_format(modularity)
        result['action_dis'] = dis_actions

        logger.info(json.dumps(result))

    def run(self):
        self._start()
        self._run()
        self._end()
