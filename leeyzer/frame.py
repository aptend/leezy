
from time import perf_counter
from copy import deepcopy


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

