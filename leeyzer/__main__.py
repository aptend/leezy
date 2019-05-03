import argparse
from leeyzer.crawler import Problem, ProblemEntryRepo

parser = argparse.ArgumentParser(prog='python -m leezyer')
parser.add_argument('cmd', choices=['show', 'pull', 'updatedb'])
parser.add_argument('id')
args = parser.parse_args()

if args.cmd == 'show':
    print(Problem(args.id).show())
elif args.cmd == 'pull':
    Problem(args.id).pull()
elif args.cmd == 'updatedb':
    ProblemEntryRepo().update()


    

