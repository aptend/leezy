import argparse

from leeyzer.crawler import Problem, ProblemEntryRepo
from leeyzer.utils import CFG


def update(args):
    ProblemEntryRepo().update()


def pull(args):
    Problem(args.id).pull()


def show(args):
    Problem(args.id).show()


def config(args):
    kvs = CFG.open()
    if args.list:
        print('\n'.join(map('='.join, CFG.fetch_all(kvs, ''))))
    elif args.add:
        CFG.store(kvs, args.add[0], args.add[1])
    elif args.unset:
        CFG.unset(kvs, args.unset[0])
    if args.add or args.unset:
        CFG.write(kvs)
        

parser = argparse.ArgumentParser(prog='python -m leezyer')
subs = parser.add_subparsers(
    title="commands",
    description="use 'python -m leeyzer command -h' to see more",
    metavar='')

pull_parser = subs.add_parser('pull', help='拉取题目到本地文件')
pull_parser.add_argument('id', help="题目编号")
pull_parser.set_defaults(func=pull)

show_parser = subs.add_parser('show', help='打印编号的题目')
show_parser.add_argument('id', help="题目编号")
show_parser.set_defaults(func=show)

update_parser = subs.add_parser('update', help='更新题库')
update_parser.set_defaults(func=update)

config_parser = subs.add_parser('config', help='全局配置')
group = config_parser.add_mutually_exclusive_group()
group.add_argument('--add', nargs=2, metavar='', help='name value')
group.add_argument('--unset', nargs=1, metavar='', help='name')
group.add_argument('--list', action='store_true')
config_parser.set_defaults(func=config)

args = parser.parse_args()
args.func(args)

