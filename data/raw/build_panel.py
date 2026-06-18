"""
build_panel.py : reproducibly build the county panel from the raw badata source.

Run once to regenerate data/raw/ba_unemployment_panel.csv from the
RegioHub badata package (DOI 10.5281/zenodo.7664361).

Steps:
  1. Download the zip from Zenodo
  2. Read the .rda files with pyreadr
  3. Aggregate unemployment to county-year
  4. Build the 2014 bite proxy and East/West flag
"""
import pyreadr, pandas as pd, numpy as np, urllib.request, zipfile, io, tempfile, os

URL = "https://zenodo.org/records/7664361/files/RegioHub/badata-v0.1.3.zip?download=1"

def main():
    print("Downloading badata from Zenodo...")
    raw = urllib.request.urlopen(URL, timeout=120).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    tmp = tempfile.mkdtemp()
    z.extractall(tmp)
    root = [d for d in os.listdir(tmp) if d.startswith("RegioHub")][0]
    data_dir = os.path.join(tmp, root, "data")

    unemp   = pyreadr.read_r(os.path.join(data_dir, "unemployed_total.rda"))["unemployed_total"]
    regions = pyreadr.read_r(os.path.join(data_dir, "region_codes.rda"))["region_codes"]

    panel = (unemp.groupby(["region","year"])["total"].sum().reset_index()
             .rename(columns={"total":"unemployed"}))
    panel = panel.merge(unemp.groupby(["region","year"])["women"].sum().reset_index(),
                        on=["region","year"])
    panel = panel.merge(regions, left_on="region", right_on="code", how="left")
    panel["year"] = panel["year"].astype(int)
    panel = panel[(panel["year"]>=2012)&(panel["year"]<=2018)].copy()
    panel["state_code"] = panel["region"].str[:2].astype(int)
    panel["east"] = panel["state_code"].isin([11,12,13,14,15,16]).astype(int)
    bite = (panel[panel["year"]==2014]
            .assign(bite_proxy=lambda d: d["unemployed"]/d["unemployed"].mean())
            [["region","bite_proxy"]])
    panel = panel.merge(bite, on="region", how="left").dropna()
    panel = panel.rename(columns={"region":"kreis_id","name":"kreis_name"})
    panel.to_csv("ba_unemployment_panel.csv", index=False)
    print(f"Saved ba_unemployment_panel.csv : {panel['kreis_id'].nunique()} counties, {len(panel)} rows")

if __name__ == "__main__":
    main()
