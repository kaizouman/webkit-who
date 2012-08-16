#!/usr/bin/python

import getopt, sys
import webkit
import pylab
import matplotlib.pyplot as plot
import matplotlib.dates as dates
import datetime
import numpy
import sys

def load_from_git(since,until,company=None):
    data = []
    for date, author, topics in webkit.parse_log(since,until):
		filtered_out = False
		if company:
			author = webkit.canonicalize_email(author)
			author_company = webkit.classify_email(author)
			filtered_out = (author_company != company)
		if not filtered_out: 
			date = datetime.date(*map(int, date.split('-')))
			if topics:
				for topic in topics:
					topic_lower = webkit.canonicalize_topic(topic.lower())
					# We only count Test topics if we haven't anything else
					if "test" not in topic.lower() or len(topics) == 1:
						data.append((date, topic))
			else:
				data.append((date, 'other'))
    data.reverse()
    return data

def load_from_file():
    data = []
    for line in open('dates').readlines():
        date, company = line.strip().split(' ', 1)
        date = datetime.date(*map(int, date.split('-')))
        data.append((date, company))
    return data

def lin_smooth(array, window=7):
    out = numpy.zeros(len(array))
    avg = sum(array[0:window])
    for i in range(window, len(array)):
        avg += array[i]
        avg -= array[i - window]
        out[i] = avg / window
    return out

def gauss(window):
    gauss = numpy.exp(-numpy.arange(-window+1, window)**2/(2*float(window)))
    return gauss / gauss.sum()

def gauss_smooth(data, window=14):
    g = gauss(window)
    return numpy.convolve(data, g, mode='same')

def smooth(data):
    #return gauss_smooth(data, window=30)
    return lin_smooth(data, window=30)

try:
	opts, args = getopt.getopt(sys.argv[1:], "s:u:c:", ["since=", "until=", "company="])
except getopt.GetoptError, err:
	print str(err)
since = "2 years ago"
until = "today"
company = None
for opt, arg in opts:
	if opt in ("-s","--since="):
		since = arg
	elif opt in ("-u","--until="):
		until = arg
	elif opt in ("-c","--company="):
		company = arg
print "Generate commit counts graph by ports between " + since + " and " + until
data = load_from_git(since,until,company)

start = pylab.date2num(data[0][0])
end = pylab.date2num(data[-1][0])
time_range = numpy.arange(start, end + 1)

ports = set(['mac', 'chromium', 'qt', 'gtk', 'efl','blackberry', 'other'])
commits = {}
for port in ports:
    commits[port] = numpy.zeros(end - start + 1)

for date, what in data:
    date = pylab.date2num(date)
    if what not in ports:
        what = 'other'
    commits[what][date - start] += 1

fig = plot.figure()
ax = fig.add_subplot(111)
ax.plot_date(time_range, smooth(commits['mac']), '-',label='Mac')
ax.plot_date(time_range, smooth(commits['chromium']), '-',label='Chromium')
ax.plot_date(time_range, smooth(commits['qt']), '-',label='Qt')
ax.plot_date(time_range, smooth(commits['gtk']), '-',label='GTK')
ax.plot_date(time_range, smooth(commits['efl']), '-',label='EFL')
ax.plot_date(time_range, smooth(commits['blackberry']), '-',label='BlackBerry')
ax.plot_date(time_range, smooth(commits['other']), '-',label='Other')
ax.xaxis.set_major_locator(dates.MonthLocator(range(1,13), bymonthday=1, interval=3))
ax.xaxis.set_minor_locator(dates.MonthLocator(range(1,13), bymonthday=1, interval=1))
fig.autofmt_xdate()
ax.legend(loc='upper left')
filename = 'graph-by-ports.png'
if company:
	filename = company + '-' + filename
pylab.savefig(filename)
