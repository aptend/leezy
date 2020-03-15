from .config import Config
from .errors import ConfigError
import pytest
from pathlib import Path
from unittest import mock



test_config_file = '.leeezy'


@pytest.fixture(scope='function')
def config():
    Config._instance = None
    Config.init.__globals__['CONFIG_FILE'] = test_config_file
    config = Config()
    return config


def test_config_get_default(config):
    assert config.get('core.workdir') == '.'
    assert config.get('core.zone') == 'cn'

    core_dict = config.get('core')
    assert core_dict['workdir'] == '.'
    assert core_dict['zone'] == 'cn'


def test_config_put(config):
    token = 'abcdefg'
    expires = 12432552
    config.put('session.token', token)
    config.put('session.expires', expires)

    sess = config.get('session')
    assert sess['expires'] == expires

    file = Path(test_config_file)
    content = file.read_text()
    assert token in content
    assert str(expires) in content

    Config._instance = None
    c = Config()
    assert config.get('session.token') == token
    file.write_text('{}')


def test_config_patch(config):
    config.patch('universe.mystery.answer', 42)
    assert config.get('universe.mystery.answer') == 42
    assert len(config.file_data) == 0


def test_config_patch_error(config):
    config.patch('a.b.c', 42)
    with pytest.raises(ConfigError):
        config.patch('a.b.c.d', 41)
