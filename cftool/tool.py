import argparse
from colorama import init, Fore
from download import find_contest, get_contest_task_file, create_contest
from submit import submit_problem
from watch import get_status_table_string, get_standings_table_string, normal_buffer, alternate_buffer, clear_buffer
from tester import test_contest_problem
import editor
import time
import os
import atexit

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-w", "--watch", action="store_true", help="watch contest status")
group.add_argument("-d", "--download", metavar="contest-identifier", help="download contest")
group.add_argument("-s", "--submit", metavar="problem-index", help="submit a problem to current contest")
group.add_argument("-t", "--test", metavar="problem-index", help="test a problem from current contest")
group.add_argument("-a", "--add", metavar="problem-index", help="add a custom test case to the problem")
group.add_argument("-e", "--edit", metavar="problem-index", help="edit problem from current contest")
group.add_argument("-c", "--config", action="store_true", help="edit tool configurations")

args = parser.parse_args()

init(autoreset=True)

def contest_not_found():
    print Fore.RED + "Contest could not be found."
    
def main():
    if args.watch:
        contest = find_contest()
        if contest != None:
            atexit.register(normal_buffer)
            alternate_buffer()
            while 1:
                status = get_status_table_string(contest)
                standings = get_standings_table_string(contest)
                clear_buffer()
                print status
                print standings
                print Fore.YELLOW + "Last update at %s." % (time.strftime("%H:%M:%S"))
                time.sleep(3)

    elif args.download:
        if create_contest(args.download):
            print Fore.GREEN + "Contest downloaded successfully."
        else:
            print Fore.RED + "Contest could not be downloaded."

    elif args.submit:
        contest = find_contest()
        if contest != None:
            os.chdir(contest["dir"])
            if submit_problem(contest, args.submit, get_contest_task_file(contest, args.submit)):
                print Fore.GREEN + "Problem submitted. Make sure it was not identical to some previous submission."
            else:
                print Fore.RED + "The problem could not be submitted."
        else:
            contest_not_found()

    elif args.test:
        contest = find_contest()
        if contest != None:
            os.chdir(contest["dir"])
            test_contest_problem(contest, args.test)
        else:
            contest_not_found()

    elif args.add:
        contest = find_contest()
        if contest != None:
            editor.add_test_contest_problem(contest, args.add)
        else:
            contest_not_found()

    elif args.edit:
        contest = find_contest()
        if contest != None:
            editor.edit_contest_problem(contest, args.edit)
        else:
            contest_not_found()

    elif args.config:
        editor.edit_config()
        editor.edit_template()