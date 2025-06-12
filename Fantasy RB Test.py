import requests
import pandas as pd
from bs4 import BeautifulSoup

# URLs of the two tables
PROJ_URL = "https://www.fantasypros.com/nfl/projections/rb.php?week=draft"
ADP_URL = "https://www.fantasypros.com/nfl/adp/rb.php"


def fetch_projection_table():
    r = requests.get(PROJ_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    # Find the projections table and pull rows
    table = soup.find("table")
    cols = ["Player", "ATT", "YDS", "TDs", "REC", "REC_YDS", "REC_TDs", "FL", "FPTS"]
    df = pd.read_html(str(table), header=0)[0]
    df = df.rename(columns={"YDS.1": "REC_YDS", "TDs.1": "REC_TDs", "FPTS": "FPTS"})
    df["Player"] = df["Player"].str.replace(r"\s+\w+$", "", regex=True)  # strip trailing team abbrev link
    return df[["Player", "FPTS"]]


def fetch_adp_table():
    r = requests.get(ADP_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    df = pd.read_html(str(table), header=0)[0]
    df = df.rename(columns={"Player": "Player", "AVG": "ADP"})
    df["Player"] = df["Player"].str.replace(r"\s+\(.+?\)$", "", regex=True)  # strip team/bye
    return df[["Player", "ADP"]]


# Fetch and merge
proj_df = fetch_projection_table()
adp_df = fetch_adp_table()
full = pd.merge(proj_df, adp_df, on="Player", how="inner")

# Compute value score
full["Value Score"] = (full["FPTS"] / full["ADP"]).round(2)

# Save to CSV
out_path = "rb_value_scores_2025.csv"
full.to_csv(out_path, index=False)
print(f"Wrote {len(full)} running backs to {out_path}")
