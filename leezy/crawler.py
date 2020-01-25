import re
import sys
import json
import logging
import tempfile
from pathlib import Path

import requests

from leezy.render import Render
from leezy.errors import *
from leezy.config import config


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
        self.difficulty = difficulty


class ProblemEntryRepo:
    def __init__(self, cn=False):
        if cn:
            src_url = "https://leetcode-cn.com/api/problems/algorithms/"
        else:
            src_url = "https://leetcode.com/api/problems/algorithms/"
        self.all_problem_url = src_url
        path = str(Path(tempfile.gettempdir()) / "leezy_problems.json")
        self.problems_file = path
        self.problems = self._load_local_cache()

    def entry_by_id(self, id_):
        r = self.problems.get(str(id_), None)
        if r is None:
            self._update_cache()
            r = self.problems.get(str(id_), None)
            if r is None:
                raise NotFound(f'Problem<{id_}> is not found')
        return Entry(**r)

    def _load_local_cache(self):
        try:
            f = open(self.problems_file, encoding='utf8')
        except FileNotFoundError:
            return {}
        problems = json.load(f)
        f.close()
        return problems

    def _update_cache(self):
        raw_problems = self._raw_web_all_problems()
        self.problems = self._flush_raw_all_problems(raw_problems)
        self.write_down_problems(self.problems)
 
    def _raw_web_all_problems(self):
        description = "can't fetch the list of problem entry"
        try:
            r = requests.get(self.all_problem_url)
        except requests.ConnectionError as err:
            raise NetworkError(description, err)
        raise_for_status(r, description)
        return r.json()

    def _flush_raw_all_problems(self, raw_json):
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
        self.entry_repo = ProblemEntryRepo()

    def info_by_id(self, id_):
        return self.entry_repo.entry_by_id(id_)

    def detail_by_id(self, id_):
        entry = self.entry_repo.entry_by_id(id_)
        raw = self._raw_problem_detail(entry.title_slug)
        detail = self._flush_raw_problem_detail(entry.title_slug, raw)
        return detail

    def _query_payload(self, slug_title):
        query = {
            "operationName": "questionData",
            "query": QUERY
        }
        query['variables'] = {'titleSlug': slug_title}
        return query

    def _raw_problem_detail(self, slug_title):
        payload = self._query_payload(slug_title)
        description = f"cat't fetch problem {slug_title!r} detail"
        try:
            r = requests.post(self.grapql_url, json=payload)
        except requests.ConnectionError as e:
            raise NetworkError(description, e)
        raise_for_status(r, description)
        return r.json()

    def _flush_raw_problem_detail(self, slug_title, raw_json):
        if 'errors' in raw_json:
            raise FetchError(
                description=f"found errors when fetching {slug_title!r}",
                cause=raw_json['errors'][0]['message'])
        raw = raw_json['data']['question']
        if raw is None:
            raise FetchError("No content in response.")
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

        basic_info = self.provider.info_by_id(id_)
        self.title = NAME_BLACKLIST_RE.sub('', basic_info.title).strip()
        self.slug_title = NAME_BLACKLIST_RE.sub('', basic_info.title_slug).strip()
        self.difficulty = basic_info.difficulty
        workdir = Path(config.get('core.workdir'))
        self.folder_path = workdir / Path(f'{self.id_} - {self.title}')
        self.html_path = self.folder_path / f'{self.id_}.html'
        self.py_path = self.folder_path / f'{self.id_}_{self.slug_title}.py'

        self.frontend_id = None
        self.content = None
        self.smilar_problem = None
        self.code_snippet = None
        self.sample_testcase = None

    def _lazy_init(self):
        detail = self.provider.detail_by_id(self.query_id)
        self.__dict__.update(detail)

    def __str__(self):
        return f'Problem<{self.id_}: {self.title}>'

    def _generate_solution_tmpl(self):
        render = Render(self)
        return render.render()

    def digest(self):
        return f'Problem<{self.id_}: {self.title}> @{self.difficulty}'

    def pull(self):
        if not self.frontend_id:
            self._lazy_init()
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.html_path.write_text(self.content, encoding='utf8')
        self.py_path.write_text(self._generate_solution_tmpl(), encoding='utf8')
