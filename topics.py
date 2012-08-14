#!/usr/bin/python

import getopt, sys
import operator
import webkit

try:
	opts, args = getopt.getopt(sys.argv[1:], "s:u:", ["since=", "until="])
except getopt.GetoptError, err:
	print str(err)
since = "1 week ago"
until = "today"
for opt, arg in opts:
	if opt in ("-s","--since="):
		since = arg
	elif opt in ("-u","--until="):
		until = arg
print "Commit counts by topics between " + since + " and " + until

counts = {}
for date, author, topics in webkit.parse_log(since,until):
	if topics:
		for topic in topics:
			counts[topic] = counts.get(topic, 0) + 1
	else:
		counts['Other'] = counts.get('Other',0) + 1

for topic, count in sorted(counts.iteritems(), key=operator.itemgetter(1),
                             reverse=True):
    print '%s: %d' % (topic, count)

