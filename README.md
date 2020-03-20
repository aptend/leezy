# Leezy ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/leezy?style=plastic) ![PyPI](https://img.shields.io/pypi/v/leezy?style=plastic)


给Python的LeetCode刷题工具，在本地管理你的一题多解🍖🍗🥩


## Install

在终端执行：
```shell
$ pip install leezy
```

## Examples

0. 设置工作目录
```shell
$ leezy config --add core.workdir <DIR>
```
例如`leezy config --add core.workdir D:\leetcode`

1. 拉取题目


```shell
$ leezy pull 1
```


在`workdir`下生成如下目录和文件
```
$ tree
.
└── 001 - Two Sum
    ├── 001.html # 题目描述，在浏览器或者其他html预览器中查看
    └── 001_two-sum.py # solution模板，在这里编辑解法
```

```python
# 001_two-sum.py(initial)
from leezy import Solution, solution


class Q001(Solution):  # 继承Solution
    @solution    # 被solution装饰的函数将参与最后的结果输出或测试
    def twoSum(self, nums, target):
        pass


def main():
    q = Q001()
    q.add_case(q.case([2, 7, 11, 15], 9)) # 添加自己的测试用例
    q.run()


if __name__ == "__main__":
    main()
```

2. 尝试死磕多种解法
```python
# 001_two-sum.py(modified)
from leezy import Solution, solution


class Q001(Solution):
    @solution
    def twoSum(self, nums, target):
        for i,x in enumerate(nums):
            for j, y in enumerate(nums[i+1:], i+1):
                if x + y == target:
                    return [i, j]

    @solution
    def twoSum_sort(self, nums, target):
        L, i, j = len(nums), 0, len(nums)-1
        sorted_i = sorted(range(L), key=nums.__getitem__)
        while i < j:
            s = nums[sorted_i[i]] + nums[sorted_i[j]]
            if s > target:
                j -= 1
            elif s < target:
                i += 1
            else:
                return [sorted_i[i], sorted_i[j]]

    @solution
    def twoSum_hash(self, nums, target):
        hash_table = {}
        for i, x in enumerate(nums):
            another = target - x
            if x in hash_table:
                return [hash_table[x], i]
            else:
                hash_table[another] = i


def main():
    q = Q001()
    q.add_case(q.case([3, 2, 4], 6))
    q.add_case(q.case([3,3], 6))
    q.add_case(q.case([2, 7, 11, 15], 9))
    q.add_case(q.case([2, 7, 11, 15], 17))
    q.add_case(q.case([2, 7, 11, 15], 26))
    q.run()


if __name__ == "__main__":
    main()

```

3. 运行/查看结果
```shell
$ leezy run 1
+----------+----------+---------------+---------------+
|          |  twoSum  |  twoSum_sort  |  twoSum_hash  |
+==========+==========+===============+===============+
|  case 0  |  [1, 2]  |  [1, 2]       |  [1, 2]       |
+----------+----------+---------------+---------------+
|  case 1  |  [0, 1]  |  [0, 1]       |  [0, 1]       |
+----------+----------+---------------+---------------+
|  case 2  |  [0, 1]  |  [0, 1]       |  [0, 1]       |
+----------+----------+---------------+---------------+
|  case 3  |  [0, 3]  |  [0, 3]       |  [0, 3]       |
+----------+----------+---------------+---------------+
|  case 4  |  [2, 3]  |  [2, 3]       |  [2, 3]       |
+----------+----------+---------------+---------------+
```

4. 执行测试

在添加测试用例时，可以使用`assert_equal`添加期望的输出，这类测试用例将自动生成测试代码。
```python
# 001_two-sum.py(modified, testcase-added)

...

def main():
    q = Q001()
    q.add_case(q.case([3, 2, 4], 6))
    q.add_case(q.case([3,3], 6))
    q.add_case(q.case([2, 7, 11, 15], 9).assert_equal([0, 1]))
    q.add_case(q.case([2, 7, 11, 15], 17).assert_equal([0, 3]))
    q.add_case(q.case([2, 7, 11, 15], 26).assert_equal([2, 3]))
    q.run()
```

运行后，为3个 solution 各自运行3个测试，总共通过9个
```shell
$ leezy run 1
+----------+----------+-----------+
|          |  twoSum  |  two_sum  |
+==========+==========+===========+
|  case 0  |  [1, 2]  |  [1, 2]   |
+----------+----------+-----------+
|  case 1  |  [0, 1]  |  [0, 1]   |
+----------+----------+-----------+
.........                                                                   [100%]
9 passed in 0.09s
```

此外，测试用例支持`assert_true_with(fn)`，传入自定义测试函数。比如第1054题，要求结果数组相邻的两个数不相等，因此可以构建如下的测试函数

```python
from itertools import chain
from collections import Counter


class Q1054(Solution):
    @solution
    def rearrangeBarcodes(self, barcodes):
        # 452ms 92.03%
        N = len(barcodes)
        idx = chain(range(0, N, 2), range(1, N, 2))
        counter = Counter(barcodes)
        ans = [0] * N
        for x, cnt in counter.most_common():
            for _ in range(cnt):
                ans[next(idx)] = x
        return ans


def main():
    q = Q1054()

    def check(A):
        return all(x != nx for x, nx in zip(A, A[1:])

    q.add_case(q.case([1, 1, 1, 2, 2, 2]).assert_true_with(check))
    q.add_case(q.case([1, 2, 2, 2, 5]).assert_true_with(check))
    q.add_case(q.case([1, 1, 1, 1, 2, 2, 3, 3]).assert_true_with(check))
    q.run()
```

5. 提交解法

提交第一题的第三个解法

```shell
$ leezy submit 3@1
Is it OK to submit function 'twoSum'?

class Solution:
    def twoSum(self, nums, target):  
        hash_table = {}
        for i, x in enumerate(nums): 
            another = target - x
            if x in hash_table:
                return [hash_table[x], i]
            else:
                hash_table[another] = i

> [Yes/No]? y
----------------Accepted!----------------
  time used & rank: 40 ms faster than 93.07%
memory used & rank: 14.9 MB less than 6.25%

more helpful links:
    https://leetcode-cn.com/submissions/detail/55171676
    https://leetcode.com/problems/two-sum/discuss/

```

## Why leezy?

leezy名字来自于leetcode和lazy的组合。懒惰就是生产力。



如果你有以下标签所描述的倾向，leezy可能会给你一些参考：

【第一遍刷Leetcode】【使用本地编辑器】【愿意尝试一题多解】【少些重复print、测试用例】

还可以通过下面的问题进一步了解为什么要使用leezy

- 为什么不在线刷题？

    首先，因为是第一次做题，希望把重点放在解题本身，环境就使用自己习惯的就好。
    
    其次，在线run code的速度不稳定，不适合初期的debug。
    
    最后，在本地记录解法，管理起来更直接，离线也可以随时搜索复习。

    如果是第n遍刷题了，直接上web更方便。

- leezy的核心是什么？

    少写print，少写重复测试用例。和上面提到的标签所暗示的那样，做题大概率不能一次成功，需要在本地用自己的测试用例反复运行，打印结果，修改。当使用多个解法时，又需要重复这些工作。所以一次性写完这些重复的print、测试用例就是leezy最平常且简单的目的

- 和其他刷题工具有什么区别？

    其他的刷题工具，典型的有基于CLI的[leetcode-cli](https://github.com/skygragon/leetcode-cli), 基于VSCode的[leetcode for vscode](https://marketplace.visualstudio.com/items?itemName=shengchen.vscode-leetcode)(也基于leetcode-cli)，都支持完整的刷题流程：用户登录、题目拉取、编写、测试、提交、查看统计数据。本质是把网页版的功能在用另一套接口进行实现。

    leezy虽然也可以登录、拉取、测试以及提交，但相比上述工具，leezy对题目拉取后，**模板文件不再和网页上提供的模板一致，更方便实现一题多解的本地调试**。




## More things

### 命令行

使用`leezy [command]`完成拉取题目及设置相关操作
```
usage: leezy [options] COMMAND

Manage your Python solutions better

optional arguments:
  -h, --help     show this help message and exit
  -V, --version  show program's version number and exit
  --zone ZONE    'cn' or 'us', default is 'cn'
  --dir DIR      assign a temporary workdir for this session
  -v             verbose, use multiple -vv... to show more log

COMMANDS:
  use 'leezy <COMMAND> -h' to see more

  -⭐-
    show         show basic info of problems
    pull         pull problems to local files
    run          run your solutions, see outputs or test them
    submit       submit your solution to leetcode
    plot         show a heatmap of your all accepted solutions
    config       manage global configs
```

其中config支持git风格的属性配置，目前的可配置项为：


| name                     | description                                                  | default  |
| ------------------------ | ------------------------------------------------------------ | -------- |
| table.max_col_width      | 表格列的最大宽度                                             | 40字符   |
| table.max_content_length | 每个单元格支持的最长内容长度，超过部分将被截断(-1表示不截断) | 100字符  |
| core.workdir             | 刷题目录，每次pull、run都将基础该目录                        | 当前目录 |
| core.zone                | 刷题网站版本，中国区还是美区                                   | cn       |
| log.level                | 日志等级                                                     | warning  |

---


### 辅助类

针对使用链表或者树结构的题目，也提供了和网页版类似的基础类型，初始化的参数也和网页版保持一致。

从`leezy.assists`中导入

```python
from leezy.assists import TreeNode, ListNode

t = TreeNode.make_tree([1, 2, 3, 4, 5, None, 6])
print(type(t)) # <class 'leezy.assists.TreeNode'>
print(t)       # Tree(1-2-3-4-5-None-6)
print(t.left)  # Tree(2-4-5)
print(t.right) # Tree(3-None-6)


l = ListNode.make_linked_list([1, 2, 3, 4, 5])
print(type(l)) # <class 'leezy.assists.ListNode'>
print(l)       # 1->2->3->4->5
print(l.next)  # 2->3->4->5
```

现在支持的类型:

- TreeNode
- ListNode



除了手动使用`make_tree`, `make_linkedlist`构造，还提供了TreeContext，LinkedListContext，将`add_case`传入的集合类型参数自动构造为树或链表。省得每次添加测试用例都要写`make_*`函数

```python
from leezy import Solution, solution
from leezy.assists import TreeContext # 导入TreeContext


class Q700(Solution):
    @solution
    def searchBST(self, root, val):
        if root is None:
            return
        if root.val > val:
            return self.searchBST(root.left, val)
        elif root.val < val:
            return self.searchBST(root.right, val)
        else:
            return root
        
    @solution
    def search(self, root, val):
        while root:
            if root.val > val:
                root = root.left
            elif root.val < val:
                root = root.right
            else:
                return root
        return None


def main():
    q = Q700()
    q.set_context(TreeContext)  # 设置TreeContex
    q.add_case(q.case([4, 2, 7, 1, 3], 2)) # 这里传入的列表自动会被转化为Tree
    q.run()
```

为了进一步简化，`pull`命令支持--context选项
```
$ leezy pull --context tree 700 701
```

这样700、701题的源文件自动添加好TreeContext

---

更多功能和限制说明，待更新
