from unittest import mock
import pytest
import textwrap
import re

from .templite import (Templite, CodeBuilder,
                      TempliteSyntaxError, TempliteRenderError)


@pytest.fixture
def empty_templite():
    return Templite("")


def test_codebuilder():
    builder = CodeBuilder()
    builder.add_line('def hi():')
    builder.indent()
    builder.add_line('print("hello, world")')
    builder.dedent()
    builder.add_empty_line()
    builder.add_line('DEBUG = True')
    global_ns = builder.globals_after_exec()
    assert 'hi' in global_ns and 'DEBUG' in global_ns
    assert global_ns['DEBUG'] is True


def test_codebuilder_unbalanced():
    builder = CodeBuilder()
    builder.add_line('def hi():')
    builder.indent()
    builder.add_line('print("hello, world")')
    with pytest.raises(SyntaxError):
        builder.globals_after_exec()


def test_expr(empty_templite):
    t = empty_templite
    code = t._expr("obj1.attr.val|obj2.dump")
    assert code == "do_dots(c_obj2, 'dump')(do_dots(c_obj1, 'attr', 'val'))"
    assert len(t.all_variables) == 2
    assert 'obj1' in t.all_variables and 'obj2' in t.all_variables


@pytest.mark.parametrize('expr', ['51day', 'my-goods',
                                  'flag and flag1', 'class.upper'])
def test_invalid_expr(empty_templite, expr):
    t = empty_templite
    with pytest.raises(TempliteSyntaxError):
        t._expr(expr)
    assert len(t.all_variables) == 0


def test_do_dots(empty_templite):
    t = empty_templite
    assert 'N' == t._do_dots('name', 'upper', '0')
    import sys
    assert 'Win32' == t._do_dots(sys, 'platform', 'title')


@pytest.mark.parametrize(
    'args', [['day', 'nomethod'], [mock, 'nomock()'], [[1, 2], '3']])
def test_do_dots_caught_fail(empty_templite, args):
    t = empty_templite
    with pytest.raises(TempliteRenderError):
        t._do_dots(args[0], *args[1:])


@pytest.mark.parametrize(
    'text',
    [
        '{& unkown tag &}',  # 未知tag
        '{% if a %} skr ',  # 没有end
        'skr {% endif %}',  # 单独end
        '{% if a %} skr {% endfor %}',  # 错误匹配
        # 错误语法
        '{% if a: %} skr {% endif %}',
        '{% if a %} skr {% end if %}',
        '{% for a in p | transfer %} {{a}} {% endfor %}',  # 多余的空格
        # 未支持语法
        '{% while a %} skr {% endwhile %}'
        '{{ name().upper }}',
        '{% if a and b %} skr {% endif %}',
        '{% for a, b in a.enumerate %} skr {% endfor %}',
    ]
)
def test_syntax_error_actions(text):
    with pytest.raises(TempliteSyntaxError):
        Templite(text)


TEXT_VAR = """
<p>Welcome, {{ user_name.upper|json_dump }}!</p>
<p>Ula, {{ user_age }}!</p>
{# this is a comment #}
"""

TEXT_IF = """
-----------Cyberpunk-------------
{% if position %}
Mid-night Bar{% if time %} · 2077 {% endif %}
{% endif %}
...
"""

TEXT_FOR = """
Points:
{% for x in xs -%}
{% for y in ys -%}
    ({{ x }}, {{ y }})
{% endfor -%}
{% endfor -%}
"""


def test_tokens(empty_templite):
    t = empty_templite
    assert len(t._tokens(TEXT_VAR)) == 7
    assert len(t._tokens(TEXT_IF)) == 9
    assert len(t._tokens(TEXT_FOR)) == 13


def assert_executable_codebuilder(code):
    global_ns = code.globals_after_exec()
    assert 'render_template' in global_ns
    assert callable(global_ns['render_template'])


def test_build_var(empty_templite):
    t = empty_templite
    tokens = t._tokens(TEXT_VAR)
    code = t._build(tokens)
    code_str = str(code)
    # 纯变量，使用buffer写入，因此有expand_result的调用
    assert 'expand_result([' in code_str
    assert "to_str(c_json_dump(do_dots(c_user_name, 'upper')))" in code_str
    # 可以成功执行，生成代码没有语法错误
    assert_executable_codebuilder(code)


def test_build_if(empty_templite):
    t = empty_templite
    tokens = t._tokens(TEXT_IF)
    code = t._build(tokens)
    code_str = str(code)
    assert 'if c_position:' in code_str
    assert 'if c_time' in code_str
    assert_executable_codebuilder(code)


def test_build_for(empty_templite):
    t = empty_templite
    tokens = t._tokens(TEXT_FOR)
    code = t._build(tokens)
    code_str = str(code)
    assert 'for c_x in c_xs:' in code_str
    assert 'for c_y in c_ys:' in code_str
    assert_executable_codebuilder(code)


def test_render_var():
    import json
    from functools import partial
    t = Templite(TEXT_VAR, {
        'format_price': lambda x: f"{x:.2f}",
        'json_dump': partial(json.dumps, ensure_ascii=False)
    })
    result = t.render({
        'user_name': 'Gimo',
        'user_age': 42,
    })
    expected = """
    <p>Welcome, "GIMO"!</p>
    <p>Ula, 42!</p>

    """
    assert textwrap.dedent(expected) == result

    result = t.render({
        'user_name': '梭哈',
        'user_age': 33,
    })
    expected = """
    <p>Welcome, "梭哈"!</p>
    <p>Ula, 33!</p>

    """
    assert textwrap.dedent(expected) == result


def test_render_if():
    t = Templite(TEXT_IF)
    result = t.render({
        'position': True,
        'time': True,
    })
    assert "Mid-night Bar · 2077" in result

    result = t.render({
        'position': True,
        'time': False,
    })
    assert "Mid-night Bar" in result
    assert "2077" not in result

    result1 = t.render({
        'position': False,
        'time': False,
    })
    result2 = t.render({
        'position': False,
        'time': True,
    })
    assert result1 == result2
    assert "Bar" not in result1 and "2077" not in result1


def test_render_for():
    t = Templite(TEXT_FOR)
    point_re = re.compile(r"\(.+?, .+?\)", re.MULTILINE)
    result = t.render({
        'xs': [1, 2],
        'ys': [3, 4],
    })
    assert len(point_re.findall(result)) == 4

    result = t.render({
        'xs': [1, 2],
        'ys': [3, 4, 5],
    })
    assert len(point_re.findall(result)) == 6


def test_render_squash():
    t = Templite(TEXT_FOR)
    result = t.render({
        'xs': [1, 2],
        'ys': [3, 4],
    })
    assert len(result.split('\n')) == 7

    result = t.render({
        'xs': [1, 2],
        'ys': [3, 4, 5],
    })
    assert len(result.split('\n')) == 9
