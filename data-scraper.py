import requests
import json
import pandas as pd

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

def get_by_doses(untildate=None, cache=False):
    global somm_data_cache
    if "somm_data_cache" in globals():
        c, d = somm_data_cache
    if not cache or not "somm_data_cache" in globals():
        url = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv"
        ch = pd.read_csv(url)
        c = ch.groupby(["data_somministrazione","fornitore","area"]).sum()[["prima_dose","seconda_dose"]]
        c=c.unstack("fornitore",fill_value=0)
        c["mono"]=c.prima_dose.Janssen+c.seconda_dose.Janssen
        c.loc[:,("prima_dose","Janssen")] = 0
        c = c.groupby(level=0, axis=1).sum()
        c["totale"] = c.prima_dose + c.seconda_dose + c.mono
        c.reset_index(inplace=True)
        url = "https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/consegne-vaccini-latest.csv"
        d = pd.read_csv(url)
    if cache:
        somm_data_cache = c, d
    if untildate:
        c = c[c.data_somministrazione <= untildate]
        d = d[d.data_consegna <= untildate]
    cm = c.groupby(c.area) \
                .sum()[["prima_dose","seconda_dose","mono","totale"]]
    dm = d.numero_dosi.groupby(d.area).sum()
    # shortname-region : {first doses given, second doses given, ..}
    merged = cm.merge(dm,how='outer',on='area').fillna(0).astype(int)
    return merged.transpose().to_dict()
