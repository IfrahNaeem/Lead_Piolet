"""
ai_engine.py — AI Provider Interface for LeadPilot AI.

Every call to the AI provider goes through call_claude_json(). Nothing else
in the app talks to Anthropic directly — if you ever want to swap providers
or add a second one, this is the only file that needs to change.

All public functions here return (ok: bool, message: str, data) so the
Streamlit layer (app.py) can stay simple: check `ok`, show `message` as a
success/error, and use `data` if ok is True. No Streamlit imports happen
in this file on purpose, so it's easy to test on its own.
"""

import json
import re
import streamlit as st


# ---------------------------------------------------------------------------
# CLIENT SETUP
# ---------------------------------------------------------------------------

def set_api_key(api_key, workspace_id=""):
    """Stores an Anthropic client in this browser session's state.
    Nothing is ever written to disk."""
    import anthropic

    if not api_key or not api_key.strip():
        st.session_state["lp_client"] = None
        return False, "Please paste a valid Anthropic API key."

    extra_headers = {}
    if workspace_id and workspace_id.strip():
        extra_headers["anthropic-workspace-id"] = workspace_id.strip()

    st.session_state["lp_client"] = anthropic.Anthropic(
        api_key=api_key.strip(),
        default_headers=extra_headers or None,
    )
    return True, "API key connected. AI features are now active."


def _get_client():
    return st.session_state.get("lp_client")


def is_connected():
    return _get_client() is not None


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def call_claude_json(system_prompt, user_prompt, max_tokens=1200):
    client = _get_client()
    if client is None:
        raise RuntimeError("No API key connected yet. Go to Setup and connect your Anthropic API key first.")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return _extract_json(text)


# ---------------------------------------------------------------------------
# RESEARCH
# ---------------------------------------------------------------------------

RESEARCH_SYSTEM_PROMPT = """You are a careful B2B research assistant helping a freelancer/agency
qualify a sales lead. You must be strictly honest about what is a verified fact vs a guess.

Rules you must always follow:
- Never invent specific facts you cannot support (no fake news, no fake funding rounds, no fake quotes).
- Anything not directly given to you in the input must go under "inferences", clearly framed as a
  reasonable possibility, NOT a certainty.
- potential_need_score (0-20) and recent_activity_score (0-10) must be conservative and justified
  by the observations/inferences you listed, not invented separately.
- Respond with ONLY a single valid JSON object. No markdown fences, no preamble, no commentary.
"""

RESEARCH_JSON_SHAPE = """{
  "company_summary": "string, 2-3 sentences",
  "verified_observations": ["string", "..."],
  "inferences": ["string", "..."],
  "potential_opportunities": ["string", "..."],
  "personalization_angles": ["string", "..."],
  "confidence_notes": ["string", "..."],
  "potential_need_score": 0,
  "recent_activity_score": 0,
  "why_this_lead": "string, 2-3 sentences, plain language"
}"""


def run_research(lead, profile):
    user_prompt = f"""
MY SERVICE PROFILE:
- Service: {profile.get('service_name','')}
- Description: {profile.get('description','')}
- Target industries: {', '.join(profile.get('target_industries', []))}
- Target locations: {', '.join(profile.get('target_locations', []))}

LEAD INFORMATION (this is ALL the information you have — do not assume more exists):
- Company: {lead['company_name']}
- Website: {lead['company_url']}
- Industry: {lead['industry']}
- Location: {lead['location']}
- Employee count: {lead['employee_count']}
- Contact: {lead['contact_name']} ({lead['contact_role']})

Return ONLY a JSON object with exactly this shape:
{RESEARCH_JSON_SHAPE}
"""
    try:
        data = call_claude_json(RESEARCH_SYSTEM_PROMPT, user_prompt)
        return True, "Research complete.", data
    except Exception as e:
        return False, f"Research failed: {e}", None


# ---------------------------------------------------------------------------
# DETERMINISTIC SCORING
# The AI only ever supplies two bounded sub-scores (need + recent activity).
# Everything else is plain arithmetic, so the final number is always
# explainable — never a mystery output from the model.
# ---------------------------------------------------------------------------

def calculate_score(lead, research_data, profile):
    target_industries = [i.lower() for i in profile.get("target_industries", [])]

    # Service Relevance (30)
    if lead["industry"] and lead["industry"].lower() in target_industries:
        service_relevance = 30
    elif lead["industry"]:
        service_relevance = 15
    else:
        service_relevance = 8

    # Company Fit (20)
    company_fit = 16 if lead["employee_count"].strip() else 10

    # Potential Need (20) — from AI, clamped
    potential_need = max(0, min(20, int(research_data.get("potential_need_score", 10))))

    # Decision Maker Found (15)
    decision_maker = 15 if lead["contact_name"].strip() and lead["contact_role"].strip() else 5

    # Recent Activity (10) — from AI, clamped
    recent_activity = max(0, min(10, int(research_data.get("recent_activity_score", 4))))

    # Data Quality (5)
    data_quality = 5 if lead["contact_email"].strip() else 2

    total = service_relevance + company_fit + potential_need + decision_maker + recent_activity + data_quality
    total = max(0, min(100, total))

    breakdown = {
        "Service Relevance": (service_relevance, 30),
        "Company Fit": (company_fit, 20),
        "Potential Need": (potential_need, 20),
        "Decision Maker Found": (decision_maker, 15),
        "Recent Activity": (recent_activity, 10),
        "Data Quality": (data_quality, 5),
    }
    reason = research_data.get("why_this_lead", "")
    return breakdown, total, reason


# ---------------------------------------------------------------------------
# MESSAGE GENERATION
# ---------------------------------------------------------------------------

MESSAGE_SYSTEM_PROMPT = """You write short, honest, non-spammy outbound sales messages for a
freelancer/agency. You may ONLY reference facts given to you in verified_observations or
personalization_angles. Never invent client names, results, testimonials, or prior interactions.
Respond with ONLY a single valid JSON object, no markdown fences, no commentary."""


def _lead_context(lead, profile, research):
    research = research or {}
    return f"""
MY SERVICE PROFILE:
- Service: {profile.get('service_name','')}
- Description: {profile.get('description','')}
- Portfolio: {profile.get('portfolio_url','')}

LEAD:
- Company: {lead['company_name']}
- Contact: {lead['contact_name']} ({lead['contact_role']})

VERIFIED OBSERVATIONS (only source of truth you may reference):
{chr(10).join('- ' + o for o in research.get('verified_observations', [])) or '- none'}

ALLOWED PERSONALIZATION ANGLES:
{chr(10).join('- ' + a for a in research.get('personalization_angles', [])) or '- none'}
"""


def generate_email(lead, profile, research):
    prompt = _lead_context(lead, profile, research) + """
Write a cold outreach EMAIL. Return ONLY:
{"subject": "string", "body": "string with a personal observation, a value proposition, and a clear CTA. Under 150 words."}
"""
    try:
        data = call_claude_json(MESSAGE_SYSTEM_PROMPT, prompt)
        return True, "Email draft generated.", data
    except Exception as e:
        return False, f"Generation failed: {e}", None


def generate_linkedin(lead, profile, research):
    prompt = _lead_context(lead, profile, research) + """
Write a short LINKEDIN connection/outreach message (under 300 characters). Return ONLY:
{"body": "string"}
"""
    try:
        data = call_claude_json(MESSAGE_SYSTEM_PROMPT, prompt)
        return True, "LinkedIn draft generated.", data
    except Exception as e:
        return False, f"Generation failed: {e}", None


def generate_followups(lead, profile, research):
    prompt = _lead_context(lead, profile, research) + """
Write three short follow-up messages for day 3, day 7, and day 14 after the first email
(assume no reply yet; each one slightly shorter/lower-pressure than the last). Return ONLY:
{"day3": "string", "day7": "string", "day14": "string"}
"""
    try:
        data = call_claude_json(MESSAGE_SYSTEM_PROMPT, prompt)
        return True, "Follow-ups generated.", data
    except Exception as e:
        return False, f"Generation failed: {e}", None


# ---------------------------------------------------------------------------
# REPLY CLASSIFICATION
# ---------------------------------------------------------------------------

REPLY_SYSTEM_PROMPT = """You classify inbound email replies to cold outreach for a
freelancer/agency. Be conservative about risk flags. Respond with ONLY a single valid
JSON object, no markdown fences, no commentary."""

CLASSIFICATIONS = ["INTERESTED", "QUESTION", "PRICING", "NOT_INTERESTED", "NOT_NOW",
                    "UNSUBSCRIBE", "OUT_OF_OFFICE", "UNKNOWN"]
RISK_CATEGORIES = ["LEGAL", "CONTRACT", "NEGOTIATION", "ANGRY_CUSTOMER", "REFUND", "CUSTOM_PRICING", "NONE"]


def classify_reply(reply_text):
    prompt = f"""
Classify this inbound reply.

REPLY TEXT:
\"\"\"{reply_text}\"\"\"

Return ONLY:
{{
  "classification": "one of {CLASSIFICATIONS}",
  "risk_flag": true or false,
  "risk_category": "one of {RISK_CATEGORIES}",
  "suggested_reply": "string, a short honest draft reply, or empty string if risk_flag is true"
}}
"""
    try:
        data = call_claude_json(REPLY_SYSTEM_PROMPT, prompt)
        return True, "Classified.", data
    except Exception as e:
        return False, f"Classification failed: {e}", None
