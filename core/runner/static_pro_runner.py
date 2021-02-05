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
from core.detection.normal import louvain
from core.detection.normal import fast_resistance
from utils.convert import args_join_with_sep
from utils.convert import data_format
from utils.convert import line_contain_word
from utils.convert import seconds2datetime


class StaticProRunner(object):
    def __init__(self, graph, init_iter_num, iter_num, available_action, edge_sum, mode, one_time_edge_num, edges=None, init_with_membership=False, init_social_learning=None):
        self.graph: Graph = graph
        self.init_iter_num = init_iter_num
        self.iter_num: int = iter_num
        self.available_action = available_action
        self.gutil: GUtil = GUtil(graph)
        self.initial_membership = self.gutil.membership.copy()

        init_learners = None if not init_social_learning else init_social_learning['learners']
        init_payoff = None if not init_social_learning else init_social_learning['payoff']

        self.learning: SocialLearning = SocialLearning(self.gutil, available_action, init_with_membership=init_with_membership, init_learners=init_learners, init_payoff=init_payoff)
        self.strategy: EdgeStrategy = EdgeStrategy(self.gutil)

        self.edge_sum = edge_sum
        self.mode = mode
        self.one_time_edge_num = one_time_edge_num
        self.edges = edges
        self.flag = "sig"
        self.init_learners = init_social_learning

        self.start_time = time.time()
        self.log_handlers = list()

        self._preprocess()

    def _preprocess(self):
        self._check()
        self._set_log()

    def _check(self):
        assert not self.edge_sum % self.one_time_edge_num
        if not self.edges:
            self.flag = "all"

    def _set_log(self):
        log_path = args_join_with_sep(
            "logs/" + self.graph.name,
            self.available_action,
            self.iter_num,
            self.flag,
            self.edge_sum,
            self.one_time_edge_num,
            self.mode,
            "StaticPro"
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
            f"s: {self.edge_sum}, "
            f"o: {self.one_time_edge_num}"
        )

    def _end(self):
        logger.info(f"t: {seconds2datetime(time.time() - self.start_time)}")
        logger.info(line_contain_word("END"))
        logger.info("\n\n")

        for i in self.log_handlers:
            logger.remove(i)

    def _has_global_norm(self):
        return len(
            set(
                learner.action for learner in self.learning.learners
            )
        ) == 1

    def _run(self):
        logger.info(line_contain_word("RECORD", char="-"))

        if not self.init_learners: self.learning.emerge(self.init_iter_num)

        self._desc(0)
        self._update()

        for i in range(self.one_time_edge_num, self.edge_sum + self.one_time_edge_num, self.one_time_edge_num):
            if self._has_global_norm():
                self._desc(i)
                continue

            if self.edges:
                self.strategy.add_edge(self.one_time_edge_num, self.mode, self.edges[i - self.one_time_edge_num: i])
            else:
                self.strategy.add_edge(self.one_time_edge_num, self.mode)

            self.learning.emerge(self.iter_num)
            self._desc(i)
            self._update()

        logger.info(line_contain_word("RECORD", char="-"))

    def _update(self):
        membership = [i for i in self.gutil.membership]
        self.strategy.update_parts(VertexClustering(self.graph, membership=membership))

    def _desc(self, i):
        parts = VertexClustering(self.graph, membership=self.initial_membership)
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

        try:
            self._run()
        except AssertionError:
            print("Assertion Error in running.")

        self._end()