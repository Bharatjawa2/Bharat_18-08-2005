import pandas as pd
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import List, Tuple

def build_business_windows(store_id, tz: ZoneInfo, bh_df, start_utc, end_utc) -> List[Tuple[pd.Timestamp,pd.Timestamp]]:
    windows = []
    if bh_df.empty:
        return [(start_utc, end_utc)]

    week = {int(r['dayOfWeek']):(r['start_time_local'], r['end_time_local']) for _,r in bh_df.iterrows()}

    if isinstance(start_utc, pd.Timestamp):
        start_dt_utc = start_utc.to_pydatetime()
    else:
        start_dt_utc = start_utc
    if isinstance(end_utc, pd.Timestamp):
        end_dt_utc = end_utc.to_pydatetime()
    else:
        end_dt_utc = end_utc

    local_start = start_dt_utc.astimezone(tz)
    local_end = end_dt_utc.astimezone(tz)
    cur_local_date = local_start.date() - timedelta(days=1)
    end_local_date = local_end.date() + timedelta(days=1)

    while cur_local_date <= end_local_date:
        dow = cur_local_date.weekday()
        if dow in week:
            def parse_hms(s: str):
                parts = [int(x) for x in s.split(":")]
                while len(parts) < 3:
                    parts.append(0)
                return parts[0], parts[1], parts[2]

            s_h,s_m,s_s = parse_hms(week[dow][0])
            e_h,e_m,e_s = parse_hms(week[dow][1])
            s_dt = datetime.combine(cur_local_date, time(s_h, s_m, s_s), tz)
            e_dt = datetime.combine(cur_local_date, time(e_h, e_m, e_s), tz)
            if e_dt <= s_dt: e_dt += timedelta(days=1)
            s_utc = pd.Timestamp(s_dt.astimezone(ZoneInfo("UTC")))
            e_utc = pd.Timestamp(e_dt.astimezone(ZoneInfo("UTC")))
            if e_utc>=start_utc and s_utc<=end_utc:
                windows.append((max(s_utc,start_utc), min(e_utc,end_utc)))
        cur_local_date += timedelta(days=1)
    return windows

def interpolate_status(polls, wstart, wend):
    if polls.empty:
        return 0, (wend-wstart).total_seconds()

    polls = polls.sort_values("timestamp_utc").reset_index(drop=True)
    times = list(polls["timestamp_utc"])
    statuses = [str(s).lower() for s in list(polls["status"])]

    intervals = []
    for i, current_time in enumerate(times):
        if i == 0:
            seg_start = current_time - pd.Timedelta(days=365)
        else:
            prev_time = times[i-1]
            seg_start = prev_time + (current_time - prev_time) / 2

        if i == len(times) - 1:
            seg_end = current_time + pd.Timedelta(days=365)
        else:
            next_time = times[i+1]
            seg_end = current_time + (next_time - current_time) / 2

        intervals.append((seg_start, seg_end, statuses[i]))

    up,down=0,0
    for seg_start,seg_end,status in intervals:
        inter_start, inter_end = max(seg_start,wstart), min(seg_end,wend)
        if inter_end>inter_start:
            secs = (inter_end-inter_start).total_seconds()
            if status.lower()=="active": up+=secs
            else: down+=secs
    return up,down
