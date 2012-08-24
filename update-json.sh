#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path-to-webkit-git-repo> [year]"
    exit
fi
if [ $# -eq 2 ]; then
year=$2
else
year=$(date "+%Y")
fi
Since="${year}-01-01"
if [ $year == $(date "+%Y") ]; then
Until="HEAD"
else
Until="${year}-12-31"
fi
BASEDIR=$(dirname $0)
GIT_DIR=$1/.git GIT_WORK_TREE=$1 $BASEDIR/git-log-to-json.py -s $Since -u $Until -p $year

