# http://aosabook.org/en/500L/a-template-engine.html

import re
import keyword


class TempliteSyntaxError(ValueError):
    """编译时，语法无法识别"""
    pass


class TempliteRenderError(ValueError):
    """运行时，do_dots出现异常"""
    pass


class CodeBuilder:
    INDENT = 4

    def __init__(self, init_indent=0):
        self.indent_lv = init_indent
        self.code = []

    def indent(self):
        self.indent_lv += self.INDENT

    def dedent(self):
        self.indent_lv -= self.INDENT

    def add_line(self, line):
        self.code.extend([' '*self.indent_lv, line, '\n'])

    def add_empty_line(self):
        self.code.append('\n')

    def add_section(self):
        """添加一个子CodeBuilder

        功能上等效于增加一个占位符，构建完后续代码后才能确定当前section的内容
        例子是绑定局部变量之前，必须解析后续代码才能直到有那些局部变量被使用了
        """
        section = CodeBuilder(self.indent_lv)
        self.code.append(section)
        return section

    def __str__(self):
        return ''.join(str(c) for c in self.code)

    def globals_after_exec(self):
        """执行代码，获取global名字空间

        Raises:
            SyntaxError: 如果执行时indent_lv不为0或者代码本身存在语法错误
        """
        if self.indent_lv != 0:
            raise SyntaxError("unbalanced CodeBuilder")
        source_code = str(self)
        global_namespace = {}
        exec(source_code, global_namespace)
        return global_namespace


class Templite:
    def __init__(self, text, *context):
        self.text = text
        self.context = {}
        for cxt in context:
            self.context.update(cxt)

        # context_variables = all_variables - native_variables
        self.all_variables = set()
        self.native_variables = set()

        code = self._build(self._tokens(self.text))
        self._co_code = code
        self._render_func = code.globals_after_exec()['render_template']

    def render(self, context=None):
        context = context or {}
        context.update(self.context)
        return self._render_func(context, self._do_dots)

    def _tokens(self, text):
        # 单独切分token，之后如果要处理转义在这里执行？
        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)
        return tokens

    def _build(self, tokens):
        code = CodeBuilder()
        code.add_line('def render_template(context, do_dots):')
        code.indent()
        code.add_line('result = []')
        # 速度优化之一，查用名字固定到local空间，减少查找
        code.add_line('append_result = result.append')
        code.add_line('expand_result = result.extend')
        code.add_line('to_str = str')
        # context的变量初始化，明确哪些变量被使用后再添加赋值语句
        context_vars_section = code.add_section()

        buffer = []

        # 速度优化之二，对于非控制语句，填充入buffer，一次性由extend拓展，减少扩容操作
        def flush():
            if len(buffer) == 0:
                return
            elif len(buffer) == 1:
                code.add_line(f'append_result({buffer[0]})')
            else:
                code.add_line(f'expand_result([{", ".join(buffer)}])')
            buffer.clear()

        squash = False
        ops_stack = []
        for token in tokens:
            if token.startswith('{'):
                # '{' or '%' or '#'
                tag = token[1]
                content = token[2:-2].strip()
                # 每次遇到控制语句，都更新squash，指示下一个文本值如何处理
                # 注意token的顺序一定是 文本 - 控制 - 文本 - 控制 - ... 的顺序
                if content[-1] == '-':
                    squash = True
                    content = content[:-1].strip()
                else:
                    squash = False
                if tag == '#':
                    continue
                elif tag == '{':
                    buffer.append(f'to_str({self._expr(content)})')
                elif tag == '%':
                    flush()
                    if content.startswith('if'):
                        parts = content.split()
                        if len(parts) != 2:
                            self._syntax_error("Don't understand if", content)
                        var_code = self._expr(parts[1])
                        code.add_line(f'if {var_code}:')
                        code.indent()
                        ops_stack.append('if')
                    elif content.startswith('for'):
                        parts = content.split()
                        if len(parts) != 4 or parts[2] != 'in':
                            self._syntax_error("Don't understand for", content)
                        self._record_variable(parts[1], self.native_variables)
                        iter_var = self._expr(parts[3])
                        code.add_line(f'for c_{parts[1]} in {iter_var}:')
                        code.indent()
                        ops_stack.append('for')
                    elif content.startswith('end'):
                        parts = content.split()
                        if len(parts) != 1:
                            self._syntax_error("Don't understand end", content)
                        act = content[3:]
                        if len(ops_stack) == 0:
                            self._syntax_error("Too many ends", token)
                        if ops_stack.pop() != act:
                            self._syntax_error("unmatched end tag", token)
                        code.dedent()
                    else:
                        self._syntax_error('Unkown action', content)
                else:
                    self._syntax_error("Unkown tag", token)

            elif token:
                if squash:
                    token = self._delete_first_leading_newline(token)
                # 字面值，直接加入buffer中
                if token:
                    buffer.append(repr(token))

        if ops_stack:
            self._syntax_error("No matched end tag", ops_stack[-1])

        for cxt_var in self.all_variables - self.native_variables:
            context_vars_section.add_line(f"c_{cxt_var} = context[{cxt_var!r}]")

        flush()
        code.add_line('return "".join(result)')
        code.dedent()
        return code

    def _delete_first_leading_newline(self, token):
        """删除先导空白字符中的第一个换行符

        Examples::
        >>> _delete_first_leading_newline('  \n    \ntoken content\n')
        '    \ntoken content\n'
        >>> _delete_first_leading_newline('  token content\n')
        '  token content\n'
        """
        idx = token.find('\n')
        if token[:idx+1].isspace():
            token = token[idx+1:]
        return token

    def _syntax_error(self, msg, thing):
        raise TempliteSyntaxError(f"{msg}: {thing}")

    def _expr(self, expr):
        """展开表达式

        Examples:
        >>> _expr('obj1.attr.val|obj2.dump')
        do_dots(c_obj2, 'dump')(do_dots(c_obj1, 'attr', 'val'))

        Args:
            expr: 可能混合 . 和 | 符号的字符串, 出现在 {{ expr }} {% if expr %}
                    {% for x in expr %}语句中

        Returns:
            code: 展开后的可执行的源码

        Raises:
            TempliteSyntaxError: 如果展开过程中发现不合法的变量名
        """
        # TODO: 支持|左右存在空格？
        if '|' in expr:
            parts = expr.split('|')
            code = self._expr(parts[0])
            for p in parts[1:]:
                code = "{}({})".format(self._expr(p), code)
        elif '.' in expr:
            # 此时expr中不存在'|'
            parts = expr.split('.')
            code = self._expr(parts[0])
            tag_args = ', '.join(repr(p) for p in parts[1:])
            code = f"do_dots({code}, {tag_args})"
        else:
            # 单独一个变量名，如果不是，交给record抛出异常
            self._record_variable(expr, self.all_variables)
            code = f"c_{expr}"
        return code

    def _record_variable(self, name, var_set):
        if not name.isidentifier() or keyword.iskeyword(name):
            self._syntax_error("Not a valid name", name)
        var_set.add(name)

    def _do_dots(self, obj, *tags):
        """运行时解析dot语法

        模板中的dot语法共三种行为::
            1. 方法调用， obj.method()
            2. 取attribute， obj.attr
            3. index， obj[tag]，比如列表和字典的索引行为
        前两种行为优先级更高
        """
        for tag in tags:
            try:
                obj = getattr(obj, tag)
            except AttributeError:
                try:
                    obj = obj[tag]
                except (TypeError, KeyError):
                    if tag.isdigit():
                        try:
                            obj = obj[int(tag)]
                        except (TypeError, KeyError, IndexError):
                            raise TempliteRenderError(
                                f"Can't resolve dot: {obj}.{tag}")
                    else:
                        raise TempliteRenderError(
                            f"Can't resolve dot: {obj}.{tag}")
            else:
                if callable(obj):
                    obj = obj()
        return obj
