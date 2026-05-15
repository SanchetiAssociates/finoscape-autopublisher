import os,json,requests,smtplib,datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
WP_URL=os.environ.get("WP_URL","https://finoscape.com")
WP_USER=os.environ.get("WP_USER","finoscapehuf")
WP_APP_PASS=os.environ.get("WP_APP_PASS","")
GROQ_KEY=os.environ.get("GROQ_API_KEY","")
NOTIFY_EMAIL=os.environ.get("NOTIFY_EMAIL","")
GMAIL_USER=os.environ.get("GMAIL_USER","")
GMAIL_PASS=os.environ.get("GMAIL_PASS","")

def log(m):print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}")
def wp_auth():return(WP_USER,WP_APP_PASS)

def get_cats():
    cats={}
    r=requests.get(f"{WP_URL}/wp-json/wp/v2/categories?per_page=50",auth=wp_auth(),timeout=30)
    if r.status_code==200:
        for c in r.json():cats[c['name']]=c['id']
    log(f"Categories:{list(cats.keys())}")
    return cats

def fetch_news():
    import re
    news=[]
    for t in["GST India tax 2026","Income Tax CBDT India 2026","FEMA RBI India 2026","Companies Act MCA India 2026"]:
        try:
            r=requests.get(f"https://news.google.com/rss/search?q={t.replace(' ','+')}&hl=en-IN&gl=IN",timeout=10,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200:
                titles=re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>',r.text)[:3]
                news.extend(titles)
        except:pass
    result="\n".join(news[:12])
    log(f"News:{len(result)} chars")
    return result if result else "Write about the latest Indian GST or Income Tax developments in May 2026."

def generate(news):
    today=datetime.date.today().strftime("%B %d, %Y")
    log(f"Calling Groq for {today}...")

    prompt=f"""You are the editor of Finoscape — India's Tax Intelligence Hub. Today is {today}.

Recent Indian tax/law headlines:
{news}

Write ONE complete, polished morning digest blog post about the MOST IMPORTANT development above.

CRITICAL RULES:
- Return ONLY valid JSON. No markdown. No code blocks. No explanatory text outside JSON.
- The "content" field must be complete, valid HTML with ONLY inline styles (no CSS classes).
- Do NOT include any labels like "Hook Story:", "Law box:", "Expert box:", "Author:" — these labels must NEVER appear.
- Every section must start directly with its HTML element.
- The post must be publication-ready with no placeholders.

REQUIRED POST STRUCTURE (write directly in HTML, no section labels):

1. Opening hook paragraph — a real scenario in 2-3 vivid sentences. Start directly with <p style="font-size:17px;color:#333;line-height:1.8;margin-bottom:20px">

2. What the Law Says heading + law box:
<h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">What the Law Actually Says</h2>
<div style="background:#f0ebff;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:8px">BARE ACT</div><p style="font-size:14px;font-style:italic;color:#1a0533;margin:0;line-height:1.75">ACTUAL SECTION TEXT HERE</p></div>

3. Plain English explanation heading + paragraphs:
<h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">What This Means for You</h2>

4. Real example heading + content:
<h2 style="font-size:26px;font-weight:700;color:#3a0ca3;border-bottom:2px solid #e8e4f7;padding-bottom:8px;margin:32px 0 16px">A Real Example</h2>

5. Expert corner box (NO label text before it):
<div style="background:#E1F5EE;border-left:4px solid #085041;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#085041;letter-spacing:1px;margin-bottom:10px">EXPERT CORNER — FOR CA PROFESSIONALS</div><p style="font-size:14px;color:#173404;line-height:1.75;margin:0">EXPERT INSIGHTS HERE</p></div>

6. Takeaways box (NO label text before it):
<div style="background:#EAF3DE;border-left:4px solid #3B6D11;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3B6D11;letter-spacing:1px;margin-bottom:12px">THREE THINGS TO DO THIS WEEK</div><p style="font-size:14px;color:#333;line-height:1.9;margin:0">1. FIRST ACTION<br><br>2. SECOND ACTION<br><br>3. THIRD ACTION</p></div>

7. Interactive quiz (NO label text before it — use EXACTLY this HTML structure with the correct answer pre-filled):
<div style="background:#EEEDFE;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:24px;margin:32px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px;margin-bottom:14px">QUICK QUIZ — TEST YOURSELF</div><p style="font-size:17px;font-weight:700;color:#1a0533;margin-bottom:18px;line-height:1.4">QUESTION TEXT HERE?</p><div id="q1" style="display:flex;flex-direction:column;gap:10px"><div onclick="ansQ(this,'wrong')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer;transition:all .15s">A. OPTION A</div><div onclick="ansQ(this,'correct')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer;transition:all .15s">B. OPTION B (CORRECT)</div><div onclick="ansQ(this,'wrong')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer;transition:all .15s">C. OPTION C</div><div onclick="ansQ(this,'wrong')" style="background:#fff;border:1.5px solid #c5c1f5;border-radius:10px;padding:12px 16px;font-size:14px;color:#333;cursor:pointer;transition:all .15s">D. OPTION D</div></div><div id="qans" style="display:none;margin-top:16px;background:#EAF3DE;border-radius:10px;padding:14px 16px"><div style="font-size:12px;font-weight:700;color:#3B6D11;margin-bottom:6px">CORRECT ANSWER EXPLANATION HERE</div></div></div><script>function ansQ(el,type){if(document.querySelector('[data-answered]'))return;el.setAttribute('data-answered','1');document.querySelectorAll('#q1>div').forEach(function(o){o.style.pointerEvents='none';o.style.opacity='0.6'});if(type==='correct'){el.style.background='#EAF3DE';el.style.borderColor='#3B6D11';el.style.color='#3B6D11';el.style.fontWeight='700';el.style.opacity='1'}else{el.style.background='#FCEBEB';el.style.borderColor='#F09595';el.style.color='#A32D2D';el.style.opacity='1';document.querySelectorAll('#q1>div').forEach(function(o){if(o.getAttribute('onclick')&&o.getAttribute('onclick').includes('correct')){o.style.background='#EAF3DE';o.style.borderColor='#3B6D11';o.style.color='#3B6D11';o.style.opacity='1'}})}document.getElementById('qans').style.display='block'}</script>

8. Author box at the very end (NO label text — start directly with the div):
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;border-radius:0 12px 12px 0;padding:22px 24px;margin-top:48px;display:flex;gap:16px;align-items:flex-start"><div style="width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#3a0ca3,#7209b7);color:#fff;font-size:18px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">SS</div><div><div style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:4px">CA Siddharth S. Sancheti</div><div style="font-size:14px;color:#7209b7;font-weight:500;margin-bottom:8px">Practising Chartered Accountant · Mumbai, India</div><div style="font-size:14px;color:#555;line-height:1.7">Founder, S S Sancheti and Associates, Chartered Accountants, Mumbai. Expert in GST advisory, Income Tax litigation, FEMA compliance, and Companies Act matters.</div></div></div>

Return ONLY this JSON (no other text):
{{"title":"Compelling post title — max 80 chars, no quotes","category":"GST Updates OR Income Tax OR FEMA & RBI OR Companies Act","excerpt":"One punchy sentence describing the post — max 155 chars","tags":["tag1","tag2","tag3","tag4","tag5"],"content":"COMPLETE HTML with all 8 sections above, no section labels, all inline styles"}}"""

    r=requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
        json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],
              "temperature":0.7,"max_tokens":4000,"response_format":{"type":"json_object"}},timeout=120)
    if r.status_code!=200:raise Exception(f"Groq error {r.status_code}:{r.text[:300]}")
    raw=r.json()["choices"][0]["message"]["content"]
    data=json.loads(raw.strip())
    log(f"Generated:{data.get('title','')}")
    return data

def get_tag_ids(names):
    ids=[]
    for name in(names or[])[:5]:
        r=requests.get(f"{WP_URL}/wp-json/wp/v2/tags",params={"search":name},auth=wp_auth(),timeout=15)
        if r.status_code==200 and r.json():ids.append(r.json()[0]['id'])
        else:
            r2=requests.post(f"{WP_URL}/wp-json/wp/v2/tags",json={"name":name},auth=wp_auth(),timeout=15)
            if r2.status_code==201:ids.append(r2.json()['id'])
    return ids

def save_draft(data,cats):
    cid=cats.get(data.get("category","GST Updates"))
    wp={"title":data["title"],"content":data["content"],"excerpt":data.get("excerpt",""),
        "status":"draft","categories":[cid]if cid else[],"tags":get_tag_ids(data.get("tags",[]))}
    r=requests.post(f"{WP_URL}/wp-json/wp/v2/posts",json=wp,auth=wp_auth(),timeout=30)
    if r.status_code not in(200,201):raise Exception(f"WP error {r.status_code}:{r.text[:200]}")
    pid=r.json()["id"]
    url=f"{WP_URL}/wp-admin/post.php?post={pid}&action=edit"
    log(f"Draft saved ID:{pid}")
    return pid,url

def notify(pid,url,title,cat):
    if not all([GMAIL_USER,GMAIL_PASS,NOTIFY_EMAIL]):log("Email skipped");return
    today=datetime.date.today().strftime("%B %d, %Y")
    html=f'<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto"><div style="background:#1a0533;padding:20px 24px;border-radius:10px 10px 0 0"><div style="font-size:20px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div><div style="font-size:11px;color:#c084fc;letter-spacing:1.5px">TAX INTELLIGENCE HUB</div></div><div style="background:#fff;padding:28px;border:1px solid #e8e4f7;border-top:none;border-radius:0 0 10px 10px"><h2 style="color:#1a0533;font-size:18px;margin:0 0 16px">Your draft is ready for review</h2><div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px;border-radius:0 10px 10px 0;margin-bottom:20px"><div style="font-size:11px;font-weight:700;color:#3a0ca3;letter-spacing:1px">{cat.upper()} · {today}</div><div style="font-size:17px;font-weight:700;color:#1a0533;margin-top:6px">{title}</div></div><p style="color:#555;font-size:15px;line-height:1.7;margin:0 0 20px">Saved as <strong>draft</strong>. Not visible to visitors yet. Review and publish when happy.</p><a href="{url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:13px 26px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">Review and Publish →</a><p style="font-size:12px;color:#999;margin-top:16px">Post ID: {pid} | Status: Draft | {today}</p></div></div>'
    msg=MIMEMultipart("alternative")
    msg["Subject"]=f"Finoscape Draft Ready — {today}: {title[:45]}"
    msg["From"]=f"Finoscape <{GMAIL_USER}>"
    msg["To"]=NOTIFY_EMAIL
    msg.attach(MIMEText(html,"html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465)as s:
            s.login(GMAIL_USER,GMAIL_PASS);s.send_message(msg)
        log(f"Email sent to {NOTIFY_EMAIL}")
    except Exception as e:log(f"Email error:{e}")

def main():
    log("="*55)
    log("Finoscape Auto-Publisher — Groq FREE")
    log("="*55)
    if not GROQ_KEY:raise ValueError("GROQ_API_KEY not set")
    if not WP_APP_PASS:raise ValueError("WP_APP_PASS not set")
    cats=get_cats()
    news=fetch_news()
    data=generate(news)
    pid,url=save_draft(data,cats)
    notify(pid,url,data["title"],data.get("category","GST Updates"))
    log("="*55)
    log(f"DONE — Draft {pid} ready for review")
    log(f"Edit: {url}")
    log("="*55)

if __name__=="__main__":main()
