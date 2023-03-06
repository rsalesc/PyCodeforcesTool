from pprint import pprint
import subprocess
import os
from .download import cfg, get_contest_task_file, config_path, get_relative_problem_dir
import shlex

editor = cfg["editor"] if "editor" in list(cfg.keys()) else "xdg-open"
folder_editor = cfg["folder-editor"] if "folder-editor" in list(cfg.keys()) else False

def open_editor(*paths):
    ls = shlex.split(editor)
    ls.extend(paths)
    subprocess.call(ls)

def open_folder(path):
	if not folder_editor:
		print("Your folder editor was not configured.")
		return
	subprocess.call([folder_editor, path])

def edit_config():
	open_editor(config_path)

def edit_contest_problem(contest, problem):
	open_editor(get_contest_task_file(contest, problem))

def edit_contest_folder(contest):
	open_folder(contest["dir"])

def get_input_name(index):
	return "test%d.in" % (index)

def get_output_name(index):
	return "test%d.out" % (index)

def add_test_contest_problem(contest, problem):
	problem_dir = os.path.join(contest["dir"], get_relative_problem_dir(contest, problem))
	idx = 0
	while os.path.exists(os.path.join(problem_dir, get_input_name(idx))):
		idx += 1
		print(problem_dir)
	in_path = os.path.abspath(os.path.join(problem_dir, get_input_name(idx)))
	out_path = os.path.abspath(os.path.join(problem_dir, get_output_name(idx)))
	open_editor(in_path, out_path)
