"""
db.py — Data layer for LeadPilot AI.

In a real deployment this would be PostgreSQL (see the full phased build plan).
For this prototype we keep everything in memory, stored inside Streamlit's
st.session_state so each browser tab/session gets its own isolated data and
nothing survives a server restart. That's intentional: it keeps the demo
dependency-free.

This file owns:
- the profile / leads / research / messages / conversations / audit_log tables
- the Safe Mode message state machine (GENERATED -> EDITED/APPROVED/REJECTED -> SENT)
No AI calls happen here. No Streamlit widgets are rendered here either —
this file only manages data, so it stays testable on its own.
"""

import datetime as dt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# SAFE MODE STATE MACHINE
# A message may only move along these edges. In particular:
#   GENERATED -> SENT directly is NOT allowed.
#   Only APPROVED -> SENT is allowed.
# This is enforced in transition_message() below, not just in the UI.
# ---------------------------------------------------------------------------
VALID_MESSAGE_TRANSITIONS = {
    "GENERATED": {"EDITED", "APPROVED", "REJECTED"},
    "EDITED": {"APPROVED", "REJECTED"},
    "APPROVED": {"SENT", "REJECTED"},
    "REJECTED": set(),
    "SENT": set(),
}


def _default_store():
    return {
        "profile": {
            "service_name": "",
            "description": "",
            "portfolio_url": "",
            "target_industries": [],
            "target_locations": [],
        },
        "leads": [],
        "research": {},      # lead_id -> research dict
        "messages": [],
        "conversations": [],
        "audit_log": [],
        "next_lead_id": 1,
        "next_msg_id": 1,
    }


def get_store():
    """Returns this browser session's data store, creating it on first use."""
    if "lp_store" not in st.session_state:
        st.session_state["lp_store"] = _default_store()
    return st.session_state["lp_store"]


def log_audit(action, details=""):
    get_store()["audit_log"].append({
        "action": action,
        "details": details,
        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------

def save_profile(service_name, description, portfolio_url, industries_csv, locations_csv):
    store = get_store()
    store["profile"] = {
        "service_name": service_name.strip(),
        "description": description.strip(),
        "portfolio_url": portfolio_url.strip(),
        "target_industries": [s.strip() for s in industries_csv.split(",") if s.strip()],
        "target_locations": [s.strip() for s in locations_csv.split(",") if s.strip()],
    }
    log_audit("PROFILE_SAVED", service_name)


def get_profile():
    return get_store()["profile"]


def profile_is_set():
    return bool(get_profile().get("service_name"))


# ---------------------------------------------------------------------------
# LEADS
# ---------------------------------------------------------------------------

def add_lead(company_name, company_url, industry, location, employee_count,
             contact_name, contact_role, contact_email, source="MANUAL"):
    if not company_name.strip():
        return False, "Company name is required."
    store = get_store()
    lead = {
        "id": store["next_lead_id"],
        "company_name": company_name.strip(),
        "company_url": company_url.strip(),
        "industry": industry.strip(),
        "location": location.strip(),
        "employee_count": str(employee_count).strip(),
        "contact_name": contact_name.strip(),
        "contact_role": contact_role.strip(),
        "contact_email": contact_email.strip(),
        "lead_score": None,
        "score_breakdown": None,
        "score_reason": "",
        "source": source,
        "status": "NEW",
        "created_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    store["leads"].append(lead)
    store["next_lead_id"] += 1
    log_audit("LEAD_ADDED", lead["company_name"])
    return True, f"Added lead: {lead['company_name']}"


def import_csv(dataframe):
    """dataframe: a pandas DataFrame already read from the uploaded CSV."""
    cols = {c.lower().strip() for c in dataframe.columns}
    if "company_name" not in cols:
        return 0, "CSV must contain at least a 'company_name' column."
    dataframe = dataframe.rename(columns={c: c.lower().strip() for c in dataframe.columns})
    count = 0
    for _, row in dataframe.iterrows():
        ok, _ = add_lead(
            str(row.get("company_name", "") or ""),
            str(row.get("company_url", "") or ""),
            str(row.get("industry", "") or ""),
            str(row.get("location", "") or ""),
            str(row.get("employee_count", "") or ""),
            str(row.get("contact_name", "") or ""),
            str(row.get("contact_role", "") or ""),
            str(row.get("contact_email", "") or ""),
            source="CSV_IMPORT",
        )
        if ok:
            count += 1
    return count, f"Imported {count} lead(s)."


def all_leads():
    return get_store()["leads"]


def leads_dataframe():
    leads = all_leads()
    if not leads:
        return pd.DataFrame(columns=["ID", "Company", "Industry", "Location", "Score", "Status", "Source"])
    return pd.DataFrame([{
        "ID": l["id"],
        "Company": l["company_name"],
        "Industry": l["industry"],
        "Location": l["location"],
        "Score": l["lead_score"] if l["lead_score"] is not None else "—",
        "Status": l["status"],
        "Source": l["source"],
    } for l in leads])


def get_lead(lead_id):
    for l in all_leads():
        if l["id"] == int(lead_id):
            return l
    return None


def lead_options():
    """Returns {display_label: lead_id} for use in a selectbox."""
    return {f"#{l['id']} — {l['company_name']}": l["id"] for l in all_leads()}


def is_opted_out(lead_id):
    lead = get_lead(lead_id)
    return lead is not None and lead["status"] == "OPTED_OUT"


# ---------------------------------------------------------------------------
# RESEARCH (data storage only — the AI call itself lives in ai_engine.py)
# ---------------------------------------------------------------------------

def save_research(lead_id, research_data):
    get_store()["research"][lead_id] = research_data
    lead = get_lead(lead_id)
    if lead:
        lead["status"] = "RESEARCHED"
    log_audit("LEAD_RESEARCHED", str(lead_id))


def get_research(lead_id):
    return get_store()["research"].get(lead_id)


def save_score(lead_id, breakdown, total, reason):
    lead = get_lead(lead_id)
    if lead:
        lead["lead_score"] = total
        lead["score_breakdown"] = breakdown
        lead["score_reason"] = reason


# ---------------------------------------------------------------------------
# MESSAGES + SAFE MODE APPROVAL WORKFLOW
# ---------------------------------------------------------------------------

def new_message(lead_id, message_type, subject, body):
    store = get_store()
    msg = {
        "id": store["next_msg_id"],
        "lead_id": lead_id,
        "message_type": message_type,
        "subject": subject,
        "body": body,
        "status": "GENERATED",
        "created_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    store["messages"].append(msg)
    store["next_msg_id"] += 1
    log_audit("MESSAGE_GENERATED", f"{message_type} for lead {lead_id}")
    return msg


def all_messages():
    return get_store()["messages"]


def get_message(msg_id):
    for m in all_messages():
        if m["id"] == int(msg_id):
            return m
    return None


def messages_for_lead(lead_id, message_type=None):
    msgs = [m for m in all_messages() if m["lead_id"] == lead_id]
    if message_type:
        msgs = [m for m in msgs if m["message_type"] == message_type]
    return msgs


def messages_dataframe():
    msgs = all_messages()
    if not msgs:
        return pd.DataFrame(columns=["ID", "Lead", "Type", "Status", "Preview"])
    rows = []
    for m in msgs:
        lead = get_lead(m["lead_id"])
        preview = (m["body"][:70] + "…") if len(m["body"]) > 70 else m["body"]
        rows.append({
            "ID": m["id"],
            "Lead": lead["company_name"] if lead else "?",
            "Type": m["message_type"],
            "Status": m["status"],
            "Preview": preview,
        })
    return pd.DataFrame(rows)


def update_message_body(msg_id, new_body):
    msg = get_message(msg_id)
    if msg and new_body.strip() != msg["body"].strip():
        msg["body"] = new_body
        if msg["status"] == "GENERATED":
            msg["status"] = "EDITED"
            log_audit("MESSAGE_EDITED", f"message {msg_id}")


def transition_message(msg_id, new_status):
    """The ONLY function allowed to change a message's status.
    Enforces the Safe Mode state machine — this is a backend rule,
    not just something the UI happens to respect."""
    msg = get_message(msg_id)
    if msg is None:
        return False, "Message not found."

    current = msg["status"]
    if new_status == current:
        return False, f"Message is already {current}."

    allowed = VALID_MESSAGE_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        return False, f"Not allowed: cannot move a message from {current} to {new_status}."

    msg["status"] = new_status
    log_audit(f"MESSAGE_{new_status}", f"message {msg_id}")
    return True, f"Message #{msg_id} moved to {new_status}."


# ---------------------------------------------------------------------------
# CONVERSATIONS / INBOX
# ---------------------------------------------------------------------------

def save_inbound_reply(lead_id, content, classification, risk_category):
    get_store()["conversations"].append({
        "lead_id": lead_id,
        "direction": "INBOUND",
        "content": content,
        "classification": classification,
        "risk_category": risk_category,
        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    if classification == "UNSUBSCRIBE":
        lead = get_lead(lead_id)
        if lead:
            lead["status"] = "OPTED_OUT"
        log_audit("OPT_OUT_RECEIVED", str(lead_id))


def conversations_for_lead(lead_id):
    return [c for c in get_store()["conversations"] if c["lead_id"] == lead_id]


def all_conversations():
    return get_store()["conversations"]


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

def dashboard_stats():
    leads = all_leads()
    msgs = all_messages()
    return {
        "total_leads": len(leads),
        "qualified_leads": len([l for l in leads if (l["lead_score"] or 0) >= 60]),
        "awaiting_approval": len([m for m in msgs if m["status"] in ("GENERATED", "EDITED")]),
        "sent": len([m for m in msgs if m["status"] == "SENT"]),
        "replies": len(all_conversations()),
        "opted_out": len([l for l in leads if l["status"] == "OPTED_OUT"]),
    }


def audit_log_dataframe():
    log = get_store()["audit_log"]
    if not log:
        return pd.DataFrame(columns=["Timestamp", "Action", "Details"])
    return pd.DataFrame([{"Timestamp": e["timestamp"], "Action": e["action"], "Details": e["details"]} for e in log])
