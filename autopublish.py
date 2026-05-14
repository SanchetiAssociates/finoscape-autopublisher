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
    news=[]
    for t in["GST India 2026","Income Tax CBDT India 2026","FEMA RBI India 2026","Companies Act MCA 2026"]:
        try:
            import re
            r=requests.get(f"https://news.google.com/rss/search?q={t.replace(' ','+')}&hl=en-IN&gl=IN",timeout=10,headers={"User-Agent":"Mozilla/5.0"})
            if r.status_code==200:news.extend(re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>',r.text)[:3])
        except:pass
    return"\n".join(news[:12])if news else"Write about latest Indian tax developments."
def generate(news):
    today=datetime.date.today().strftime("%B %d, %Y")
    log(f"Calling Groq for {today}...")
    prompt=f"""You are the editor of Finoscape, India's Tax Intelligence Hub. Today is {today}.
News headlines:\n{news}\n
Write a complete morning digest post about the most important Indian tax/law development above.
Return ONLY valid JSON with keys: title, category (one of: GST Updates, Income Tax, FEMA & RBI, Companies Act), excerpt, tags (list of 5), content (full HTML post with inline styles including law box, expert corner, takeaways box, quiz box, and author box for CA Siddharth S. Sancheti Practising CA Mumbai).
Use purple brand color #3a0ca3 for box borders."""
    r=requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
        json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],
              "temperature":0.7,"max_tokens":4000,"response_format":{"type":"json_object"}},timeout=120)
    if r.status_code!=200:raise Exception(f"Groq error {r.status_code}:{r.text[:200]}")
    data=json.loads(r.json()["choices"][0]["message"]["content"])
    log(f"Generated: {data.get('title','')}")
    return data
def save_draft(data,cats):
    cid=cats.get(data.get("category","GST Updates"))
    r=requests.post(f"{WP_URL}/wp-json/wp/v2/posts",
        json={"title":data["title"],"content":data["content"],"excerpt":data.get("excerpt",""),
              "status":"draft","categories":[cid]if cid else[]},
        auth=wp_auth(),timeout=30)
    if r.status_code not in(200,201):raise Exception(f"WP error {r.status_code}:{r.text[:200]}")
    pid=r.json()["id"]
    url=f"{WP_URL}/wp-admin/post.php?post={pid}&action=edit"
    log(f"Draft saved ID:{pid}")
    return pid,url
def notify(pid,url,title,cat):
    if not all([GMAIL_USER,GMAIL_PASS,NOTIFY_EMAIL]):log("Email skipped");return
    today=datetime.date.today().strftime("%B %d, %Y")
    html=f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
<div style="background:#1a0533;padding:20px"><div style="font-size:20px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div></div>
<div style="background:#fff;padding:28px;border:1px solid #e8e4f7">
<h2 style="color:#1a0533">Today's draft is ready for review</h2>
<div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px;margin-bottom:20px">
<div style="font-size:11px;font-weight:700;color:#3a0ca3">{cat.upper()} · {today}</div>
<div style="font-size:17px;font-weight:700;color:#1a0533">{title}</div></div>
<p style="color:#555">Saved as draft. Review and publish when ready.</p>
<a href="{url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:13px 26px;border-radius:8px;text-decoration:none;font-weight:700">Review and Publish</a>
</div></div>"""
    msg=MIMEMultipart("alternative")
    msg["Subject"]=f"Finoscape Draft Ready - {today}"
    msg["From"]=f"Finoscape <{GMAIL_USER}>"
    msg["To"]=NOTIFY_EMAIL
    msg.attach(MIMEText(html,"html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465)as s:
            s.login(GMAIL_USER,GMAIL_PASS);s.send_message(msg)
        log(f"Email sent to {NOTIFY_EMAIL}")
    except Exception as e:log(f"Email error:{e}")
def main():
    log("="*50)
    log("Finoscape Auto-Publisher - Groq FREE")
    if not GROQ_KEY:raise ValueError("GROQ_API_KEY not set")
    if not WP_APP_PASS:raise ValueError("WP_APP_PASS not set")
    cats=get_cats()
    news=fetch_news()
    data=generate(news)
    pid,url=save_draft(data,cats)
    notify(pid,url,data["title"],data.get("category","GST Updates"))
    log(f"DONE - Draft {pid} ready at {url}")
if __name__=="__main__":main()
