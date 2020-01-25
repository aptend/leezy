from itertools import zip_longest
from textwrap import wrap, shorten


class Table:
    """ Table format tool

    Example:
    >>> table = Table()
    >>> table.add_header(['', 'Earth', 'Moon'])
    >>> table.add_row(['Size', '42', '42'])
    >>> print(table)
    +--------+---------+--------+
    |        |  Earth  |  Moon  |
    +========+=========+========+
    |  Size  |  42     |  42    |
    +--------+---------+--------+

    Args(Optional):
        max_col_width: int, max column width
        max_content_width: int, exceeded content will be shortened
    """
    def __init__(self, **kwargs):
        self.__rows = [None]
        self.col_n = 0
        self.max_col_width = int(kwargs.get('max_col_width', 30))
        self.max_content_length = int(kwargs.get('max_content_length', 100))
        self.pad = 2
        self.pad_str = ' ' * 2
        self.col_widths = []
        self.fillup = '<unkown>'
        self.lines = []

    def add_header(self, header):
        self.__rows[0] = [str(h) for h in header]

    def add_row(self, row):
        self.__rows.append([str(x) for x in row])

    def __determine_col_widths(self):
        for colx in zip_longest(*self.__rows, fillvalue=self.fillup):
            self.col_widths.append(
                min(self.max_col_width, max(map(len, colx))))
        self.col_n = max(map(len, self.__rows))
        self.dummy_iter = tuple(range(self.col_n))

    def _format_row(self, row):
        cells = []
        height = 0
        for text, i in zip_longest(row, self.dummy_iter, fillvalue=self.fillup):
            if self.max_content_length > 6:
                text = shorten(text, self.max_content_length)
            col_width = max(1, self.col_widths[i])
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
            parts.append(ch * (w + 2 * self.pad))
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
        self.__determine_col_widths()
        self.format_head()
        self.format_body()
        return '\n'.join(self.lines)
