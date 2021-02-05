import math
from collections import Counter


def _count_community_conformity(actions, available_action):
    part_size = len(actions)
    cls_actions = Counter(actions)
    result = 0

    for freq in cls_actions.values():
        val = freq / part_size
        result -= val * math.log2(val)

    return 1 - 1 / math.log2(available_action) * result


def count_conformity(parts, actions, available_action):
    result = 0

    for part in parts:
        part_actions = [actions[i] for i in part]
        part_conformity = _count_community_conformity(part_actions, available_action)
        result += len(part) / parts.graph.vcount() * part_conformity

    return result


def count_diversity(parts, actions, available_action):
    if available_action == 1:
        return 0

    result = 0
    cls_actions = Counter(actions)

    for freq in cls_actions.values():
        val = freq / parts.graph.vcount()
        result -= val * math.log2(val)

    return 1 / math.log2(available_action) * result
