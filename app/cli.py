
import argparse, sys, csv, datetime as dt
from .ost_reader import iter_inbox_messages

def main(argv=None):
    ap = argparse.ArgumentParser(description="Filter Inbox emails in an OST by time window")
    ap.add_argument("--ost", required=True, help="Path to .ost file")
    ap.add_argument("--start", required=True, help="Start ISO local, e.g. 2024-01-01T00:00:00")
    ap.add_argument("--end", required=True, help="End ISO local, e.g. 2024-02-01T00:00:00")
    ap.add_argument("--mode", choices=["received","sent"], default="received", help="Filter by received or sent time")
    ap.add_argument("--csv", help="Output CSV path")
    args = ap.parse_args(argv or sys.argv[1:])

    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
    rows = []
    for msg in iter_inbox_messages(args.ost):
        ts = msg.get("received_time") if args.mode == "received" else msg.get("sent_time")
        if not ts: continue
        msg_dt = dt.datetime.fromisoformat(ts.split("Z")[0] if "Z" in ts else ts)
        if start <= msg_dt < end:
            rows.append(msg)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["received_time","sent_time","from","to","cc","subject","snippet"])
            w.writeheader(); w.writerows(rows)
        print(f"Wrote {len(rows)} rows to {args.csv}")
    else:
        for r in rows:
            print(f"[{r.get('received_time') or r.get('sent_time')}] {r.get('from')} -> {r.get('subject')}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
