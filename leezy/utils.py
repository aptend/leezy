import re
from itertools import zip_longest
from textwrap import wrap, shorten
from getpass import getuser, getpass
from datetime import datetime
from leezy.errors import ConfigError


class SecretDialog:
    def __init__(self, prelude):
        self.prelude = prelude

    def collect(self):
        print(self.prelude)
        username = input("> username: ")
        password = getpass("> password: ")
        return username, password


class YesNoDialog:
    def __init__(self, prelude):
        self.prelude = prelude

    def collect(self):
        print(self.prelude)
        while True:
            answer = input("> [Yes/No]?")
            if answer.upper() in ['Y', 'YES', 'YEAH']:
                return True
            elif answer.upper() in ['N', 'No']:
                return False
            else:
                print(f'< what does {answer!r} mean?')


class SessionTokenDialog:
    def collect(self):
        token = input('> LEETCODE_SESSION token: ')
        print('\n you can set expires using following format:\n',
              '    1.absolute timestamp\n',
              '    2.absolute date like 2020-03-31T00:39:14.945Z\n',
              "    3.relative date like '10s', '11h', '12d'")
        expires = input("> expires: ")

        match = re.findall(r'^(\d+)([dhms]?)$', expires)
        if match:
            num, ty = match[0]
            now_ts = datetime.timestamp(datetime.now())
            num = int(num)
            if ty == '':
                if num <= now_ts:
                    raise ConfigError('Expires is too old')
                expires = num
            elif ty == 'd':
                expires = now_ts + num * 3600 * 24
            elif ty == 'h':
                expires = now_ts + num * 60 * 60
            elif ty == 'm':
                expires = now_ts + num * 60
            elif ty == 's':
                expires = now_ts + num
        else:
            try:
                expires = datetime.strptime(expires, '%Y-%m-%dT%H:%M:%S.%fZ')\
                                  .timestamp()
            except ValueError:
                raise ConfigError('Unrecognized expires formt')
        return (token, int(expires))


if __name__ == "__main__":
    print(SessionTokenDialog().collect())


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
