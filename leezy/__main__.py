import sys
import logging
import argparse
import subprocess

from leezy.crawler import Problem
from leezy.config import config, session_token, Urls

from leezy.errors import show_error_and_exit, LeezyError

import traceback

LOG = logging.getLogger(__name__)
Info = LOG.info
Debug = LOG.debug
Warn = LOG.warning

VERSION = '0.5.2'


def show_uncaught_exc(e):
    print(f'Uncaught Exception: {e!r}')
    Debug(traceback.format_exc(limit=10))


def _exit(msg):
    print('leezy: ' + msg)
    sys.exit(1)


def expand_ids(ids_arg):
    if len(ids_arg) == 1 and ids_arg[0].count('-') == 1:
        # handle input like '40-43'
        s, e = ids_arg[0].split('-')[:2]
        try:
            s, e = int(s), int(e)
        except ValueError:
            _exit('a-b is valid only when a and b are both numbers')
        return [str(x) for x in range(s, e+1)]
    else:
        return ids_arg


def parse_solution_pos(s):
    # handle input like 2@42
    parts = s.strip().split('@')
    N = len(parts)
    if N == 0 or N > 2:
        _exit(f'unrecognized soution input: {s!r}')
    if N == 1:
        return (1, s)
    else:
        try:
            sol_num = int(parts[0])
        except ValueError:
            _exit(f'{parts[0]!r} is not a number')
        return (sol_num, parts[1])


parser = argparse.ArgumentParser(
    prog='leezy',
    description='Manage your Python solutions better',
    usage='leezy [options] COMMAND')

parser.add_argument('-V', '--version',
                    action='version',
                    version=VERSION)
parser.add_argument('--zone',
                    choices=['cn', 'us'],
                    metavar='ZONE',
                    help="'cn' or 'us', default is 'cn'")
parser.add_argument('--dir',
                    help="assign a temporary workdir for this session")
parser.add_argument('-v',
                    action='count',
                    help="verbose, use multiple -vv... to show more log")


subs = parser.add_subparsers(
    title="COMMANDS",
    description="use 'leezy <COMMAND> -h' to see more",
    metavar='-⭐-')


def show(args):
    for pid in expand_ids(args.ids):
        try:
            print(Problem(pid).digest())
        except LeezyError as e:
            show_error_and_exit(e)
        except Exception as e:
            show_uncaught_exc(e)


show_parser = subs.add_parser(
    'show',
    usage=argparse.SUPPRESS,
    help='show basic info of problems',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=r"""examples:
    leezy show 1          show the first problem
    leezy show 1 2 3      show (1st, 2nd, 3rd) problems together
    leezy show 1-3        show (1st, 2nd, 3rd) problems together""")
show_parser.add_argument('ids', nargs='+', help="question ids")
show_parser.set_defaults(func=show)


def pull(args):
    for pid in expand_ids(args.ids):
        try:
            Problem(pid, args.context).pull()
        except LeezyError as e:
            show_error_and_exit(e)
        except Exception as e:
            show_uncaught_exc(e)


pull_parser = subs.add_parser(
    'pull',
    usage=argparse.SUPPRESS,
    help='pull problems to local files',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=r"""examples:
    leezy pull 1                 pull the first problem
    leezy pull 1 2 3             pull (1st, 2nd, 3rd) problems together
    leezy pull 1-3               pull (1st, 2nd, 3rd) problems together
    leezy pull 700 -c tree       pull no.700 and set tree context
    leezy pull 2 -c linkedlist   pull no.2 and set linkedlist context""")

pull_parser.add_argument('ids', nargs='+', help="problem ids")
pull_parser.add_argument('-c', '--context',
                         metavar='',
                         choices=['tree', 'linkedlist'],
                         help="set a context for this problem [tree or linkedlist]")
pull_parser.set_defaults(func=pull)


def run(args):
    try:
        py_path = Problem(args.id).py_path
    except LeezyError as e:
        show_error_and_exit(e)
    except Exception as e:
        show_uncaught_exc(e)

    if not py_path.is_file():
        print(f'File not found: {py_path}')
    else:
        try:
            subprocess.run(['python', str(py_path)],
                           timeout=5,
                           cwd=py_path.parent)
        except FileNotFoundError:
            print('python can\'t be launched by command \'python\'')
        except subprocess.TimeoutExpired:
            print('Timeout(10s). Is there an infinite loop in the solution?')
        except Exception:
            raise


run_parser = subs.add_parser(
    'run',
    usage=argparse.SUPPRESS,
    help='run your solutions, see outputs or test them',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=r"""examples:
    leezy run 1       run the first problem""")
run_parser.add_argument('id', help="problem id")
run_parser.set_defaults(func=run)


def submit(args):
    sol_id, front_id = parse_solution_pos(args.solution)
    try:
        Problem(front_id).submit(sol_id)
    except LeezyError as e:
        show_error_and_exit(e)
    except Exception as e:
        show_uncaught_exc(e)


submit_parser = subs.add_parser(
    'submit',
    usage=argparse.SUPPRESS,
    help='submit your solution to leetcode',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=r"""examples:
    leezy submit 1@1      submit the 1st solution of problem 1
    leezy submit 2@1      submit the 2nd solution of problem 1
    leezy submit 1        same with 1@1, just a shortcut""")

submit_parser.add_argument('solution', help="postion of your solution")
submit_parser.set_defaults(func=submit)


def plot(args):
    from leezy.plot import SNSPlotter, DataFeeder
    SNSPlotter(DataFeeder()).plot()


plot_parser = subs.add_parser(
    'plot',
    usage=argparse.SUPPRESS,
    help='show a heatmap of your all accepted solutions',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""examples:
    leezy plot
    """)

plot_parser.set_defaults(func=plot)


def handle_config(args):
    if args.list:
        print('\n'.join('='.join((k, str(v)))
                        for k, v in config.get_all_file_data()))
    elif args.add:
        config.put(args.add[0], args.add[1])
    elif args.delete:
        config.delete(args.delete[0])


config_parser = subs.add_parser(
    'config',
    usage=argparse.SUPPRESS,
    help='manage global configs',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=r"""examples:
    leezy config -l                               show all config entries
    leezy config -a core.workdir  D:\leetcode     set workdir
    leezy config -a core.zone cn                  run leezy on cn every time
    leezy config -a log.level debug               run leezy at debug log level
    leezy config -d core                          remove all core settings""")

group = config_parser.add_mutually_exclusive_group()
group.add_argument('-l', '--list',
                   action='store_true',
                   help='show all config entries')
group.add_argument('-d', '--del',
                   nargs=1,
                   metavar='',
                   dest='delete',
                   help='delete settings')
group.add_argument('-a', '--add',
                   nargs=2,
                   metavar='',
                   help='add a <Key Value> setting pair')
config_parser.set_defaults(func=handle_config)

args = parser.parse_args()
if not hasattr(args, 'func'):
    parser.print_help()
else:
    if args.zone is not None:
        config.patch('core.zone', args.zone)
    if args.v is not None:
        if args.v == 1:
            config.patch('log.level', 'info')
        else:
            config.patch('log.level', 'debug')
    if args.dir is not None:
        config.patch('core.workdir', args.dir)

    session_token.init()
    Urls.init(config)

    log_lv = getattr(logging, config.get('log.level').upper())

    def reject_modules(modules, lv=logging.INFO):
        def _reject_filter(record):
            mod_name = record.name
            mod_lv = record.levelno
            for mod in modules:
                if mod_name.startswith(mod) and mod_lv <= lv:
                    return False
            return True
        return _reject_filter

    logging.basicConfig(level=log_lv)
    root = logging.getLogger()
    rej_mat = reject_modules(['matplotlib'])
    for hld in root.handlers:
        hld.addFilter(rej_mat)

    args.func(args)


# this is for setup:entry_points:console_scripts
def dummy_main(*_args, **_kwargs):
    return
