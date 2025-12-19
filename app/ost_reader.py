
import datetime as dt
from typing import Iterator, Dict, Optional, Tuple
import json

# Defensive import: allow app to start without pypff (for unit tests)
try:
    import pypff  # provided by libpff-python
except Exception:  # pragma: no cover
    pypff = None  # type: ignore

#pypff is needed when importing emails from outlook
# Defensive import: allow app to start without pypff (for unit tests)
try:
    import pypff  
except Exception:
    pypff = None 
#It is taking care of synthetic file
def _read_synthetic_ost(ost_path: str):
    """
    If the file is a synthetic OST, return a list of message dicts.
    Otherwise return None.
    Magic header: b'OSTFTEST1\\n'
    """
    try:
        with open(ost_path, "rb") as f:
            head = f.read(10)
            if not head.startswith(b"OSTFTEST1\n"):
                return None
            payload = f.read().decode("utf-8", errors="ignore")
        data = json.loads(payload)
        # normalize to expected keys
        out = []
        for m in data:
            out.append({
                "subject": m.get("subject",""),
                "from": m.get("from",""),
                "to": m.get("to",""),
                "cc": m.get("cc",""),
                "received_time": m.get("received_time"),
                "sent_time": m.get("sent_time"),
                "snippet": m.get("snippet",""),
            })
        return out
    except Exception:
        return None

#Converts various timestamp formats into ISO-8601 strings.
def _to_iso(ts) -> Optional[str]:
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        return dt.datetime.utcfromtimestamp(ts).isoformat()
    try:
        return ts.isoformat()
    except Exception:
        return None

##Extracts To and Cc recipients from a pypff message object.
#Returns comma-separated strings for UI display.
def _collect_recipients(message) -> Tuple[str, str]:
    to_list, cc_list = [], []
    try:
        n = message.get_number_of_recipients()
        for i in range(n):
            r = message.get_recipient(i)
            rtype = getattr(r, "get_type", lambda: None)()
            name = getattr(r, "get_name", lambda: None)() or ""
            email = getattr(r, "get_email_address", lambda: None)() or ""
            label = f"{name} <{email}>" if email else (name or "")
            if rtype == 1:
                to_list.append(label)
            elif rtype == 2:
                cc_list.append(label)
    except Exception:
        pass
    return (", ".join(to_list), ", ".join(cc_list))

#Helper function: Recursively searches the folder tree to locate the Inbox folder
def _find_inbox(folder) -> Optional[object]:
    try:
        name = getattr(folder, "get_name", lambda: "")() or ""
    except Exception:
        name = ""
    if name.lower() == "inbox":
        return folder
    try:
        count = getattr(folder, "get_number_of_sub_folders", lambda: 0)()
        for i in range(count):
            child = getattr(folder, "get_sub_folder", lambda idx: None)(i)
            if child:
                found = _find_inbox(child)
                if found:
                    return found
    except Exception:
        return None
    return None

def _iter_synthetic_ost(ost_path: str):
    """Support a synthetic test format:
    File starts with magic bytes b'OSTFTEST1\\n', followed by a UTF-8 JSON array of messages.
    """
    try:
        with open(ost_path, "rb") as f:
            head = f.read(10)
            if not head.startswith(b"OSTFTEST1\\n"):
                return None
            payload = f.read().decode("utf-8", errors="ignore")
        data = json.loads(payload)
        for m in data:
            yield {
                "subject": m.get("subject",""),
                "from": m.get("from",""),
                "to": m.get("to",""),
                "cc": m.get("cc",""),
                "received_time": m.get("received_time"),
                "sent_time": m.get("sent_time"),
                "snippet": m.get("snippet",""),
            }
        return True
    except Exception:
        return None

#Core generator function.
def iter_inbox_messages(ost_path: str) -> Iterator[Dict]:
    # Synthetic test path first
    syn = _read_synthetic_ost(ost_path)
    if syn is True:
        return
    elif syn is not None:
        for x in syn:
            yield x
        return

    ##Note: the following code is being used for pypff to run it through the pypff and its not needed to run on the Web
    if pypff is None:
        raise RuntimeError("pypff not available. See README for libpff installation.")

    pf = pypff.file()
    pf.open(ost_path)
    root = pf.get_root_folder()
    inbox = _find_inbox(root)
    if inbox is None:
        return
    get_msgs = getattr(inbox, "get_number_of_sub_messages", None) or getattr(inbox, "get_number_of_messages", None)
    get_msg = getattr(inbox, "get_sub_message", None) or getattr(inbox, "get_message", None)
    total = get_msgs() if get_msgs else 0
    #Stream messages one by one
    for i in range(total):
        try:
            m = get_msg(i)
            subject = getattr(m, "get_subject", lambda: None)()
            sender = getattr(m, "get_sender_name", lambda: None)() or getattr(m, "get_sender_email_address", lambda: None)()
            rec_time = getattr(m, "get_delivery_time", lambda: None)() or getattr(m, "get_client_submit_time", lambda: None)()
            sent_time = getattr(m, "get_client_submit_time", lambda: None)()
            #Extract body safely
            body = None
            for getter in ("get_plain_text_body", "get_html_body", "get_body"):
                try:
                    body = getattr(m, getter)()
                    if body:
                        break
                except Exception:
                    continue
            #Create short preview snippet
            snippet = (body or "")
            if isinstance(snippet, bytes):
                snippet = snippet.decode(errors="ignore")
            snippet = snippet.replace("\\r\\n", " ").replace("\\n", " ")[:200]
            to, cc = _collect_recipients(m)
            yield {
                "subject": subject or "",
                "from": sender or "",
                "to": to,
                "cc": cc,
                "received_time": _to_iso(rec_time),
                "sent_time": _to_iso(sent_time),
                "snippet": snippet,
            }
        except Exception:
            #Skip corrupted messages without stopping the app
            continue
