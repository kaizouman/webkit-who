#!/usr/bin/python

import getopt, sys
import operator
import webkit

try:
	opts, args = getopt.getopt(sys.argv[1:], "s:u:", ["since=", "until="])
except getopt.GetoptError, err:
	print str(err)
since = "1 year ago"
until = "today"
for opt, arg in opts:
	if opt in ("-s","--since="):
		since = arg
	elif opt in ("-u","--until="):
		until = arg
print "Commit counts by company between " + since + " and " + until

counts = {}
for date, author, topics in webkit.parse_log(since,until):
    author = webkit.canonicalize_email(author)
    counts[author] = counts.get(author, 0) + 1

companies = {}
unknown = {}
for email, count in counts.iteritems():
    company = webkit.classify_email(email)
    companies[company] = companies.get(company, 0) + count
    if company == 'unknown':
        unknown[email] = count
    elif company == 'misc':
        unknown['*' + email] = count


if unknown:
    print ("unclassified (star denotes \"commits examined, and their "
           "backer is a minor contributor\"):")
    for email, count in sorted(unknown.iteritems(), key=operator.itemgetter(1),
                               reverse=True):
        print '  %s (%d)' % (email, count)


for company, count in sorted(companies.iteritems(), key=operator.itemgetter(1),
                             reverse=True):
    print '%s: %d' % (company, count)

