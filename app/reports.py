import sqlite3, os, uuid, pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .db import DB_PATH
from .utils import build_business_windows, build_status_segments, accumulate_overlap_seconds

REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def read_polls():
    df = pd.read_sql("SELECT * FROM polls", sqlite3.connect(DB_PATH))
    if "timestamp_utc" in df.columns:
        ts = df["timestamp_utc"].astype(str).str.replace(" UTC", "", regex=False)
        parsed = pd.to_datetime(ts, errors="coerce")
        parsed = parsed.dt.tz_localize("UTC")
        df["timestamp_utc"] = parsed
    return df
def read_bh(): return pd.read_sql("SELECT * FROM business_hours", sqlite3.connect(DB_PATH))
def read_tz(): return pd.read_sql("SELECT * FROM timezones", sqlite3.connect(DB_PATH))

def max_poll_time(polls):
    return polls["timestamp_utc"].max()

def compute_uptime_for_store(store, polls, bh_store, tz_str, now):
    tz = ZoneInfo(tz_str or "America/Chicago")
    intervals = {
        "hour": (now - pd.Timedelta(hours=1), now),
        "day":  (now - pd.Timedelta(days=1), now),
        "week": (now - pd.Timedelta(days=7), now)
    }
    results={}
    polls_store = polls[polls["store_id"]==store]
    segments = build_status_segments(polls_store)

    for k,(s,e) in intervals.items():
        windows = build_business_windows(store, tz, bh_store, s, e)
        up,down=0,0
        for wstart,wend in windows:
            u,d = accumulate_overlap_seconds(segments, wstart, wend)
            up+=u; down+=d
        results[k]=(round(up/3600,3),round(down/3600,3), int(round(up/60)), int(round(down/60)))
    return {
        "store_id": store,
        "uptime_last_hour(in minutes)": results["hour"][2],
        "uptime_last_day(in hours)": results["day"][0],
        "uptime_last_week(in hours)": results["week"][0],
        "downtime_last_hour(in minutes)": results["hour"][3],
        "downtime_last_day(in hours)": results["day"][1],
        "downtime_last_week(in hours)": results["week"][1],
    }

def generate_report(report_id):
    conn=sqlite3.connect(DB_PATH)
    conn.execute("UPDATE reports SET status=? WHERE report_id=?",("Running",report_id)); conn.commit()
    try:
        polls, bh, tzs = read_polls(), read_bh(), read_tz()
        now=max_poll_time(polls)
        stores = pd.concat([polls["store_id"],bh["store_id"],tzs["store_id"]]).unique()
        rows=[]
        for store in stores:
            tz_row=tzs[tzs["store_id"]==store]
            tz_str=tz_row["timezone_str"].iloc[0] if not tz_row.empty else "America/Chicago"
            bh_store=bh[bh["store_id"]==store]
            rows.append(compute_uptime_for_store(store,polls,bh_store,tz_str,now))
        out=pd.DataFrame(rows)
        path=os.path.join(REPORTS_DIR,f"{report_id}.csv")
        out.to_csv(path,index=False)
        conn.execute("UPDATE reports SET status=?, csv_path=? WHERE report_id=?",
                     ("Complete",path,report_id))
        conn.commit()
    except Exception as e:
        conn.execute("UPDATE reports SET status=? WHERE report_id=?",(f"Failed: {e}",report_id)); conn.commit()
    finally: conn.close()
