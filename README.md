Tracks vaccinations data region by region for Italy and calculates approximate numbers of total of first doses and total of second doses given (assuming a 21 days intervall between two doses). The data is taken from https://app.powerbi.com/view?r=eyJrIjoiMzg4YmI5NDQtZDM5ZC00ZTIyLTgxN2MtOTBkMWM4MTUyYTg0IiwidCI6ImFmZDBhNzVjLTg2NzEtNGNjZS05MDYxLTJjYTBkOTJlNDIyZiIsImMiOjh9, which only supplies the latest number of vaccinations given in total and vaccines shipped to region in total.

## {regionname}.csv
A `{regionname}.csv` lists data day-by-day. If the script is started multiple times a day, the last line is always subsituted by the newest data. That is, each line shows the data for that day at the time of the last run of the script on that day. (started logging on 2021-01-10. Data before that day was linearly interpolated)
The columns are:

- **d**: vaccinations given on a specific day (difference sum until today - sum until yesterday)
- **vcc**: total vaccinations given until now
- **sum_1d**: total first dose vaccinations until now (could sink temporarily since we just approximate by subsituting the number of first doses 21 days ago)
- **sum_monotone_1d**: like sum_1d but never dropping (i.e. the maximum of all past sum_1d values)
- **sum_2d**: total people with first and second dose vaccinations until now (i.e. vaccinated as prescribed)
- **sum_monotone_2d**: like sum_2d but never dropping
- **perc_doses**: percentage of supplied doses that were used (as reported by the government website)
- **perc_inh_1d**: percentage of inhabitants of region that fot the first dose
- **perc_inh_monotone_1d**: like perc_inh_1d but never dropping
- **perc_inh_2d**: percentage of inhabitants of region that fot the first and second dose
- **perc_inh_monotone_2d**: like perc_inh_2d but never dropping
- **date**: date of this row's data

## region-history.json
A JSON file including all server data day -by-day since 2021-01-10. The format is:
```
List(Dict("date":date as string "%y-%m-%d", 
          "regions": Dict("regionname":
                     [doses used, ratio of doses used / doses supplied (both accumulated), doses supplied, ratio doses used / inhabitants of that region]
                           , ...
                         )
          )
    )
```

## Installation
Run `sh install-updater.sh`. It pulls from remote and then installs a cronjob to run `sh loadvacc.sh` every 30 minutes.

`loadvacc.sh` itself runs `python update-history.py` and adds, commits and pushes the modifications to remote if any file was changed.
