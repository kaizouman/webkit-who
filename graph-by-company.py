#!/usr/bin/python

import getopt, sys
import webkit
import pylab
import matplotlib.pyplot as plot
import matplotlib.dates as dates
import datetime
import numpy
import sys

def load_from_git(since,until):
    data = []
    for date, author, topics in webkit.parse_log(since,until):
        author = webkit.canonicalize_email(author)
        company = webkit.classify_email(author)
        date = datetime.date(*map(int, date.split('-')))
        data.append((date, company))
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
	opts, args = getopt.getopt(sys.argv[1:], "s:u:", ["since=", "until="])
except getopt.GetoptError, err:
	print str(err)
since = "2 years ago"
until = "today"
for opt, arg in opts:
	if opt in ("-s","--since="):
		since = arg
	elif opt in ("-u","--until="):
		until = arg
print "Generate commit counts graph by company between " + since + " and " + until    

data = load_from_git(since,until)

start = pylab.date2num(data[0][0])
end = pylab.date2num(data[-1][0])
time_range = numpy.arange(start, end + 1)

companies = set(['google', 'apple', 'nokia', 'intel', 'samsung','igalia', 'other'])
commits = {}
for company in companies:
    commits[company] = numpy.zeros(end - start + 1)

for date, who in data:
    date = pylab.date2num(date)
    if who not in companies:
        who = 'other'
    commits[who][date - start] += 1

fig = plot.figure()
ax = fig.add_subplot(111)
ax.plot_date(time_range, smooth(commits['apple']), '-',label='Apple')
ax.plot_date(time_range, smooth(commits['google']), '-',label='Google')
ax.plot_date(time_range, smooth(commits['nokia']), '-',label='Nokia')
ax.plot_date(time_range, smooth(commits['intel']), '-',label='Intel')
ax.plot_date(time_range, smooth(commits['samsung']), '-',label='Samsung')
ax.plot_date(time_range, smooth(commits['igalia']), '-',label='Igalia')
ax.plot_date(time_range, smooth(commits['other']), '-',label='Other')
ax.xaxis.set_major_locator(dates.MonthLocator(range(1,13), bymonthday=1, interval=3))
ax.xaxis.set_minor_locator(dates.MonthLocator(range(1,13), bymonthday=1, interval=1))
fig.autofmt_xdate()
ax.legend(loc='upper left')
pylab.savefig('graph.png')