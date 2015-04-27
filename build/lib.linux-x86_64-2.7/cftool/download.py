from pprint import pprint
import requests
import os
import json
import re
import shutil
from colorama import Fore, init
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser
from pkg_resources import resource_string

app_folder = os.path.join(os.path.expanduser("~"), ".cftool/")

if not os.path.isdir(app_folder):
	os.makedirs(app_folder)

template_path = os.path.join(app_folder, "template")
config_path = os.path.join(app_folder, "config.json")

if not os.path.isfile(template_path):
	template_tmp = resource_string(__name__, "template")
	with open(template_path, "wb") as f:
		f.write(template_tmp)

if not os.path.isfile(config_path):
	config_tmp = resource_string(__name__, "config.json")
	with open(config_path, "wb") as f:
		f.write(config_tmp)

def load_config():
	json_data = open(config_path)
	data = json.load(json_data)
	json_data.close()
	return data

cfg = load_config()

def find_contest():
	dir = os.getcwd()
	contest_file = os.path.join(dir, "contest.json")
	level = 0
	while not os.path.isfile(contest_file) and level < 4:
		dir = os.path.dirname(dir)
		contest_file = os.path.join(dir, "contest.json")
		level += 1
	if level == 4:
		return None
	else:
		with open(contest_file, "rb") as f:
			data = json.load(f)
			data["dir"] = dir
			return data

def get_contest_task_file(contest, index):
	return os.path.join(contest["dir"], "%s/%s.%s" % (index, index, cfg["extension"]))

def get_relative_problem_dir(contest, index):
	return "%s/" % (index)

def normalize_html(str):
	return HTMLParser().unescape(re.sub(r"(?i)<br\s*?/?>","\n",str))

def create_contest(contest_id):
	url="http://www.codeforces.com/contest/" + str(contest_id) + "/problems"
	print Fore.YELLOW + "Downloading contest "  + str(contest_id) + " from " + url
	page = requests.get(url) # rember to check if page was down suc
	if page.status_code != requests.codes.ok:
		return False
	q = pq(page.text)
	q.make_links_absolute(base_url=url)

	contest = { "id": contest_id, "problems" : [] }

	def process_problem_elem(index, elem):
		elem = pq(elem)
		problem = {
			"idx": elem.attr("problemindex"),
			"name": pq(elem.find(".title")[0]).text(),
			"tests": []
		}

		def process_sample_test_elem(index, elem):
			elem = pq(elem)
			input_elems = elem.find(".input")
			output_elems = elem.find(".output")
			for idx, inelem in enumerate(input_elems):
				test = {
					"input": normalize_html(pq(pq(inelem).find("pre")[0]).html()),
					"output": normalize_html(pq(pq(output_elems[idx]).find("pre")[0]).html())
				}
				problem["tests"].append(test)

		elem.find(".sample-test").each(process_sample_test_elem)
		contest["problems"].append(problem)

	q("[problemIndex]").each(process_problem_elem)

	dir = str(contest_id)
	if not os.path.exists(dir):
		os.makedirs(dir)
	with open(os.path.join(dir, "contest.json"), "wb") as f:
		json.dump(contest, f, indent=4)

	for problem in contest["problems"]:
		problem_dir = os.path.join(dir, problem["idx"]+"/")
		if not os.path.exists(problem_dir):
			os.makedirs(problem_dir)

		shutil.copyfile(template_path, os.path.join(problem_dir, problem["idx"]+"."+cfg["extension"]))
		for i,test in enumerate(problem["tests"]):
			in_path = problem_dir + ("test%d.in" % i)
			out_path = problem_dir + ("test%d.out" % i)
			with open(in_path, "wb") as f:
				f.write(test["input"])
			with open(out_path, "wb") as f:
				f.write(test["output"])

	return True