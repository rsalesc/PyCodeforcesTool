from pprint import pprint
import requests
import json
import os
from download import find_contest, cfg
from colorama import init, Fore

def submit_problem(contest, problem, file):
    if not os.path.exists(file):
        return False
    if cfg["xuser"] and cfg["token"] and cfg["cfdomain"]:
        parts = {
            "csrf_token":            cfg["token"],
            "action":                "submitSolutionFormSubmitted",
            "submittedProblemIndex": problem,
            "source":                open(file, "rb").read(),
            "programTypeId":         "16",
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