Tracks vaccinations data region by region for Italy and calculates approximate numbers of total of first doses and total of second doses given (assuming a 21 days intervall between two doses). The data is taken from https://github.com/italia/covid19-opendata-vaccini. In the meanwhile the fields prima_dose, seconda_dose were added to the source repo, so the approximation algorithm is still here just for fun.

## {regionname}.csv
A `vacc-history/{regionname}.csv` lists data day-by-day. If the script is started multiple times a day, the last line is always subsituted by the newest data. That is, each line shows the data for that day at the time of the last run of the script on that day. (started logging on 2021-01-10. Data before that day was linearly interpolated)
The columns are:

- **delta_1d**: number of first-doses given on a specific day
- **delta_2d**: number of first-doses given on a specific day
- **delta_all**: new vaccinations given on a specific day
- **sum_doses**: total vaccinations given until now (counted in doses)
- **sum_1d**: total first dose vaccinations until now
- **sum_2d**: total people with first and second dose vaccinations until now
- **delta_1d_pred**: number of first-doses given on a specific day -- estimated (difference sum until today - sum until yesterday - first doses given 21 days ago)
- **sum_1d_pred**: total first dose vaccinations until now with original estimating algorithm (could sink temporarily since we just approximate by substituting the number of first doses 21 days ago)
- **sum_2d_pred**: total people with first and second dose vaccinations until now with original estimating algorithm
- **perc_doses**: percentage of supplied doses that were used (as reported by the government website)
- **perc_inh_1d**: percentage of inhabitants of region that got the first dose
- **perc_inh_2d**: percentage of inhabitants of region that got the first and second dose
- **sum_monotone_1d**: here for legacy, equals sum_1d
- **sum_monotone_2d**: here for legacy, equals sum_2d
- **perc_inh_monotone_1d**: here for legacy, equals perc_inh_1d
- **perc_inh_monotone_2d**: here for legacy, equals perc_inh_2d
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
