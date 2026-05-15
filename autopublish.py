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
    return result if result else"Write about latest Indian GST or Income Tax developments."
def generate(news):
    today=datetime.date.today().strftime("%B %d, %Y")
    log(f"Calling Groq for {today}...")
    prompt=f"""You are editor of Finoscape, India Tax Intelligence Hub. Today is {today}.
News:\n{news}\nWrite ONE complete morning digest blog post about the most important Indian tax development.
Include hook story, bare act text, plain English, real example, expert corner, 3 takeaways, quiz, author box.
Law box: <div style="background:#f0ebff;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;margin-bottom:8px">BARE ACT</div><p style="font-size:14px;font-style:italic;color:#1a0533;margin:0;line-height:1.75">text</p></div>
Expert box: <div style="background:#E1F5EE;border-left:4px solid #085041;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#085041;margin-bottom:8px">EXPERT CORNER</div><p style="font-size:14px;color:#173404;line-height:1.75;margin:0">text</p></div>
Takeaways: <div style="background:#EAF3DE;border-left:4px solid #3B6D11;border-radius:0 10px 10px 0;padding:18px 20px;margin:24px 0"><div style="font-size:11px;font-weight:700;color:#3B6D11;margin-bottom:12px">THREE THINGS TO DO</div><p style="font-size:14px;color:#333;line-height:1.8;margin:0">1. a<br>2. b<br>3. c</p></div>
Quiz: <div style="background:#EEEDFE;border-left:4px solid #3a0ca3;border-radius:0 10px 10px 0;padding:20px;margin:28px 0"><div style="font-size:11px;font-weight:700;color:#3a0ca3;margin-bottom:12px">QUICK QUIZ</div><p style="font-size:16px;font-weight:700;color:#1a0533;margin-bottom:14px">Q?</p><p style="font-size:14px;color:#333">A.<br>B.<br>C.<br>D.</p><p style="font-size:14px;font-weight:700;color:#3B6D11;margin-top:12px">Answer: X</p></div>
Author: <div style="background:#f3e8ff;border-left:4px solid #3a0ca3;border-radius:0 12px 12px 0;padding:22px 24px;margin-top:40px"><div style="font-size:16px;font-weight:700;color:#1a0533">CA Siddharth S. Sancheti</div><div style="font-size:14px;color:#7209b7">Practising Chartered Accountant, Mumbai</div><div style="font-size:14px;color:#555;line-height:1.7">Founder, S S Sancheti and Associates.</div></div>
Return ONLY JSON: {{"title":"","category":"GST Updates OR Income Tax OR FEMA & RBI OR Companies Act","excerpt":"","tags":[],"content":""}}"""
    r=requests.post("https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
        json={"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":prompt}],
              "temperature":0.7,"max_tokens":4000,"response_format":{"type":"json_object"}},timeout=120)
    if r.status_code!=200:raise Exception(f"Groq error {r.status_code}:{r.text[:300]}")
    import json
    data=json.loads(r.json()["choices"][0]["message"]["content"])
    log(f"Generated:{data.get('title','')}");return data
def save_draft(data,cats):
    cid=cats.get(data.get("category","GST Updates"))
    r=requests.post(f"{WP_URL}/wp-json/wp/v2/posts",
        json={"title":data["title"],"content":data["content"],"excerpt":data.get("excerpt",""),"status":"draft","categories":[cid]if cid else[]},
        auth=wp_auth(),timeout=30)
    if r.status_code not in(200,201):raise Exception(f"WP error {r.status_code}:{r.text[:200]}")
    pid=r.json()["id"];url=f"{WP_URL}/wp-admin/post.php?post={pid}&action=edit"
    log(f"Draft saved ID:{pid}");return pid,url
def notify(pid,url,title,cat):
    if not all([GMAIL_USER,GMAIL_PASS,NOTIFY_EMAIL]):log("Email skipped");return
    today=datetime.date.today().strftime("%B %d, %Y")
    html=f'<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto"><div style="background:#1a0533;padding:20px 24px;border-radius:10px 10px 0 0"><div style="font-size:20px;font-weight:800;color:#fff">fino<span style="color:#c084fc">scape</span></div></div><div style="background:#fff;padding:28px;border:1px solid #e8e4f7;border-top:none;border-radius:0 0 10px 10px"><h2 style="color:#1a0533">Draft ready for review</h2><div style="background:#f3e8ff;border-left:4px solid #3a0ca3;padding:16px;border-radius:0 10px 10px 0;margin-bottom:20px"><div style="font-size:11px;font-weight:700;color:#3a0ca3">{cat.upper()} - {today}</div><div style="font-size:17px;font-weight:700;color:#1a0533">{title}</div></div><a href="{url}" style="display:inline-block;background:#3a0ca3;color:#fff;padding:13px 26px;border-radius:8px;text-decoration:none;font-weight:700">Review and Publish</a></div></div>'
    msg=MIMEMultipart("alternative")
    msg["Subject"]=f"Finoscape Draft - {today}"
    msg["From"]=f"Finoscape <{GMAIL_USER}>"
    msg["To"]=NOTIFY_EMAIL
    msg.attach(MIMEText(html,"html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465)as s:
            s.login(GMAIL_USER,GMAIL_PASS);s.send_message(msg)
        log(f"Email sent to {NOTIFY_EMAIL}")
    except Exception as e:log(f"Email error:{e}")
def main():
    log("="*50);log("Finoscape Auto-Publisher GROQ FREE");log("="*50)
    if not GROQ_KEY:raise ValueError("GROQ_API_KEY not set")
    if not WP_APP_PASS:raise ValueError("WP_APP_PASS not set")
    cats=get_cats();news=fetch_news();data=generate(news)
    pid,url=save_draft(data,cats)
    notify(pid,url,data["title"],data.get("category","GST Updates"))
    log(f"DONE Draft:{pid} at {url}")
if __name__=="__main__":main()
