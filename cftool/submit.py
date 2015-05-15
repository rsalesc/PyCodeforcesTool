from pprint import pprint
import requests
import json
import os
from download import find_contest, cfg
from colorama import init, Fore

def get_index_and_language(string):
    language = None
    splitted = string.split(".")
    if len(splitted) > 1 and splitted[1] in cfg["languages"].keys():
        language = cfg["languages"][splitted[1]]

    return (splitted[0], language)

def get_problem_and_language(string):
    language = None
    name, extension = os.path.splitext(os.path.basename(string))
    language = cfg["languages"][extension[1:]]
    ps = name.split()[0]
    i = 0
    while ps[i].isdigit():
        i += 1

    if i == 0 or i == len(ps):
        return False
    else:    
        return (int(ps[:i]), ps[i:], language)

def submit_problem(contest, problem, file, language=None):
    if not language:
        language = cfg["languages"][cfg["languages"]["default"]]

    if not "typeid" in language.keys():
        print Fore.RED + "Typeid for this language is not set."
        return False

    if not os.path.exists(file):
        return False
    if cfg["xuser"] and cfg["token"] and cfg["cfdomain"]:
        parts = {
            "csrf_token":            cfg["token"],
            "action":                "submitSolutionFormSubmitted",
            "submittedProblemIndex": problem,
            "source":                open(file, "rb").read(),
            "programTypeId":         language["typeid"],
            "sourceFile":            "",
            "_tta":                  "222"
        }
        url = "http://codeforces.%s/contest/%s/problem/%s" % (cfg["cfdomain"], contest["id"], problem)
        print Fore.YELLOW + "Submitting to %s" % (url)
        r = requests.post(url, data=parts, cookies={"X-User":cfg["xuser"]}, timeout=3)
        return r.status_code == requests.codes.ok
    print Fore.RED + "X-User/Token/CFDomain not set in config.json."
    return False

if __name__ == "__main__":
    init(autoreset=True)
    contest = find_contest()
    if contest != None:
        os.chdir(contest["dir"])
        if submit_problem(contest, "A", "A/A.cpp"):
            print Fore.GREEN + "Problem submitted. Make sure it was not identical to some previous submission."
        else:
            print Fore.RED + "The problem could not be submitted."
    else:
        print Fore.RED + "Contest could not be found."