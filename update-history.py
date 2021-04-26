import requests
import json
import os, sys
import argparse
from datetime import datetime, timedelta
import csv
import numpy as np
import pandas as pd
import importlib

scraper = importlib.import_module("data-scraper")

def round_perc(p):
    acc = 1e5
    return round(acc * p) / acc

def subst_last_row(loaded, vacc_count, d1, d2, mono, perc_of_doses, inhabitants, today):
    loaded["sum_doses"][-1] = vacc_count
    loaded["sum_1d"][-1] = d1
    loaded["sum_2d"][-1] = d2 + mono
    loaded["delta_1d"][-1] = loaded["sum_1d"][-1]-loaded["sum_1d"][-2]
    loaded["delta_2d"][-1] = loaded["sum_2d"][-1]-loaded["sum_2d"][-2]
    loaded["delta_all"][-1] = loaded["sum_doses"][-1]-loaded["sum_doses"][-2]
    loaded["perc_doses"][-1] = round_perc(perc_of_doses)
    loaded["date"][-1] = today
    calc(loaded, inhabitants)

def add_row(loaded, *args, **kvargs):
    for v in loaded.values():
        v.append('')
    subst_last_row(loaded, *args, **kvargs)

def calc(data, inhabitants):
    tday = len(data["sum_doses"]) - 1
    if tday == 0:
        return

    if inhabitants > 0:
        data["perc_inh_1d"][tday] = round_perc(100 * data["sum_1d"][tday] / inhabitants)
        data["perc_inh_2d"][tday] = round_perc(100 * data["sum_2d"][tday] / inhabitants)
        data["perc_inh_tot"][tday] = round_perc(100 * data["sum_doses"][tday] / inhabitants)

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


parser = argparse.ArgumentParser()
parser.add_argument("-f", help="Force update", action='store_true')
parser.add_argument("--reset", "-r", help="Reset total history of csv \
                            files to data in repo. (useful when data wasn't \
                            updated for some days)", action='store_true')
args = parser.parse_args()

savefile_all = "vacc-history/regioni-history.json"
savefile_csvall = "vacc-history/all-regions.json"
regions_to_consider = ["all"] # or, e.g., ["PAB", "TOS"]
savefiles_calc_base = "vacc-history"
inhabitants_file = "popolazione.json"

date_vaccination_start = "2020-12-27"

header = ["delta_1d","delta_2d","delta_all","sum_doses","sum_1d","sum_2d","perc_doses",
    "perc_inh_tot","perc_inh_1d", "perc_inh_2d","sum_monotone_1d","sum_monotone_2d",
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
dose_numbers = scraper.get_by_doses(cache=True)

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
    if args.reset or not os.path.exists(savefile_calc):
        print("Creating new table for " + reg_long + "...")
        with open(savefile_calc,"w") as f:
            f.write(",".join(header) + "\n")
            day_before_start = (datetime.fromisoformat(date_vaccination_start) -
                                        timedelta(days=1)).strftime('%Y-%m-%d')
            f.write(",".join(["0"]*(len(header)-1)) + "," + day_before_start + "\n")
        changed = True
    loaded = load_csv(savefile_calc)

    missing_days = (datetime.fromisoformat(today)-datetime.fromisoformat(loaded["date"][-1])).days
#     print("Missing days:", missing_days)

    if args.reset:
        interpolation_dates = map(lambda ds: ds.strftime('%Y-%m-%d'),
                    [datetime.fromisoformat(loaded["date"][-1]) + timedelta(days=delta)
                          for delta in range(1, missing_days+1)])
        for date in interpolation_dates:
            d = scraper.get_by_doses(untildate=date, cache=True)
            if reg_short not in d:
                d = {'prima_dose': 0, 'seconda_dose': 0, 'totale': 0, 'numero_dosi': 0}
            else:
                d = d[reg_short]
            add_row(loaded, d["totale"], d["prima_dose"], d["seconda_dose"], d["mono"],
                    round(1000*d["totale"]/d["numero_dosi"])/10, inhabitants[reg_short], date)
        changed = True
    else:
        today_count = regjs[reg_short][0]
        d1_count = dose_numbers[reg_short]["prima_dose"]
        d2_count = dose_numbers[reg_short]["seconda_dose"] + dose_numbers[reg_short]["mono"]
        perc_of_doses = 100 * regjs[reg_short][1]
        # print("Today counter {}: {}".format(reg_short,today_count))

        # -- update calculations for specific region --
        # if not enough rows, fill with interpolation from the last inserted day up to today
        # (1 entry per day since vaccination start)
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
                add_row(loaded, count, d1, d2, 0, perc, inhabitants[reg_short], date)
            changed = True
        elif loaded["sum_doses"][-1] != today_count or loaded["perc_doses"][-1] != round_perc(perc_of_doses):
            # if we started the script for a second time this day, substitute last line with new data
            print("{}: subsitute today with updated calculations".format(reg_long))
            subst_last_row(loaded, today_count, d1_count, d2_count, 0, perc_of_doses, inhabitants[reg_short], today)
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

# -- update all-region json file (unition of all csv files) --
if regions_changed or args.f or args.reset:
    fcs = []
    for f in os.listdir(savefiles_calc_base):
        if f.endswith(".csv"):
            reg_long = os.path.splitext(os.path.basename(f))[0]
            reg_short = [k for k,v in regnames.items() if v == reg_long][0]
            fc = pd.read_csv(os.path.join(savefiles_calc_base, f))
            fc.insert(0, "area", reg_short)
            fcs.append(fc)
    df = pd.concat(fcs)[1:]
    df["date"] = pd.to_datetime(df["date"], format='%Y-%m-%d')
    df["perc_inh"]=df["perc_inh_tot"]/2
    df["perc_supply"]=100*df.perc_inh_tot/df.perc_doses/2
    df["tot_supply"]=df.sum_doses/df.perc_doses*100
    df.reset_index(drop=True, inplace=True)
    df.to_json(savefile_csvall, orient="table", indent=2)
    print("Collected all csv files into json.")

print("-")
