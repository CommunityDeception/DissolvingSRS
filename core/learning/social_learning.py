import random
from collections import defaultdict
from copy import deepcopy

from utils.search import random_max_val_index
from utils.search import random_pop


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
            self._rows[action] = 0.001
            self._cols[action] = 0.001

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
    def __init__(self, gutil, available_action, init_with_membership=False, init_learners=None, init_payoff=None):
        self.gutil = gutil
        self.available_action = available_action
        self.learners = init_learners
        self.payoff = init_payoff
        self.init_with_membership = init_with_membership

        self._preprocess()

    def _preprocess(self):
        self._init_learners()

    def _init_learners(self):
        if self.learners: return
        else: self.learners = list()

        init_record = defaultdict()
        init_record.default_factory = lambda: random.randint(0, self.available_action - 1)

        for member in self.gutil.membership:
            if self.init_with_membership:
                choose_action = init_record[member]
            else: choose_action = None

            self.learners.append(Learner(self.available_action, choose_action))

    def _game(self, i, j):
        li, lj = self.learners[i], self.learners[j]
        if random.random() < 0.5:
            li.is_row = True
            lj.is_row = False
        else:
            li.is_row = False
            lj.is_row = True

        li.select_action(); lj.select_action()
        utility = 1 if li.action == lj.action else -1
        li.update(utility); lj.update(utility)

        return [utility, utility]

    def _round(self, rounds=0):
        if not rounds: rounds = self.gutil.graph.vcount() // 2

        payoff = list()
        for _ in range(rounds):
            payoff.extend(self._single_round())

        self.payoff = payoff

    def _single_round(self):
        src, tar = None, None

        while True:
            src = random.randint(0, self.gutil.graph.vcount() - 1)
            if not self.gutil.neighbors[src]: continue

            tar = random.choice(self.gutil.neighbors[src])
            break

        assert src is not None and tar is not None
        return self._game(src, tar)

    def emerge(self, iter_num, rounds=0):
        for _ in range(iter_num):
            self._round(rounds)
