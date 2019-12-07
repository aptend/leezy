import re
from enum import Enum
from .templite import Templite

class TemplateType(Enum):
    Normal = 0  # single function solution
    Design = 1  # design a data structure
    Unkown = 2  # rare situation


NormalTempl = """from leezy import solution, Solution
{% if tree_context -%}
from leezy.assists import TreeContext
{% endif -%}
{% if linkedlist_context -%}
from leezy.assists import LinkedListContext
{% endif -%}


class Q{{id_}}(Solution):
    @solution
    {{defs.0}}
        pass


def main():
    q = Q{{id_}}()
{% if tree_context -%}
    q.set_context(TreeContext)
{% endif -%}
{% if linkedlist_context -%}
    q.set_context(LinkedListContext)
{% endif -%}
    q.add_case(q.case({{testcase}}))
    q.run()

if __name__ == '__main__':
    main()
"""

DesignTempl = """
{{ code_snippet }}

def main():
    {{inst}} = {{clss.0}}({{init_args}})
    operations = {{testcase.0}}
    oprands = {{testcase.1}}
    for opt, opd in zip(operations, oprands):
        if hasattr({{inst}}, opt):
            print(getattr({{inst}}, opt).__call__(*opd))


if __name__ == '__main__':
    main()
"""

UnkownTempl = """
# unrecoginzed solution pattern, leave it on your own

{{code_snippet}}

def main():
    pass

if __name__ == '__main__':
    main()
"""

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

    def render(self):
        tmpl_type = self.template_type()
        defs, clss = self.extract_def_and_cls()
        problem = self.problem
        context = {
            'defs': defs,
            'clss': clss,
        }

        code = ''
        if tmpl_type == TemplateType.Normal:
            context.update({
                'tree_context': self.problem.context == 'tree',
                'linkedlist_context': self.problem.context == 'linked_list',
                'id_': problem.id_,
                'testcase': ", ".join(repr(x) for x in problem.sample_testcase)
            })
            t = Templite(NormalTempl)
            code = t.render(context)
        elif tmpl_type == TemplateType.Design:
            testcase = problem.sample_testcase
            init_args = ''
            if testcase[0][0] == clss[0]: # first operation is initializing
                init_args = ', '.join(repr(x) for x in testcase[1][0])
                testcase[0] = testcase[0][1:]
                testcase[1] = testcase[1][1:]
            context.update({
                'code_snippet': problem.code_snippet,
                'inst': clss[0].lower(),
                'init_args': init_args,
                'testcase': [repr(case) for case in testcase],
            })
            t = Templite(DesignTempl)
            code = t.render(context)
        else:
            t = Templite(UnkownTempl)
            code = t.render(dict(code_snippet=problem.code_snippet))

        return code.replace('(object):', ':')
