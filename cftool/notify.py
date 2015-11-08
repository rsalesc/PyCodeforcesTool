import notify2 as ntf
import time
import os
import json
import urllib2
import threading
from download import cfg
from pkg_resources import resource_filename

def gr(p):
    return resource_filename(__name__, "imgs/"+p+".png")

ICONS = {
    "self":{
        "FAIL": gr("fail"),
        "OK": gr("ok"),
        "CHALLENGED": gr("hack"),
        "WRONG_ANSWER": gr("wa"),
        "TIME_LIMIT_EXCEEDED": gr("tle"),
        "COMPILATION_ERROR": gr("compilation")
    },
    "friend":{
        "FAIL": gr("friend_fail"),
        "OK": gr("friend_ok"),
        "CHALLENGED": gr("friend_hack"),
        "WRONG_ANSWER": gr("friend_wa"),
        "TIME_LIMIT_EXCEEDED": gr("friend_tle"),
        "COMPILATION_ERROR": gr("friend_compilation")
    }
}

TESTSETS = {
    "TESTS": "systests",
    "PRETESTS": "pretests",
    "CHALLENGES": "hack tests"
}

FAIL=["COMPILATION_ERROR", "RUNTIME_ERROR", "WRONG_ANSWER", "PRESENTATION_ERROR", "TIME_LIMIT_EXCEEDED", "MEMORY_LIMIT_EXCEEDED",
"IDLENESS_LIMIT_EXCEEDED", "SECURITY_VIOLATED"]

MAX_REQUESTS_PER_SECOND = 4
sema = threading.BoundedSemaphore(MAX_REQUESTS_PER_SECOND)

def request(url):
    sema.acquire()
    try:
        res = urllib2.urlopen(url, timeout=4)
        sema.release()
        data = json.load(res)
        if data["status"] != "OK":
            return None

        return data["result"]
    except Exception:
        sema.release()
        return None

class Request(threading.Thread):
    def __init__(self, id, url, result):
        threading.Thread.__init__(self)
        self.url = url
        self.result = result
        self.id = id
    def run(self):
        data = request(self.url)
        if data != None:
            self.result.append((self.id, data))

class StandingsRequest(threading.Thread):
    def __init__(self, contestId):
        threading.Thread.__init__(self)
        self.url = "http://codeforces.com/api/contest.standings?contestId=%d" % int(contestId)
        self.result = None

    def run(self):
        self.result = request(self.url)

def watch(user, handles, contest, watch_all=True, fetch_standings=False):
    mp = {}
    happened = {}

    is_self = lambda x: x == user
    ntf.init("CF Notifier")
    while 1:
        #print "trying..."
        #print mp
        
        data = []
        threads = []

        for handle in handles:
            count = 50 if handle not in happened else 15
            threads.append(Request(handle, "http://codeforces.com/api/user.status?handle=%s&count=%d" % (handle, count), data))

        standings = StandingsRequest(contest)
        if fetch_standings:
            threads.append(standings)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        rank = {}
        if standings.result != None:
            for row in standings.result["rows"]:
                for member in row["party"]["members"]:
                    if member["handle"] in handles:
                        rank[member["handle"]] = (row["rank"], row["points"])

        for (handle, subs) in data:
            subs = filter(lambda x: x["contestId"] == int(contest), subs)
            subs.reverse()

            pos = " %s now ranked #%d with %d points." % ("You are" if is_self(handle) else "(S)he is", int(rank[handle][0]), int(rank[handle][1])) if handle in rank else ""

            for sub in subs:
                ntuple = (sub["testset"], sub["verdict"])
                if sub["id"] not in mp or mp[sub["id"]] != ntuple:
                    mp[sub["id"]] = ntuple
                    
                    testset = TESTSETS.get(sub["testset"], "tests")
                    verdict = sub["verdict"].replace("_", " ")
                    passed_count = sub["passedTestCount"]
                    pc = " on %s %d" % (testset[:-1], passed_count+1)
                    letter = sub["problem"]["index"]
                    subject = "Your" if is_self(handle) else "%s's" % (handle)
                    tsubject = "You" if is_self(handle) else "Someone"
                    icon_group = "self" if is_self(handle) else "friend"

                    if handle in happened:
                        if sub["verdict"] == "OK":
                            ICON = ICONS[icon_group]["OK"]
                            ntf.Notification("%s got accepted on %s!" % (tsubject, testset), "%s submission on problem %s got %s.%s" % (subject, letter, verdict, pos), ICON).show()
                        elif sub["verdict"] == "CHALLENGED":
                            ICON = ICONS[icon_group]["CHALLENGED"]
                            if is_self(handle) or watch_all:
                                ntf.Notification("%s got hacked!" % (tsubject), "%s submission on problem %s got hacked!" % (subject, letter), ICON).show()
                        elif sub["verdict"] in FAIL:
                            ICON = ICONS[icon_group].get(sub["verdict"], ICONS[icon_group]["FAIL"])
                            if is_self(handle) or (watch_all and sub["verdict"] != "COMPILATION_ERROR"):
                                ntf.Notification("%s failed on %s!" % (tsubject, testset), "%s submission on problem %s got %s%s.%s"  % (subject, letter, verdict, pc, pos), ICON).show()

            happened[handle] = True

        time.sleep(3)

def process(contest):
    handles = []
    if cfg.get("handle", "") != "":
        handles.append(cfg["handle"])

    if cfg.get("watchFriends", True) and cfg.get("friends", "") != "":
        handles += cfg["friends"].split()

    watch(cfg.get("handle", ""), handles, contest["id"], cfg.get("showFriendsFails", True), cfg.get("showRank", False))