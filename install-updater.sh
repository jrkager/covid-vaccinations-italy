#!/bin/bash

echo "Pulling..."
git pull

crontab -l > mycron
echo "*/30 * * * * cd $(pwd) && sh $(pwd)/loadvacc.sh >> hist.log" >> mycron
crontab mycron
rm mycron
echo "crontab installed to run every 30 minutes"
