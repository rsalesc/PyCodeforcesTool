from pprint import pprint
from prettytable import PrettyTable
import requests
import json
import os
from .download import cfg, find_contest
from colorama import Fore, init
import time
import atexit
from datetime import datetime

verdict_map = {
    "OK" : Fore.GREEN + "Accepted",
    "FAILED" : Fore.RED + "Failed",
    "COMPILATION_ERROR" : Fore.CYAN + "Compilation Error",
    "WRONG_ANSWER" : Fore.RED + "Wrong Answer",
    "RUNTIME_ERROR" : Fore.RED + "Runtime error",
    "TIME_LIMIT_EXCEEDED" : Fore.RED + "Time limit exceeded",
    "MEMORY_LIMIT_EXCEEDED" : Fore.RED + "Memory limit exceeded",
    "TESTING" : "Running tests",
    "" : "In queue",
    "CHALLENGED" : Fore.MAGENTA + "Hacked"
}

def alternate_buffer():
    print("\033[?47h")

def normal_buffer():
    print("\033[?47l")

def clear_buffer():
    print("\x1b[2J\x1b[1;1H")

def delta_time(ts):
    return ""

def get_contest_time(secs):
    if(secs > 1e7):
        return "--:--"
    return "%02d:%02d"% (secs//60//60, secs//60%60)

def get_hacks(ok, fail):
    res=""
    if ok > 0:
        res += Fore.GREEN + "+%d" % (ok)
        if fail > 0:
            res += " : "

    if fail > 0:
        res += "-%d" % (fail)

    if ok > 0 or fail > 0:
        return "(" + res + ")" + Fore.RESET
    else:
        return ""

run_verdicts = {"WRONG_ANSWER", "RUNTIME_ERROR", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED", "TESTING"}
def parse_verdict(verdict, passed):
    if verdict in run_verdicts:
        return ("%s" + Fore.RESET + " (%d)") % (verdict_map[verdict], passed+1)
    else:
        return verdict_map[verdict] + Fore.RESET

def table_header(str):
    return Fore.CYAN + str + Fore.RESET

def get_standings_table_string(contest):
    qs = {
        "contestId": contest["id"],
        "handles": cfg["handle"] + ";" + ";".join(cfg["friends"].split())
    }
    r = requests.get("http://codeforces.com/api/contest.standings", params=qs, timeout=4)
    if r.status_code == requests.codes.ok:
        head = list(map(table_header, ["#", "Handle", "Points (Hacks)"]))
        data = r.json()
        for problem in data["result"]["problems"]:
            head.append(table_header("%s (%d)" % (problem["index"], int(problem["points"]))))

        table = PrettyTable(head)
        for row in data["result"]["rows"]:
            arr = [row["rank"], row["party"]["members"][0]["handle"], "%d%s" % (int(row["points"]), get_hacks(row["successfulHackCount"], row["unsuccessfulHackCount"]))]

            for result in row["problemResults"]:
                if result["points"] > 0:
                    arr.append( (Fore.GREEN + "%d" + Fore.RESET + " (%s)")  % (result["points"], get_contest_time(result["bestSubmissionTimeSeconds"])))
                else:
                    if result["rejectedAttemptCount"] > 0:
                        arr.append( (Fore.RED + "-%d" + Fore.RESET) % (result["rejectedAttemptCount"]))
                    else:
                        arr.append("")

            table.add_row(arr)

        return table.get_string()
    else:
        return Fore.RED + "Contest standings could not be retrieved."

def get_status_table_string(contest):
    if cfg.get("handle", "") == "":
        return Fore.RED + "Status table could not be retrieved. Handle is not set."

    qs = {
        "contestId": contest["id"],
        "handle": cfg["handle"],
        "from": 1,
        "count": cfg.get("subsCount", 4)
    }
    r = requests.get("http://codeforces.com/api/contest.status", params=qs, timeout=4)
    if r.status_code == requests.codes.ok:
        table = PrettyTable(list(map(table_header, ["#", "Time", "Contest Time", "Problem", "Verdict", "Exec. Time", "Memory"])))
        data = r.json()
        if data["status"] == "FAILED":
            return Fore.RED + "Contest status could not be retrieved.\n" + Fore.RESET + "Reason: " + data["comment"]

        for sub in data["result"]:
            table.add_row([sub["id"], delta_time(sub["creationTimeSeconds"]), get_contest_time(sub["relativeTimeSeconds"]), "%s - %s" % (sub["problem"]["index"],
                sub["problem"]["name"]), parse_verdict(sub.get("verdict", ""), sub.get("passedTestCount", 0)), "%d ms" %(sub["timeConsumedMillis"]), "%d KB" % (sub["memoryConsumedBytes"] // 1024)])

        return table.get_string()
    else:
        return Fore.RED + "Contest status could not be retrieved. Check if handles are correctly set."

def get_last_table_string(contest=None):
    handle = cfg.get("handle", "")
    if handle == "":
        return Fore.RED + "Last submissions table could not be retrieved. Handle is not set."

    maxsub = cfg.get("subsCount", 4)
    qs = {
        "handle": handle,
        "from": 1,
        "count": maxsub*2
    }

    r = None
    if contest == None:
        r = requests.get("http://codeforces.com/api/user.status", params=qs, timeout=4)
    else:
        qs["contestId"] = contest["id"]
        r = requests.get("http://codeforces.com/api/contest.status", params=qs, timeout=4)

    if r.status_code == requests.codes.ok:
        table = PrettyTable(list(map(table_header, ["#", "Time", "Problem", "Verdict", "Exec. Time", "Memory"])))
        data = r.json()
        if data["status"] == "FAILED":
            return Fore.RED + "Last submissions could not be retrieved.\n" + Fore.RESET + "Reason: " + data["comment"]

        result = data["result"]
        if contest != None:
            contest_id = contest["id"]
            tmp = [i for i in result if str(i.get("contestId", "")).strip() == str(contest_id).strip()]
            result = tmp

        cnt = 0
        for sub in result:
            if cnt >= maxsub:
                break
            cnt += 1
            table.add_row([sub["id"], delta_time(sub["creationTimeSeconds"]), "%s - %s" % (sub["problem"]["index"],
                sub["problem"]["name"]), parse_verdict(sub.get("verdict", ""), sub["passedTestCount"]), "%d ms" %(sub["timeConsumedMillis"]), "%d KB" % (sub["memoryConsumedBytes"] // 1024)])

        return table.get_string()
    else:
        return Fore.RED + "Last submissions could not be retrieved."
