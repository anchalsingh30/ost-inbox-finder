
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile, os, uuid, csv, io, datetime as dt

from .ost_reader import iter_inbox_messages

#“main.py is the entry point of the FastAPI backend. It defines API routes, serves the UI, handles file uploads,
#filters emails, and exposes CSV export functionality.”
app = FastAPI(title="OST Inbox Finder", version="1.0.0")
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

#parses date input coming from UI
def _parse_dt(s):
    if not s: return None
    try: return dt.datetime.fromisoformat(s)
    except Exception: return None

_EXPORTS = {}

#"This endpoint handles file upload along with optional filtering parameters sent from UI."
@app.post("/api/search")
async def search(ost: UploadFile, start: str = Form(default=None), end: str = Form(default=None), mode: str = Form(default="received")):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ost") as tf:
        tf.write(await ost.read())
        temp_path = tf.name

    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    #input validation
    if start_dt and end_dt and end_dt < start_dt:
        os.unlink(temp_path)
        return JSONResponse({"error": "End before start"}, status_code=400)

    items = []
    #Inbox messages are streamed using a generator to avoid loading the entire mailbox into memory
    for msg in iter_inbox_messages(temp_path):
        ts = msg.get("received_time") if mode == "received" else msg.get("sent_time")
        if not ts: continue
        try:
            msg_dt = dt.datetime.fromisoformat(ts.split("Z")[0] if "Z" in ts else ts)
        except Exception:
            continue
        if start_dt and msg_dt < start_dt: continue
        if end_dt and msg_dt >= end_dt: continue
        items.append(msg)

    #Token generation: unique per request, safe for temp access
    token = str(uuid.uuid4())
    _EXPORTS[token] = items
    try: os.unlink(temp_path)
    except Exception: pass
    return {"items": items, "token": token}

#This endpoint allows users to export search results without reprocessing the OST file
@app.get("/api/export.csv")
def export_csv(token: str):
    rows = _EXPORTS.get(token, [])
    if not rows:
        return JSONResponse({"error": "Token not found or expired"}, status_code=404)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["received_time","sent_time","from","to","cc","subject","snippet"])
    w.writeheader(); w.writerows(rows)
    mem = io.BytesIO(out.getvalue().encode("utf-8")); mem.seek(0)
    return FileResponse(mem, media_type="text/csv", filename="results.csv")


    # Build CSV in memory
    out = io.StringIO()
    w = csv.DictWriter(
        out,
        fieldnames=["received_time", "sent_time", "from", "to", "cc", "subject", "snippet"],
    )
    w.writeheader()
    w.writerows(rows)

    csv_bytes = out.getvalue().encode("utf-8")

    # Return as downloadable file
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="results.csv"'
        },
    )
#Starts API server
def run():
    import uvicorn, webbrowser
    webbrowser.open("http://127.0.0.1:8000", new=2, autoraise=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    run()
