import json
from collections import abc, defaultdict
from functools import partial
from pathlib import Path

from leezy.errors import ConfigError


__all__ = ['config']

DEFAULT = {
    "table": {
        "max_col_width": 30,
        "max_content_length": 100
    },
    "core": {
        "workdir": "."
    },
    "log": {
        "level": "INFO"
    }
}


CHECK_MAP = {
    "table.max_col_width": int,
    "table.max_content_length": int
}

CONFIG_FILE = '~/.leezy'


def recursive_dd():
    return defaultdict(recursive_dd)


hook = partial(defaultdict, recursive_dd)


class Config:
    """
    >>> config = Config()
    >>> config.put('answer', 42)
    >>> config.get('answer')
    42
    >>> config.put('user.name', 'x')
    >>> config.put('user.email', 'x@example.com')
    >>> config.get('user')
    {'name': 'x', 'email': 'x@example.com'}
    >>> config.reset()
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.init(cls._instance)
        return cls._instance

    def init(self):
        self.cfg_path = Path(CONFIG_FILE).expanduser()
        self.default_data = DEFAULT
        try:
            self.data = json.loads(self.cfg_path.read_text(
                encoding='utf8'), object_hook=hook)
        except FileNotFoundError:
            self.reset()

    def _expand_loc_expr(self, dot_key):
        return ''.join([f"[{x!r}]" for x in dot_key.split('.')])

    def reset(self):
        self.data = recursive_dd()
        self._write_down({})

    def _write_down(self, data):
        with open(self.cfg_path, 'w') as f:
            json.dump(data, f)

    def delete(self, key):
        loc_expr = self._expand_loc_expr(key)
        del_expr = f"del self.data{loc_expr}"
        try:
            exec(del_expr)
        except (KeyError, TypeError):
            raise ConfigError(f"config: {key!r} is not found")
        self._write_down(self.data)

    def put(self, key, value):
        check = CHECK_MAP.get(key, None)
        if check:
            try:
                check(value)
            except:
                raise ConfigError(
                    f"config: {value!r} is not valid for {key!r}")
        loc_expr = self._expand_loc_expr(key)
        put_expr = f"self.data{loc_expr} = value"
        try:
            exec(put_expr)
        except (KeyError, TypeError):
            raise ConfigError(f"config: {key!r} is a invalid key")
        self._write_down(self.data)

    def get_from_default(self, key):
        loc_expr = self._expand_loc_expr(key)
        try:
            exec(f"standby = self.default_data{loc_expr}")
        except (KeyError, TypeError):
            raise ConfigError(f"config: {key!r} is not found")
        else:
            return locals()['standby']

    def get(self, key):
        loc_expr = self._expand_loc_expr(key)
        get_expr = f"value = self.data{loc_expr}"
        try:
            exec(get_expr)
        except (KeyError, TypeError):
            raise ConfigError(f"config: {key!r} is not found")
        get_value = locals()['value']
        if isinstance(get_value, defaultdict):
            if len(get_value) == 0:
                return self.get_from_default(key)
            return dict(get_value)
        return get_value

    def _get_all(self, mapping, prefix):
        for key, value in mapping.items():
            next_prefix = prefix+'.'+key if prefix else key
            if isinstance(value, abc.Mapping):
                yield from self._get_all(value, next_prefix)
            else:
                yield next_prefix, value

    def get_all(self, prefix=''):
        yield from self._get_all(self.data, prefix)


config = Config()
