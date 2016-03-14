import argparse
from colorama import init, Fore
from download import find_contest, get_contest_task_file, create_contest, find_or_create_global_contest, app_folder, \
                    get_contest_task_submit_file
from submit import submit_problem, get_index_and_language, get_problem_and_language
from watch import get_status_table_string, get_standings_table_string, normal_buffer, alternate_buffer, clear_buffer
from watch import get_last_table_string
from tester import test_contest_problem, test_single_problem
import notify
import editor
import time
import os
import atexit
import sys
import signal

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
watch = parser.add_mutually_exclusive_group()
watch.add_argument("-w", "--watch", action="store_true", help="watch contest status")
watch.add_argument("-l", "--last", action="store_true", help="watch your 5 last submissions")

group.add_argument("-d", "--download", metavar="contest-identifier", help="download contest")
group.add_argument("-s", "--submit", metavar="problem-index", help="submit a problem to current contest")
group.add_argument("-t", "--test",  help="test a problem from current contest")
group.add_argument("-a", "--add", metavar="problem-index", help="add a custom test case to the problem")
group.add_argument("-e", "--edit", metavar="problem-index", help="edit problem from current contest")
group.add_argument("-f", "--folder", action="store_true", help="open folder in desired application")
group.add_argument("-c", "--config", action="store_true", help="edit tool configurations")
group.add_argument("-n", "--notify", action="store_true", help="watch for notifications")

parser.add_argument("-x", "--single", action="store_true", help="modifier to run commands for a single file")
parser.add_argument("-v", "--stream", action="store_true", help="print results in streaming way")

args = parser.parse_args()

init(autoreset=True)

def dump_table(name, str):
    file = open(os.path.join(app_folder, name), "wb")
    file.write(str)
    file.close()

def confirmation(text="Are you sure you want to continue?"):
    choices = {"Y":True, "y":True, "n": False, "N": False}

    print text + " (Y/n)"
    while True:
        r = raw_input().strip()
        if not r in choices:
            print "Please, type only (Y/n) as response."
            continue
        else:
            return choices[r]


def contest_not_found():
    print Fore.RED + "Contest could not be found."

def get_absolute_path(path):
    return os.path.normpath(os.path.join(os.getcwd(), path))

def get_last_update():
    return Fore.YELLOW + "Last update at %s." % (time.strftime("%H:%M:%S"))

def sigint_handler(signal, frame):
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, sigint_handler)
    problem_submitted = False

    if args.notify:
        contest = find_contest()
        if contest != None:
            notify.process(contest)
        return

    if args.download:
        if create_contest(args.download):
            print Fore.GREEN + "Contest downloaded successfully."
        else:
            print Fore.RED + "Contest could not be downloaded."

    elif args.submit:
        print Fore.CYAN + "Problem: " + Fore.RESET + str(args.submit)
        print Fore.RED + "Have you checked all the corner cases, constraints and overflow possibilities?" + Fore.RESET
        if not confirmation():
            sys.exit(0)

        if args.single:
            file = get_absolute_path(args.submit)
            contest_id, idx, language = get_problem_and_language(file)
            contest = find_or_create_global_contest(contest_id)
            if not contest:
                contest_not_found()
            else:
                if submit_problem(contest, idx, file, language):
                    problem_submitted = True
                    print Fore.GREEN + "Problem submitted. Make sure it was not identical to some previous submission."
                else:
                    print Fore.RED + "The problem could not be submitted."
        else:
            contest = find_contest()
            if contest != None:
                os.chdir(contest["dir"])

                (index, language) = get_index_and_language(args.submit)

                if submit_problem(contest, args.submit, get_contest_task_submit_file(contest, index, language), language):
                    problem_submitted = True
                    print Fore.GREEN + "Problem submitted. Make sure it was not identical to some previous submission."
                else:
                    print Fore.RED + "The problem could not be submitted."
            else:
                contest_not_found()

    elif args.test:
        if args.single:
            test_single_problem(args.test[0], args=args.test[1:], stream=args.stream)
        else:
            contest = find_contest()
            if contest != None:
                os.chdir(contest["dir"])
                (index, language) = get_index_and_language(args.test)

                test_contest_problem(contest, index, language, stream=args.stream)
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

    elif args.folder:
        contest = find_contest()
        if contest != None:
            editor.edit_contest_folder(contest)
        else:
            contest_not_found()

    elif args.config:
        editor.edit_config()
        # editor.edit_template()

    if args.last:
        atexit.register(normal_buffer)
        alternate_buffer()
        while 1:
            last = get_last_table_string()
            clear_buffer()
            text = last
            text += '\n'
            if problem_submitted:
                text += Fore.GREEN + "Request was sent. Check if problem was received by the server.\n"
            text += get_last_update()+"\n"
            print text
            # dump_table("last", text)
            time.sleep(3)

    elif args.watch:
        contest = find_contest()
        if contest != None:
            atexit.register(normal_buffer)
            alternate_buffer()
            while 1:
                status = get_last_table_string(contest)
                standings = get_standings_table_string(contest)
                clear_buffer()
                print status
                print standings
                print get_last_update()
                time.sleep(3)
