给Python的leetcode本地刷题小工具，少写一点print

# Quick Start

## install

Requirement: 
- **Python >= 3.6**
- requests >= 2.18.0

在终端执行：
```shell
$ git clone https://github.com/aptend/leezyer.git

$ python setup.py install
```
## example

1. 拉取题目

在终端进入刷题目录：

 `$ python -m leeyzer pull 1`

将在当前目录生成如下目录和文件
```
$ tree
.
└── 001
    ├── 001.html # 题目描述，在浏览器或者其他html预览器中查看
    └── 001_two-sum.py # solution模板，在这里编辑解法
```

```python
# 001_two-sum.py(initial)
from leeyzer import Solution, solution


class Q001(Solution):  # 继承Solution
    @solution    # 被solution装饰的函数将参与最后的结果输出
    def twoSum(self, nums, target):
        pass


def main():
    q = Q001()
    q.add_args([2, 7, 11, 15], 9) # 添加自己的测试用例
    q.run()


if __name__ == "__main__":
    main()
```

2. 尝试死磕多种解法
```python
# 001_two-sum.py(modified)
from leeyzer import Solution, solution


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
    q.add_args([3, 2, 4], 6)
    q.add_args([3,3], 6)
    q.add_args([2, 7, 11, 15], 9)
    q.add_args([2, 7, 11, 15], 17)
    q.add_args([2, 7, 11, 15], 26)
    q.run()


if __name__ == "__main__":
    main()

```
3. 运行/查看结果
```shell
$ python 001/001_two-sum.py
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

# Why am I here?

如果以下标签所描述的倾向，leeyzer可能会给你一些参考：

【第一遍刷Leetcode】【使用本地编辑器】【愿意尝试一题多解】【希望少写print】

还可以通过下面的问题进一步了解为什么要使用leeyzer

- 为什么不在线刷题？

    在线编辑器没有智能提示，run code的速度不稳定，不适合初期的debug。
    因为是第一次做题，希望把重点放在解题本身，环境就使用自己习惯的就好。
    在本地通过自己构想的测试用例后，再到网上提交。如果是第n遍刷题了，直接上web更方便。

- leeyzer的核心是什么？

    少写print。和上面提到的标签所暗示的那样，做题大概率不能一次成功，需要在本地用自己的测试用例反复运行，打印结果，修改。当使用多个解法时，又需要重复这些工作。所以一次性写完这些重复的print就是leeyzer最最平常且简单的目的

- 和其他刷题工具有什么区别？
    
    其他的刷题工具，典型的有基于CLI的[leetcode-cli](https://github.com/skygragon/leetcode-cli), 基于VSCode的[leetcode for vscode](https://marketplace.visualstudio.com/items?itemName=shengchen.vscode-leetcode)，都支持完整的刷题流程：用户登录、题目拉取、编写、测试、提交、查看统计数据。本质也是把网页版的功能在用另一套接口进行实现。
    
    leeyzer仅仅把目标放在拉取、编写、测试上。相比上述工具，leeyzer对题目拉取后，模板文件不再和网页上提供的模板一致，更方便实现一题多解的本地调试

- 之后有什么计划，会支持更完整的流程吗，比如登录、提交？

    会考虑。但目前觉得提交并不是第一遍刷题过程中的阻碍点。个人更希望有一个导出功能，将每个solution连带其docstring导出为md格式，这样鼓励对每一个solution做笔记。最后这个md可以用作博客或者github仓库的原料。当然目前还要继续完善刷题的辅助类





# Features

## 命令行

使用`python -m leeyzer [command]`完成拉取题目及设置相关操作
```
$ python -m leeyzer -h
usage: python -m leezyer [-h]  ...

optional arguments:
  -h, --help  show this help message and exit

commands:
  use 'python -m leeyzer command -h' to see more

    pull      拉取题目到本地文件
    show      打印编号的题目
    update    更新题库
    config    全局配置
```

其中config支持git风格的属性配置
```
usage: python -m leezyer config [-h] [--add | --unset | --list]

optional arguments:
  -h, --help  show this help message and exit
  --add       name value
  --unset     name
  --list
```

目前支持使用config设置solution结果的表格设置, example:

```
$ python -m leeyzer config --add table.max_col_width 50

$ python -m leeyzer config --add table.max_content_length -1

$ python -m leeyzer config --unset table
```

可用配置项：


| name | description | default | 
|---|---|---|
| table.max_col_width | 表格列的最大宽度 | 40字符 |
| table.max_content_length | 每个单元格支持的最长内容长度，超过部分将被截断(-1表示不截断) | 100字符 |

---


## 辅助类

针对使用链表或者树结构的题目，也提供了和网页版相同的基础类型，初始化的参数也和网页版保持一致。

从`leeyzer.assists`中导入

```python
from leeyzer.assists import TreeNode, ListNode

t = TreeNode.make_tree([1, 2, 3, 4, 5, None, 6])
print(type(t)) # <class 'leeyzer.assists.TreeNode'>
print(t)       # Tree(1-2-3-4-5-None-6)
print(t.left)  # Tree(2-4-5)
print(t.right) # Tree(3-None-6)


l = ListNode.make_linked_list([1, 2, 3, 4, 5])
print(type(l)) # <class 'leeyzer.assists.ListNode'>
print(l)       # 1->2->3->4->5
print(l.next)  # 2->3->4->5
```

现在支持的类型:

- TreeNode
- ListNode

---

## 计时⏲

除了solution装饰器，还有一个timeit装饰器，可以输出每个solution的运行时间
```
from leeyzer improt solution, timeit, Solution
...

@timeit
@solution
def s2(self):
    time.sleep(1.234)
    return 42
...

#output
+----------+---------------+
|          |  s2           |
+==========+===============+
|  case 0  |  42(1.2342s)  |
+----------+---------------+
```

timeit的默认精度为小数点后4位，自定义精度可以使用@timeit_with_precison(precison: int)
