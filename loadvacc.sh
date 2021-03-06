#!/bin/bash

# make sure you cd to the repo first
git pull

/usr/bin/python3 update-history.py

if ! git diff --quiet vacc-history/
then
        today=$(date +"%Y-%m-%d")
	git add vacc-history/
        git commit -m "update ${today}"
        git push
fi
