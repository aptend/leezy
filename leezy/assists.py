
# --------------------------------------------------------
# - linked list
# - tree
# --------------------------------------------------------
from collections import deque
from itertools import zip_longest, islice


class LinkedListContext:
    @staticmethod
    def transform_args(args, kwargs):
        args = [LinkedListNode.make_linked_list(x) if isinstance(x, list) else x for x in args]
        return args, kwargs


class TreeContext:
    @staticmethod
    def transform_args(args, kwargs):
        args = [TreeNode.make_tree(x) if isinstance(x, list) else x for x in args]
        return args, kwargs


class Context:
    @staticmethod
    def transform_args(args, kwargs):
        return args, kwargs


class LinkedListNode:
    def __init__(self, x=None):
        self.val = x
        self.next = None
        self.has_cycle = False

    def __iter__(self):
        p = self
        while p is not None:
            yield p.val
            p = p.next

    def __str__(self):
        if self.has_cycle:
            return "->".join([str(v) for v in islice(self, 5)]) + '...'
        else:
            return "->".join([str(v) for v in self])

    def __eq__(self, other):
        if self.has_cycle:
            raise TypeError('__eq__ is not supported for linked list who has cycle')
        if not isinstance(other, self.__class__):
            return False
        return all(x == y for x, y in zip_longest(self, other, fillvalue=None))

    @staticmethod
    def make_linked_list(data):
        """make a linked list from a list

        Examples:
        >>> ll = LinkedListNode.make_linked_list([1, 2, 3, 4, 5])
        >>> print(ll)
        1->2->3->4->5

        Args:
            data: data source, an iterable object.

        Returns:
            the head of the linked list, class `LinkedLinkedListNode`.
        """
        data = list(data)
        if len(data) == 0:
            return None
        head = tail = LinkedListNode(data[0])
        for item in data[1:]:
            node = LinkedListNode(item)
            tail.next = node
            tail = node
        return head

    @staticmethod
    def make_cycle_list(data, n):
        """make a linked list (has a cycle) from a list

        Examples:
        >>> cl = LinkedListNode.make_cycle_list([1, 2, 3], 0)
        >>> cl.next.val
        2
        >>> cl.next.next.next.val
        1

        Args:
            data: data source, an iterable object.
            n: link the tail to the nth node. if n < 0 or n > len(data),
               the returned linked list has no cycle.

        Returns:
            the head of the linked list, class `LinkedLinkedListNode`.
        """
        head = LinkedListNode.make_linked_list(data)
        if head is None:
            return None

        if n < 0:
            return head

        # find the tail
        tail = head
        while tail.next:
            tail.has_cycle = True
            tail = tail.next
        tail.has_cycle = True
        # find nth node
        target, cnt = head, 0
        while target:
            if cnt == n:
                break
            cnt += 1
            target = target.next

        # link them
        tail.next = target
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

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return all(x == y for x, y in zip_longest(self, other, fillvalue=None))

    @staticmethod
    def make_tree(data):
        """make a binary tree from a list

        Examples:
        >>> t = TreeNode.make_tree([1, 2, 3, 4])
        >>> print(t.left)
        Tree(2-4)
        >>> print(t.right)
        Tree(3)

        Args:
            data: a tree node value list in level traversal order

        Returns:
            the root of the binary tree, class `TreeNode`.

        Raises:
            ValueError: If the given data can't be made a vliad binary tree.
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
