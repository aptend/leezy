import logging
import argparse
import subprocess

from leezy.crawler import Problem
from leezy.config import config

from leezy.errors import show_error_and_exit, LeezyError

import traceback

LOG = logging.getLogger(__name__)
Info = LOG.info
Debug = LOG.debug
Warn = LOG.warning


def show_uncaught_exc(e):
    print(f'Uncaught Exception: {e!r}')
    Debug(traceback.format_exc(limit=10))


def pull(args):
    for pid in expand_ids(args.ids):
        try:
            Problem(pid, args.context).pull()
        except LeezyError as e:
            show_error_and_exit(e)
        except Exception as e:
            show_uncaught_exc(e)


def expand_ids(ids_arg):
    if len(ids_arg) == 1 and ids_arg[0].count('-') == 1:
        s, e = ids_arg[0].split('-')[:2]
        return list(range(int(s), int(e)+1))
    else:
        return ids_arg


def show(args):
    for pid in expand_ids(args.ids):
        try:
            print(Problem(pid).digest())
        except LeezyError as e:
            show_error_and_exit(e)
        except Exception as e:
            show_uncaught_exc(e)


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


def submit(args):
    parts = args.solution.split('@')
    sol_id, id_ = int(parts[0]), int(parts[1])
    try:
        Problem(id_).submit(sol_id)
    except LeezyError as e:
        show_error_and_exit(e)
    except Exception as e:
        show_uncaught_exc(e)


def plot(args):
    from leezy.plot import SNSPlotter, DataFeeder
    SNSPlotter(DataFeeder()).plot()


def handle_config(args):
    if args.list:
        print('\n'.join('='.join((k, str(v)))
                        for k, v in config.get_all_file_data()))
    elif args.add:
        config.put(args.add[0], args.add[1])
    elif args.unset:
        config.delete(args.unset[0])


parser = argparse.ArgumentParser(
    prog='leezy', usage='leezy [-h] COMMAND [...]')
subs = parser.add_subparsers(
    title="commands",
    description="use 'leezy command -h' to see more",
    metavar='')

run_parser = subs.add_parser('run', help='运行题解')
run_parser.add_argument('id', type=int, help="题目编号")
run_parser.set_defaults(func=run)

plot_parser = subs.add_parser('plot', help='画个AC热点图')
plot_parser.set_defaults(func=plot)

submit_parser = subs.add_parser('submit', help='提交题解')
submit_parser.add_argument('solution', help="题解编号，1@1，第一题的题解1")
submit_parser.set_defaults(func=submit)

pull_parser = subs.add_parser('pull', help='拉取题目到本地文件')
pull_parser.add_argument('ids', nargs='+', help="题目编号，多个使用空格分隔")
pull_parser.add_argument('--context', choices=['tree', 'linked_list'],
                         help="题目上下文，影响题目参数转换")
pull_parser.set_defaults(func=pull)

show_parser = subs.add_parser('show', help='打印编号的题目')
show_parser.add_argument('ids', nargs='+', help="题目编号，多个使用空格分隔")
show_parser.set_defaults(func=show)

config_parser = subs.add_parser('config', help='全局配置')
group = config_parser.add_mutually_exclusive_group()
group.add_argument('--add', nargs=2, metavar='', help='NAME VALUE')
group.add_argument('--unset', nargs=1, metavar='', help='NAME')
group.add_argument('--list', action='store_true')
config_parser.set_defaults(func=handle_config)

args = parser.parse_args()
if len(args._get_kwargs()) + len(args._get_args()) == 0:
    parser.print_help()
else:
    log_lv = getattr(logging, config.get('log.level').upper())
    logging.basicConfig(level=log_lv)
    args.func(args)


# this is for setup:entry_points:console_scripts
def dummy_main(*_args, **_kwargs):
    return
