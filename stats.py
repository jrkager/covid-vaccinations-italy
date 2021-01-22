import json
from operator import itemgetter
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates as mdates
from datetime import datetime
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('actions', metavar='action', type=str, nargs='*',
                    help='choose which statistics you want to have (in order list gets ordered): \n\
                    vacc, suppl, used, vacc1, vacc2, period')

args = parser.parse_args()

actions = { "vacc" : # n vaccines in percentage to total population
                lambda vals: vals.perc_inh_tot,
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
    args.actions = ["vacc2", "vacc", "used", "period"]

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
    regfiles = []
    for f in os.listdir("vacc-history/"):
        if f.endswith(".csv"):
            regfiles.append(f)
    regfiles = sorted(regfiles)
    print("Choose region:")
    for i, f in enumerate(regfiles):
        print(f"{i+1:>2}: {f[:f.find('.csv')]}")
    #try:
    if True:
        ch = int(input("Choice: "))
        if ch < 1 or ch > len(regfiles):
            raise
        data = np.genfromtxt(f"vacc-history/{regfiles[ch-1]}", delimiter=",", usecols=(3,-1), converters={17 : lambda s: datetime.strptime(s.decode("utf-8"), "%Y-%m-%d")})
        sum_doses = [s[0] for s in data[2:]]
        dates = [s[1] for s in data[2:]]
        if sum_doses[-1] == sum_doses[-2]:
            sum_doses = sum_doses[:-1]
            dates = dates[:-1]

        x = dates
        y = sum_doses
        locator=mdates.AutoDateLocator(minticks=1,maxticks=10)
        formatter=mdates.ConciseDateFormatter(locator)
        fig,ax=plt.subplots()
        ax.set_ylim(bottom=0,top=max(y)*1.2)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.plot(x,y,'-o')
        plt.grid(True)
        plt.title("Doses given - " + regfiles[ch-1][:regfiles[ch-1].find('.csv')])
        plt.show()
    # except:
    #     pass
