#!/bin/bash
if [ $# -lt 1 ]; then
    echo "Usage: $0 <path-to-webkit-git-repo> [year]"
    exit
fi
if [ $2 != '' ]; then
year=$2
else
year=$(date "+%Y")
fi
BASEDIR=$(dirname $0)
GIT_DIR=$1/.git GIT_WORK_TREE=$1 $BASEDIR/git-log-to-json.py -s "${year}-01-01" -u "${year}-12-31" -p $year

