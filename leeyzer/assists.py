
#--------------------------------------------------------
# - linked list
# - tree
#--------------------------------------------------------
from collections import deque

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
