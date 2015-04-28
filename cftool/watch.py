from pprint import pprint
from prettytable import PrettyTable
import requests
import json
import os
from download import cfg, find_contest
from colorama import Fore, init
import time
import atexit

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
	print "\033[?47h"

def normal_buffer():
	print "\033[?47l"

def clear_buffer():
	print "\x1b[2J\x1b[1;1H"

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

def parse_verdict(verdict, passed):
	if verdict == "WRONG_ANSWER" or verdict == "RUNTIME_ERROR" or verdict == "TIME_LIMIT_EXCEEDED" or verdict == "MEMORY_LIMIT_EXCEEDED":
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
		head = map(table_header, ["#", "Handle", "Points (Hacks)"])
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
	if cfg["handle"] == "":
		return Fore.RED + "Status table could not be retrieved. Handle is not set."

	qs = {
		"contestId": contest["id"],
		"handle": cfg["handle"],
		"from": 1,
		"count": cfg["subsCount"]
	}
	r = requests.get("http://codeforces.com/api/contest.status", params=qs, timeout=4)
	if r.status_code == requests.codes.ok:
		table = PrettyTable(map(table_header, ["#", "Contest Time", "Problem", "Verdict", "Exec. Time", "Memory"]))
		data = r.json()
		for sub in data["result"]:
			table.add_row([sub["id"], get_contest_time(sub["relativeTimeSeconds"]), "%s - %s" % (sub["problem"]["index"], 
				sub["problem"]["name"]), parse_verdict(sub["verdict"], sub["passedTestCount"]), "%d ms" %(sub["timeConsumedMillis"]), "%d KB" % (sub["memoryConsumedBytes"] // 1024)])

		return table.get_string()
	else:
		return Fore.RED + "Contest status could not be retrieved."
