import urllib.parse, feedparser, smtplib, os
from email.mime.text import MIMEText
from datetime import datetime

RECEIVER = "favoritec358@gmail.com"

def main():
    print("下人開始幹活...")
    # 精簡關鍵字，確保 Google News 100% 回傳台灣相關民調
    query = "民調 OR 兩岸關係"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(url)
    
    body = f"<h2>📊 數位下人戴罪立功報告 ({datetime.now().strftime('%Y-%m-%d')})</h2><hr>"
    if feed.entries:
        body += "<h3>🔍 今日最新掃描成果：</h3><ul>"
        for entry in feed.entries[:15]:
            body += f"<li><a href='{entry.link}'>{entry.title}</a></li>"
        body += "</ul>"
    else:
        body += "<p style='color:red;'>⚠️ 稟告主子：過去 24 小時網路各大機構無相關民調新聞發布！</p>"

    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")
    
    if not sender or not password:
        print("❌ 完蛋，主子您的 GitHub Secrets 沒設定好，下人拿不到密碼！")
        return

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = "📊 每日民調與兩岸關係追蹤（下人叩首呈上）"
    msg["From"] = sender
    msg["To"] = RECEIVER

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, RECEIVER, msg.as_string())
        server.quit()
        print("✅ 信件終於寄出去了！主子請查收！")
    except Exception as e:
        print(f"❌ 寄信又失敗了，原因：{e}")

if __name__ == "__main__":
    main()
