import os, json, requests, smtplib, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

WP_URL      = os.environ.get("WP_URL", "https://finoscape.com")
WP_USER     = os.environ.get("WP_USER", "finoscapehuf")
WP_APP_PASS = os.environ.get("WP_APP_PASS", "")
GROQ_KEY    = os.environ.get("GROQ_API_KEY", "")
NOTIFY_EMAIL= os.environ.get("NOTIFY_EMAIL", "")
GMAIL_USER  = os.environ.get("GMAIL_USER", "")
GMAIL_PASS  = os.environ.get("GMAIL_PASS", "")

def log(m): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}")

def wp_auth(): return (WP_USER, WP_APP_PASS)

def get_categories():
    cats = {}
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=50", auth=wp_auth(), timeout=30)
    if r.status_code == 200:
        for c in r.json(): cats[c['name']] = c['id']
    log(f"Categories: {list(cats.keys())}")
    return cats

def fetch_news():
    today = datetime.date.today().strftime("%B %d %Y")
    topics = ["GST India tax 2026", "Income Tax India CBDT 2026", "FEMA RBI India 2026", "Companies Act MCA India 2026"]
    news = []
    for topic in topics:
        try:
            url = f"https://news.google.com/rss/search?q={topic.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                import re
                titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)[:3]
                news.extend(titles)
        except: pass
    return "\n".join(news[:12]) if news else "No news fetched — write based on current Indian tax law developments."

def generate_post(news_context):
    today = datetime.date.today().strftime("%B %d, %Y")
    log("Calling Groq API (free)...")

    prompt = f"""You are the editor of Finoscape — India's Tax Intelligence Hub.
Today is {today}.

Recent Indian tax/law news headlines:
{news_context}

Write a complete morning digest blog post about the most significant development above.
Pick ONE topic from: GST, Income Tax, FEMA & RBI, or Companies Act.

Structure the post with these HTML sections:
1. Hook opening paragraph (real scenario, 2-3 sentences)
2. <h2>What the Law Says</h2> with this law box:
<div style="background:#f0ebff;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;margin-bottom:8px">BARE ACT</div><p style="font-size:14px;font-style:italic;color:#1a0533;margin:0;line-height:1.75">Exact section text here</p></div>
3. <h2>Plain English Explanation</h2>
4. <h2>Real Example</h2>
5. <h2>Expert Corner</h2> with this box:
<div style="background:#E1F5EE;border-left:4px solid #085041;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#085041;margin-bottom:8px">EXPERT CORNER</div><p style="font-size:14px;color:#173404;line-height:1.75;margin:0">Expert insights here</p></div>
6. Three takeaways:
<div style="background:#EAF3DE;border-left:4px solid #3B6D11;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3B6D11;margin-bottom:12px">THREE THINGS TO DO</div><p style="font-size:14px;color:#333;line-height:1.8;margin:0">1. First action<br>2. Second action<br>3. Third action</p></div>
7. Quiz:
<div style="background:#EEEDFE;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:20px;margin:28px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;margin-bottom:12px">QUICK QUIZ</div><p style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:14px">Question?</p><p style="font-size:14px;color:#333">A. Option<br>B. Option<br>C. Option<br>D. Option</p><p style="font-size:14px;font-weight:700;color:#3B6D11;margin-top:12px">Answer: B — explanation</p></div>
8. Author box at the very end:
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;border-radius:0 12px 12px 0;padding:22px 24px;margin-top:40px"><div style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:4px">CA Siddharth S. Sancheti</div><div style="font-size:14px;color:#7209b7;font-weight:500;margin-bottom:8px">Practising Chartered Accountant · Mumbai, India</div><div style="font-size:14px;color:#555;line-height:1.7">Founder, S S Sancheti & Associates. Specialises in GST, Income Tax, FEMA, and Companies Act.</div></div>

Return ONLY valid JSON, no markdown:
{{"title":"compelling title max 80 chars","category":"GST Updates OR Income Tax OR FEMA & RBI OR Companies Act","excerpt":"one sentence max 155 chars","tags":["tag1","tag2","tag3","tag4","tag5"],"content":"complete HTML post"}}"""

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.7, "max_tokens": 4000, "response_format": {"type": "json_object"}},
        timeout=120
    )
    if r.status_code != 200:
        raise Exception(f"Groq API error {r.status_code}: {r.text[:300]}")
    
    raw = r.json()["choices"][0]["message"]["content"]
    data = json.loads(raw.strip())
    log(f"Post generated: '{data.get('title','')}'")
    return data

def get_tag_ids(names):
    ids = []
    for name in (names or [])[:5]:
        r = requests.get(f"{WP_URL}/wp-json/wp/v2/tags", params={"search": name}, auth=wp_auth(), timeout=15)
        if r.status_code == 200 and r.json():
            ids.append(r.json()[0]['id'])
        else:
            r2 = requests.post(f"{WP_URL}/wp-json/wp/v2/tags", json={"name": name}, auth=wp_auth(), timeout=15)
            if r2.status_code == 201: ids.append(r2.json()['id'])
    return ids

def publish_draft(post_data, cats):
    cat_id = cats.get(post_data.get("category", "GST Updates"))
    wp = {"title": post_data["title"], "content": post_data["content"],
          "excerpt": post_data.get("excerpt", ""), "status": "draft",
          "categories": [cat_id] if cat_id else [],
          "tags": get_tag_ids(post_data.get("tags", []))}
    log("Saving draft to WordPress...")
    r = requests.post(f"{WP_URL}/wp-json/wp/v2/posts", json=wp, auth=wp_auth(), timeout=30)
    if r.status_code not in (200, 201):
        raise Exception(f"WordPress error {r.status_code}: {r.text[:200]}")
    pid = r.json()["id"]
    edit_url = f"{WP_URL}/wp-admin/post.php?post={pid}&action=edit"
    log(f"Draft saved — ID: {pid}")
    return pid, edit_url

def notify(pid, edit_url, title, category):
    if not all([GMAIL_USER, GMAIL_PASS, NOTIFY_EMAIL]): 
        log("Email skipped — not configured")
        return
    today = datetime.date.today().strftime("%B %d, %Y")
    html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
<div style="background:#1a0533;padding:20px 24px;border-radius:10px 10px 0 0">
<div style="font-size:20px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div>
</div>
<div style="background:#fff;padding:28px;border:1px solid #e8e4f7;border-top:none">
<h2 style="color:#1a0533;font-size:18px;margin:0 0 16px">📝 Today's draft is ready for review</h2>
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px;border-radius:0 10px 10px 0;margin-bottom:20px">
<div style="font-size:11px;font-weight:700;color:#3a0ca3;margin-bottom:8px">{category.upper()} · {today}</div>
<div style="font-size:17px;font-weight:700;color:#1a0533">{title}</div>
</div>
<p style="color:#555;font-size:15px;line-height:1.7;margin:0 0 20px">Saved as <strong>draft</strong> — not visible to visitors. Review and publish when ready.</p>
<a href="{edit_url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:13px 26px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">Review &amp; Publish →</a>
</div>
<div style="background:#f8f5ff;padding:14px;border-radius:0 0 10px 10px;text-align:center;font-size:12px;color:#999">
Finoscape Auto-Publisher · {today} · Powered by Groq (free)
</div></div>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📝 Finoscape Draft Ready — {today}"
    msg["From"] = f"Finoscape <{GMAIL_USER}>"
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        log(f"Email sent to {NOTIFY_EMAIL}")
    except Exception as e:
        log(f"Email failed: {e}")

def main():
    log("="*50)
    log("Finoscape Auto-Publisher — Groq (FREE)")
    if not GROQ_KEY: raise ValueError("GROQ_API_KEY not set")
    if not WP_APP_PASS: raise ValueError("WP_APP_PASS not set")
    cats = get_categories()
    news = fetch_news()
    log(f"News fetched: {len(news)} chars")
    post_data = generate_post(news)
    pid, edit_url = publish_draft(post_data, cats)
    notify(pid, edit_url, post_data["title"], post_data.get("category","GST Updates"))
    log("="*50)
    log(f"DONE — Draft ID {pid} ready for review")
    log(f"Edit: {edit_url}")
    log("="*50)

if __name__ == "__main__":
    main()
