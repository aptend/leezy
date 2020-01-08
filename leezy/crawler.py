import re
import sys
import json
import logging
import tempfile
from pathlib import Path

import requests

from .render import Render
from .errors import *

ID_WIDTH = 3
NAME_BLACKLIST_RE = re.compile(r'[\\/:.?<>|]')
logger = logging.getLogger()

QUERY = """query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    questionFrontendId
    title
    titleSlug
    content
    isPaidOnly
    difficulty
    likes
    dislikes
    similarQuestions
    topicTags {
      name
      slug
    }
    companyTagStats
    codeSnippets {
      langSlug
      code
    }
    stats
    hints
    status
    sampleTestCase
  }
}
"""


class Entry:
    def __init__(self, title, title_slug, difficulty):
        self.title = title
        self.title_slug = title_slug
        self.difficulty= difficulty


class ProblemEntryRepo:
    def __init__(self, cn=False):
        if cn:
            src_url = "https://leetcode-cn.com/api/problems/algorithms/"
        else:
            src_url = "https://leetcode.com/api/problems/algorithms/"
        self.all_problem_url = src_url
        self.logger = logger
        self.problems = None
        path = str(Path(tempfile.gettempdir()) / "leezy_problems.json")
        self.problems_file = path

    def entry_by_id(self, id_):
        if self.problems is None:
            self.problems = self.all_problems()
        r = self.problems.get(str(id_), None)
        if r is None:
            self._update()
            self.problems = self.all_problems()
        r = self.problems.get(str(id_), None)
        if r is None:
            raise NotFound(f'Problem<{id_}> is not found')
        return Entry(**r)

    def all_problems(self):
        problems = self.__local_all_problems()
        if not problems:
            self._update()
            problems = self.__local_all_problems()
        return problems

    def __local_all_problems(self):
        try:
            f = open(self.problems_file, encoding='utf8')
        except FileNotFoundError:
            return {}
        problems = json.load(f)
        f.close()
        return problems

    def _update(self):
        problems = self.__web_all_problems()
        self.write_down_problems(problems)

    def __web_all_problems(self):
        raw = self.__raw_web_all_problems()
        return self.__flush_raw_all_problems(raw)

    def __raw_web_all_problems(self):
        description = "can't fetch the list of problem entry"
        try:
            r = requests.get(self.all_problem_url)
        except requests.ConnectionError as err:
            raise NetworkError(description, err)
        raise_for_status(r, description)
        return r.json()

    def __flush_raw_all_problems(self, raw_json):
        problems = raw_json['stat_status_pairs']
        levels = ['void', 'easy', 'medium', 'hard']
        maps = {}
        for p in problems:
            maps[p['stat']['frontend_question_id']] = {
                "title": p['stat']['question__title'],
                "title_slug": p['stat']['question__title_slug'],
                "difficulty": levels[p['difficulty']['level']]
            }
        return maps

    def write_down_problems(self, problems):
        with open(self.problems_file, 'w') as f:
            json.dump(problems, f)


class ProblemProvider:
    def __init__(self):
        self.grapql_url = "https://leetcode.com/graphql"
        self.logger = logger
        self.entry_repo = ProblemEntryRepo()

    def query_payload(self, slug_title):
        query = {
            "operationName": "questionData",
            "query": QUERY
        }
        query['variables'] = {'titleSlug': slug_title}
        return query

    def detail_by_id(self, id_):
        entry = self.entry_repo.entry_by_id(id_)
        raw = self.raw_problem_detail(entry.title_slug)
        detail = self.flush_raw_problem_detail(entry.title_slug, raw)
        return detail

    def raw_problem_detail(self, slug_title):
        payload = self.query_payload(slug_title)
        description = f"cat't fetch problem {slug_title!r} detail"
        try:
            r = requests.post(self.grapql_url, json=payload)
        except requests.ConnectionError as e:
            raise NetworkError(description, e)
        raise_for_status(r, description)
        return r.json()

    def flush_raw_problem_detail(self, slug_title, raw_json):
        if 'errors' in raw_json:
            raise FetchError(
                description=f"found errors when fetching {slug_title!r}",
                cause=raw_json['errors'][0]['message'])
        raw = raw_json['data']['question']
        if raw is None:
            raise FetchError(
                f"found no content in response. Perhaps the server doesn't update in time")
        if raw['isPaidOnly']:
            raise Locked(f'the problem {slug_title!r} is locked')
        new = {}
        new['frontend_id'] = raw['questionFrontendId']
        new['title'] = raw['title']
        new['slug_title'] = raw['titleSlug']
        new['content'] = raw['content']
        new['smilar_problems'] = json.loads(raw['similarQuestions'])
        new['code_snippet'] = [sp['code'] for sp in raw['codeSnippets'] if
                               sp['langSlug'] == 'python'][0].replace('\r\n', '\n')
        new['sample_testcase'] = [json.loads(s) for s
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
        self.__dict__.update(detail)
        self.title = NAME_BLACKLIST_RE.sub('', self.title).strip()
        self.slug_title = NAME_BLACKLIST_RE.sub('', self.slug_title).strip()

    def __str__(self):
        return f'Problem<{self.id_}: {self.title}>'

    def generate_solution_tmpl(self):
        render = Render(self)
        return render.render()

    def digest(self):
        entry = self.provider.entry_repo.entry_by_id(self.query_id)
        return f'Problem<{self.id_}: {entry.title}> @{entry.difficulty}'

    def pull(self):
        if not self.frontend_id:
            self.lazy_init()
        p_dir = Path(f'{self.id_} - {self.title}')
        p_dir.mkdir(exist_ok=True)
        content = p_dir / f'{self.id_}.html'
        content.write_text(self.content, encoding='utf8')
        solution = p_dir / f'{self.id_}_{self.slug_title}.py'
        solution.write_text(self.generate_solution_tmpl(), encoding='utf8')


if __name__ == "__main__":
    p = Problem(sys.argv[1])
    p.show()
