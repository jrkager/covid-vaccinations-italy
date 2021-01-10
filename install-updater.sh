#!/bin/bash

echo "Pulling..."
git pull

crontab -l > mycron
echo "*/30 * * * * sh $(pwd)/loadvacc.sh" >> mycron
crontab mycron
rm mycron
echo "crontab installed to run every 30 minutes"
