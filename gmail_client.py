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
from email.mime.text import MIMEText

import streamlit as st

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


def connect():
    """Runs the OAuth login flow.

    Instead of relying on the library to auto-launch a browser (which fails
    with "could not locate runnable browser" on servers/containers/remote
    machines with no default browser configured), we build the sign-in link
    ourselves and show it directly in the app. You click it, log in, and
    this function keeps waiting in the background until you finish."""
    import secrets
    from google_auth_oauthlib.flow import InstalledAppFlow

    config = st.session_state.get("gmail_client_config")
    if config is None:
        return False, "Upload your client_secret.json file first."

    try:
        flow = InstalledAppFlow.from_client_config(config, SCOPES)

        # Pick a free local port ourselves so we can build a matching URL
        # before starting the blocking local server.
        import socket
        sock = socket.socket()
        sock.bind(("localhost", 0))
        port = sock.getsockname()[1]
        sock.close()

        flow.redirect_uri = f"http://localhost:{port}/"
        state = secrets.token_urlsafe(16)
        auth_url, _ = flow.authorization_url(
            state=state, prompt="consent", access_type="offline"
        )

        # This link renders in the app immediately — Streamlit sends each
        # element to the browser as it's created, even though the blocking
        # call below hasn't returned yet.
        st.markdown(f"👉 **[Click here to sign in with Google]({auth_url})**")
        st.caption("Waiting for you to finish signing in in the new tab...")

        creds = flow.run_local_server(port=port, open_browser=False, state=state)
    except Exception as e:
        return False, f"Google sign-in failed: {e}"

    st.session_state["gmail_creds"] = creds
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
