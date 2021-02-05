import json
import random
import sys
import time
from collections import Counter
from collections import defaultdict

from igraph import Graph
from igraph.clustering import VertexClustering
from loguru import logger

from core.gutil import GUtil
from core.metrics.cdcounter import count_conformity
from core.metrics.cdcounter import count_diversity
from core.metrics.sicounter import count_security_index
from core.strategy.edge import EdgeStrategy
from utils.convert import args_join_with_sep
from utils.convert import data_format
from utils.convert import line_contain_word
from utils.convert import seconds2datetime
from utils.search import random_max_val_index


class Learner(object):
    LEARNING_RATE = 0.5
    EPSILON = 0.1

    def __init__(self, action_num, action=None, is_row=False):
        self.is_row = is_row
        self.action = action if action is not None else random.randint(0, action_num - 1)
        self._rows = [0] * action_num
        self._cols = [0] * action_num

        self._action_num = action_num

        if action is not None:
            self._rows[action] = 0.1
            self._cols[action] = 0.1

    def select_action(self):
        if random.random() < Learner.EPSILON:
            return random.randint(0, self._action_num - 1)

        values = self._rows if self.is_row else self._cols
        self.action = random_max_val_index(values)

    def update(self, utility):
        values = self._rows if self.is_row else self._cols
        try:
            v = values[self.action]
        except Exception as e:
            print(e)

        v = (1 - Learner.LEARNING_RATE) * v + Learner.LEARNING_RATE * utility
        values[self.action] = v


class SocialLearning(object):
    def __init__(self, gutil, available_action, threshold, init_with_membership=False, init_learners=None, init_payoff=None, iter_limit_per_round=10000000):
        self.gutil = gutil
        self.available_action = available_action
        self.learners = init_learners
        self.payoff = init_payoff
        self.init_with_membership = init_with_membership
        self.threshold = threshold
        self.punish_record = defaultdict(int)
        self.iter_limit_per_round = iter_limit_per_round

        self._preprocess()

    def _preprocess(self):
        self._init_learners()

    def _init_learners(self):
        if self.learners:
            return
        else:
            self.learners = list()

        init_record = defaultdict()
        init_record.default_factory = lambda: random.randint(0, self.available_action - 1)

        for member in self.gutil.membership:
            if self.init_with_membership:
                choose_action = init_record[member]
            else:
                choose_action = None

            self.learners.append(Learner(self.available_action, choose_action))

    def _game(self, i, j):
        li, lj = self.learners[i], self.learners[j]
        if random.random() < 0.5:
            li.is_row = True
            lj.is_row = False
        else:
            li.is_row = False
            lj.is_row = True

        li.select_action();lj.select_action()
        utility = 1 if li.action == lj.action else -1
        li.update(utility);lj.update(utility)

        return [utility, utility]

    def _round(self):
        for _ in range(self.iter_limit_per_round):
            choose_edge = random.randint(0, self.gutil.graph.ecount() - 1)
            nodes = self.gutil.graph.es[choose_edge].tuple

            payoff = self._game(*nodes)
            if sum(payoff) > 0: continue

            target = random.choice(nodes)
            if self.punish_record[target] < self.threshold:
                self.punish_record[target] += 1
                continue

            nodes_with_same_action = list()

            for node in range(self.gutil.graph.vcount()):
                if self.learners[node].action == self.learners[target].action and node != target and not self.gutil.has_edge((node, target)):
                    nodes_with_same_action.append(node)

            if not nodes_with_same_action: nodes_with_same_action = [i for i in range(self.gutil.graph.vcount()) if i != target and not self.gutil.has_edge((i, target))]
            if not nodes_with_same_action: continue

            add_edge = (random.choice(nodes_with_same_action), target)
            self.gutil.update(nodes, False)
            self.gutil.update(add_edge, True)

            return choose_edge, add_edge

        return None

    def emerge(self):
        if not self._round():
            print("Error: out of limitation")
            return False

        return True


class GlobalAdviseRunner(object):
    def __init__(self, graph, init_iter_num, iter_num, available_action, edge_sum, mode, one_time_edge_num, threshold, edges=None, init_with_membership=False):
        self.graph: Graph = graph
        self.init_iter_num = init_iter_num
        self.iter_num: int = iter_num
        self.available_action = available_action
        self.gutil: GUtil = GUtil(graph)
        self.initial_membership = self.gutil.membership.copy()
        self.threshold = threshold
        self.learning: SocialLearning = SocialLearning(self.gutil, available_action, threshold=threshold, init_with_membership=init_with_membership)

        self.edge_sum = edge_sum
        self.mode = mode
        self.one_time_edge_num = one_time_edge_num
        self.edges = edges
        self.flag = "sig"

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
            self.threshold,
            "GlobalAdvise"
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

        self._desc(0)
        self._update()

        flag = False

        for i in range(self.one_time_edge_num, self.edge_sum + self.one_time_edge_num, self.one_time_edge_num):
            if self._has_global_norm() or flag:
                self._desc(i)
                continue

            for _ in range(self.one_time_edge_num):
                # print(len(self.graph.components()))
                if not self.learning.emerge():
                    flag = True
                    break

            self._desc(i)
            self._update()

        logger.info(line_contain_word("RECORD", char="-"))

    def _update(self):
        membership = [learner.action for learner in self.learning.learners]

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
        # g_conformity = count_security_index(self.graph, clu_actions)
        g_conformity = 0
        l_diversity = count_diversity(parts, actions, len(cls_actions))
        g_diversity = count_diversity(parts, actions, self.available_action)
        # avg_payoff = sum(self.learning.payoff) / len(self.learning.payoff)
        avg_payoff = len(self.graph.components())
        modularity = clu_actions.modularity

        result = dict()
        result['index'] = data_format(i, width=6)
        result['exist_action'] = data_format(len(cls_actions), width=4)
        result['ldiversity'] = data_format(l_diversity)
        result['gdiversity'] = data_format(g_diversity)
        result['lconformity'] = data_format(l_conformity)
        result['gconformity'] = data_format(g_conformity)
        result['components'] = data_format(avg_payoff)
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
