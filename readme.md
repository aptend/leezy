leetcode本地刷题小工具，少写一点print
----


# Why am I here?

如果以下标签所描述的倾向，leeyzer可能会给你一些参考：

【第一遍刷Leetcode】【使用本地编辑器】【愿意尝试一题多解】【希望少写print】

还可以通过下面的问题进一步了解为什么要使用leeyzer

- 为什么不在线刷题？

    在线编辑器没有智能提示，run code的速度不稳定，不适合初期的debug。
    因为是第一次做题，希望把重点放在解题本身，环境就使用自己习惯的就好。
    在本地通过自己构想的测试用例后，再到网上提交。如果是第n遍刷题了，直接上web更方便。

- leeyzer的核心是什么？

    少些print。和上面提到的标签所暗示的那样，做题大概率不能一次成功，需要在本地用自己的测试用例反复运行，查看结果，debug。当使用多个解法时，又需要重复这些工作。所以一次性写完这些重复的print就是leeyzer最平常的目的

- 和其他刷题工具有什么区别？
    


- 为什么没有登陆功能？




# Quick Start

## install
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
    q.test()


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
    q.test()


if __name__ == "__main__":
    main()

```
3. 运行/查看结果
```shell
$ python 001/001_two-sum.py
[1, 2]  [1, 2]  [1, 2]
[0, 1]  [0, 1]  [0, 1]
[0, 1]  [0, 1]  [0, 1]
[0, 3]  [0, 3]  [0, 3]
[2, 3]  [2, 3]  [2, 3]
```

# Features

## 题目拉取
## 辅助类
