"""
app.py — LeadPilot AI (Streamlit prototype)

Run with:  streamlit run app.py

This file only handles navigation + rendering. All data logic lives in
db.py, all AI calls live in ai_engine.py, all shared styling lives in
ui_helpers.py — keeping this file focused on "what does the user see."
"""

import pandas as pd
import streamlit as st

import db
import ai_engine
import gmail_client
import ui_helpers as ui

st.set_page_config(page_title="LeadPilot AI", page_icon="🚀", layout="centered")
ui.inject_minimal_css()

PAGES = [
    "⚙️ Setup",
    "🎯 Leads",
    "🔍 Research & Score",
    "✉️ Messages",
    "📋 Approval Queue",
    "📥 Inbox",
    "📊 Dashboard",
]

with st.sidebar:
    st.markdown("### 🚀 LeadPilot AI")
    st.caption("Find leads. Personalize outreach. Win clients.")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("🛡️ Safe Mode: nothing sends without your approval.")
    if ai_engine.is_connected():
        st.caption("🟢 AI connected")
    else:
        st.caption("⚪ AI not connected yet")


# =============================================================================
# PAGE: SETUP
# =============================================================================
if page == "⚙️ Setup":
    ui.page_header("Setup", "Connect your AI key and tell LeadPilot who you are.")

    with st.container(border=True):
        st.markdown("#### 1. Connect your Anthropic API key")
        st.caption("Used only in this browser session. Never written to disk.")
        api_key = st.text_input("Anthropic API key", type="password")
        workspace_id = st.text_input(
            "Workspace ID (only fill in if you get an 'anthropic-workspace-id is required' error)",
            placeholder="Leave blank unless you hit that specific error",
        )
        if st.button("Connect", type="primary"):
            ok, msg = ai_engine.set_api_key(api_key, workspace_id)
            (st.success if ok else st.error)(msg)

    with st.container(border=True):
        st.markdown("#### 2. Connect Gmail (for real email sending)")
        st.caption(
            "Optional. Without this, approved emails just change status to SENT in the app "
            "without actually being emailed. Connect Gmail to have them really sent from your account."
        )
        if gmail_client.is_connected():
            st.success("🟢 Gmail is connected. Approved emails will be sent for real.")
            if st.button("Disconnect Gmail"):
                gmail_client.disconnect()
                st.rerun()
        else:
            st.caption(
                "You'll need a `client_secret.json` file from your own Google Cloud project "
                "(OAuth client type: Desktop app, scope: gmail.send)."
            )
            secret_file = st.file_uploader("Upload client_secret.json", type=["json"])
            if secret_file is not None:
                ok, msg = gmail_client.set_client_config(secret_file)
                (st.success if ok else st.error)(msg)

            if gmail_client.has_client_config():
                st.caption("Clicking below opens a Google sign-in window in your browser.")
                if st.button("Connect Gmail", type="primary"):
                    with st.spinner("Waiting for you to finish signing in with Google..."):
                        ok, msg = gmail_client.connect()
                    (st.success if ok else st.error)(msg)

    with st.container(border=True):
        st.markdown("#### 3. Your service profile")
        st.caption("This tells the AI who you are and what you sell, so leads and messages stay relevant.")
        profile = db.get_profile()
        c1, c2 = st.columns(2)
        with c1:
            service_name = st.text_input("Service name", value=profile.get("service_name", ""),
                                          placeholder="e.g. UI/UX Design for SaaS")
        with c2:
            portfolio_url = st.text_input("Portfolio URL", value=profile.get("portfolio_url", ""),
                                           placeholder="https://yourportfolio.com")
        description = st.text_area("Service description", value=profile.get("description", ""),
                                    placeholder="What do you do and who is it for?")
        c3, c4 = st.columns(2)
        with c3:
            industries = st.text_input("Target industries (comma-separated)",
                                        value=", ".join(profile.get("target_industries", [])),
                                        placeholder="SaaS, E-commerce, Fintech")
        with c4:
            locations = st.text_input("Target locations (comma-separated)",
                                       value=", ".join(profile.get("target_locations", [])),
                                       placeholder="USA, UK, Canada")
        if st.button("Save Profile", type="primary"):
            db.save_profile(service_name, description, portfolio_url, industries, locations)
            st.success("Profile saved.")


# =============================================================================
# PAGE: LEADS
# =============================================================================
elif page == "🎯 Leads":
    ui.page_header("Leads", "Add leads manually, or import a CSV list.")

    with st.container(border=True):
        st.markdown("#### Add a lead manually")
        c1, c2, c3 = st.columns(3)
        company_name = c1.text_input("Company name")
        company_url = c2.text_input("Company URL")
        industry = c3.text_input("Industry")
        c4, c5 = st.columns(2)
        location = c4.text_input("Location")
        employee_count = c5.text_input("Employee count")
        c6, c7, c8 = st.columns(3)
        contact_name = c6.text_input("Contact name")
        contact_role = c7.text_input("Contact role")
        contact_email = c8.text_input("Contact email")
        if st.button("➕ Add Lead", type="primary"):
            ok, msg = db.add_lead(company_name, company_url, industry, location, employee_count,
                                   contact_name, contact_role, contact_email)
            (st.success if ok else st.error)(msg)

    with st.container(border=True):
        st.markdown("#### Or import from CSV")
        st.caption("Required column: `company_name`. Optional: `company_url, industry, location, "
                    "employee_count, contact_name, contact_role, contact_email`.")
        csv_file = st.file_uploader("Upload CSV", type=["csv"])
        if csv_file is not None and st.button("📥 Import CSV"):
            try:
                df = pd.read_csv(csv_file)
                count, msg = db.import_csv(df)
                st.success(msg) if count else st.error(msg)
            except Exception as e:
                st.error(f"Could not read CSV: {e}")

    st.markdown("#### All leads")
    st.dataframe(db.leads_dataframe(), width='stretch', hide_index=True)


# =============================================================================
# PAGE: RESEARCH & SCORE
# =============================================================================
elif page == "🔍 Research & Score":
    ui.page_header("Research & Score", "AI researches the lead, then a deterministic formula scores it.")

    options = db.lead_options()
    if not options:
        st.info("Add a lead first on the Leads page.")
    else:
        label = st.selectbox("Select a lead", list(options.keys()))
        lead_id = options[label]
        lead = db.get_lead(lead_id)

        if st.button("Run AI Research + Scoring", type="primary"):
            ok, msg, data = ai_engine.run_research(lead, db.get_profile())
            if ok:
                db.save_research(lead_id, data)
                breakdown, total, reason = ai_engine.calculate_score(lead, data, db.get_profile())
                db.save_score(lead_id, breakdown, total, reason)
                st.success(msg)
            else:
                st.error(msg)

        research = db.get_research(lead_id)
        if research:
            st.divider()
            ui.render_research(research)
            st.divider()
            ui.render_score_breakdown(lead["score_breakdown"], lead["lead_score"], lead["score_reason"])


# =============================================================================
# PAGE: MESSAGES
# =============================================================================
elif page == "✉️ Messages":
    ui.page_header("Messages", "Generate drafts. Nothing here sends anything — see Approval Queue for that.")

    options = db.lead_options()
    if not options:
        st.info("Add a lead first on the Leads page.")
    else:
        label = st.selectbox("Select a lead", list(options.keys()))
        lead_id = options[label]
        lead = db.get_lead(lead_id)
        research = db.get_research(lead_id)
        profile = db.get_profile()

        if not research:
            st.warning("Run research on this lead first (Research & Score page) for grounded, personalized drafts.")

        with st.container(border=True):
            st.markdown("#### 📧 Cold email")
            if st.button("Generate email draft"):
                ok, msg, data = ai_engine.generate_email(lead, profile, research)
                if ok:
                    db.new_message(lead_id, "EMAIL", data.get("subject", ""), data.get("body", ""))
                    st.success(msg)
                else:
                    st.error(msg)

        with st.container(border=True):
            st.markdown("#### 💼 LinkedIn message")
            if st.button("Generate LinkedIn draft"):
                ok, msg, data = ai_engine.generate_linkedin(lead, profile, research)
                if ok:
                    db.new_message(lead_id, "LINKEDIN", "", data.get("body", ""))
                    st.success(msg)
                else:
                    st.error(msg)

        with st.container(border=True):
            st.markdown("#### 🔁 Follow-ups (Day 3 / 7 / 14)")
            if st.button("Generate follow-ups"):
                ok, msg, data = ai_engine.generate_followups(lead, profile, research)
                if ok:
                    db.new_message(lead_id, "FOLLOW_UP_DAY3", "", data.get("day3", ""))
                    db.new_message(lead_id, "FOLLOW_UP_DAY7", "", data.get("day7", ""))
                    db.new_message(lead_id, "FOLLOW_UP_DAY14", "", data.get("day14", ""))
                    st.success(msg)
                else:
                    st.error(msg)

        st.divider()
        st.markdown("#### Drafts for this lead")
        lead_msgs = db.messages_for_lead(lead_id)
        if not lead_msgs:
            st.caption("No drafts yet.")
        for m in lead_msgs:
            with st.expander(f"{m['message_type']} · {m['status']} · #{m['id']}"):
                if m["subject"]:
                    st.text_input("Subject", value=m["subject"], key=f"subj_{m['id']}", disabled=True)
                edited = st.text_area("Body", value=m["body"], key=f"body_{m['id']}")
                if edited != m["body"]:
                    db.update_message_body(m["id"], edited)
                st.caption("Go to Approval Queue to approve, reject, or mark as sent.")


# =============================================================================
# PAGE: APPROVAL QUEUE
# =============================================================================
elif page == "📋 Approval Queue":
    ui.page_header("Approval Queue", "Only APPROVED messages can ever be marked SENT — enforced in code.")

    msgs = db.all_messages()
    if not msgs:
        st.info("No messages generated yet. Go to the Messages page.")
    else:
        st.dataframe(db.messages_dataframe(), width='stretch', hide_index=True)
        st.divider()

        pending = [m for m in msgs if m["status"] in ("GENERATED", "EDITED")]
        approved = [m for m in msgs if m["status"] == "APPROVED"]

        if pending:
            st.markdown("#### Awaiting your review")
            for m in pending:
                lead = db.get_lead(m["lead_id"])
                with st.container(border=True):
                    st.markdown(f"**#{m['id']} · {m['message_type']} · {lead['company_name'] if lead else '?'}**")
                    st.write(m["body"])
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Approve", key=f"appr_{m['id']}", type="primary"):
                        ok, msg = db.transition_message(m["id"], "APPROVED")
                        (st.success if ok else st.error)(msg)
                        st.rerun()
                    if c2.button("❌ Reject", key=f"rej_{m['id']}"):
                        ok, msg = db.transition_message(m["id"], "REJECTED")
                        (st.success if ok else st.error)(msg)
                        st.rerun()

        if approved:
            st.markdown("#### Approved — ready to send")
            for m in approved:
                lead = db.get_lead(m["lead_id"])
                with st.container(border=True):
                    st.markdown(f"**#{m['id']} · {m['message_type']} · {lead['company_name'] if lead else '?'}**")
                    st.write(m["body"])

                    opted_out = lead and db.is_opted_out(lead["id"])
                    if opted_out:
                        st.error("This lead opted out — sending is blocked.")

                    elif m["message_type"] == "EMAIL" and gmail_client.is_connected():
                        # Real send via Gmail API
                        to_email = lead["contact_email"] if lead else ""
                        if st.button("📤 Send via Gmail", key=f"send_{m['id']}", type="primary"):
                            ok, msg = gmail_client.send_email(to_email, m["subject"], m["body"])
                            if ok:
                                db.transition_message(m["id"], "SENT")
                                st.success(msg)
                            else:
                                st.error(msg)
                            st.rerun()

                    elif m["message_type"] == "EMAIL" and not gmail_client.is_connected():
                        st.caption("Gmail isn't connected — this will only update the status, not really send. "
                                   "Connect Gmail on the Setup page to send for real.")
                        if st.button("📤 Mark as Sent (simulated)", key=f"send_{m['id']}"):
                            ok, msg = db.transition_message(m["id"], "SENT")
                            (st.success if ok else st.error)(msg)
                            st.rerun()

                    else:
                        # LinkedIn / follow-ups: no safe automation exists here.
                        # Give the user a one-click copy and let them send it themselves.
                        st.caption("LinkedIn sending isn't automated (doing so risks your account "
                                   "being suspended by LinkedIn). Copy the message and send it yourself.")
                        st.code(m["body"], language=None)
                        if st.button("📤 Mark as Sent (I sent it manually)", key=f"send_{m['id']}"):
                            ok, msg = db.transition_message(m["id"], "SENT")
                            (st.success if ok else st.error)(msg)
                            st.rerun()

        if not pending and not approved:
            st.caption("Nothing pending — everything's been actioned.")


# =============================================================================
# PAGE: INBOX
# =============================================================================
elif page == "📥 Inbox":
    ui.page_header("Inbox", "Paste a reply to see how the AI classifies it and checks for risk.")

    options = db.lead_options()
    if not options:
        st.info("Add a lead first on the Leads page.")
    else:
        label = st.selectbox("Which lead is this reply from?", list(options.keys()))
        lead_id = options[label]

        reply_text = st.text_area("Reply text", placeholder="Paste the email reply here...")
        if st.button("Classify Reply", type="primary"):
            if not reply_text.strip():
                st.warning("Paste some reply text first.")
            else:
                ok, msg, data = ai_engine.classify_reply(reply_text)
                if ok:
                    classification = data.get("classification", "UNKNOWN")
                    risk_flag = data.get("risk_flag", False)
                    risk_category = data.get("risk_category", "NONE") if risk_flag else "NONE"
                    db.save_inbound_reply(lead_id, reply_text, classification, risk_category)

                    if classification == "UNSUBSCRIBE":
                        st.error("🛑 UNSUBSCRIBE detected — all future outreach to this lead is now blocked.")
                    elif risk_flag:
                        st.warning(f"⚠️ HIGH RISK ({risk_category}) — flagged for you to handle personally.")
                    else:
                        st.success(f"Classified as {classification}.")

                    c1, c2 = st.columns(2)
                    c1.metric("Classification", classification)
                    c2.metric("Risk", risk_category)
                    if data.get("suggested_reply"):
                        st.markdown("**Suggested reply** (still needs your approval before sending):")
                        st.text_area("Suggested reply", value=data["suggested_reply"], label_visibility="collapsed")
                else:
                    st.error(msg)

        history = db.conversations_for_lead(lead_id)
        if history:
            st.divider()
            st.markdown("#### History for this lead")
            for c in reversed(history):
                st.caption(f"{c['timestamp']} · {c['classification']}")
                st.write(c["content"])


# =============================================================================
# PAGE: DASHBOARD
# =============================================================================
elif page == "📊 Dashboard":
    ui.page_header("Dashboard")

    stats = db.dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total leads", stats["total_leads"])
    c2.metric("Qualified (score ≥ 60)", stats["qualified_leads"])
    c3.metric("Opted-out leads", stats["opted_out"])

    c4, c5, c6 = st.columns(3)
    c4.metric("Awaiting approval", stats["awaiting_approval"])
    c5.metric("Messages sent", stats["sent"])
    c6.metric("Replies received", stats["replies"])

    st.divider()
    with st.expander("Audit log"):
        st.dataframe(db.audit_log_dataframe(), width='stretch', hide_index=True)
