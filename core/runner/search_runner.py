import sys
import time
from collections import Counter

from loguru import logger

from core.gutil import GUtil
from core.learning.social_learning import SocialLearning
from core.strategy.edge import EdgeStrategy
from utils.convert import args_join_with_sep
from utils.convert import line_contain_word
from utils.convert import seconds2datetime


class SearchRunner(object):
    def __init__(self, graph, iter_num, available_action, mode, max_edges_num, min_edges_num=0, repeat_time=50, precision=1):
        self.graph = graph
        self.iter_num = iter_num
        self.avail_action = available_action
        self.mode = mode
        self.max_edges_num = max_edges_num
        self.min_edges_num = min_edges_num
        self.repeat_time = repeat_time
        self.precision = precision

        self.start_time = time.time()

        self.log_handlers = list()
        self.result = None

        self._preprocess()

    def _preprocess(self):
        self._set_log()

    def _set_log(self):
        log_path = args_join_with_sep(
            "logs/" + self.graph.name,
            self.avail_action,
            self.iter_num,
            self.mode,
            "SEARCH"
        )
        self.log_handlers.append(logger.add(f"{log_path}.log", rotation="30MB", format="{message}"))
        self.log_handlers.append(logger.add(sys.stderr, format="{message}"))

    def _count(self, edges_num):
        graph = self.graph.copy()
        gutil = GUtil(graph)
        strategy = EdgeStrategy(gutil)
        strategy.add_edge(edges_num, self.mode)
        result_list = list()

        for i in range(self.repeat_time):
            learning = SocialLearning(gutil, self.avail_action)
            learning.emerge(self.iter_num)
            result_list.append(self._count_main_action_proportion(learning))

        return sum(result_list) / len(result_list)

    def _count_main_action_proportion(self, learning):
        actions = [learner.action for learner in learning.learners]
        vcount = self.graph.vcount()

        return max(Counter(actions).values()) / vcount * 100

    def _start(self):
        logger.info(line_contain_word("START"))
        logger.info(
            f"g: {self.graph.name}, "
            f"v: {self.graph.vcount()}, "
            f"e: {self.graph.ecount()}, "
            f"i: {self.iter_num}, "
            f"a: {self.avail_action}, "
            f"m: {self.mode}, "
            f"max: {self.max_edges_num}, "
            f"min: {self.min_edges_num}, "
            f"rep: {self.repeat_time}, "
            f"psc: {self.precision}"
        )

    def _end(self):
        logger.info(f"t: {seconds2datetime(time.time() - self.start_time)}")
        logger.info(line_contain_word("END"))
        logger.info("\n\n")

        for i in self.log_handlers:
            logger.remove(i)

    def _search(self):
        logger.info(line_contain_word("RECORD", char="-"))
        result, count = -1, 0
        i, j = self.min_edges_num, self.max_edges_num

        if self._count(i) > 90:
            logger.info(f"Min: {i} edges can make the graph converge.")

        elif self._count(j) < 90:
            logger.info(f"Max: {j} edges cannot make the graph converge.")

        else:
            while i <= j:
                mid = i + (j - i) // 2
                proportion = self._count(mid)
                if proportion >= 90:
                    result = mid
                    j = mid - self.precision
                else:
                    i = mid + self.precision

                count += 1
                logger.info(f"{count}: {mid} edges, {proportion}%")
            logger.info(f"Found: {result} edges can make the graph converge.")

        logger.info(line_contain_word("RECORD", char="-"))
        self.result = result

    def search(self):
        self._start()
        self._search()
        self._end()
