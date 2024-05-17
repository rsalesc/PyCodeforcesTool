def get_contest_url(contest_id):
  if int(contest_id) < 10000:
    return "http://codeforces.com/contest/%s" % str(contest_id)
  return "http://codeforces.com/gym/%s" % str(contest_id)