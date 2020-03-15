import re
import sys
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime

import requests

from leezy.render import Render
from leezy.errors import *
from leezy.config import config
from leezy.utils import SecreteDialog


LOG = logging.getLogger(__name__)
Info = LOG.info
Debug = LOG.debug
Warn = LOG.warning

ID_WIDTH = 3
NAME_BLACKLIST_RE = re.compile(r'[\\/:.?<>|]')


class Payload:
    def __init__(self):
        self.operation = ""
        self.variables = {}
        self.query = ""

    def set_variable(self, key, val):
        self.variables[key] = val

    def as_dict(self):
        return {
            'operationName': self.operation,
            'variables': self.variables,
            'query': self.query
        }


class LoginPayload(Payload):
    def __init__(self):
        self.operation = 'signInWithPassword'
        self.variables = {
            'data': {
                'username': 'example',
                'password': 'no-password'
            }
        }
        self.query = """\
        mutation signInWithPassword($data: AuthSignInWithPasswordInput!) {
            authSignInWithPassword(data: $data) {
                ok
                __typename
            }
        }"""

    def set_secret(self, username, password):
        self.variables['data']['username'] = username
        self.variables['data']['password'] = password
        return self


class ProblemQueryPayload(Payload):
    def __init__(self):
        self.operation = 'questionData'
        self.variables = {
            'titleSlug': 'some-problem'
        }
        self.query = """\
        query questionData($titleSlug: String!) {
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
        }"""

    def set_slug_title(self, slug_title):
        self.variables['titleSlug'] = slug_title
        return self


class NetAgent:
    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update({
            'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/80.0.3987.132 Safari/537.36')
        })

    def get(self, url, purpose='', **kwargs):
        self.ensure_login()
        purpose = purpose or f'try to GET {url!r}'
        return self._get(url, purpose=purpose, **kwargs)

    def _get(self, url, purpose='', **kwargs):
        description = purpose
        try:
            r = self.sess.get(url, **kwargs)
        except requests.ConnectionError as err:
            raise NetworkError(description, err)
        raise_for_status(r, description)
        return r

    def post(self, url, purpose='', **kwargs):
        self.ensure_login()
        purpose = purpose or f'try to POST {url!r}'
        return self._post(url, purpose=purpose, **kwargs)

    def _post(self, url, purpose='', **kwargs):
        description = purpose
        try:
            r = self.sess.post(url, **kwargs)
        except requests.ConnectionError as err:
            raise NetworkError(description, err)
        raise_for_status(r, description)
        return r

    def _update_cookie(self, token):
        self.sess.cookies.update({ 'LEETCODE_SESSION': token })

    def ensure_login(self):
        need_login = False
        try:
            token = config.get('session.token')
            expires = config.get('session.expires')
        except ConfigError:
            need_login = True
        else:
            if datetime.timestamp(datetime.now()) > expires:
                need_login = True

        if need_login:
            token = self.login()
        self._update_cookie(token)

    def login(self):
        try:
            username = config.get('user.name')
            password = config.get('user.password')
        except ConfigError:
            dialog = SecreteDialog(f"Sign to {config.get('urls.portal')}")
            username, password = dialog.collect()

        token, expires = self._login(username, password)
        Debug("Sign in successfully, persist the session token")
        config.put('session.token', token)
        config.put('session.expires', expires)
        return token

    def _login(self, username, password):
        """try to login, returns (session_token, expires) if successfully
        """
        url_graphql = config.get('urls.graphql')
        url_origin = config.get('urls.portal')
        headers = {
            'origin': url_origin,
            'x-csrftoken': 'undefined',
        }
        headers.update(self.sess.headers)
        login_payload = (LoginPayload()
                         .set_secret(username, password)
                         .as_dict())
        Debug(f"try to sign in {url_origin} as {username!r}")
        r = self._post(url_graphql, purpose="try to sign in LeetCode",
                       headers=headers, json=login_payload)
        if not r.json()['data']['authSignInWithPassword']['ok']:
            raise LoginError("Wrong username or password?")

        token = expires = None
        for c in r.cookies:
            if c.name == 'LEETCODE_SESSION':
                token = c.value
                expires = c.expires
                break
        else:
            raise LoginError("login successfully, "
                             "but didn't find session token in the response")
        return (token, expires)


class Entry:
    def __init__(self, title, title_slug, difficulty):
        self.title = title
        self.title_slug = title_slug
        self.difficulty = difficulty


class ProblemEntryRepo:
    def __init__(self, cn=False):
        self.net = NetAgent()
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
        purpose = "fetch the list of problem entry"
        r = self.net.get(config.get('urls.api_problems'), purpose=purpose)
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

    def _raw_problem_detail(self, slug_title):
        payload = ProblemQueryPayload().set_slug_title(slug_title).as_dict()
        purpose = f"fetch problem {slug_title!r} detail"
        post = self.entry_repo.net.post
        r = post(config.get('urls.graphql'), purpose=purpose, json=payload)
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
        # testcase of problem 191 is not valid json data
        # actually, the testcase of 191 is confusing
        # is it ok to abandon it?
        cases = []
        for case_row in raw['sampleTestCase'].split('\n'):
            try:
                cases.append(json.loads(case_row))
            except json.JSONDecodeError:
                pass
        new['sample_testcase'] = cases
        return new


class Problem:
    def __init__(self, id_, context=None, provider=None):
        self.query_id = id_
        self.context = context
        self.id_ = str(id_).rjust(ID_WIDTH, '0')
        self.provider = provider or ProblemProvider()

        _info = self.provider.info_by_id(id_)
        self.title = NAME_BLACKLIST_RE.sub('', _info.title).strip()
        self.slug_title = NAME_BLACKLIST_RE.sub('', _info.title_slug).strip()
        self.difficulty = _info.difficulty
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
        self.py_path.write_text(
            self._generate_solution_tmpl(), encoding='utf8')
