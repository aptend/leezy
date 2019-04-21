"""
leezyer leetcode lazyer
"""
from time import perf_counter
from collections import deque
from copy import deepcopy

#----------------------------------------------------------
# 继承Solution，有效的解决方案使用solution装饰
#----------------------------------------------------------


def solution(func):
    """decorator. Attach the `func` a solution marker
    """
    func.__dict__['solution'] = True
    return func


def timeit(func):
    """decorator. Attach the `func` a time marker
    """
    func.__dict__['timeit'] = True
    return func


class Solution:
    def __init__(self):
        self._test_args = []
        self.solutions = [item for item in self.__class__.__dict__.values()
                          if hasattr(item, 'solution')]

    def add_args(self, *args, **kwargs):
        self._test_args.append((args, kwargs))

    def _run_solution(self, solution, args, kwargs):
        ags, kws = deepcopy(args), deepcopy(kwargs)
        t1 = perf_counter()
        output = solution.__call__(self, *ags, **kws)
        duration = perf_counter() - t1
        return output, duration

    def _post_process(self, solutions, outputs, durations):
        strings = []
        for s, o, d in zip(solutions, outputs, durations):
            if hasattr(s, 'timeit'):
                string = f"{o}({d:.4f}s)"
            else:
                string = f"{o}"
            strings.append(string)
        print('  '.join(strings))

    def test(self):
        for args, kwargs in self._test_args:
            report = [self._run_solution(f, args, kwargs)
                      for f in self.solutions]
            outputs = [r[0] for r in report]
            durations = [r[1] for r in report]
            self._post_process(self.solutions, outputs, durations)


#--------------------------------------------------------
# - linked list
# - tree
#--------------------------------------------------------
class ListNode:
    def __init__(self, x=None):
        self.val = x
        self.next = None

    def __iter__(self):
        p = self
        while p is not None:
            yield p.val
            p = p.next

    def __str__(self):
        return "->".join([str(v) for v in self])

    def copy(self):
        return make_linked_list(self)


def make_linked_list(data):
    """make linked list from list
    
    [1,2,3,4] => 1(head) -> 2 -> 3 -> 4
    :param data: data source, an iterable obj  
    :return: the head of the linked list
    """
    data = list(data)
    if len(data) == 0:
        return None
    head = tail = ListNode(data[0])
    for item in data[1:]:
        node = ListNode(item)
        tail.next = node
        tail = node
    return head


class TreeNode:
    def __init__(self, x=None):
        self.val = x
        self.left = None
        self.right = None

    def __str__(self):
        return "Tree({})".format("-".join([str(v) for v in self]))

    def __iter__(self):
        remaining_nodes = [self]
        fillup = 0
        for node in remaining_nodes:
            if node is None:
                fillup += 1
            else:
                while fillup > 0:
                    yield None
                    fillup -= 1
                yield node.val
                remaining_nodes.append(node.left)
                remaining_nodes.append(node.right)


def make_tree(data):
    """make binary tree from list

    :param data: data source, an iterable obj
    :return: the root of the binary tree.
    """
    if len(data) < 1:
        return None
    root = TreeNode(data[0])
    queue = deque([root])
    i = 1
    while i < len(data):
        try:
            upper_node = queue.popleft()
        except IndexError:
            raise ValueError("bad data for binary tree")
        for val, child in zip(data[i:i+2], ('left', 'right')):
            if val is not None:
                new_node = TreeNode(int(val))
                setattr(upper_node, child, new_node)
                queue.append(new_node)
        i += 2
    return root
