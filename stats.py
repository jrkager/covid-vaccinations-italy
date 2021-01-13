import json
from operator import itemgetter
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('actions', metavar='action', type=str, nargs='*',
                    help='choose which statistics you want to have (in order list gets ordered): \n\
					vacc, suppl, used')

args = parser.parse_args()

actions = {	"vacc" : # percentage of population got a vaccine
				lambda vals: vals[3],
			"suppl" : # this ratio of population could get vaccined (2 doses) with current supply
				lambda vals: vals[2] * vals[3] / vals[0] / 2,
			"used" : # doses used out of supplied ones
				lambda vals: vals[1]
		}

order = {	"vacc" : -1,
			"suppl" : -1,
			"used" : -1
		}

name = {	"vacc" : "of pop.",
			"suppl" : "supply",
			"used" : "of doses"
		}

if "all" in args.actions:
	args.actions.extend(k for k in ["vacc", "used", "suppl"] if k not in args.actions)
args.actions = [k for k in args.actions if k in actions]
if not args.actions:
	args.actions = ["vacc", "used"]

savefile_all = "vacc-history/regioni-history.json"
with open(savefile_all, "r") as f:
	cont=json.load(f)

data = cont[-1]["regions"].items()

sortdata = sorted(data, key = lambda s: [order[act] * actions[act](s[1]) for act in args.actions])

sortdata = [(s[0], *[actions[act](s[1]) for act in args.actions]) for s in sortdata]

print()
space=11
print(f" {'':2}  {'reg':>21} " + "".join([f"{name[r]:>{space+1}}" for r in args.actions]))
for i, (reg, *rates) in enumerate(sortdata):
	l = [f"{r*100: {space}.2f}%" for r in rates]
	print(f" {i+1:2}) {reg:>21}:" + "".join(l))
print()
