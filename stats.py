import json
from operator import itemgetter
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from datetime import datetime
import pandas as pd
import re

parser = argparse.ArgumentParser()
parser.add_argument('actions', metavar='action', type=str, nargs='*',
                    help='choose which statistics you want to have (in order list gets ordered): \n\
                    vacc, suppl, used, vacc1, vacc2, period')

args = parser.parse_args()

actions = { "vacc" : # n/2 vaccines in percentage to total population
                lambda vals: vals.perc_inh_tot/2,
            "suppl" : # this ratio of population could get vaccined (2 doses) with current supply
                lambda vals: 100 * vals.perc_inh_tot / vals.perc_doses / 2,
            "used" : # doses used out of supplied ones
                lambda vals: vals.perc_doses,
            "vacc1" :
                lambda vals: vals.perc_inh_1d,
            "vacc2" :
                lambda vals: vals.perc_inh_2d,
            "period" :
                lambda vals: vals.period
        }

order = {    "vacc" : -1,
            "suppl" : -1,
            "used" : -1,
            "vacc1" : -1,
            "vacc2" : -1,
            "period" : -1
        }

name = {    "vacc" : "tot of pop.",
            "suppl" : "supply",
            "used" : "of doses",
            "vacc1" : "1d of pop.",
            "vacc2" : "2d of pop.",
            "period" : "dose dist"
        }

tostring = { "vacc" : # n vaccines in percentage to total population
                lambda v, s: f"{v: {s}.2f}%",
            "suppl" : # this ratio of population could get vaccined (2 doses) with current supply
                lambda v, s: f"{v: {s}.2f}%",
            "used" : # doses used out of supplied ones
                lambda v, s: f"{v: {s}.2f}%",
            "vacc1" :
                lambda v, s: f"{v: {s}.2f}%",
            "vacc2" :
                lambda v, s: f"{v: {s}.2f}%",
            "period" :
                lambda v, s: f" {v: >{s}}",
        }


if "all" in args.actions:
    args.actions.extend(k for k in ["vacc1", "vacc2", "used", "suppl", "period"] if k not in args.actions)
args.actions = [k for k in args.actions if k in actions]
if not args.actions:
    args.actions = ["vacc2", "vacc1", "used", "period"]

cont = {}
savefile_path = "vacc-history/"
for f in os.listdir("vacc-history/"):
    if f.endswith(".csv"):
        reg_long = os.path.splitext(os.path.basename(f))[0]
        fc = pd.read_csv(os.path.join(savefile_path, f))
        c = fc.iloc[-1].copy()
        c["period"] = fc.sum_2d.shape[0] - \
                        fc[fc.sum_1d > fc.sum_2d.iloc[-1]].index[0]
        cont[reg_long] = c


data = cont.items()

sortdata = sorted(data, key = lambda s: [order[act] * actions[act](s[1]) for act in args.actions])

sortdata = [(s[0], *zip(args.actions, [actions[act](s[1]) for act in args.actions])) for s in sortdata]

print()
space=13
print(f" {'':2}  {'reg':>21} " + "".join([f"{name[r]:>{space+1}}" for r in args.actions]))
for i, (reg, *rates) in enumerate(sortdata):
    l = [tostring[r[0]](r[1], space) for r in rates]
    print(f" {i+1:2}) {reg:>21}:" + "".join(l))
print()

if input("Proceed with plot? (y,[n]) ") == "y":
    df = pd.read_json(os.path.join(savefile_path,"all-regions.json"), orient="table")
    regs = input("Choose regions (by area shortname, comma seperated): ")
    regs = re.split(",| ", regs.upper())
    if "ALL" in regs:
        regs = df.area.unique().tolist()
    fields = input("Choose fields: ")
    fields = re.split(",| ", fields.lower())
    if "any" in fields:
        fields = ["perc_inh", "perc_doses"]
    for field in fields:
        if field not in df.columns:
            continue
        fig, ax = plt.subplots(figsize=(10,7))
        areaorder=df.groupby("area") \
                  .apply(lambda x: x.sort_values("date").tail(1)) \
                  .sort_values(field,ascending=False) \
                  .area
        if field == "perc_inh":
            ax.set_ylabel("Impfungen / Bewohner / 2 [%]", fontsize="large")
        elif field == "supply":
            ax.set_ylabel("Verf. Dosen / Bewohner / 2 [%]", fontsize="large")
        else:
            ax.set_ylabel(field)
        ax.set_xlabel("")
        locator=mdates.AutoDateLocator(minticks=4,maxticks=10)
        formatter=mdates.ConciseDateFormatter(locator)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        for a in areaorder:
            if a not in regs:
                continue
            df[df.area == a].plot(x="date", y=field, ax=ax, label=a)
        ax.legend(ncol=2, fontsize="large")
        plt.grid(True)
        plt.show()

    if input("Plot doses and supply for each region? (y,[n]) ") == "y":
        attr=["sum_doses","tot_supply"]
        for reg in regs:
          fig, ax = plt.subplots(figsize=(10,7))
          for a in attr:
            df[df.area == reg].plot(x="date", y=a, ax=ax, label=a)
          ax.set_xlabel("")
          ax.set_title(reg)
          plt.grid(True)
          plt.show()

    if input("Plot first and second doses for each region? (y,[n]) ") == "y":
        attr=["sum_1d","sum_2d"]
        df["1d_shift"] = df.groupby(df.area).sum_1d.shift(21, fill_value = 0)
        for reg in regs:
          fig, ax = plt.subplots(figsize=(10,7))
          for a in attr:
            df[df.area == reg].plot(x="date", y=a, ax=ax, label=a)
          df[df.area == reg].plot(x="date", y="1d_shift",
                        ax=ax, label="sum_1d shift by 21 days",
                        color="gray")
          ax.set_xlabel("")
          ax.set_title(reg)
          plt.grid(True)
          plt.show()
