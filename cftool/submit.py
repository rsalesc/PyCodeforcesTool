import json
import os
from pprint import pprint

import mechanize
import requests
from colorama import Fore, init

from .download import cfg, find_contest
from .utils import get_contest_url


class Session():
    def __init__(self):
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    def select_form_by_id(self, id, forms):
        for form in forms:
            if form.attrs.get("id") == id:
                return form
        return None

    def select_form_by_class(self, cl, forms):
        for form in forms:
            if form.attrs.get("class") == cl:
                return form
        return None

    def login(self, handle, password):
        response = self.br.open("http://codeforces.com/enter")
        if not response.geturl().endswith("enter"):
            return
        form = self.select_form_by_id("enterForm", self.br.forms())
        if form == None:
            raise Exception("Login form was not found")

        form["handleOrEmail"] = handle
        form["password"] = password
        self.br.form = form
        response = self.br.submit()
        if response.geturl().endswith("enter"):
            raise Exception("Login attempt was not successful. Check your credentials or your internet connection")

    def submit(self, contest_id, problem, file, language_id):
        filename = os.path.abspath(file)
        url = "%s/problem/%s" % (get_contest_url(contest_id), problem)
        self.br.open(url)
        form = self.select_form_by_class("submitForm", self.br.forms())
        if form == None:
            raise Exception("You are not logged in or problem does not exist")

        form["programTypeId"] = [str(language_id)]
        form.add_file(open(filename), "plain/text", filename)
        self.br.form = form
        response = self.br.submit()

def get_index_and_language(string):
    language = None
    splitted = string.split(".")
    if len(splitted) > 1 and splitted[1] in list(cfg["languages"].keys()):
        language = cfg["languages"][splitted[1]]
    else:
        language = cfg["languages"][cfg["languages"]["default"]]

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

    if not "typeid" in list(language.keys()):
        print((Fore.RED + "Typeid for this language is not set."))
        return False

    if not os.path.exists(file):
        return False

    if cfg["handle"] and cfg["password"]:
        session = Session()
        session.login(cfg["handle"], cfg["password"])
        session.submit(contest["id"], problem, file, language["typeid"])
        print((Fore.MAGENTA + "Request was sent. Check if the submission was received by the server executing -l command"))
        return True
    else:
        print((Fore.RED + "Credentials were not set in config.json"))
        return False

if __name__ == "__main__":
    init(autoreset=True)
    contest = find_contest()
    if contest != None:
        os.chdir(contest["dir"])
        if submit_problem(contest, "A", "A/A.cpp"):
            print((Fore.GREEN + "Problem submitted. Make sure it was not identical to some previous submission."))
        else:
            print((Fore.RED + "The problem could not be submitted."))
    else:
        print((Fore.RED + "Contest could not be found."))
