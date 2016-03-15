# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


from setuptools import setup

setup(
    name = "codeforces-tool",
    packages = ["cftool"],
    entry_points = {
        "console_scripts": ['cf = cftool.tool:main']
    },
    version = "0.6.1",
    description = "Codeforces tool python command line application.",
    long_description = "No description yet",
    author = "Roberto Sales",
    author_email = "iseme.beto@gmail.com",
    package_data = {
        "":["config.json", "template.cpp", "imgs/*.png"]
    },
    install_requires = [
        "colorama",
        "requests",
        "pyquery",
        "prettytable",
        "mechanize",
        "ago",
        "notify2"
    ]
)
