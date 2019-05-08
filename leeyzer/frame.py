from collections import defaultdict
from time import perf_counter
from copy import deepcopy

from leeyzer.utils import Table
from leeyzer.utils import CFG

def solution(func):
    """decorator. Attach the `func` a solution marker
    """
    func.__dict__['solution'] = True
    return func


def timeit(func):
    """decorator. Attach the `func` a time marker
    """
    func.__dict__['timeit'] = True
    func.__dict__['precision'] = 4
    return func


def timeit_with_precision(precision):
    def inject(func):
        func.__dict__['timeit'] = True
        func.__dict__['precision'] = int(precision)
        return func
    return inject


class ResultUnit:
    def __init__(self, **kwargs):
        self.batch_num = 0
        self.func_name = ''
        self.func_object = None
        self.args = None
        self.kwargs = None
        self.output = None
        self.duration = 0
        self.__dict__.update(kwargs)

    def __str__(self):
        if hasattr(self.func_object, 'timeit'):
            return (f'{self.output}'
                    f'({self.duration:.{self.func_object.precision}f}s)')
        return f'{self.output}'


class Solution:
    def __init__(self):
        self._test_args = []
        self.solutions = [item for item in self.__class__.__dict__.values()
                          if hasattr(item, 'solution')]
        self.name_res = defaultdict(list)
        self.batch_res = defaultdict(list)

    def add_args(self, *args, **kwargs):
        self._test_args.append((args, kwargs))

    def outputs_by_name(self, name):
        return [r.output for r in self.name_res[name]]

    def outputs_by_batch(self, batch):
        return [r.output for r in self.batch_res[batch]]

    def _run_solution(self, solution, args, kwargs):
        ags, kws = deepcopy(args), deepcopy(kwargs)
        t1 = perf_counter()
        output = solution.__call__(self, *ags, **kws)
        duration = perf_counter() - t1
        return output, duration

    def _post_process(self):
        if len(self.name_res) < 1:
            return
        table_settings = CFG.open()['table']
        table = Table(**table_settings)
        header = ['']
        header.extend(self.name_res.keys())
        table.add_header(header)
        for batch in self.batch_res:
            row = [f'case {batch}']
            row.extend(self.batch_res[batch])
            table.add_row(row)
        print(table)

    def test(self):
        for i, (args, kwargs) in enumerate(self._test_args):
            for f in self.solutions:
                output, duration = self._run_solution(f, args, kwargs)
                r = ResultUnit(
                    batch_num=i,
                    func_name=f.__name__,
                    func_object=f,
                    args=args,
                    kwargs=kwargs,
                    output=output,
                    duration=duration)
                self.name_res[r.func_name].append(r)
                self.batch_res[i].append(r)
        self._post_process()
