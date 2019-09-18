import re
from enum import Enum

class TemplateType(Enum):
    Normal = 0  # single function solution
    Design = 1  # design a data structure
    Unkown = 2  # rare situation


class CodeBuilder:
    STEP = 4

    def __init__(self, level=0):
        self.code = []
        self.level = level

    def indent(self):
        self.level += 1

    def dedent(self):
        self.level -= 1

    def add_line(self, code_line):
        self.code.extend([' ' * self.STEP * self.level, code_line, '\n'])

    def add_section(self):
        section = CodeBuilder(self.level)
        self.code.append(section)
        return section

    def __str__(self):
        return ''.join([str(c) for c in self.code])



class Render:
    def __init__(self, problem):
        self.problem = problem

    def template_type(self):
        """
        infer template type by observing number and name of `def` `class`
        """
        defs, clss = self.extract_def_and_cls()
        testcase = self.problem.sample_testcase
        if len(defs) == 1:
            return TemplateType.Normal
        elif len(clss) == 1 and clss[0] != 'Solution' and len(testcase) == 2:
            return TemplateType.Design
        else:
            return TemplateType.Unkown

    def extract_def_and_cls(self):
        code_snippet = self.problem.code_snippet
        re_def = re.compile(r'^\s*(def .*:)\n', re.MULTILINE)
        re_class = re.compile(r'^\s*class ([_\w\d]+)\(?.*\)?:\n', re.MULTILINE)
        clss = re_class.findall(code_snippet)
        defs = re_def.findall(code_snippet)
        return defs, clss

    def factory(self):
        pass
    
    def render(self):
        problem = self.problem
        tmpl_type = self.template_type()
        defs, clss = self.extract_def_and_cls()

        code = CodeBuilder()
        add = code.add_line
        if tmpl_type == TemplateType.Normal:
            add('from leeyzer import Solution, solution')
            if problem.context == 'tree':
                add('from leeyzer.assists import TreeContext')
            elif problem.context == 'linked_list':
                add('from leeyzer.assists import LinkedListContext')
            add('\n')
            add(f'class Q{problem.id_}(Solution):')
            code.indent()
            add('@solution')
            add(defs[0])
            code.indent()
            add('pass')
            code.dedent()
            code.dedent()
            add('\n')
            add('def main():')
            code.indent()
            add(f'q = Q{problem.id_}()')
            if problem.context == 'tree':
                add('q.set_context(TreeContext)')
            elif problem.context == 'linked_list':
                add('q.set_context(LinkedListContext)')
            add(f'q.add_args({", ".join(problem.sample_testcase)})')
            add('q.run()')
            code.dedent()
            add('\n')
        elif tmpl_type == TemplateType.Design:
            add(problem.code_snippet)
            inst = clss[0].lower()
            add('def main():')
            code.indent()
            add(f'{inst} = {clss[0]}()')
            add(f'operations = {problem.sample_testcase[0]}')
            add(f'operands = {problem.sample_testcase[1]}')
            add('for opt, opd in zip(operations, operands):')
            code.indent()
            add(f'if hasattr({inst}, opt):')
            code.indent()
            add(f'print(getattr({inst}, opt).__call__(*opd))')
            code.dedent()
            code.dedent()
            code.dedent()
            add('\n')
        else:
            add('# unrecoginzed solution pattern, leave it on your own\n')
            add(problem.code_snippet)
            add('def main():\n    pass\n')

        add('if __name__ == "__main__":\n    main()')

        return str(code).replace('(object):', ':')
