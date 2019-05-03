import argparse
from leeyzer.crawler import Problem, ProblemEntryRepo

def update(args):
    ProblemEntryRepo().update()


def pull(args):
    Problem(args.id).pull()


def show(args):
    print(Problem(args.id).show())

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

args = parser.parse_args()
args.func(args)




    

