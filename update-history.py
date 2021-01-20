import requests
import json
import os
from datetime import datetime, timedelta
import csv
import numpy as np
import importlib

scraper = importlib.import_module("data-scraper")

def round_perc(p):
    acc = 1e5
    return round(acc * p) / acc

def subst_last_row(loaded, vacc_count, d1, d2, perc_of_doses, inhabitants, today):
    loaded["sum_doses"][-1] = vacc_count
    loaded["sum_1d"][-1] = d1
    loaded["sum_2d"][-1] = d2
    loaded["perc_doses"][-1] = round_perc(perc_of_doses)
    loaded["date"][-1] = today
    calc(loaded, inhabitants)

def add_row(loaded, *args, **kvargs):
    for v in loaded.values():
        v.append('')
    subst_last_row(loaded, *args, **kvargs)

def calc(data, inhabitants):
    intervall=21
    tday = len(data["sum_doses"]) - 1
    if tday == 0:
        return
    if tday < intervall + 1:
        data["delta_1d"][tday] = data["sum_doses"][tday]-data["sum_doses"][tday-1]
    else:
        data["delta_1d"][tday] = data["sum_doses"][tday]-data["sum_doses"][tday-1]-data["delta_1d"][tday-intervall]
    data["sum_1d_pred"][tday] = data["delta_1d"][tday] + data["sum_1d_pred"][tday-1]
    data["sum_2d_pred"][tday] = data["sum_2d_pred"][tday-1]+data["sum_doses"][tday]-data["sum_doses"][tday-1]-data["delta_1d"][tday]

    if inhabitants > 0:
        data["perc_inh_1d"][tday] = round_perc(100 * data["sum_1d"][tday] / inhabitants)
        data["perc_inh_2d"][tday] = round_perc(100 * data["sum_2d"][tday] / inhabitants)

    data["sum_monotone_1d"][tday] = data["sum_1d"][tday]
    data["sum_monotone_2d"][tday] = data["sum_2d"][tday]
    data["perc_inh_monotone_1d"][tday] = data["perc_inh_1d"][tday]
    data["perc_inh_monotone_2d"][tday] = data["perc_inh_2d"][tday]

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
regions_to_consider = ["all"] # or, e.g., ["PAB", "TOS"]
savefiles_calc_base = "vacc-history"
inhabitants_file = "popolazione.json"

date_vaccination_start = "2020-12-27"

oldheader = ["delta_1d","sum_doses","sum_1d","sum_monotone_1d","sum_2d","sum_monotone_2d","perc_doses",
    "perc_inh_1d", "perc_inh_monotone_1d", "perc_inh_2d", "perc_inh_monotone_2d", "date"]
header = ["delta_1d","sum_doses","sum_1d","sum_2d","sum_1d_pred","sum_2d_pred","perc_doses",
    "perc_inh_1d", "perc_inh_2d","sum_monotone_1d","sum_monotone_2d",
    "perc_inh_monotone_1d", "perc_inh_monotone_2d", "date"]

# -- get new data --
timestamp = datetime.today()
today = timestamp.strftime('%Y-%m-%d')
print("Loading new data ({})".format(timestamp.strftime("%Y-%m-%d %H:%M")))
print("Regions: " + ", ".join(regions_to_consider))
print()
regjs = scraper.get_region_json()
if "all" in regions_to_consider:
    regions_to_consider = list(regjs.keys())
regnames = scraper.get_region_names()
dose_numbers = scraper.get_by_doses()

# -- load population numbers --
try:
    with open(inhabitants_file) as f:
        inhabitants=json.load(f)
except:
    print("No population data file found ({})".format(inhabitants_file))
    inhabitants = {k : -1 for k in regjs.keys()}

# -- check specific region --
regions_changed = False
for reg_short in regions_to_consider:
    reg_long = regnames[reg_short]
    changed = False
    savefile_calc = os.path.join(savefiles_calc_base, reg_long + ".csv")
    if not os.path.exists(savefile_calc):
        print("Creating new table for " + reg_long + "...")
        with open(savefile_calc,"w") as f:
            f.write(",".join(header) + "\n")
            day_before_start = (datetime.fromisoformat(date_vaccination_start) -
                                        timedelta(days=1)).strftime('%Y-%m-%d')
            f.write(",".join(["0"]*(len(header)-1)) + "," + day_before_start + "\n")
        changed = True
    loaded = load_csv(savefile_calc)

    # loaded["sum_1d_pred"] = loaded["sum_1d"].copy()
    # loaded["sum_2d_pred"] = loaded["sum_2d"].copy()
    # for i in range(1,len(loaded["sum_1d"])):
    #     if not loaded["date"][i] in dose_numbers:
    #         dose_numbers[loaded["date"][i]] = scraper.get_by_doses(loaded["date"][i])
    #     ds = dose_numbers[loaded["date"][i]][reg_short]
    #     loaded["sum_1d"][i] = ds[0]
    #     loaded["sum_2d"][i] = ds[1]
    #     loaded["perc_inh_1d"][i] = round_perc(100 * loaded["sum_1d"][i] / inhabitants[reg_short])
    #     loaded["perc_inh_2d"][i] = round_perc(100 * loaded["sum_2d"][i] / inhabitants[reg_short])
    # loaded["sum_monotone_1d"] = loaded["sum_1d"].copy()
    # loaded["sum_monotone_2d"] = loaded["sum_2d"].copy()
    # loaded["perc_inh_monotone_1d"] = loaded["perc_inh_1d"].copy()
    # loaded["perc_inh_monotone_2d"] = loaded["perc_inh_2d"].copy()
    # changed = True


    today_count = regjs[reg_short][0]
    d1_count = dose_numbers[reg_short][0]
    d2_count = dose_numbers[reg_short][1]
    perc_of_doses = 100 * regjs[reg_short][1]
    # print("Today counter {}: {}".format(reg_short,today_count))

    # -- update calculations for specific region --
    # if not enough rows, fill with interpolation from the last inserted day up to today
    # (1 entry per day since vaccination start)
    diff = (datetime.fromisoformat(today)-datetime.fromisoformat(date_vaccination_start)).days
    days_of_vacc = diff + 1
    missing_days = days_of_vacc - (len(loaded["sum_doses"]) - 1)
    if missing_days > 0:
        print("{}: add values for {} day(s)".format(reg_short, missing_days))
        interpolation_count = map(int,
                         np.linspace(loaded["sum_doses"][-1], today_count, missing_days+1)[1:])
        interpolation_1d = map(int,
                      np.linspace(loaded["sum_1d"][-1], d1_count, missing_days+1)[1:])
        interpolation_2d = map(int,
                      np.linspace(loaded["sum_2d"][-1], d2_count, missing_days+1)[1:])
        interpolation_perc = [perc_of_doses] * missing_days
        interpolation_date = map(lambda ds: ds.strftime('%Y-%m-%d'),
                    [datetime.fromisoformat(loaded["date"][-1]) + timedelta(days=delta)
                          for delta in range(0, missing_days+1)][1:])
        for count, d1, d2, perc, date in zip(interpolation_count,interpolation_1d,interpolation_2d,
                                     interpolation_perc,
                                     interpolation_date):
            # add row to csv data
            add_row(loaded, count, d1, d2, perc, inhabitants[reg_short], date)
        changed = True
    elif loaded["sum_doses"][-1] != today_count or loaded["perc_doses"][-1] != round_perc(perc_of_doses):
        # if we started the script for a second time this day, substitute last line with new data
        print("{}: subsitute today with updated calculations".format(reg_long))
        subst_last_row(loaded, today_count, d1_count, d2_count, perc_of_doses, inhabitants[reg_short], today)
        changed = True
    if changed:
        regions_changed = True
        with open(savefile_calc, "w") as f:
            cwr = csv.writer(f, lineterminator="\n")
            cwr.writerow(header)
            for row in zip(*[loaded[k] for k in header]):
                cwr.writerow(row)

if not regions_changed:
    print("None of the considered regions was updated.")
print()

# -- update all-regions-stats file --
latest_date = None
try:
    with open(savefile_all, "r") as f:
        cont=json.load(f)
        latest_date = cont[-1]["date"]
except:
    print("Creating new region-history json list")
    cont = []

# only if something changed
regjs = {k : list(v) if isinstance(v, tuple) else v for k, v in regjs.items()}
# get only the first 3 values (the fourth is calculated locally)
if len(cont) > 0:
    tempcont = {k : v[0:3] for k,v in cont[-1]["regions"].items()}
if len(cont) == 0 or tempcont != regjs: # compare dicts in keys and vals
    if today == latest_date:
        print("Substitute last day in regions-history")
        del cont[-1]
    else:
        print("New day in regions-history")
    # append value somministrazioni / abitanti
    for rn, rv in regjs.items():
        if inhabitants[rn] == -1:
            rv.append(-1)
        else:
            rv.append(rv[0] / inhabitants[rn])
    newday = {"date" : today,
             "regions" : regjs}
    cont.append(newday)
    with open(savefile_all, "w") as f:
        json.dump(cont, f, indent=4)
else:
    print("regions-history was already up-to-date.")

print("-")
