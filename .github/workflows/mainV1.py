import urllib.parse
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# 目標收件人
RECEIVER_EMAIL = "favoritec358@gmail.com"

# 1. 一般民調機構清單 (掃描與民調、Poll相關)
general_orgs = [
    "美麗島電子報", "國政民調", "民主文教基金會", "皮尤", "Pew Research Center",
    "雷根總統基金會", "Ronald Reagan Presidential Foundation", "Lowy Institute",
    "Chicago Council on Global Affairs", "YouGov", "Angus Reid Institute"
]

# 2. 特定議題機構清單 (僅掃描兩岸關係 + 民調)
cross_strait_orgs = [
    "國防安全研究院", "聯合報", "TVBS"
]

def fetch_google_news(query):
    """透過 Google News RSS 取得搜尋結果"""
    # when:1d 代表只搜尋過去 24 小時內的資料
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries:
        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })
    return results

def build_queries():
    """建構搜尋字串"""
    # 組合一般機構的搜尋條件：(機構A OR 機構B...) AND (民調 OR Poll)
    general_orgs_str = " OR ".join(f'"{org}"' for org in general_orgs)
    query_general = f"({general_orgs_str}) AND (民調 OR Poll)"

    # 組合兩岸關係的搜尋條件：(機構A OR 機構B...) AND (兩岸關係 OR 兩岸) AND (民調 OR Poll)
    cross_strait_orgs_str = " OR ".join(f'"{org}"' for org in cross_strait_orgs)
    query_cross_strait = f"({cross_strait_orgs_str}) AND (兩岸關係 OR 兩岸) AND (民調 OR Poll)"
    
    return query_general, query_cross_strait

def send_email(html_content):
    """發送 Email"""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD") # 需要使用 Gmail 應用程式密碼
    
    if not sender_email or not sender_password:
        print("錯誤：未設定 SENDER_EMAIL 或 SENDER_PASSWORD 環境變數")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 每日民調與兩岸關係新聞追蹤 ({datetime.now().strftime('%Y-%m-%d')})"
    msg["From"] = sender_email
    msg["To"] = RECEIVER_EMAIL

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        # 使用 Gmail SMTP 伺服器
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email 發送成功！")
    except Exception as e:
        print(f"❌ Email 發送失敗: {e}")

def main():
    print("開始掃描新聞...")
    query_general, query_cross_strait = build_queries()
    
    # 抓取資料
    general_news = fetch_google_news(query_general)
    cross_strait_news = fetch_google_news(query_cross_strait)

    # 如果都沒有新聞，也可以選擇不寄信，這裡預設還是寄出告知無更新
    if not general_news and not cross_strait_news:
        html_content = "<h3>今日無相關民調或兩岸關係新聞更新。</h3>"
    else:
        # 組裝 HTML 郵件內容
        html_content = "<h2>📊 每日民調與兩岸關係追蹤報告</h2>"
        
        html_content += "<h3>🌐 國際與國內機構民調動態</h3>"
        if general_news:
            html_content += "<ul>"
            for news in general_news:
                html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
            html_content += "</ul>"
        else:
            html_content += "<p>過去 24 小時無相關資料。</p>"

        html_content += "<h3>🇹🇼🇨🇳 兩岸關係特定機構民調動態</h3>"
        if cross_strait_news:
            html_content += "<ul>"
            for news in cross_strait_news:
                html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
            html_content += "</ul>"
        else:
            html_content += "<p>過去 24 小時無相關資料。</p>"

    send_email(html_content)

if __name__ == "__main__":
    main()
