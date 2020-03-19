import re
import sys
import json
import time
import logging
import tempfile
from pathlib import Path
from textwrap import indent, shorten
from datetime import datetime
from types import SimpleNamespace

import requests

from leezy.render import Render
from leezy.errors import *
from leezy.utils import SecretDialog, YesNoDialog, SessionTokenDialog
from leezy.config import config, session_token, Urls


LOG = logging.getLogger(__name__)
Info = LOG.info
Debug = LOG.debug
Warn = LOG.warning

ID_WIDTH = 3
NAME_BLACKLIST_RE = re.compile(r'[\\/:.?<>|]')

# this is awesome
GUIDE = """
x  x  | Elements | ... | Memory | > Application < | Security | ...
-----------------------------------------------------------------------------
Application                  | Name | Value | Domain | Path | Expires | ... |
  ...                        |  ..
Storage                      |  ..
  ...                        | LEETCODE_SESSION | ⭐ | .leetcode.com | / | ⭐
  IndexedDB                  |  ..
  Web SQL                    |  ..
  Cookies                    |  ..
   > https://leetcode.com <  |  ..
Cache                        |  ..
   ...                       |  ..
-----------------------------------------------------------------------------
"""


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

    def set_title_slug(self, title_slug):
        self.variables['titleSlug'] = title_slug
        return self


class Net:
    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update({
            'origin': Urls.portal(),
            'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/80.0.3987.132 Safari/537.36')
        })
        # init csrf once using last local storage
        # `session` will hanlde the upating of csrf caused by multiple requests
        self.sess.cookies.update(session_token.get_csrf())

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
        # try to record csrf if there is any
        session_token.try_update_csrf(r)
        raise_for_status(r, description)
        return r

    def post(self, url, purpose='', **kwargs):
        self.ensure_login()
        purpose = purpose or f'try to POST {url!r}'

        # add 'x-csrftoken' into POST headers
        csrf = None
        for d in ('leetcode.com', 'leetcode-cn.com', ''):
            csrf = self.sess.cookies.get('csrftoken', default=None, domain=d)
            if csrf:
                break

        headers = {'x-csrftoken': csrf} if csrf else {}
        if 'headers' in kwargs:
            kwargs['headers'].update(headers)
        else:
            kwargs['headers'] = headers

        return self._post(url, purpose=purpose, **kwargs)

    def _post(self, url, purpose='', **kwargs):
        description = purpose
        try:
            r = self.sess.post(url, **kwargs)
        except requests.ConnectionError as err:
            raise NetworkError(description, err)
        session_token.try_update_csrf(r)
        raise_for_status(r, description)
        return r

    def ensure_login(self):
        if not session_token.is_existed() or session_token.is_expired():
            # login() will update session_token
            Login(self, config.get('core.zone')).login()
        self.sess.cookies.update(session_token.get_token())


class Login:
    def __init__(self, net, zone):
        self.net = net
        if zone == 'cn':
            self.login = self.cn_login
        elif zone == 'us':
            self.login = self.us_login
        else:
            raise ConfigError(f'Unrecognized zone {zone!r}')

    def cn_login(self):
        username, password = self._collect_secret()
        token, expires = self._cn_login_by_secret(username, password)
        session_token.store_token(token, expires)

    def us_login(self):
        Warn('Leetcode.com enables reCAPTCHA verification now.\n'
             'We can\'t sign you in easily anymore. \n'
             'You have to sign in leetcode.com first and then '
             'find LEETCODE_SESSION in the debug panel of browser\n'
             'If you use Chrome: \n'
             '  1. sign in leetcode.com\n'
             '  2. press F12\n'
             '  3. follow the guide of the graph to copy the token out\n'
             + GUIDE)
        token, expires = self._login_by_bare_hand()
        session_token.store_token(token, expires)

    def _login_by_bare_hand(self):
        return SessionTokenDialog().collect()

    def _collect_secret(self):
        try:
            username = config.get('user.name')
            password = config.get('user.password')
        except ConfigError:
            dialog = SecretDialog(f"Sign to {Urls.portal()}")
            username, password = dialog.collect()
        return (username, password)

    def _cn_login_by_secret(self, username, password):
        Debug(f"try to sign in {Urls.portal()} as {username!r}")
        # leetcode-cn.com
        payload = (LoginPayload().set_secret(username, password).as_dict())
        r = self.net._post(Urls.graphql(),
                           purpose="try to sign in LeetCode",
                           json=payload)

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
    def __init__(self, question_id, title, title_slug, difficulty):
        self.question_id = question_id
        self.title = title
        self.title_slug = title_slug
        self.difficulty = difficulty


class ProblemEntryRepo:
    def __init__(self, cn=False):
        self.net = Net()
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
        r = self.net.get(Urls.api_problems_algo(), purpose=purpose)
        return r.json()

    def _flush_raw_all_problems(self, raw_json):
        problems = raw_json['stat_status_pairs']
        levels = ['void', 'easy', 'medium', 'hard']
        maps = {}
        for p in problems:
            maps[p['stat']['frontend_question_id']] = {
                "question_id": p['stat']['question_id'],
                "title": p['stat']['question__title'],
                "title_slug": p['stat']['question__title_slug'],
                "difficulty": levels[p['difficulty']['level']]
            }
        return maps

    def write_down_problems(self, problems):
        with open(self.problems_file, 'w') as f:
            json.dump(problems, f, ensure_ascii=False)


class ProblemProvider:
    def __init__(self):
        self.grapql_url = "https://leetcode.com/graphql"
        self.entry_repo = ProblemEntryRepo()
        self.net = self.entry_repo.net

    def info_by_id(self, id_):
        """return a `Entry`, provide some basic infomation like title and id
        """
        return self.entry_repo.entry_by_id(id_)

    def detail_by_id(self, id_):
        """return a `dict`, provide code_snippets / description etc, including
        the basic information returned by `info_by_id`
        """
        entry = self.entry_repo.entry_by_id(id_)
        raw = self._raw_problem_detail(entry.title_slug)
        detail = self._flush_raw_problem_detail(entry.title_slug, raw)
        # append basic infomation about this problem
        detail.update(entry.__dict__)
        return detail

    def _raw_problem_detail(self, title_slug):
        payload = ProblemQueryPayload().set_title_slug(title_slug).as_dict()
        purpose = f"fetch problem {title_slug!r} detail"
        post = self.entry_repo.net.post
        r = post(Urls.graphql(), purpose=purpose, json=payload)
        return r.json()

    def _flush_raw_problem_detail(self, title_slug, raw_json):
        if 'errors' in raw_json:
            raise FetchError(
                description=f"found errors when fetching {title_slug!r}",
                cause=raw_json['errors'][0]['message'])
        raw = raw_json['data']['question']
        if raw is None:
            raise FetchError("No content in response.")
        if raw['isPaidOnly']:
            raise Locked(f'the problem {title_slug!r} is locked')
        new = {}
        new['content'] = raw['content']
        new['similar_problems'] = json.loads(raw['similarQuestions'])
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


def _find_func_names(text):
    return re.findall(r'def\s+(\S+)\s*\(', text)


class Problem:
    def __init__(self, id_, context=None, provider=None):
        # id_ is frontend_id of a problem
        self.query_id = id_
        self.context = context
        self.provider = provider or ProblemProvider()

        _info = self.provider.info_by_id(id_)
        self.basic_info = _info
        # eliminate all invalid characters before making new files or folders
        # loc means local
        self.loc_id = str(id_).rjust(ID_WIDTH, '0')
        self.loc_title = NAME_BLACKLIST_RE.sub('', _info.title).strip()
        self.loc_slug = NAME_BLACKLIST_RE.sub('', _info.title_slug).strip()
        workdir = Path(config.get('core.workdir'))
        self.folder_path = workdir / Path(f'{self.loc_id} - {self.loc_title}')
        self.html_path = self.folder_path / f'{self.loc_id}.html'
        self.py_path = self.folder_path / f'{self.loc_id}_{self.loc_slug}.py'

        self.content = None
        self.similar_problem = None
        self.code_snippet = None
        self.sample_testcase = None

    def _lazy_init(self):
        detail = self.provider.detail_by_id(self.query_id)
        self.__dict__.update(detail)

    def __str__(self):
        return f'Problem<{self.loc_id}: {self.loc_title}>'

    def _generate_solution_tmpl(self):
        render = Render(self)
        return render.render()

    def digest(self):
        return (f'Problem<{self.loc_id}: {self.loc_title}> '
                f'@{self.basic_info.difficulty}')

    def pull(self):
        if self.content is None:
            self._lazy_init()
        self.folder_path.mkdir(parents=True, exist_ok=True)
        self.html_path.write_text(self.content, encoding='utf8')
        self.py_path.write_text(
            self._generate_solution_tmpl(), encoding='utf8')

    def submit(self, n):
        if not self.py_path.is_file():
            raise LeezyError(f'File not found: {self.py_path}')
        extractor = SolutionExtractor(self.py_path.read_text())
        func, code = extractor.submission(n)
        # if there are multiple solutions,
        # we need to change function name before submitting
        if len(extractor) > 1:
            if self.content is None:
                self._lazy_init()
            origin_func_name = _find_func_names(self.code_snippet)[0]
            code = code.replace(func+'(', origin_func_name+'(')

        prelude = f"Is it OK to submit function {func!r}:\n{code}\n"
        if not YesNoDialog(prelude).collect():
            return

        payload = {
            "question_id": str(self.basic_info.question_id),
            "lang": "python3",
            "typed_code": code,
            "test_mode": False,
            "test_judger": "",
            "questionSlug": self.basic_info.title_slug
        }

        net = self.provider.net
        headers = {"referer": Urls.problem_home(self.basic_info.title_slug)}
        r = net.post(Urls.problem_submit(self.basic_info.title_slug),
                     purpose="submit a solution",
                     json=payload,
                     headers=headers)
        submission_id = r.json()['submission_id']
        check_url = Urls.submission_check(submission_id)

        check_cnt = 0
        r = None
        while True:
            time.sleep(1)
            r = net.get(check_url, purpose=f'check submission x {check_cnt}')
            if len(r.json()) > 1:
                break

        rjson = r.json()
        if 'status_code' in rjson:
            # append more infomation
            rjson.update({
                'discuss_url': Urls.problem_discussion(self.basic_info.title_slug),
                'submission_detail': Urls.submission_detail(submission_id),
            })
            SubmissionReporter(rjson).report()
        else:
            raise LeezyError(f'Bad submission: {r.text}')


class Reporter:
    def __init__(self, data):
        self.data = data

    def summary(self):
        print(f'----------------{self.data.status_msg}!----------------')

    def explain(self):
        data = self.data
        print(f'passed cases: {data.total_correct}/{data.total_testcases}')

    def report(self):
        self.summary()
        self.explain()


class RuntimeErrorReporter(Reporter):
    def explain(self):
        print('\nerror:\n', self.data.runtime_error)
        print('\ndetail:\n', self.data.full_runtime_error)


class CompileErrorReporter(Reporter):
    def explain(self):
        print('\nerror:\n', self.data.complie_error)
        print('\ndetail:\n', self.data.full_compile_error)


class WrongAnswerReporter(Reporter):
    def explain(self):
        data = self.data
        print('   passed cases: ',
              f'{data.total_correct}/{data.total_testcases}')
        print('  last testcase: ', shorten(data.input_formatted, 50))
        print('    your output: ', shorten(data.code_output, 50))
        print('expected output: ', shorten(data.expected_output, 50))
        if len(data.input_formatted) < 50 and len(data.expected_output) < 50:
            print('\nconsider to add the following line to your local test?')
            print(f"q.add_case(q.case({data.input_formatted})"
                  f".assert_equal({data.expected_output}))")


class TLEReporter(Reporter):
    def explain(self):
        data = self.data
        print('   passed cases: ',
              f'{data.total_correct}/{data.total_testcases}')
        print('  last testcase: ', shorten(data.input_formatted, 50))


class AcceptedReporter(Reporter):
    def explain(self):
        data = self.data
        print('  time used & rank:',
              f'{data.status_runtime} faster than {data.runtime_percentile:.2f}%')
        print('memory used & rank:',
              f'{data.status_memory} less than {data.memory_percentile:.2f}%')

        print('\nmore helpful links:')
        links = '\n'.join([data.submission_detail, data.discuss_url])
        print(indent(links, '    '))


class SubmissionReporter:
    def __init__(self, data):
        data = SimpleNamespace(**data)
        stat_code = data.status_code
        reporter_map = {
            10: AcceptedReporter,
            11: WrongAnswerReporter,
            14: TLEReporter,
            15: RuntimeErrorReporter,
            20: CompileErrorReporter
        }
        if stat_code not in reporter_map:
            raise LeezyError(f"unkown report type: \n {data!r}")

        r = reporter_map[stat_code](data)
        self.reporter = r

    def report(self):
        self.reporter.report()


class Liner:
    def __init__(self, content):
        self.lines = content.split('\n')
        self.curidx = 0
        self.N = len(self.lines)

    def eat(self):
        self.curidx += 1

    def has_next(self):
        return self.curidx < self.N

    def is_empty(self):
        return self.peek().strip() == ''

    def peek(self):
        return self.lines[self.curidx]

    def indent(self):
        i = 0
        line = self.peek()
        while i < len(line) and line[i] == ' ':
            i += 1
        return i

    def peek_next(self, n):
        nxt = self.curidx + n
        if nxt >= self.N:
            return ''
        else:
            return self.lines[nxt]


class SolutionExtractor:
    def __init__(self, content):
        liner = Liner(content)
        imports = []
        solutions = []
        helpers = []
        while liner.has_next():
            cur_line = liner.peek()
            s_cur = cur_line.strip()
            if s_cur.startswith('import ') or s_cur.startswith('from '):
                if 'leezy' not in cur_line:
                    imports.append(s_cur)
                liner.eat()
            elif '@solution' in liner.peek():
                liner.eat()
                solutions.append(self.get_function(liner))
            elif 'def ' in liner.peek():
                func, code = self.get_function(liner)
                if func != 'main':
                    helpers.append((func, code))
            else:
                liner.eat()

        submits = []
        for solution, code in solutions:
            blocks = [code]
            for helper, helper_code in helpers:
                if helper in code:
                    blocks.append(helper_code)
            parts = imports[:]
            parts.append("\nclass Solution:")
            parts.extend(indent(block, '    ') + '\n' for block in blocks)
            submits.append((solution, '\n'.join(parts)))

        self.submits = submits

    def submission(self, n):
        if n <= 0:
            raise LeezyError('Solution index starts with 1')
        N = len(self.submits)
        be = 'are' if N > 1 else 'is'
        plural = 's' if N > 1 else ''
        if n > N:
            raise LeezyError(f'There {be} only {N} solution{plural}')
        return self.submits[n-1]

    def __len__(self):
        return len(self.submits)

    def __iter__(self):
        yield from self.submits

    def get_function(self, liner):
        indent = liner.indent()
        claim = liner.peek()[indent:]
        func_name = _find_func_names(claim)[0]
        codes = [claim]
        liner.eat()
        while liner.has_next():
            if liner.is_empty():
                codes.append('\n')
            elif liner.indent() > indent:
                codes.append(liner.peek()[indent:])
            else:
                break  # non-empty and smaller indent
            liner.eat()
        # remove trailing new lines
        while codes and codes[-1] == '\n':
            codes.pop()
        return (func_name, '\n'.join(codes) + '\n')
