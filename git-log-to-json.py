#!/usr/bin/python

import json
import getopt, sys
import operator
import webkit
import datetime

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:u:p:", ["since=", "until=", "prefix="])
except getopt.GetoptError, err:
    print str(err)
since = "1 year ago"
until = "today"
prefix = None
for opt, arg in opts:
    if opt in ("-s","--since="):
        since = arg
    elif opt in ("-u","--until="):
        until = arg
    elif opt in ("-p","--prefix="):
        prefix = arg
        
start = None
end = None
companies = {}
keywords = {}
data_aggregated_by_company = []
data_aggregated_by_keyword = []
current_date = None
count = 0
for date, author, topics in webkit.parse_log(since,until):
    if date != current_date:
        if start == None:
            start = date
        if current_date:
            # Done with aggregation for this date
            data_aggregated_by_company.append([current_date,count,companies])
            companies = {}
            data_aggregated_by_keyword.append([current_date,count,keywords])
            keywords = {}
            count = 0
        current_date = date
    count = count+1
    author = webkit.canonicalize_email(author)
    company = webkit.classify_email(author)
    if company in companies:
        companies[company][0] += 1
    else:
        companies[company] = [1,{}]
    canon_topics = []
    if topics:
        for topic in topics:
            # TODO: filter out tags based on their type (canon_tag[1])
            canon_topic = webkit.canonicalize_tag(topic.lower())
            if canon_topic[0] not in canon_topics:
                canon_topics.append(canon_topic)
    else:
        if 'unknown' not in canon_topics:
            canon_topics.append(['none','unknown',1])
    # Sort canon topics by priority
    canon_topics.sort(key=operator.itemgetter(2))
    for canon_topic in canon_topics:
        tag_name = canon_topic[0]        
        tag_type = canon_topic[1]
        if tag_type in keywords:
            keywords[tag_type][0] +=1
        else:
            keywords[tag_type] = [1,{}]
        if tag_name in keywords[tag_type][1]:
            keywords[tag_type][1][tag_name][0] +=1
        else:
            keywords[tag_type][1][tag_name] = [1,{}]
        keywords[tag_type][1][tag_name][1][company] = keywords[tag_type][1][tag_name][1].get(company,0) +1
        if tag_type in companies[company][1]:
            companies[company][1][tag_type][0] +=1
        else:
            companies[company][1][tag_type] = [1,{}]
        companies[company][1][tag_type][1][tag_name] = companies[company][1][tag_type][1].get(tag_name,0) +1

end = current_date
# Don't miss the last date
data_aggregated_by_company.append([current_date,count,companies])
data_aggregated_by_keyword.append([current_date,count,keywords])

data_aggregated_by_company.reverse()
data_aggregated_by_keyword.reverse()

if prefix == None:
    prefix = start + '-' + end

with open(prefix + '-by-company.json', 'w') as f:                                   
    json.dump(data_aggregated_by_company,f,separators=(',',':'))
with open(prefix + '-by-keyword.json', 'w') as f:                                   
    json.dump(data_aggregated_by_keyword,f,separators=(',',':'))
