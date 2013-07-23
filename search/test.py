#!/usr/bin/python
#
# This program does a Google search for "quick and dirty" and returns
# 50 results.
#

from parser.google import GoogleSearch, SearchError
try:
  gs = GoogleSearch("materialized view",random_agent=True, debug=True, lang="ru", tld="ru", re_search_strings=None)
  gs.results_per_page = 10
  results = gs.get_results()
  for res in results:
    print res.title.encode('utf8')
    print res.desc.encode('utf8')
    print res.url.encode('utf8')
    print
except SearchError, e:
  print "Search failed: %s" % e

