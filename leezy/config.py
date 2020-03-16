import json
import logging
from collections import abc, defaultdict
from functools import partial
from pathlib import Path
from types import SimpleNamespace

from leezy.errors import ConfigError


__all__ = ['config']


DEFAULT = {
    "table": {
        "max_col_width": 30,
        "max_content_length": 100
    },
    "core": {
        "workdir": ".",
        "zone": "cn"
    },
    "log": {
        "level": "INFO"
    },
    "timeout": {
        "submit": 10,
        "net": 5
    }
}


CHECK_FUNCTIONS = {
    "table.max_col_width": int,
    "table.max_content_length": int
}

CONFIG_FILE = './.leezy'


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
        self.mem_data = {}
        try:
            content = self.cfg_path.read_text(encoding='utf8')
            self.file_data = json.loads(content)
        except FileNotFoundError:
            self.reset()

    def reset(self):
        self.mem_data = {}
        self.file_data = {}
        self.commit()

    def commit(self):
        with open(self.cfg_path, 'w') as f:
            json.dump(self.file_data, f, indent=2)

    def _get(self, src_data, key):
        next_item = src_data
        for part in key.split('.'):
            try:
                next_item = next_item[part]
            except KeyError:
                raise
        return next_item

    def _get_from_chain(self, key, src_chain):
        for src_data in src_chain:
            try:
                ret = self._get(src_data, key)
            except KeyError:
                pass
            else:
                return ret
        else:
            raise ConfigError(f"config: {key!r} is not found")

    def get(self, key):
        return self._get_from_chain(key, (self.mem_data,
                                          self.file_data,
                                          self.default_data))

    def _get_all(self, mapping, prefix):
        for key, value in mapping.items():
            next_prefix = prefix+'.'+key if prefix else key
            if isinstance(value, abc.Mapping):
                yield from self._get_all(value, next_prefix)
            else:
                yield next_prefix, value

    def get_all_file_data(self, prefix=''):
        yield from self._get_all(self.file_data, prefix)

    def _put(self, key, value, src_data):
        check_fn = CHECK_FUNCTIONS.get(key, None)
        if check_fn:
            try:
                check_fn(value)
            except:
                raise ConfigError(f"config: {value!r} is invalid for {key!r}")
        parts = key.split('.')
        next_item = src_data
        for part in parts[:-1]:
            if part not in next_item:
                next_item[part] = {}
            next_item = next_item[part]

        if not isinstance(next_item, dict):
            path = '.'.join(parts[:-1])
            raise ConfigError(f"config: failed to assign {key!r}, "
                              f"because {path!r} is not a map")
        next_item[parts[-1]] = value

    def put(self, key, value):
        """update config entry and persist the data"""
        self._put(key, value, self.file_data)
        self.commit()

    def patch(self, key, value):
        """update config entry in memory"""
        self._put(key, value, self.mem_data)

    def _del(self, key, src_data):
        parts = key.split('.')
        next_item = src_data
        for part in parts[:-1]:
            try:
                next_item = next_item[part]
            except KeyError:
                raise
        try:
            del next_item[parts[-1]]
        except KeyError:
            raise

    def delete(self, key):
        deleted = 0
        for src_data in (self.mem_data, self.file_data):
            try:
                self._del(key, src_data)
                deleted += 1
            except KeyError:
                pass
        if deleted == 0:
            raise ConfigError(f"config: {key!r} is not found")
        self.commit()
        return deleted


class Urls:
    PORTAL = None

    @classmethod
    def init(cls, zone):
        if zone == 'cn':
            cls.PORTAL = 'https://leetcode-cn.com'
        else:
            cls.PORTAL = 'https://leetcode.com'

    @staticmethod
    def portal():
        return Urls.PORTAL

    @staticmethod
    def graphql():
        return f"{Urls.PORTAL}/graphql"

    @staticmethod
    def api_problems():
        return f"{Urls.PORTAL}/api/problems/algorithms"

    @staticmethod
    def submit(slug_title):
        # POST  https://leetcode-cn.com/problems/two-sum/submit/
        return f"{Urls.PORTAL}/problems/{slug_title}/submit/"

    @staticmethod
    def submission_detail(sub_id):
        # GET https://leetcode-cn.com/submissions/detail/53947058/
        return f"{Urls.PORTAL}/submissions/detail/{sub_id}"

    @staticmethod
    def submission_check(sub_id):
        # GET https://leetcode-cn.com/submissions/detail/53947058/check/
        return f"{Urls.PORTAL}/submissions/detail/{sub_id}/check/"

    @staticmethod
    def dicussion(slug_title):
        # you may don't want to see discussion in cn for now
        return f"https://leetcode.com/problems/{slug_title}/discuss/"


config = Config()
Urls.init(config.get('core.zone'))
