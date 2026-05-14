#!/usr/bin/env python3
"""
Finoscape Auto-Publisher — FREE VERSION
========================================
Uses Google Gemini API (FREE tier — no credit card needed)
Runs daily at 7 AM IST via Render.com free cron
Saves as DRAFT in WordPress — you review and publish

How to get your free Gemini API key:
1. Go to aistudio.google.com
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the key (starts with AIza...)

Cost: ZERO — Free tier handles 1,500 requests/day
"""

import os
import json
import requests
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIGURATION ─────────────────────────────────────────────────────────
WP_URL         = os.environ.get("WP_URL",         "https://finoscape.com")
WP_USER        = os.environ.get("WP_USER",        "finoscapehuf")
WP_APP_PASS    = os.environ.get("WP_APP_PASS",    "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")   # FREE from aistudio.google.com
NOTIFY_EMAIL   = os.environ.get("NOTIFY_EMAIL",   "")   # Your email
GMAIL_USER     = os.environ.get("GMAIL_USER",     "")   # Gmail sending account
GMAIL_PASS     = os.environ.get("GMAIL_PASS",     "")   # Gmail App Password

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ── CATEGORY CACHE ────────────────────────────────────────────────────────
CATEGORY_IDS = {}

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def wp_auth():
    return (WP_USER, WP_APP_PASS)

# ── LOAD WORDPRESS CATEGORIES ────────────────────────────────────────────
def load_categories():
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=50",
                     auth=wp_auth(), timeout=30)
    if r.status_code == 200:
        for cat in r.json():
            CATEGORY_IDS[cat['name']] = cat['id']
        log(f"Categories: {list(CATEGORY_IDS.keys())}")

# ── GENERATE POST WITH GEMINI ─────────────────────────────────────────────
def generate_post():
    today = datetime.date.today().strftime("%B %d, %Y")
    log(f"Generating post for {today} using Gemini (free)...")

    prompt = f"""You are the editor of Finoscape — India's Tax Intelligence Hub.
Today is {today}. 

Search for and write about the MOST IMPORTANT recent development in Indian 
tax law (GST, Income Tax, FEMA, or Companies Act) from the past 48 hours.

Use Google Search to find:
- New CBIC circulars or GST portal updates
- Significant ITAT or High Court rulings
- CBDT notifications or press releases
- RBI circulars with tax implications
- MCA notifications or NCLT orders

Write a complete Finoscape morning digest post with this EXACT structure:

1. Opening story/hook (2-3 sentences — a real scenario that illustrates the issue)
2. What the law says (include exact statutory text in a styled box)
3. Plain English explanation
4. Real case or example
5. Expert corner (for CA professionals — nuances and litigation tips)
6. Three actionable takeaways
7. Quiz question with 4 options and the correct answer

WRITING STYLE:
- Conversational but authoritative
- Plain English — no unexplained jargon
- Include rupee amounts and Indian examples
- Reference actual sections and case names

Return ONLY valid JSON with these exact keys (no markdown, no code blocks):
{{
  "title": "Compelling title max 80 chars",
  "category": "GST Updates OR Income Tax OR FEMA & RBI OR Companies Act",
  "excerpt": "One sentence summary max 155 chars",
  "meta_description": "SEO meta description max 155 chars",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "content": "Complete HTML post content with inline styles"
}}

For the HTML content, use these styled boxes with inline styles:

LAW BOX:
<div style="background:#f0ebff;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0">
<div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#3a0ca3;margin-bottom:8px">📜 BARE ACT</div>
<p style="font-size:14px;font-style:italic;color:#1a0533;margin:0;line-height:1.75">Section text here</p>
</div>

EXPERT BOX:
<div style="background:#E1F5EE;border-left:4px solid #085041;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0">
<div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#085041;margin-bottom:10px">🎯 EXPERT CORNER</div>
<p style="font-size:14px;color:#173404;line-height:1.75;margin:0">Expert content here</p>
</div>

TAKEAWAYS BOX:
<div style="background:#EAF3DE;border-left:4px solid #3B6D11;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0">
<div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#3B6D11;margin-bottom:12px">✅ THREE THINGS TO DO THIS WEEK</div>
<p style="font-size:14px;color:#333;line-height:1.8;margin:0">1. Action one<br>2. Action two<br>3. Action three</p>
</div>

QUIZ BOX:
<div style="background:#EEEDFE;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:20px;margin:28px 0">
<div style="font-size:11px;font-weight:700;letter-spacing:1px;color:#3a0ca3;margin-bottom:12px">🧩 QUICK QUIZ</div>
<p style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:14px">Question here?</p>
<p style="font-size:14px;color:#333;margin-bottom:6px">A. Option one</p>
<p style="font-size:14px;color:#333;margin-bottom:6px">B. Option two</p>
<p style="font-size:14px;color:#333;margin-bottom:6px">C. Option three</p>
<p style="font-size:14px;color:#333;margin-bottom:14px">D. Option four</p>
<p style="font-size:14px;font-weight:700;color:#3B6D11;margin-bottom:6px">Answer: B — Correct option</p>
<p style="font-size:13px;color:#555;margin:0">Explanation here</p>
</div>

AUTHOR BOX (add at the very end of content):
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;border-radius:0 12px 12px 0;padding:22px 24px;margin-top:40px;display:flex;gap:16px;align-items:flex-start">
<div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#3a0ca3,#7209b7);display:flex;align-items:center;justify-content:center;color:#fff;font-size:16px;font-weight:800;flex-shrink:0">SS</div>
<div>
<div style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:4px">CA Siddharth S. Sancheti</div>
<div style="font-size:14px;color:#7209b7;font-weight:500;margin-bottom:8px">Practising Chartered Accountant · Mumbai, India</div>
<div style="font-size:14px;color:#555;line-height:1.7">Founder & Partner, S S Sancheti & Associates, Chartered Accountants, Mumbai. Specialises in GST advisory, Income Tax litigation, FEMA compliance, and Companies Act matters.</div>
</div>
</div>"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json"
        }
    }

    r = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        timeout=120
    )

    if r.status_code != 200:
        raise Exception(f"Gemini API error {r.status_code}: {r.text[:500]}")

    data = r.json()
    raw = data["candidates"][0]["content"]["parts"][0]["text"]

    # Clean and parse
    clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()

    post_data = json.loads(clean)
    log(f"✅ Post generated: '{post_data.get('title', '')}'")
    return post_data

# ── PUBLISH AS DRAFT ──────────────────────────────────────────────────────
def get_tag_ids(tag_names):
    ids = []
    for name in (tag_names or [])[:5]:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags",
                         params={"search": name}, auth=wp_auth(), timeout=15)
        if r.status_code == 200 and r.json():
            ids.append(r.json()[0]['id'])
        else:
            r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags",
                                json={"name": name}, auth=wp_auth(), timeout=15)
            if r2.status_code == 201:
                ids.append(r2.json()['id'])
    return ids

def publish_draft(post_data):
    cat_name = post_data.get("category", "GST Updates")
    cat_id   = CATEGORY_IDS.get(cat_name)
    tag_ids  = get_tag_ids(post_data.get("tags", []))

    wp_post = {
        "title":      post_data["title"],
        "content":    post_data["content"],
        "excerpt":    post_data.get("excerpt", ""),
        "status":     "draft",          # ← DRAFT — not published
        "categories": [cat_id] if cat_id else [],
        "tags":       tag_ids,
    }

    log("Saving draft to WordPress...")
    r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts",
                      json=wp_post, auth=wp_auth(), timeout=30)

    if r.status_code not in (200, 201):
        raise Exception(f"WordPress error {r.status_code}: {r.text[:300]}")

    resp = r.json()
    post_id  = resp["id"]
    edit_url = f"{WP_URL}/wp-admin/post.php?post={post_id}&action=edit"
    log(f"✅ Draft saved — Post ID: {post_id}")
    return post_id, edit_url, post_data["title"], cat_name

# ── EMAIL NOTIFICATION ────────────────────────────────────────────────────
def notify(post_id, edit_url, title, category):
    if not all([GMAIL_USER, GMAIL_PASS, NOTIFY_EMAIL]):
        log("Email not configured — skipping. Add GMAIL_USER, GMAIL_PASS, NOTIFY_EMAIL.")
        return

    today = datetime.date.today().strftime("%B %d, %Y")
    all_drafts = f"{WP_URL}/wp-admin/edit.php?post_status=draft&post_type=post"

    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;border-radius:12px;overflow:hidden">
  <div style="background:#1a0533;padding:24px 28px">
    <div style="font-size:22px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div>
    <div style="font-size:11px;color:#c084fc;letter-spacing:1.5px;margin-top:2px">TAX INTELLIGENCE HUB</div>
  </div>
  <div style="background:#fff;padding:28px;border:1px solid #e8e4f7;border-top:none">
    <h2 style="color:#1a0533;font-size:19px;margin:0 0 18px">📝 Today's draft is ready for your review</h2>
    <div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px 18px;border-radius:0 10px 10px 0;margin-bottom:22px">
      <div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:8px">{category.upper()} · {today}</div>
      <div style="font-size:17px;font-weight:700;color:#1a0533;line-height:1.4">{title}</div>
    </div>
    <p style="color:#555;font-size:15px;line-height:1.7;margin:0 0 22px">
      Your morning digest has been generated and saved as a <strong>draft</strong>. 
      It is <strong>not visible</strong> to site visitors yet. 
      Review it, make any edits, and click <strong>Publish</strong> when ready.
    </p>
    <a href="{edit_url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:13px 26px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;margin-right:10px">
      Review &amp; Publish →
    </a>
    <a href="{all_drafts}" style="display:inline-block;background:transparent;color:#3a0ca3;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;border:2px solid #3a0ca3">
      All drafts
    </a>
    <div style="margin-top:24px;background:#faf5ff;border-radius:8px;padding:14px 16px;font-size:13px;color:#666">
      <strong>Post ID:</strong> {post_id} &nbsp;·&nbsp;
      <strong>Category:</strong> {category} &nbsp;·&nbsp;
      <strong>Status:</strong> Draft
    </div>
  </div>
  <div style="background:#f8f5ff;padding:16px;text-align:center;font-size:12px;color:#999">
    Finoscape Auto-Publisher · {today} · Powered by Google Gemini (free)
  </div>
</div>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📝 Finoscape Draft Ready — {today}: {title[:45]}..."
    msg["From"]    = f"Finoscape <{GMAIL_USER}>"
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    log(f"✅ Notification sent to {NOTIFY_EMAIL}")

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    log("=" * 55)
    log("Finoscape Auto-Publisher (FREE — Google Gemini)")
    log(f"Site: {WP_URL}")
    log("=" * 55)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Get free key at aistudio.google.com")
    if not WP_APP_PASS:
        raise ValueError("WP_APP_PASS not set.")

    load_categories()
    post_data = generate_post()
    post_id, edit_url, title, category = publish_draft(post_data)
    notify(post_id, edit_url, title, category)

    log("=" * 55)
    log("✅ COMPLETE")
    log(f"   Title:    {title}")
    log(f"   Category: {category}")
    log(f"   Status:   DRAFT — awaiting your review")
    log(f"   Edit:     {edit_url}")
    log("=" * 55)

if __name__ == "__main__":
    main()
