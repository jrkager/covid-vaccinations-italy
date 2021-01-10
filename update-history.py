import requests
import json
import os
from datetime import datetime, timedelta
import csv
import numpy as np
import importlib

scraper = importlib.import_module("data-scraper")

def subst_last_row(loaded, vacc_count, perc_of_doses, inhabitants, today):
    loaded["vcc"][-1] = vacc_count
    loaded["perc_doses"][-1] = perc_of_doses
    loaded["date"][-1] = today
    calc(loaded, inhabitants)

def add_row(loaded, *args, **kvargs):
    for v in loaded.values():
        v.append('')
    subst_last_row(loaded, *args, **kvargs)

def calc(data, inhabitants):
    intervall=21
    heute = len(data["vcc"]) - 1
    if heute == 0:
        return
    if heute < intervall + 1:
        data["d"][heute] = data["vcc"][heute]-data["vcc"][heute-1]
    else:
        data["d"][heute] = data["vcc"][heute]-data["vcc"][heute-1]-data["d"][heute-intervall]
    data["sum_1d"][heute] = data["d"][heute] + data["sum_1d"][heute-1]
    data["sum_monotone_1d"][heute] = max([data["sum_1d"][heute],
                                        data["sum_monotone_1d"][heute - 1]])
    data["sum_2d"][heute] = data["vcc"][heute]-data["vcc"][heute-1]-data["d"][heute]
    data["sum_monotone_2d"][heute] = max([data["sum_2d"][heute],
                                        data["sum_monotone_2d"][heute - 1]])
    if inhabitants > 0:
        data["perc_inh_1d"][heute] = data["sum_1d"][heute] / inhabitants
        data["perc_inh_monotone_1d"][heute] = data["sum_monotone_1d"][heute] / inhabitants
        data["perc_inh_2d"][heute] = data["sum_2d"][heute] / inhabitants
        data["perc_inh_monotone_2d"][heute] = data["sum_monotone_2d"][heute] / inhabitants

def load_csv(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        columns = {}
        for h in headers:
            columns[h] = []
        for row in reader:
            if len(row) == 0 or all(s == '' for s in row):
                continue
            for h, v in zip(headers, row):
                try: columns[h].append(int(v))
                except:
                    try: columns[h].append(float(v))
                    except:
                        columns[h].append(v)
        return columns

savefile_all = "vacc-history/regioni-history.json"
regions_to_consider = ["all"]
savefiles_calc_base = "vacc-history"
inhabitants_file = "popolazione.json"

date_vaccination_start = "2020-12-27"

header = ["d","vcc","sum_1d","sum_monotone_1d","sum_2d","sum_monotone_2d","perc_doses",
    "perc_inh_1d", "perc_inh_monotone_1d", "perc_inh_2d", "perc_inh_monotone_2d", "date"]

# -- get new data --
regjs = scraper.get_region_json()
if "all" in regions_to_consider:
    regions_to_consider = list(regjs.keys())
today = datetime.today().strftime('%Y-%m-%d')
regjs["date"] = today

# -- load population numbers --
try:
    with open(inhabitants_file) as f:
        inhabitants=json.load(f)
except:
    print("No population data file found ({})".format(inhabitants_file))
    inhabitants = {k : -1 for k in regions_to_consider}

# -- check specific region --
for region_name in regions_to_consider:
    savefile_calc = os.path.join(savefiles_calc_base, region_name + ".csv")
    if not os.path.exists(savefile_calc):
        with open(savefile_calc,"w") as f:
            f.write(",".join(header) + "\n")
            day_before_start = (datetime.fromisoformat(date_vaccination_start) -
                                        timedelta(days=1)).strftime('%Y-%m-%d')
            f.write(",".join(["0"]*(len(header)-1)) + "," + day_before_start + "\n")
    loaded = load_csv(savefile_calc)

    today_count = regjs[region_name][0]
    perc_of_doses = regjs[region_name][1]
    # print("Today counter {}: {}".format(region_name,today_count))

    # -- update calculations for specific region --
    # if not enough rows, fill with interpolation from the last inserted day up to today
    # (1 entry per day since vaccination start)
    diff = (datetime.fromisoformat(today)-datetime.fromisoformat(date_vaccination_start)).days
    days_of_vacc = diff + 1
    missing_days = days_of_vacc - (len(loaded["vcc"]) - 1)
    if missing_days > 0:
        print("{}: add values for {} day(s)".format(region_name, missing_days))
        interpolation_count = map(int,
                         np.linspace(loaded["vcc"][-1], today_count, missing_days+1)[1:])
        interpolation_perc = [perc_of_doses] * missing_days
        interpolation_date = map(lambda ds: ds.strftime('%Y-%m-%d'),
                    [datetime.fromisoformat(loaded["date"][-1]) + timedelta(days=delta)
                          for delta in range(0, missing_days+1)][1:])
        for count, perc, date in zip(interpolation_count,
                                     interpolation_perc,
                                     interpolation_date):
            # add row to csv data
            add_row(loaded, count, perc, inhabitants[region_name], date)
    elif loaded["vcc"][-1] != today_count or loaded["perc_doses"][-1] != perc_of_doses:
        # if we started the script for a second time this day, substitute last line with new data
        print("{}: subsitute today with updated calculations".format(region_name))
        subst_last_row(loaded, today_count, perc_of_doses, inhabitants[region_name], today)
    with open(savefile_calc, "w") as f:
        cwr = csv.writer(f, lineterminator="\n")
        cwr.writerow(header)
        for row in zip(*[loaded[k] for k in header]):
            cwr.writerow(row)


# -- update all-regions-stats file --
latest_date = None
try:
    with open(savefile_all, "r") as f:
        cont=json.loads(f.read())
        latest_date = cont[-1]["date"]
except:
    cont = []

# only if something changed
regjs = {k : list(v) if isinstance(v, tuple) else v for k, v in regjs.items()}

if cont[-1] != regjs: # compare dicts in keys and vals
    if today == latest_date:
        print("subst last day in regions")
        del cont[-1]
    cont.append(regjs)
    with open(savefile_all, "w") as f:
        json.dump(cont, f)
