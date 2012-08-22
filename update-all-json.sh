#!/bin/bash
BASEDIR=$(dirname $0)
for ((i=2001; i<=$(date "+%Y");i++))
do
$BASEDIR/git-log-to-json.py -s "${i}-01-01" -u "${i}-12-31" -p $i
done

