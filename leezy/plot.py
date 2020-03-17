import sys
import json
from types import SimpleNamespace

try:
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
except ImportError:
    print("plot a heatmap needs package 'seaborn', try to install first:")
    print("    $ pip install seaborn")
    sys.exit(1)


from leezy.crawler import Net
from leezy.config import Urls


MAX_NUM = 3000


class DataFeeder:
    def __init__(self):
        self.net = Net()
        self.raw = self.net.get(Urls.api_problems_algo()).json()
        self.metadata = SimpleNamespace(**{
            'user_name': self.raw['user_name'],
            'num_solved': self.raw['num_solved'],
            'ac_easy': self.raw['ac_easy'],
            'ac_medium': self.raw['ac_medium'],
            'ac_hard': self.raw['ac_hard'],
        })

        ac = [None] * MAX_NUM
        attempt = [None] * MAX_NUM
        locked = [None] * MAX_NUM
        for stat in self.raw['stat_status_pairs']:
            try:
                front_id = int(stat['stat']['frontend_question_id'])
            except ValueError:
                continue
            if front_id > MAX_NUM:
                pass
            ac[front_id] = stat['status'] == 'ac'
            locked[front_id] = stat['paid_only']
            attempt[front_id] = stat['status'] == 'notac'

        max_id = MAX_NUM - 1
        while ac[max_id] is None:
            max_id -= 1
        max_id += 1
        ac = ac[:max_id]
        attempt = attempt[:max_id]
        locked = locked[:max_id]

        def none2false(arr):
            for i, x in enumerate(arr):
                if x is None:
                    arr[i] = False
            return arr

        self.max_id = max_id
        self.ac = none2false(ac)
        self.attempt = none2false(attempt)
        self.locked = none2false(locked)

class SNSPlotter:
    def __init__(self, feeder):
        self.feeder = feeder
        self.max_id = feeder.max_id
        self.ac_vector = feeder.ac

    def plot(self):
        sns.set()

        row_cnt, remaining = divmod(self.max_id, 100)
        row_cnt += 1
        size = row_cnt * 100
        vector = self.ac_vector + [False] * (size - self.max_id)
        data = np.reshape(vector, (row_cnt, 100))
        mask = np.zeros_like(data)
        mask[0, 0] = True
        mask[row_cnt-1, remaining:] = True

        with sns.axes_style("white"):
            f, ax = plt.subplots(figsize=(16, 9), dpi=100)
            sns.heatmap(
                data, mask=mask, ax=ax,
                center=0.6,
                linewidths=2,
                yticklabels=list(range(0, size, 100)),
                square=True,
                cbar=False,
            )

        plt.show()
