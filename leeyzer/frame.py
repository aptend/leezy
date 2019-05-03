from collections import defaultdict
from time import perf_counter
from copy import deepcopy
from functools import partial
from itertools import zip_longest
from textwrap import shorten, wrap


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


class Table:
    def __init__(self, **kwargs):
        self.__rows = [None]
        self.col_n = 0
        self.max_col_width = 30
        self.max_cell_length = 100
        self.pad = 2
        self.pad_str = ' ' * 2
        self.col_widths = []
        self.fillup = '<unkown>'
        self.lines = []

    def add_header(self, header):
        self.__rows[0] = [str(h) for h in header]

    def add_row(self, row):
        self.__rows.append([str(x) for x in row])

    def __determin_col_widths(self):
        for colx in zip_longest(*self.__rows, fillvalue=self.fillup):
            self.col_widths.append(
                min(self.max_col_width, max(map(len, colx))))
        self.col_n = max(map(len, self.__rows))
        self.dummy_iter = tuple(range(self.col_n))

    def _format_row(self, row):
        cells = []
        height = 0
        for text, i in zip_longest(row, self.dummy_iter, fillvalue=self.fillup):
            if self.max_cell_length > 6:
                text = shorten(text, self.max_cell_length)
            col_width = self.col_widths[i]            
            text = wrap(text, col_width)
            height = max(height, len(text))
            cells.append([f"{txt:<{col_width}}" for txt in text])

        for i in range(height):
            line = []
            for j, cell in enumerate(cells):
                if len(cell) <= i:
                    line.append(' ' * self.col_widths[j])
                else:
                    line.append(cell[i])
            pad = self.pad_str
            content = f'{pad}|{pad}'.join(line)
            self.lines.append(f'|  {content}  |')          
    
    def format_sep_line(self, ch='-', sep='+'):
        parts = []
        for w in self.col_widths:
            parts.append(ch*(w+2*self.pad))
        self.lines.append(f"{sep}{'+'.join(parts)}{sep}")

    def format_head(self):
        self.format_sep_line()
        self._format_row(self.__rows[0])
        self.format_sep_line(ch='=')

    def format_body(self):
        for row in self.__rows[1:]:
            self._format_row(row)
            self.format_sep_line()

    def __str__(self):
        self.__determin_col_widths()
        self.format_head()
        self.format_body()
        return '\n'.join(self.lines)


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
        table = Table()
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
                    func_name = f.__name__,
                    func_object = f,
                    args = args,
                    kwargs = kwargs,
                    output = output,
                    duration = duration)
                self.name_res[r.func_name].append(r)
                self.batch_res[i].append(r)
        self._post_process()


