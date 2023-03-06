from pprint import pprint
import subprocess
import json
import os
import shlex
from colorama import init, Fore
from .download import cfg, get_contest_task_file, find_contest, get_relative_problem_dir, find_or_create_global_contest, \
                get_contest_submit_file_name, get_contest_task_submit_file
from .submit import get_problem_and_language

def check_token(output_tk, expected_tk):
    return output_tk == expected_tk

def check_tokens(output, expected):
    output_tk = output.split()
    expected_tk = expected.split()
    if len(output_tk) != len(expected_tk):
        return "Difference at token count. Expected %d but found %d." % (len(expected_tk), len(output_tk))

    for idx, tk in enumerate(output_tk):
        if not check_token(tk, expected_tk[idx]):
            return "Difference at token #%d. Expected '%s' but found '%s'." % (idx+1, expected_tk[idx], tk)

def preprocess(contest, problem, language, task_file, submit_file):
    print((Fore.CYAN + "Pre-processing %s..." % (task_file)))
    preexec_list = language["preexec"] if "preexec" in list(language.keys()) else []

    for pre in preexec_list:
        preexec_line = pre.replace("%{file}", task_file) \
                        .replace("%{submit-file}", submit_file)

        p = subprocess.Popen(shlex.split(preexec_line), cwd=contest["dir"])
        p.wait()
        if p.returncode != 0:
            return False
    return True

def get_task_and_submit_files(contest, problem, language):
    task_file = os.path.relpath(get_contest_task_file(contest, problem, language), contest["dir"])
    submit_file = os.path.relpath(get_contest_task_submit_file(contest, problem, language), contest["dir"])
    return (task_file, submit_file)

def test_contest_problem(contest, problem, language=None, task_file=None, stream=False):
    if not language:
        language = cfg["languages"][cfg["languages"]["default"]]

    problem_dir = os.path.join(contest["dir"], get_relative_problem_dir(contest, problem))
    if not task_file:
        (task_file, submit_file) = get_task_and_submit_files(contest, problem, language)
    else:
        base = os.path.basename(task_file)
        submit_file = os.path.join(os.path.dirname(task_file),
            '.'.join(base.split(".")[:-1] + ['pre'] + base.split(".")[-1:]))

    preexec_ok = preprocess(contest, problem, language, task_file, submit_file)

    if preexec_ok:
        executable = language["exec"].replace("%{file}", task_file).replace("%{submit-file}", submit_file)
        inputs = [file for file in os.listdir(problem_dir) if file.endswith(".in")]
        for idx, input_file in enumerate(sorted(inputs)):
            input_path = os.path.join(problem_dir, input_file)
            ans_path = os.path.join(problem_dir, "%s.out" % (os.path.splitext(input_file)[0]))
            input_string = None
            ans_string = ""
            with open(input_path, "r") as f:
                input_string = f.read()

            if os.path.exists(ans_path):
                with open(ans_path, "r") as f:
                    ans_string = f.read()

            if input_string != None:
                print(Fore.YELLOW + "Executing test #%d (%s):" % (idx, os.path.splitext(input_file)[0]))
                print(Fore.MAGENTA + "Input:")
                print(Fore.WHITE + input_string.strip())
                print("")
                print(Fore.MAGENTA + "Output:")
                p = subprocess.Popen(shlex.split(executable), bufsize=1 if stream else 0, cwd=contest["dir"], stdin=open(input_path, "rb"), stdout=subprocess.PIPE, stderr=(subprocess.STDOUT if cfg["mergeouterr"] else None))
                # output_tuple = p.communicate(input=input_string)
                output_print = ""

                if stream:
                    with p.stdout:
                        for line in iter(p.stdout.readline, b''):
                            print(Fore.WHITE + line.rstrip())
                            output_print += line
                    p.wait() # wait for the subprocess to exit
                    output_print = output_print.strip()
                else:
                    p.wait()
                    output_print = p.communicate()[0].strip().decode("utf-8")
                    print(Fore.WHITE + output_print)

                ans_print = ans_string.strip()

                # print Fore.WHITE + output_print
                print("")
                print(Fore.MAGENTA + "Expected Output:")
                print(Fore.WHITE + ans_print)
                print("")
                if p.returncode != 0:
                    print(Fore.MAGENTA + "Verdict: " + Fore.CYAN + "Execution error")
                else:
                    verdict = check_tokens(output_print, ans_print)
                    if verdict:
                        print(Fore.MAGENTA + "Verdict: " + Fore.RED + verdict)
                    else:
                        print(Fore.MAGENTA + "Verdict: " + Fore.GREEN + "Accepted")
                print("")

            else:
                print(Fore.RED + "Error reading input files.")
    else:
        print(Fore.RED + "Error at some step of pre-processing.")


def test_single_problem(path, stream=False):
    contest_id, idx, language = get_problem_and_language(path)
    contest = find_or_create_global_contest(contest_id)
    if not contest:
        print("Failed testing problem. Contest does not exists.")
    else:
        test_contest_problem(contest, idx, language, task_file=path, stream=stream)

if __name__ == "__main__":
    init(autoreset=True)
    contest = find_contest()
    if contest != None:
        os.chdir(contest["dir"])
        test_contest_problem(contest, "A")
    else:
        print("Contest could not be found.")
