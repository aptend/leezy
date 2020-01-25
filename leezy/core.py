import os
import inspect

from pathlib import Path
from collections import defaultdict
from time import perf_counter
from copy import deepcopy
from enum import Enum
from io import StringIO
from textwrap import shorten, dedent

import pytest

from leezy.utils import Table
from leezy.config import config
from leezy.assists import Context


def solution(func):
    """Attach the `func` a solution marker
    """
    func.__dict__['solution'] = True
    return func


def timeit(func):
    """Attach the `func` a time marker
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
        self.case_num = 0
        self.func_name = ''
        self.func_object = None
        self.args = None
        self.kwargs = None
        self.output = None
        self.duration = 0
        self.__dict__.update(kwargs)

    def __str__(self):
        if hasattr(self.func_object, 'timeit'):
            return (f'({self.duration:.{self.func_object.precision}f}s)'
                    f'{self.output}')
        return f'{self.output}'


FnTempl = """
def test_{func}_case_{case_num}(solution_obj, case{case_num}):
    output = solution_obj.{func}(*case{case_num}.args, **case{case_num}.kwargs)
    assert case{case_num}.assert_fn(output)

"""

OutputTempl = """
def test_{func}_case_{case_num}(solution_obj, case{case_num}):
    output = solution_obj.{func}(*case{case_num}.args, **case{case_num}.kwargs)
    assert output == case{case_num}.assert_output

"""


class TestKind(Enum):
    Null = 0
    Output = 1
    WithFn = 2


class Testcase:
    def __init__(self, args, kwargs):
        self.args = list(args)
        self.kwargs = kwargs
        self.assert_output = None
        self.assert_fn = None
        self._test_kind = TestKind.Null

    def __str__(self):
        args = [str(arg) for arg in self.args]
        for k, v in self.kwargs:
            args.append(f"{k}={v}")
        sig = ','.join(args)
        return f"Testcase({shorten(sig, 100)})"

    def __repr__(self):
        return f'<{self}>'

    def test_kind(self):
        return self._test_kind

    def assert_equal(self, x):
        self.assert_output = x
        self._test_kind = TestKind.Output
        return self

    def assert_true_with(self, fn):
        self.assert_fn = fn
        self._test_kind = TestKind.WithFn
        return self


class Solution:
    def __init__(self):
        self.solutions = [item for item in self.__class__.__dict__.values()
                          if hasattr(item, 'solution')]
        self.nontest_cases = []
        self.test_cases = []
        self.context = Context

    def __str__(self):
        n = len(self.solutions)
        plural = 's' if n > 0 else ''
        return f"{self.__class__.__name__} with {n} solution{plural}"

    def __repr__(self):
        return f"<{self}>"

    def set_context(self, context_cls):
        self.context = context_cls

    def case(self, *args, **kwargs):
        args, kwargs = self.context.transform_args(args, kwargs)
        return Testcase(deepcopy(args), deepcopy(kwargs))

    def add_case(self, case):
        if case.test_kind() == TestKind.Null:
            self.nontest_cases.append(case)
        else:
            self.test_cases.append(case)

    # deprecated method. use add_case instead.
    def add_args(self, *args, **kwargs):
        self.add_case(self.case(*args, **kwargs))

    def _run_solution(self, solution, args, kwargs):
        ags, kws = deepcopy(args), deepcopy(kwargs)
        t1 = perf_counter()
        output = solution.__call__(self, *ags, **kws)
        duration = perf_counter() - t1
        return output, duration

    def run_cases_to_table(self):
        result_by_case = []
        for i, case in enumerate(self.nontest_cases):
            case_row = []
            for f in self.solutions:
                output, duration = self._run_solution(
                    f, case.args, case.kwargs)
                r = ResultUnit(
                    case_num=i,
                    func_name=f.__name__,
                    func_object=f,
                    args=case.args,
                    kwargs=case.kwargs,
                    output=output,
                    duration=duration)
                case_row.append(r)
            result_by_case.append(case_row)

        # draw table
        if not result_by_case:
            return
        table_settings = config.get('table')
        table = Table(**table_settings)
        header = ['']
        header.extend([func.__name__ for func in self.solutions])
        table.add_header(header)
        for case_num, case_row in enumerate(result_by_case):
            row = [f'case {case_num}']
            row.extend(case_row)
            table.add_row(row)
        print(table)

    def run_cases_to_test(self):
        if not self.test_cases:
            return
        test_code = StringIO()
        for i, case in enumerate(self.test_cases):
            for func in self.solutions:
                if case.test_kind() == TestKind.WithFn:
                    templ = FnTempl
                elif case.test_kind() == TestKind.Output:
                    templ = OutputTempl
                code = templ.format(case_num=i, func=func.__name__)
                test_code.write(code)

        plugin_text = """
        class FixturePlugin:
            def __init__(self, q_instance):
                self.q = q_instance

            @pytest.fixture(scope='module')
            def solution_obj(self):
                return self.q
        """

        case_text = """
            @pytest.fixture(scope='module')
            def case{case_num}(self):
                return self.q.test_cases[{case_num}]
        """
        for i in range(len(self.test_cases)):
            plugin_text += case_text.format(case_num=i)

        exec(dedent(plugin_text))

        fixture_class = locals()['FixturePlugin']

        project_dir = Path(inspect.getfile(self.__class__)).parent.parent
        test_filename = f'test_{self.__class__.__name__}.py'
        test_file = project_dir / test_filename
        with open(test_file, 'w') as f:
            f.write(test_code.getvalue())
        try:
            pytest.main(['-q', str(test_file)], plugins=[fixture_class(self)])
        finally:
            os.remove(test_file)

    def run(self):
        self.run_cases_to_table()
        self.run_cases_to_test()
