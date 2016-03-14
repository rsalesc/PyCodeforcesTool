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
global_contest_folder = os.path.join(app_folder, ".contests")

def load_config(path):
	json_data = open(path)
	data = json.load(json_data)
	json_data.close()
	return data

def deprecated_config(path):
	cur_config = load_config(path)
	new_config = json.loads(resource_string(__name__, "config.json"))
	if not "release" in cur_config.keys() or cur_config["release"] < new_config["release"]:
		return True
	return False

if not os.path.isdir(app_folder):
	os.makedirs(app_folder)

default_template_path = os.path.join(app_folder, "template.cpp")
config_path = os.path.join(app_folder, "config.json")

if not os.path.isfile(default_template_path):
	template_tmp = resource_string(__name__, "template.cpp")
	with open(default_template_path, "wb") as f:
		f.write(template_tmp)

if not os.path.isfile(config_path) or deprecated_config(config_path):
	config_tmp = resource_string(__name__, "config.json")
	with open(config_path, "wb") as f:
		f.write(config_tmp)

cfg = load_config(config_path)

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

def find_global_contest(contest_id):
	dir = os.path.join(global_contest_folder, str(contest_id))
	contest_file = os.path.join(dir, "contest.json")
	if not os.path.exists(contest_file):
		return None
	else:
		with open(contest_file, "rb") as f:
			data = json.load(f)
			data["dir"] = dir
			return data

def get_contest_file_name(contest, index, language=None):
	if not language:
		language = cfg["languages"][cfg["languages"]["default"]]

	return language["file"].replace("%{problem-index}", index)

def get_contest_task_file(contest, index, language=None):
	if not language:
		language = cfg["languages"][cfg["languages"]["default"]]

	return os.path.join(contest["dir"], "%s/%s" % (index, get_contest_file_name(contest, index, language)))

def get_contest_submit_file_name(contest, index, language=None):
    if not language:
		language = cfg["languages"][cfg["languages"]["default"]]

    if not "submitFile" in language:
        return get_contest_file_name(contest, index, language)
    else:
        return language["submitFile"].replace("%{problem-index}", index) \
                .replace("%{file}", get_contest_file_name(contest, index, language))

def get_contest_task_submit_file(contest, index, language=None):
    if not language:
		language = cfg["languages"][cfg["languages"]["default"]]
    return os.path.join(contest["dir"], "%s/%s" % (index, get_contest_submit_file_name(contest, index, language)))

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

		# shutil.copyfile(template_path, os.path.join(problem_dir, problem["idx"]+"."+cfg["extension"])) # check this
		for key, language in cfg["languages"].iteritems():
			if key == "default":
				continue
			if "template" in language.keys():
				template_path = os.path.join(app_folder, language["template"])
				if os.path.exists(template_path):
					shutil.copyfile(template_path, os.path.join(problem_dir, get_contest_file_name(contest, problem["idx"], language)))

		for i,test in enumerate(problem["tests"]):
			in_path = os.path.join(problem_dir, ("test%d.in" % i))
			out_path = os.path.join(problem_dir, ("test%d.out" % i))
			with open(in_path, "wb") as f:
				f.write(test["input"])
                        with open(out_path, "wb") as f:
				f.write(test["output"])

	return True

def create_global_contest(contest_id):
	url="http://www.codeforces.com/contest/" + str(contest_id) + "/problems"
	print Fore.YELLOW + "Downloading contest "  + str(contest_id) + " from " + url
	page = requests.get(url) # rember to check if page was down suc
	if page.status_code != requests.codes.ok:
		return None
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

	dir = os.path.join(global_contest_folder, str(contest_id))
	if not os.path.exists(dir):
		os.makedirs(dir)
	contest["dir"] = dir
	with open(os.path.join(dir, "contest.json"), "wb") as f:
		json.dump(contest, f, indent=4)

	for problem in contest["problems"]:
		problem_dir = os.path.join(dir, problem["idx"]+"/")
		if not os.path.exists(problem_dir):
			os.makedirs(problem_dir)

		for i,test in enumerate(problem["tests"]):
			in_path = os.path.join(problem_dir, ("test%d.in" % i))
			out_path = os.path.join(problem_dir, ("test%d.out" % i))
			with open(in_path, "wb") as f:
				f.write(test["input"])
			with open(out_path, "wb") as f:
				f.write(test["output"])

	return contest

def find_or_create_global_contest(contest_id):
	contest = find_global_contest(contest_id)
	if not contest:
		contest = create_global_contest(contest_id)
	return contest
