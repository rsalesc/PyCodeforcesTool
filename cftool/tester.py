from pprint import pprint
import subprocess
import json
import os
import shlex
from colorama import init, Fore
from download import cfg, get_contest_task_file, find_contest, get_relative_problem_dir

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

def test_contest_problem(contest, problem):
    problem_dir = get_relative_problem_dir(contest, problem)
    task_file = os.path.relpath(get_contest_task_file(contest, problem))
    print Fore.CYAN + "Compiling %s..." % (task_file)
    compilation_line = cfg["compilation"].replace("%{file}", "\"%s\"" % (task_file))
    p = subprocess.Popen(shlex.split(compilation_line), cwd=contest["dir"])
    p.wait()
    if p.returncode == 0:
        executable = cfg["executable"].replace("%{problem-index}", problem)
        inputs = [file for file in os.listdir(problem_dir) if file.endswith(".in")]
        for idx, input_file in enumerate(sorted(inputs)):
            input_path = os.path.join(problem_dir, input_file)
            ans_path = os.path.join(problem_dir, "%s.out" % (os.path.splitext(input_file)[0]))
            input_string = None
            ans_string = ""
            with open(input_path, "rb") as f:
                input_string = f.read()

            if os.path.exists(ans_path):
                with open(ans_path, "rb") as f:
                    ans_string = f.read()

            if input_string != None:
                print Fore.YELLOW + "Executing test #%d (%s):" % (idx, os.path.splitext(input_file)[0])
                print Fore.MAGENTA + "Input:"
                print input_string.strip()
                print ""
                print Fore.MAGENTA + "Output:"
                p = subprocess.Popen([executable], cwd=contest["dir"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=(subprocess.STDOUT if cfg["mergeouterr"] else None))
                output_tuple = p.communicate(input=input_string)
                output_print = output_tuple[0].strip()
                ans_print = ans_string.strip()

                print output_print
                print ""
                print Fore.MAGENTA + "Expected Output:"
                print ans_print
                print ""
                if p.returncode != 0:
                    print Fore.MAGENTA + "Verdict: " + Fore.CYAN + "Execution error"
                else:
                    verdict = check_tokens(output_print, ans_print)
                    if verdict:
                        print Fore.MAGENTA + "Verdict: " + Fore.RED + verdict
                    else:
                        print Fore.MAGENTA + "Verdict: " + Fore.GREEN + "Accepted"
                print ""

            else:
                print Fore.RED + "Error reading input files."
    else:
        print Fore.RED + "Compilation error."


if __name__ == "__main__":
    init(autoreset=True)
    contest = find_contest()
    if contest != None:
        os.chdir(contest["dir"])
        test_contest_problem(contest, "A")
    else:
        print "Contest could not be found."