import random
import sys


def random_max_val_index(data):
    if not len(data):
        raise Exception("length is 0.")

    max_val, indexes = -sys.maxsize, list()
    for index, val in enumerate(data):
        if val > max_val:
            max_val, indexes = val, [index]
        elif val == max_val:
            indexes.append(index)

    return random.choice(indexes)


def random_min_val_index(data):
    if not len(data):
        raise Exception("length is 0.")

    min_val, indexes = sys.maxsize, list()
    for index, val in enumerate(data):
        if val < min_val:
            min_val, indexes = val, [index]
        elif val == min_val:
            indexes.append(index)

    return random.choice(indexes)


def random_pop(data_list, data_set):
    ele = data_list.pop(random.randint(0, len(data_list) - 1))
    data_set.remove(ele)
    return ele
