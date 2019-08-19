import re
import sys
import json
import logging
import tempfile
from pathlib import Path

import requests

ID_WIDTH = 3
NAME_BLACKLIST_RE = re.compile(r'[\\/:.?<>|]')
logger = logging.getLogger()


class ProblemEntryRepo:
    def __init__(self, cn=False):
        if cn:
            src_url = "https://leetcode-cn.com/api/problems/algorithms/"
        else:
            src_url = "https://leetcode.com/api/problems/algorithms/"
        self.all_problem_url = src_url
        self.logger = logger
        self.problems = None
        path = str(Path(tempfile.gettempdir()) / "leeyzer_problems.json")
        self.problems_file = path

    def entry_by_id(self, id_):
        if self.problems is None:
            self.problems = self.all_problems()
        none_item = {
            "question__title": "",
            "question__title_slug": "",
            "difficulty": ""
        }
        return self.problems.get(id_, none_item)

    def title_by_id(self, id_):
        return self.entry_by_id(str(id_))['question__title']

    def slug_title_by_id(self, id_):
        return self.entry_by_id(str(id_))['question__title_slug']

    def difficulty_by_id(self, id_):
        return self.entry_by_id(str(id_))['difficulty']

    def all_problems(self):
        problems = self.local_all_problems()
        if not problems:
            self.update()
            problems = self.local_all_problems()
        return problems

    def local_all_problems(self):
        try:
            f = open(self.problems_file, encoding='utf8')
        except FileNotFoundError:
            self.logger.info(
                f'{self.problems_file} is not existed. updating expected')
            return {}
        problems = json.load(f)
        f.close()
        return problems

    def update(self):
        problems = self.web_all_problems()
        if problems:
            self.write_down_problems(problems)
        else:
            self.logger.warning("fetched 0 problem. updating aborted")

    def web_all_problems(self):
        raw = self.raw_web_all_problems()
        return self.flush_raw_all_problems(raw)

    def raw_web_all_problems(self):
        try:
            r = requests.get(self.all_problem_url)
        except requests.ConnectionError as err:
            self.logger.warning("fetch all problems error: %r", err)
            return {}
        if r.status_code != 200:
            self.logger.warning(
                "fetch all problems bad status code: %d", r.status_code)
        return r.json()

    def flush_raw_all_problems(self, raw_json):
        if not raw_json:
            return {}
        problems = raw_json['stat_status_pairs']
        levels = ['void', 'easy', 'medium', 'hard']
        maps = {}
        for p in problems:
            maps[p['stat']['frontend_question_id']] = {
                "question__title": p['stat']['question__title'],
                "question__title_slug": p['stat']['question__title_slug'],
                "difficulty": levels[p['difficulty']['level']]
            }
        return maps

    def write_down_problems(self, problems):
        with open(self.problems_file, 'w') as f:
            json.dump(problems, f)


class ProblemProvider:
    def __init__(self):
        self.grapql_url = "https://leetcode-cn.com/graphql"
        self.logger = logger
        self.entry_repo = ProblemEntryRepo()

    def query_payload(self, slug_title):
        query = {
            "operationName": "questionData",
            "query": "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n     questionFrontendId\n   title\n   titleSlug\n    content\n    isPaidOnly\n    similarQuestions\n   codeSnippets {\n   langSlug\n    code\n  }\n    sampleTestCase\n   }\n}\n"
        }
        query['variables'] = {'titleSlug': slug_title}
        return query

    def detail_by_id(self, id_):
        slug_title = self.entry_repo.slug_title_by_id(id_)
        raw = self.raw_problem_detail(slug_title)
        detail = self.flush_raw_problem_detail(slug_title, raw)
        return detail

    def raw_problem_detail(self, slug_title):
        payload = self.query_payload(slug_title)
        try:
            r = requests.post(self.grapql_url, json=payload)
        except requests.ConnectionError as err:
            self.logger.warning(
                "fetch problem %r detail error: %r", slug_title, err)
            return {}
        if r.status_code != 200:
            self.logger.warning(
                "fetch problem %r bad status code: %d", slug_title, r.status_code)
        return r.json()

    def flush_raw_problem_detail(self, slug_title, raw_json):
        if not raw_json:
            return raw_json
        if 'errors' in raw_json:
            self.logger.warning("%r: %s",
                                slug_title, raw_json['errors'][0]['message'])
            return {}
        raw = raw_json['data']['question']
        if raw['isPaidOnly']:
            self.logger.warning('%r: locked', slug_title)
            return {}
        new = {}
        new['frontend_id'] = raw['questionFrontendId']
        new['title'] = raw['title']
        new['slug_title'] = raw['titleSlug']
        new['content'] = raw['content']
        new['smilar_problems'] = json.loads(raw['similarQuestions'])
        new['code_snippet'] = [sp['code'] for sp in raw['codeSnippets'] if
                               sp['langSlug'] == 'python'][0].replace('\r\n', '\n')
        new['sample_testcase'] = [repr(json.loads(s)) for s
                                  in raw['sampleTestCase'].split('\n')]
        return new


class Problem:
    def __init__(self, id_, context=None, provider=None):
        self.query_id = id_
        self.context = context
        self.id_ = str(id_).rjust(ID_WIDTH, '0')
        self.provider = provider or ProblemProvider()
        self.frontend_id = None
        self.title = None
        self.slug_title = None
        self.content = None
        self.smilar_problem = None
        self.code_snippet = None
        self.sample_testcase = None

    def lazy_init(self):
        detail = self.provider.detail_by_id(self.query_id)
        if not detail:
            return False
        self.__dict__.update(detail)
        self.title = NAME_BLACKLIST_RE.sub('', self.title)
        self.slug_title = NAME_BLACKLIST_RE.sub('', self.slug_title)
        return True

    def __str__(self):
        return f'Problem<{self.id_}: {self.title}>'

    def generate_solution_tmpl(self):
        re_def = re.compile(r'^\s*(def .*:)\n', re.MULTILINE)
        re_class = re.compile(r'^\s*class ([_\w\d]+)\(?.*\)?:\n', re.MULTILINE)
        clss = re_class.findall(self.code_snippet)
        defs = re_def.findall(self.code_snippet)

        code = CodeBuilder()
        if len(defs) == 1:
            code.add_line('from leeyzer import Solution, solution')
            if self.context == 'tree':
                code.add_line('from leeyzer.assists import TreeContext')
            elif self.content == 'linked_list':
                code.add_line('from leeyzer.assists import LinkedListContext')
            code.add_line('\n')
            code.add_line(f'class Q{self.id_}(Solution):')
            code.indent()
            code.add_line('@solution')
            code.add_line(defs[0])
            code.indent()
            code.add_line('pass')
            code.dedent()
            code.dedent()
            code.add_line('\n')
            code.add_line('def main():')
            code.indent()
            code.add_line(f'q = Q{self.id_}()')
            if self.context == 'tree':
                code.add_line('q.set_context(TreeContext)')
            elif self.content == 'linked_list':
                code.add_line('q.set_context(LinkedListContext)')
            code.add_line(f'q.add_args({", ".join(self.sample_testcase)})')
            code.add_line('q.run()')
            code.dedent()
            code.add_line('\n')
        elif len(clss) == 1 and clss[0] != 'Solution' and len(self.sample_testcase) == 2:
            code.add_line(self.code_snippet)
            inst = clss[0].lower()
            code.add_line('def main():')
            code.indent()
            code.add_line(f'{inst} = {clss[0]}()')
            code.add_line(f'operations = {self.sample_testcase[0]}')
            code.add_line(f'operands = {self.sample_testcase[1]}')
            code.add_line('for opt, opd in zip(operations, operands):')
            code.add_line(f'    if hasattr({inst}, opt):')
            code.add_line(f'        print(getattr({inst}, opt).__call__(*opd))')
            code.dedent()
            code.add_line('\n')
        else:
            code.add_line(
                '# unrecoginzed solution pattern, leave it on your own\n')
            code.add_line(self.code_snippet)
            code.add_line('def main():\n    pass\n')

        code.add_line('if __name__ == "__main__":\n    main()')

        return str(code).replace('(object):', ':')

    def show(self):
        title = self.provider.entry_repo.title_by_id(self.query_id)
        difficulty = self.provider.entry_repo.difficulty_by_id(self.query_id)
        if title:
            print(f'Problem<{self.id_}: {title}> @{difficulty}')
        else:
            print('not found')

    def pull(self):
        if self.frontend_id or self.lazy_init():
            p_dir = Path(f'{self.id_} - {self.title}')
            p_dir.mkdir(exist_ok=True)
            content = p_dir / f'{self.id_}.html'
            content.write_text(self.content, encoding='utf8')
            solution = p_dir / f'{self.id_}_{self.slug_title}.py'
            solution.write_text(self.generate_solution_tmpl(), encoding='utf8')
        else:
            print('fetch problem failed: \n'
                  '1. check network; or\n'
                  '2. this problem is locked; or\n'
                  '3. this problem does not exist')


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


if __name__ == "__main__":
    p = Problem(sys.argv[1])
    p.show()
