#!/bin/bash
BASEDIR=$(dirname $0)
current=$(date "+%Y")
$BASEDIR/git-log-to-json.py -s "${current}-01-01" -u "${current}-12-31" -p $current

