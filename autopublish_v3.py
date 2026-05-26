import os,json,requests,smtplib,datetime,re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

WP_URL      = os.environ.get("WP_URL","https://finoscape.com")
WP_USER     = os.environ.get("WP_USER","finoscapehuf")
WP_APP_PASS = os.environ.get("WP_APP_PASS","")
GROQ_KEY    = os.environ.get("GROQ_API_KEY","")
NOTIFY_EMAIL= os.environ.get("NOTIFY_EMAIL","")
GMAIL_USER  = os.environ.get("GMAIL_USER","")
GMAIL_PASS  = os.environ.get("GMAIL_PASS","")

def log(m): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}")
def wp_auth(): return (WP_USER, WP_APP_PASS)

def get_cats():
    cats={}
    r=requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=50",auth=wp_auth(),timeout=30)
    if r.status_code==200:
        for c in r.json(): cats[c['name']]=c['id']
    log(f"Categories: {list(cats.keys())}")
    return cats

def fetch_news():
    news=[]
    for t in ["GST India 2026","Income Tax CBDT 2026","FEMA RBI India 2026","Companies Act MCA 2026"]:
        try:
            r=requests.get(f"https://news.google.com/rss/search?q={t.replace(' ','+')}&hl=en-IN&gl=IN",
                          timeout=10,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200:
                titles=re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>',r.text)[:3]
                news.extend(titles)
        except: pass
    result="\n".join(news[:12])
    log(f"News: {len(result)} chars")
    return result if result else "Write about latest Indian tax developments in 2026."

def generate(news):
    today=datetime.date.today().strftime("%B %d, %Y")
    log(f"Calling Groq for {today}...")

    prompt=f"""You are the editor of Finoscape — India's Tax Intelligence Hub. Today is {today}.

Recent Indian tax news headlines:
{news}

Generate a complete Finoscape morning post AND a newsletter digest for the same story.

Return ONLY valid JSON with these exact keys:

{{
  "title": "Compelling post title max 80 chars",
  "category": "GST Updates OR Income Tax OR FEMA & RBI OR Companies Act",
  "excerpt": "One punchy sentence max 155 chars",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "content": "FULL HTML POST — complete article with all sections below",
  "newsletter_subject": "Email subject line max 60 chars",
  "newsletter_headline": "One punchy headline for the newsletter",
  "newsletter_summary": "2-3 sentence plain English summary for newsletter teaser — ends with a hook that makes reader want to read more",
  "newsletter_actions": "3 bullet actions as plain text separated by | character",
  "newsletter_puzzle_q": "One quiz question for the newsletter",
  "newsletter_puzzle_opts": "4 options separated by | character e.g. A. opt1 | B. opt2 | C. opt3 | D. opt4",
  "newsletter_puzzle_answer": "Just the letter e.g. B"
}}

For the FULL HTML POST content field, write complete HTML with NO section labels, ALL inline styles:

1. Opening hook: <p style="font-size:17px;color:#333;line-height:1.8;margin-bottom:20px">vivid opening scenario</p>

2. <h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">What the Law Actually Says</h2>
<div style="background:#f0ebff;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:8px">BARE ACT</div><p style="font-size:14px;font-style:italic;color:#1a0533;margin:0;line-height:1.75">actual section text</p></div>

3. <h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">What This Means for You</h2>
<p style="font-size:16px;color:#444;line-height:1.8;margin-bottom:16px">plain English explanation paragraphs</p>

4. <h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">A Real Example</h2>

5. Expert corner: <div style="background:#E1F5EE;border-left:4px solid #085041;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#085041;letter-spacing:1px;margin-bottom:10px">EXPERT CORNER</div><p style="font-size:14px;color:#173404;line-height:1.75;margin:0">expert insights for CAs</p></div>

6. Takeaways: <div style="background:#EAF3DE;border-left:4px solid #3B6D11;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3B6D11;letter-spacing:1px;margin-bottom:12px">THREE THINGS TO DO THIS WEEK</div><p style="font-size:14px;color:#333;line-height:1.9;margin:0">1. action<br><br>2. action<br><br>3. action</p></div>

7. Interactive quiz: <div style="background:#EEEDFE;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:24px;margin:32px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:14px">QUICK QUIZ</div><p style="font-size:17px;font-weight:700;color:#1a0533;margin-bottom:18px;line-height:1.4">question?</p><div id="q1" style="display:flex;flex-direction:column;gap:10px"><div onclick="ansQ(this,'w')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer">A. option</div><div onclick="ansQ(this,'c')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer">B. correct option</div><div onclick="ansQ(this,'w')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer">C. option</div><div onclick="ansQ(this,'w')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer">D. option</div></div><div id="qans" style="display:none;margin-top:16px;background:#EAF3DE;border-radius:10px;padding:14px"><div style="font-size:12px;font-weight:700;color:#3B6D11;margin-bottom:6px">CORRECT ANSWER: explanation</div></div></div><script>function ansQ(el,t){{if(document.querySelector('[data-done]'))return;el.setAttribute('data-done','1');document.querySelectorAll('#q1>div').forEach(function(o){{o.style.pointerEvents='none';o.style.opacity='0.6'}});if(t==='c'){{el.style.background='#EAF3DE';el.style.borderColor='#3B6D11';el.style.color='#3B6D11';el.style.fontWeight='700';el.style.opacity='1'}}else{{el.style.background='#FCEBEB';el.style.borderColor='#F09595';el.style.color='#A32D2D';el.style.opacity='1';document.querySelectorAll('#q1>div').forEach(function(o){{if(o.getAttribute('onclick')&&o.getAttribute('onclick').includes("'c'")){{o.style.background='#EAF3DE';o.style.borderColor='#3B6D11';o.style.opacity='1'}}}})}};document.getElementById('qans').style.display='block'}}</script>

8. Author box at the end: <div style="background:#f3e8ff;border-left:4px solid #3a0ca3;border-radius:0 12px 12px 0;padding:22px 24px;margin-top:48px;display:flex;gap:16px;align-items:flex-start"><div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#3a0ca3,#7209b7);color:#fff;font-size:18px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">SS</div><div><div style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:4px">CA Siddharth S. Sancheti</div><div style="font-size:14px;color:#7209b7;font-weight:500;margin-bottom:8px">Practising Chartered Accountant · Mumbai, India</div><div style="font-size:14px;color:#555;line-height:1.7">Founder, S S Sancheti and Associates, Chartered Accountants, Mumbai.</div></div></div>"""

    r=requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
        json={"model":"llama-3.3-70b-versatile",
              "messages":[{"role":"user","content":prompt}],
              "temperature":0.7,"max_tokens":4000,
              "response_format":{"type":"json_object"}},timeout=120)
    if r.status_code!=200: raise Exception(f"Groq error {r.status_code}:{r.text[:300]}")
    data=json.loads(r.json()["choices"][0]["message"]["content"])
    log(f"Generated: '{data.get('title','')}'")
    return data

def get_tag_ids(names):
    ids=[]
    for name in (names or[])[:5]:
        r=requests.get(f"{WP_URL}/wp-json/wp/v2/tags",params={"search":name},auth=wp_auth(),timeout=15)
        if r.status_code==200 and r.json(): ids.append(r.json()[0]['id'])
        else:
            r2=requests.post(f"{WP_URL}/wp-json/wp/v2/tags",json={"name":name},auth=wp_auth(),timeout=15)
            if r2.status_code==201: ids.append(r2.json()['id'])
    return ids

def save_draft(data, cats):
    cid=cats.get(data.get("category","GST Updates"))
    wp={"title":data["title"],"content":data["content"],
        "excerpt":data.get("excerpt",""),"status":"draft",
        "categories":[cid] if cid else [],
        "tags":get_tag_ids(data.get("tags",[]))}
    r=requests.post(f"{WP_URL}/wp-json/wp/v2/posts",json=wp,auth=wp_auth(),timeout=30)
    if r.status_code not in(200,201): raise Exception(f"WP error {r.status_code}:{r.text[:200]}")
    pid=r.json()["id"]
    post_url=r.json().get("link","")
    edit_url=f"{WP_URL}/wp-admin/post.php?post={pid}&action=edit"
    log(f"Draft saved — ID:{pid}")
    return pid, edit_url, post_url

def build_newsletter_html(data, post_url, issue_num, today_str):
    """Build beautiful Finoscape-branded newsletter HTML"""
    actions = data.get("newsletter_actions","").split("|")
    opts = data.get("newsletter_puzzle_opts","A. — | B. — | C. — | D. —").split("|")
    answer_letter = data.get("newsletter_puzzle_answer","B")

    opts_html = ""
    for opt in opts:
        opts_html += f'<div style="background:#f8f5ff;border:1px solid #e8e4f7;border-radius:8px;padding:10px 14px;font-size:14px;color:#333;margin-bottom:8px">{opt.strip()}</div>'

    actions_html = ""
    for i, action in enumerate(actions[:3], 1):
        if action.strip():
            actions_html += f'<div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:12px"><div style="width:24px;height:24px;border-radius:50%;background:#3a0ca3;color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{i}</div><p style="font-size:14px;color:#444;line-height:1.6;margin:0">{action.strip()}</p></div>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Finoscape Daily Digest — {today_str}</title>
</head>
<body style="margin:0;padding:0;background:#f0ebff;font-family:'Helvetica Neue',Arial,sans-serif">
<div style="max-width:620px;margin:0 auto;padding:20px">

<!-- HEADER -->
<div style="background:linear-gradient(135deg,#1a0533,#3a0ca3);border-radius:16px 16px 0 0;padding:28px 32px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
    <div>
      <div style="font-size:26px;font-weight:800;color:#fff;letter-spacing:-.5px">fino<span style="color:#c084fc">scape</span></div>
      <div style="font-size:10px;color:#c084fc;letter-spacing:2px;font-weight:600;margin-top:2px">TAX INTELLIGENCE HUB</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:11px;color:rgba(255,255,255,.6);letter-spacing:.5px">ISSUE #{issue_num}</div>
      <div style="font-size:13px;color:rgba(255,255,255,.8);font-weight:500;margin-top:2px">{today_str}</div>
    </div>
  </div>
  <div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,.15)">
    <div style="font-size:18px;font-weight:700;color:#fff;line-height:1.35">{data.get('newsletter_headline','Today\'s Tax Intelligence Digest')}</div>
  </div>
</div>

<!-- BODY -->
<div style="background:#fff;padding:28px 32px">

  <!-- TODAY'S STORY -->
  <div style="margin-bottom:24px">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
      <div style="width:3px;height:20px;background:#3a0ca3;border-radius:2px"></div>
      <div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;text-transform:uppercase">{data.get('category','GST Updates')} · Today's Focus</div>
    </div>
    <h2 style="font-size:20px;font-weight:800;color:#1a0533;line-height:1.3;margin:0 0 12px">{data.get('title','')}</h2>
    <p style="font-size:15px;color:#555;line-height:1.75;margin:0 0 16px">{data.get('newsletter_summary','')}</p>
    <a href="{post_url}" style="display:inline-flex;align-items:center;gap:6px;background:#3a0ca3;color:#fff;font-size:14px;font-weight:600;padding:10px 20px;border-radius:8px;text-decoration:none">Read full analysis on Finoscape →</a>
  </div>

  <hr style="border:none;border-top:1px solid #e8e4f7;margin:24px 0">

  <!-- WHAT TO DO -->
  <div style="margin-bottom:24px">
    <div style="font-size:11px;font-weight:700;color:#3B6D11;letter-spacing:1px;text-transform:uppercase;margin-bottom:14px">✅ Three Things To Do This Week</div>
    {actions_html}
    <a href="{post_url}#takeaways" style="font-size:13px;color:#3a0ca3;text-decoration:none;font-weight:600">See full action guide on Finoscape →</a>
  </div>

  <hr style="border:none;border-top:1px solid #e8e4f7;margin:24px 0">

  <!-- PUZZLE -->
  <div style="background:#EEEDFE;border-radius:12px;padding:20px;margin-bottom:24px">
    <div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:12px">🧩 TODAY'S PUZZLE — What's the Answer?</div>
    <p style="font-size:15px;font-weight:700;color:#1a0533;margin:0 0 14px;line-height:1.4">{data.get('newsletter_puzzle_q','')}</p>
    {opts_html}
    <a href="{post_url}#quiz" style="display:inline-block;margin-top:12px;background:#3a0ca3;color:#fff;font-size:13px;font-weight:600;padding:9px 18px;border-radius:7px;text-decoration:none">Reveal answer on Finoscape →</a>
    <p style="font-size:12px;color:#888;margin:10px 0 0">Answer: {answer_letter} — but don't peek before trying! 😊</p>
  </div>

  <!-- COMPLIANCE REMINDER -->
  <div style="background:#fff8e1;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:24px">
    <div style="font-size:11px;font-weight:700;color:#b45309;letter-spacing:1px;margin-bottom:6px">📅 COMPLIANCE REMINDER</div>
    <p style="font-size:14px;color:#333;margin:0;line-height:1.6">Check your compliance calendar for this month's key deadlines — GST returns, TDS deposits, and ROC filings.</p>
    <a href="{WP_URL}/compliance-calendar/" style="font-size:13px;color:#b45309;font-weight:600;text-decoration:none">View full calendar →</a>
  </div>

</div>

<!-- FOOTER -->
<div style="background:#1a0533;border-radius:0 0 16px 16px;padding:24px 32px">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;margin-bottom:16px">
    <div>
      <div style="font-size:16px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div>
      <div style="font-size:12px;color:rgba(255,255,255,.5);margin-top:3px">India's Tax Intelligence Hub</div>
    </div>
    <div style="display:flex;gap:12px">
      <a href="{WP_URL}" style="font-size:12px;color:rgba(255,255,255,.5);text-decoration:none">Website</a>
      <a href="{WP_URL}/daily-updates/" style="font-size:12px;color:rgba(255,255,255,.5);text-decoration:none">All Updates</a>
      <a href="{WP_URL}/act-explainers/" style="font-size:12px;color:rgba(255,255,255,.5);text-decoration:none">Explainers</a>
    </div>
  </div>
  <p style="font-size:12px;color:rgba(255,255,255,.35);margin:0 0 8px;line-height:1.6">Content is for educational and informational purposes only. Does not constitute legal, tax or financial advice. Consult a qualified professional before acting on any information.</p>
  <p style="font-size:11px;color:rgba(255,255,255,.25);margin:0">Operated by Siddharth S Sancheti HUF, Mumbai, India. <a href="#" style="color:rgba(255,255,255,.4);text-decoration:none">Unsubscribe</a></p>
</div>

</div>
</body>
</html>"""

def save_newsletter_to_wordpress(html, today_str, issue_num, post_url):
    """Save newsletter as a WordPress page for archive"""
    # Find or create Newsletter Archive category page
    pages = requests.get(f"{WP_URL}/wp-json/wp/v2/pages?per_page=50", auth=wp_auth()).json()
    
    # Save this issue as a page
    page_data = {
        "title": f"Newsletter Issue #{issue_num} — {today_str}",
        "content": html,
        "status": "publish",
        "slug": f"newsletter-{datetime.date.today().strftime('%Y-%m-%d')}",
        "template": "elementor_canvas"
    }
    r = requests.post(f"{WP_URL}/wp-json/wp/v2/pages", json=page_data, auth=wp_auth(), timeout=30)
    if r.status_code in (200, 201):
        nid = r.json()["id"]
        nurl = r.json().get("link", "")
        log(f"Newsletter page saved — ID:{nid} URL:{nurl}")
        return nid, nurl
    else:
        log(f"Newsletter page save failed: {r.status_code}")
        return None, None

def get_issue_number():
    """Count existing newsletter pages to get issue number"""
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/pages",
                     params={"search": "Newsletter Issue", "per_page": 100},
                     auth=wp_auth(), timeout=20)
    if r.status_code == 200:
        return len(r.json()) + 1
    return 1

def send_notification_and_newsletter(pid, edit_url, post_url, newsletter_url, data, newsletter_html):
    """Send both admin notification AND newsletter to subscribers"""
    if not all([GMAIL_USER, GMAIL_PASS, NOTIFY_EMAIL]):
        log("Email not configured — skipping")
        return

    today = datetime.date.today().strftime("%B %d, %Y")

    # Admin notification email
    admin_html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
<div style="background:#1a0533;padding:20px 24px;border-radius:10px 10px 0 0">
<div style="font-size:20px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div>
</div>
<div style="background:#fff;padding:28px;border:1px solid #e8e4f7;border-top:none;border-radius:0 0 10px 10px">
<h2 style="color:#1a0533;font-size:18px">Daily draft + newsletter ready for review</h2>
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px;border-radius:0 10px 10px 0;margin-bottom:20px">
<div style="font-size:11px;font-weight:700;color:#3a0ca3">{data.get('category','').upper()} · {today}</div>
<div style="font-size:17px;font-weight:700;color:#1a0533;margin-top:6px">{data.get('title','')}</div>
</div>
<p style="color:#555;font-size:15px;line-height:1.7;margin:0 0 16px">Both the full post draft and the newsletter are ready.</p>
<a href="{edit_url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;margin-right:10px">Review Post Draft →</a>
<a href="{newsletter_url or '#'}" style="display:inline-block;background:transparent;color:#3a0ca3;padding:11px 22px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;border:2px solid #3a0ca3">View Newsletter →</a>
<div style="margin-top:16px;background:#faf5ff;border-radius:8px;padding:12px;font-size:13px;color:#666">
Post ID: {pid} | Newsletter saved to archive<br>
<strong>Action needed:</strong> Review post → Publish → Then send newsletter to subscribers
</div>
</div></div>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Finoscape Draft + Newsletter Ready — {today}"
    msg["From"] = f"Finoscape <{GMAIL_USER}>"
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(admin_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        log(f"Admin notification sent to {NOTIFY_EMAIL}")
    except Exception as e:
        log(f"Email error: {e}")

def main():
    log("="*55)
    log("Finoscape Auto-Publisher v3 — Post + Newsletter")
    log("="*55)

    if not GROQ_KEY: raise ValueError("GROQ_API_KEY not set")
    if not WP_APP_PASS: raise ValueError("WP_APP_PASS not set")

    cats = get_cats()
    news = fetch_news()
    data = generate(news)

    # Save full post as draft
    pid, edit_url, post_url = save_draft(data, cats)

    # Get issue number and generate newsletter
    issue_num = get_issue_number()
    today_str = datetime.date.today().strftime("%B %d, %Y")
    newsletter_html = build_newsletter_html(data, post_url, issue_num, today_str)

    # Save newsletter to WordPress archive
    nid, newsletter_url = save_newsletter_to_wordpress(newsletter_html, today_str, issue_num, post_url)

    # Send admin notification
    send_notification_and_newsletter(pid, edit_url, post_url, newsletter_url, data, newsletter_html)

    log("="*55)
    log(f"DONE")
    log(f"Post draft: {edit_url}")
    log(f"Newsletter: {newsletter_url}")
    log("="*55)

if __name__ == "__main__":
    main()
