from pprint import pprint
import subprocess
from download import cfg, get_contest_task_file, config_path, get_relative_problem_dir

editor = cfg["editor"] if cfg["editor"] else "xdg-open"

def open_editor(path):
	subprocess.call([editor, path])

def edit_config():
	open_editor(config_path)

def edit_contest_problem(contest, problem):
	open_editor(get_contest_task_file(contest, problem))

def get_input_name(index):
	return "test%d.in" % (index)

def get_output_name(index):
	return "test%d.out" % (index)

def add_test_contest_problem(contest, problem):
	problem_dir = get_relative_problem_dir(contest, problem)
	idx = 0
	while os.path.exists(os.path.join(problem_dir, get_input_name(idx))):
		idx += 1
	in_path = os.path.join(problem_dir, get_input_name(idx))
	out_path = os.path.join(problem_dir, get_output_name(idx))
	open_editor(in_path)
	open_editor(out_path)