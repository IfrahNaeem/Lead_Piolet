"""
gmail_client.py — Real Gmail sending via OAuth, for LeadPilot AI.

This is the ONLY file that talks to Google. Everything else (app.py) just
calls connect() and send_email() and handles the (ok, message) result —
same pattern as ai_engine.py talking to Anthropic.

How the OAuth flow works, in short:
1. You (the developer/user) create your own Google Cloud project and
   download a "client_secret.json" file — this identifies YOUR app to Google.
2. You upload that file into the Setup page.
3. Clicking "Connect Gmail" opens a Google login window in your browser.
   You log in and click Allow.
4. Google hands back a short-lived token, stored only in this browser
   session (st.session_state) — never written to disk.
5. send_email() uses that token to call Gmail's official API, so the email
   genuinely leaves YOUR Gmail account and lands in YOUR Sent folder.

Nothing in this file ever sends anything on its own — app.py only calls
send_email() from the Approval Queue, and only for messages that are
already APPROVED. That rule lives in app.py/db.py, not here.
"""

import base64
import json
import os
from email.mime.text import MIMEText

import streamlit as st

# Google's local-redirect OAuth strategy technically only works over https
# in general, but explicitly allows http for localhost. This tells the
# underlying OAuth library that's OK for our case.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# We only ask for permission to SEND mail — not read, not delete, not
# manage anything else. Keep the scope as narrow as the task needs.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def set_client_config(uploaded_file):
    """Takes the client_secret.json file the user uploaded (downloaded from
    Google Cloud Console) and stores its parsed contents for this session."""
    try:
        config = json.load(uploaded_file)
    except Exception as e:
        return False, f"Could not read that file as JSON: {e}"

    if "installed" not in config and "web" not in config:
        return False, "That doesn't look like a Google OAuth client_secret.json file."

    st.session_state["gmail_client_config"] = config
    return True, "Google credentials file loaded. Now click 'Connect Gmail'."


def has_client_config():
    return "gmail_client_config" in st.session_state


def is_connected():
    return st.session_state.get("gmail_creds") is not None


def start_signin():
    """Step 1 of a two-step sign-in that works even when the app isn't
    running on the same machine as your browser (a remote server, cloud
    dev environment, container, etc). Builds the Google sign-in link and
    returns it — it does NOT wait/block for anything."""
    import secrets
    from google_auth_oauthlib.flow import InstalledAppFlow

    config = st.session_state.get("gmail_client_config")
    if config is None:
        return False, "Upload your client_secret.json file first.", None

    try:
        flow = InstalledAppFlow.from_client_config(config, SCOPES)
        flow.redirect_uri = "http://localhost"
        state = secrets.token_urlsafe(16)
        auth_url, _ = flow.authorization_url(
            state=state, prompt="consent", access_type="offline"
        )
    except Exception as e:
        return False, f"Could not start sign-in: {e}", None

    # Keep the in-progress flow object around so step 2 can finish it.
    st.session_state["gmail_flow"] = flow
    return True, "Sign-in link ready.", auth_url


def complete_signin(pasted_value):
    """Step 2: you log in via the link from start_signin(), Google redirects
    your browser to a localhost URL that will fail to load — that's expected.
    You copy that URL (or just the 'code=' part of it) from your address bar
    and paste it in. This function exchanges it for a real access token by
    calling Google directly over the internet — no local listener needed."""
    flow = st.session_state.get("gmail_flow")
    if flow is None:
        return False, "Start the sign-in process first."

    text = (pasted_value or "").strip()
    if not text:
        return False, "Paste the URL (or the code) you got after logging in."

    try:
        if text.startswith("http"):
            flow.fetch_token(authorization_response=text)
        else:
            flow.fetch_token(code=text)
    except Exception as e:
        return False, f"Could not complete sign-in: {e}"

    st.session_state["gmail_creds"] = flow.credentials
    st.session_state.pop("gmail_flow", None)
    return True, "Gmail connected. Approved emails can now be sent for real."


def disconnect():
    st.session_state["gmail_creds"] = None


def _build_raw_message(to_email, subject, body):
    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(to_email, subject, body):
    """Sends one email through the connected Gmail account.
    Returns (ok, message). Only ever called for an already-APPROVED message —
    that check happens in app.py before this function is called."""
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    creds = st.session_state.get("gmail_creds")
    if creds is None:
        return False, "Gmail isn't connected yet. Go to Setup and connect it first."

    if not to_email or not to_email.strip():
        return False, "This lead has no contact email on file — can't send."

    try:
        service = build("gmail", "v1", credentials=creds)
        raw_message = _build_raw_message(to_email.strip(), subject, body)
        service.users().messages().send(userId="me", body=raw_message).execute()
        return True, f"Email actually sent to {to_email}."
    except HttpError as e:
        return False, f"Gmail API rejected the send: {e}"
    except Exception as e:
        return False, f"Send failed: {e}"
