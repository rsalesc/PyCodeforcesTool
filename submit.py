from pprint import pprint
import requests
import json
from download import load_config

def submit_problem(contest, problem, file):
	cfg = load_config()
	if cfg["xuser"] && cfg["token"] && cfg["cfdomain"]:
        parts = {
            "csrf_token":            cfg["token"],
            "action":                "submitSolutionFormSubmitted",
            "submittedProblemIndex": problem,
            "source":                open(file, "rb").read(),
            "programTypeId":         "16",
            "sourceFile":            "",
            "_tta":                  "222"
        }
        url = "http://codeforces.%s/contest/%s/%s" % (cfg["cfdomain"], str(contest), problem)
        r = requests.post(url, data=parts, cookies={"X-User:":cfg["xuser"]}, timeout=3)
        return r.status_code == requests.codes.ok