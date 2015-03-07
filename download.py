from pprint import pprint
import requests
import os.path
import json
import re
import shutil
from pyquery import PyQuery as pq
from HTMLParser import HTMLParser

template_path = "template.cpp"

def normalize_html(str):
	return HTMLParser().unescape(re.sub(r"(?i)<br\s*?/?>","\n",str))

def create_contest(contest_id):
	url="http://www.codeforces.com/contest/" + str(contest_id) + "/problems"
	print ("Downloading contest "  + str(contest_id))
	page = requests.get(url) # rember to check if page was down suc
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

	dir = str(contest_id)+"/"
	if not os.path.exists(dir):
		os.makedirs(dir)
	with open(dir+"contest.json", "wb") as f:
		json.dump(contest, f, indent=4)

	for problem in contest["problems"]:
		problem_dir = dir+problem["idx"]+"/"
		if not os.path.exists(problem_dir):
			os.makedirs(problem_dir)

		shutil.copyfile(template_path, problem_dir+problem["idx"]+".cpp")
		for i,test in enumerate(problem["tests"]):
			in_path = problem_dir + ("test%d.in" % i)
			out_path = problem_dir + ("test%d.out" % i)
			with open(in_path, "wb") as f:
				f.write(test["input"])
			with open(out_path, "wb") as f:
				f.write(test["output"])

if __name__ == "__main__":
	create_contest("518")