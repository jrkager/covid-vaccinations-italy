import requests
import json

def get_region_json():
    url = 'https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/vaccini-summary-latest.json'

    r = requests.get(url)
    if r.status_code != 200:
        print(r.status_code, r.reason)
        return dict()
    cont=json.loads(r.content)

    regions = cont["data"]

    # shortname-region : (doses used, ratio of available doses that were used, available doses)
    d = {e["area"] :
         (e["dosi_somministrate"], e["percentuale_somministrazione"] / 100, e["dosi_consegnate"])
         for e in regions}

    return d

def get_region_names():
    with open("region-names.json") as f:
        return json.load(f)
