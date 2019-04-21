给懒汉的leetcode本地刷题小工具，少写一点print


1. 编写自己的solution
```python
# 617_merge-two-binary-trees.py
from leeyer import solution, timeit, Solution, make_tree, TreeNode

class Q617(Solution):
    @solution
    def merge_better_inplace(self, t1, t2):
        if t1 and t2:
            t1.val += t2.val
            t1.left = self.merge(t1.left, t2.left)
            t1.right = self.merge(t1.right, t2.right)
            return t1
        else:
            return t1 or t2  
    
    
    @timeit
    @solution
    def merge_better(self, t1, t2):
        if t1 and t2:
            cur_node = TreeNode(t1.val + t2.val)
            cur_node.left = self.merge(t1.left, t2.left)
            cur_node.right = self.merge(t1.right, t2.right)
            return cur_node
        else:
            return t1 or t2  

def main():
    q = Q617()
    q.add_args(make_tree([1, 3, 2, 5]), make_tree([2, 1, 3, None, 4, None, 7]))
    q.add_args(make_tree([1]), make_tree([2]))
    q.test()

if __name__ == "__main__":
    main()
```

2. 运行
```shell
$ python 617_merge-two-binary-trees.py
Tree(3-4-5-5-4-None-7)  Tree(3-4-5-5-4-None-7)(0.0000s)
Tree(3)  Tree(3)(0.0000s)

$
```
