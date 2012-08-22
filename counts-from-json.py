#!/usr/bin/python

import json
import sys
import operator
import webkit

if len(sys.argv) != 2:
    print "Usage: " + sys.argv[0] + " <json-data-file>"
    exit(0)

data = []
with open(sys.argv[1], 'r') as f:
     data = json.load(f)

nbcommits = 0
counts = {}
for date, count, records in data:
    nbcommits += count
    for keyword in records:
        counts[keyword] = counts.get(keyword, 0) + records[keyword][0] 

print "Total number of commits:"

print nbcommits
        
print "Commit counts by keywords:"

for keyword, count in sorted(counts.iteritems(), key=operator.itemgetter(1),
                             reverse=True):
    print '%s: %d' % (keyword, count)
