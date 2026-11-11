#!/usr/bin/env python3
"""
Measure the latency of the four SaafHawa tools on YOUR machine and append to timing_log.csv.

Usage (run on at least TWO different days, >= 20 calls per API tool in total):
    export OPENAQ_API_KEY=...        # free key from https://explore.openaq.org (OpenAQ v3 needs one)
    python measure_tool_latency.py --runs 10        # run twice per day, or use --runs 20
    python measure_tool_latency.py --summary        # prints counts + overall median

Each log row = one tool call:  timestamp_utc, tool, date_utc, latency_s
Tools: openaq (locations lookup + latest readings), open_meteo, heat_index (local), kb_lookup (local).
The overall MEDIAN of every row is the delay used for every tool call in the latency model.
Paste the CSV into the ToolLog sheet of Q1_Calculations.xlsx (columns A-D).
"""
import argparse, csv, json, math, os, statistics, sys, time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request, urllib.parse

LOG = Path(__file__).with_name("timing_log.csv")
LAT, LON = 24.8607, 67.0011   # Karachi

def http_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "saafhawa-timing/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def tool_openaq():
    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAQ_API_KEY")
    h = {"X-API-Key": key, "User-Agent": "saafhawa-timing/1.0"}
    q = urllib.parse.urlencode({"coordinates": f"{LAT},{LON}", "radius": 25000, "limit": 3})
    locs = http_json(f"https://api.openaq.org/v3/locations?{q}", h)
    loc_id = locs["results"][0]["id"]
    return http_json(f"https://api.openaq.org/v3/locations/{loc_id}/latest", h)

def tool_open_meteo():
    q = urllib.parse.urlencode({"latitude": LAT, "longitude": LON,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"})
    return http_json(f"https://api.open-meteo.com/v1/forecast?{q}")

def heat_index_c(t_c, rh):
    """NWS Rothfusz regression (valid for T >= 80F); simple formula below 80F."""
    t = t_c * 9 / 5 + 32
    hi = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (hi + t) / 2 >= 80:
        hi = (-42.379 + 2.04901523*t + 10.14333127*rh - 0.22475541*t*rh - 6.83783e-3*t*t
              - 5.481717e-2*rh*rh + 1.22874e-3*t*t*rh + 8.5282e-4*t*rh*rh - 1.99e-6*t*t*rh*rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t - 95)) / 17)
        elif rh > 85 and 80 <= t <= 87:
            hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return (hi - 32) * 5 / 9

def tool_heat_index():
    return heat_index_c(36.0, 62.0)

# PLACEHOLDER knowledge base: replace with real excerpts of official advisories (PMD, NDMA, WHO, ...)
KB = [
 {"id": "heat-1", "text": "During a heatwave avoid outdoor activity between noon and 4 pm and drink water regularly."},
 {"id": "heat-2", "text": "Children, the elderly and outdoor labourers are at higher risk of heat stroke."},
 {"id": "aq-1", "text": "When PM2.5 is high, people with asthma should limit outdoor exercise and keep inhalers handy."},
 {"id": "aq-2", "text": "Masks rated N95 reduce exposure to fine particles when air quality is poor."},
 {"id": "school-1", "text": "Schools should shift outdoor activities indoors when heat index is in the danger range."},
]
def tool_kb_lookup(query="evening jog asthma pm2.5 heatwave children"):
    qs = set(query.lower().split())
    scored = sorted(KB, key=lambda d: -len(qs & set(d["text"].lower().replace(".", "").split())))
    return scored[:3]

TOOLS = {"openaq": tool_openaq, "open_meteo": tool_open_meteo,
         "heat_index": tool_heat_index, "kb_lookup": tool_kb_lookup}

def log_row(tool, dt):
    new = not LOG.exists()
    now = datetime.now(timezone.utc)
    with LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["timestamp_utc", "tool", "date_utc", "latency_s"])
        w.writerow([now.isoformat(timespec="seconds"), tool, now.date().isoformat(), f"{dt:.6f}"])

def summary():
    if not LOG.exists(): print("no log yet"); return
    rows = list(csv.DictReader(LOG.open()))
    vals = [float(r["latency_s"]) for r in rows]
    print(f"rows={len(vals)}  overall median={statistics.median(vals):.4f} s")
    for t in TOOLS:
        v = [float(r["latency_s"]) for r in rows if r["tool"] == t]
        d = {r["date_utc"] for r in rows if r["tool"] == t}
        if v: print(f"  {t:11s} n={len(v):3d} days={len(d)} median={statistics.median(v):.4f} s")
    print("Requirement check: >=20 openaq, >=20 open_meteo, on >=2 different days each.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.summary: return summary()
    for name, fn in TOOLS.items():
        for i in range(a.runs):
            t0 = time.perf_counter()
            try:
                fn()
            except Exception as e:
                print(f"[{name}] run {i+1} FAILED: {e}", file=sys.stderr); continue
            dt = time.perf_counter() - t0
            log_row(name, dt); print(f"[{name}] run {i+1}: {dt:.4f} s")
            time.sleep(1 if name in ("openaq", "open_meteo") else 0)
    summary()

if __name__ == "__main__":
    main()
