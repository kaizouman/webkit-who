#!/bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: $0 <path-to-webkit-git-repo>"
    exit
fi
BASEDIR=$(dirname $0)
for ((i=2001; i<=$(date "+%Y");i++))
do
$BASEDIR/update-json.sh $1 $i
done

