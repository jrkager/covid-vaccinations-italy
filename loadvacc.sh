#!/bin/bash

# make sure you cd to the repo first
git pull > /dev/null

pip install --user "pandas>=1.0.0"

python update-history.py

if ! git diff --quiet vacc-history/
then
        today=$(date +"%Y-%m-%d")
	git add vacc-history/
        git commit -m "update ${today}"
        git push
fi
