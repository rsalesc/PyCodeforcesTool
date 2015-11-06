import requests
import os
import json

def get_seed(contest, handle):
    qs = {
            "contestId":contest["id"]
            }

    r = requests.get("http://codeforces.com/api/contest.standings", params=qs, timeout=4)
    
