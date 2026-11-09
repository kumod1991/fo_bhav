"""
Load NSE F&O bhavcopy (UDiFF format) -> Supabase table `fut_bhav_copy`.
Futures only (STF = stock futures, IDF = index futures).

Env:  SUPABASE_URL, SUPABASE_SERVICE_KEY
Usage:
  python fetch_fut_bhav.py                         # today
  python fetch_fut_bhav.py 2026-11-06              # one day
  python fetch_fut_bhav.py 2024-07-08 2026-11-07   # range (backfill)
"""
import csv, io, os, sys, time, zipfile
from datetime import date, datetime, timedelta

import requests

URL = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d}_F_0000.csv.zip"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/all-reports-derivatives",
}
FUT_TYPES = ("STF", "IDF")


def num(x, cast=float):
    x = (x or "").strip()
    if not x:
        return None
    return cast(float(x))


def fetch_day(d: date, retries: int = 3):
    """Return list of rows, or None if NSE has no file for that day."""
    url = URL.format(d=d.strftime("%Y%m%d"))
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code in (403, 404):  # holiday / not published yet
                return None
            r.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt == retries:
                raise
            print(f"  retry {attempt} for {d}: {e}")
            time.sleep(3 * attempt)

    z = zipfile.ZipFile(io.BytesIO(r.content))
    rd = csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8"))
    out = []
    for x in rd:
        if x["FinInstrmTp"] not in FUT_TYPES:
            continue
        out.append({
            "trade_date": x["TradDt"],
            "instrument_type": x["FinInstrmTp"],
            "symbol": x["TckrSymb"].strip(),
            "expiry_date": x["XpryDt"],
            "open": num(x["OpnPric"]),
            "high": num(x["HghPric"]),
            "low": num(x["LwPric"]),
            "close": num(x["ClsPric"]),
            "last_price": num(x["LastPric"]),
            "prev_close": num(x["PrvsClsgPric"]),
            "settle_price": num(x["SttlmPric"]),
            "underlying_price": num(x["UndrlygPric"]),
            "open_interest": num(x["OpnIntrst"], int),
            "chg_in_oi": num(x["ChngInOpnIntrst"], int),
            "volume": num(x["TtlTradgVol"], int),
            "turnover": num(x["TtlTrfVal"]),
            "trades": num(x["TtlNbOfTxsExctd"], int),
            "lot_size": num(x["NewBrdLotQty"], int),
        })
    return out


def upsert(rows, batch: int = 1000):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    ep = (f"{base}/rest/v1/fut_bhav_copy"
          "?on_conflict=trade_date,instrument_type,symbol,expiry_date")
    for i in range(0, len(rows), batch):
        r = requests.post(ep, headers=headers, json=rows[i:i + batch], timeout=60)
        if not r.ok:
            raise RuntimeError(f"Supabase {r.status_code}: {r.text[:300]}")


def parse(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    start = parse(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    end = parse(sys.argv[2]) if len(sys.argv) > 2 else start
    d, loaded = start, 0
    while d <= end:
        if d.weekday() < 5:
            rows = fetch_day(d)
            if rows:
                upsert(rows)
                loaded += 1
                print(f"{d}: {len(rows)} rows")
            else:
                print(f"{d}: no file")
            time.sleep(1)
        d += timedelta(days=1)
    print(f"done, {loaded} day(s) loaded")


if __name__ == "__main__":
    main()
