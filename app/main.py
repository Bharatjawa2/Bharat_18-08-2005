from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import sqlite3, threading, uuid, os
from datetime import datetime
from .db import init_db, DB_PATH
from .models import TriggerResp
from .reports import generate_report

app = FastAPI(title="Store Monitoring API")
init_db()

@app.post("/trigger_report", response_model=TriggerResp)
def trigger_report():
    report_id=str(uuid.uuid4())
    conn=sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO reports(report_id,status,csv_path,created_at) VALUES(?,?,?,?)",
                 (report_id,"Queued","",datetime.utcnow().isoformat()))
    conn.commit(); conn.close()
    threading.Thread(target=generate_report,args=(report_id,)).start()
    return {"report_id":report_id}

@app.get("/get_report/{report_id}")
def get_report(report_id: str, statusOnly: bool = False):
    conn=sqlite3.connect(DB_PATH); cur=conn.cursor()
    cur.execute("SELECT status,csv_path FROM reports WHERE report_id=?",(report_id,))
    row=cur.fetchone(); conn.close()
    if not row: raise HTTPException(404,"report_id not found")
    status,csv=row
    if status!="Complete":
        return PlainTextResponse(status if statusOnly else "Running")
    if statusOnly:
        return PlainTextResponse("Complete")
    if not os.path.exists(csv): raise HTTPException(500,"CSV missing")
    return FileResponse(csv,media_type="text/csv",filename=os.path.basename(csv))

@app.get("/")
def index():
    return {"msg":"Use /trigger_report then /get_report/{id}"}
