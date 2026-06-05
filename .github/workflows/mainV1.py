import urllib.parse
import feedparser
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime

# 收件人
RECEIVER = "favoritec358@gmail.com"

def main():
    print("開始抓取新聞...")
    
    # 用最簡單的關鍵字搜尋：(民調 OR 兩岸) 過去1天內的新聞
    query = "(民調 OR 兩岸 OR Poll)"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(url)
    
    # 整理信件內容
    body = f"<h2>📊 每日民調與兩岸關係追蹤報告 ({datetime.now().strftime('%Y-%m-%d')})</h2><ul>"
    
    # 只抓前 20 則最相關的新聞，避免信件爆炸
    for entry in feed.entries[:20]:
        body += f"<li><a href='{entry.link}'>{entry.title}</a></li>"
    body += "</ul>"

    # 寄信
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("SENDER_PASSWORD")
    
    if not sender or not password:
        print("❌ 錯誤：GitHub Secrets 沒設定好！")
        return

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = f"📊 每日民調與兩岸追蹤"
    msg["From"] = sender
    msg["To"] = RECEIVER

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, RECEIVER, msg.as_string())
        server.quit()
        print("✅ 信件發送成功！")
    except Exception as e:
        print(f"❌ 寄信失敗: {e}")

if __name__ == "__main__":
    main()
