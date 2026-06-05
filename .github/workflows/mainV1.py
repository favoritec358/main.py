import urllib.parse
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

# 目標收件人
RECEIVER_EMAIL = "favoritec358@gmail.com"

# 1. 一般民調機構清單
general_orgs = [
    "美麗島電子報", "國政民調", "民主文教基金會", "皮尤", "Pew Research Center",
    "雷根總統基金會", "Ronald Reagan Presidential Foundation", "Lowy Institute",
    "Chicago Council on Global Affairs", "YouGov", "Angus Reid Institute"
]

# 2. 特定議題機構清單
cross_strait_orgs = [
    "國防安全研究院", "聯合報", "TVBS"
]

def fetch_and_filter_general(query, org_list):
    """抓取一般機構，並嚴格限制【標題】必須同時包含機構名稱與(民調/Poll)"""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        title_lower = entry.title.lower()
        # 檢查標題是否包含至少一個指定的機構名稱
        has_org = any(org.lower() in title_lower for org in org_list)
        # 檢查標題是否包含民調相關字眼
        has_poll = "民調" in title_lower or "poll" in title_lower
        
        # 兩者都在標題成立，才放行
        if has_org and has_poll:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def fetch_and_filter_cross_strait(query, org_list):
    """抓取特定機構，並嚴格限制【標題】必須同時包含(機構)與(兩岸)與(民調)"""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        title_lower = entry.title.lower()
        has_org = any(org.lower() in title_lower for org in org_list)
        has_cross = "兩岸" in title_lower or "兩岸關係" in title_lower
        has_poll = "民調" in title_lower or "poll" in title_lower
        
        # 三者都在標題成立，才放行
        if has_org and has_cross and has_poll:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def build_queries():
    """建構原始搜尋字串 (維持寬鬆搜尋，交給後面做標題過濾)"""
    general_orgs_str = " OR ".join(f'"{org}"' for org in general_orgs)
    query_general = f"({general_orgs_str}) AND (民調 OR Poll)"

    cross_strait_orgs_str = " OR ".join(f'"{org}"' for org in cross_strait_orgs)
    query_cross_strait = f"({cross_strait_orgs_str}) AND (兩岸關係 OR 兩岸) AND (民調 OR Poll)"
    
    return query_general, query_cross_strait

def send_email(html_content):
    """發送 Email"""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("❌ 錯誤：未設定 SENDER_EMAIL 或 SENDER_PASSWORD 環境變數")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 每日民調與兩岸關係精選追蹤 ({datetime.now().strftime('%Y-%m-%d')})"
    msg["From"] = sender_email
    msg["To"] = RECEIVER_EMAIL

    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ Email 發送成功！")
    except Exception as e:
        print(f"❌ Email 發送失敗: {e}")

def main():
    print("下人開始實施【標題嚴格過濾】防噪聲掃描...")
    query_general, query_cross_strait = build_queries()
    
    # 執行嚴格過濾抓取
    general_news = fetch_and_filter_general(query_general, general_orgs)
    cross_strait_news = fetch_and_filter_cross_strait(query_cross_strait, cross_strait_orgs)

    # 組裝 HTML 報告
    html_content = f"<h2>📊 每日民調與兩岸關係精確追蹤報告</h2>"
    html_content += f"<p>報告時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (已啟動標題精確過濾)</p><hr>"
    
    html_content += "<h3>🌐 國際與國內機構民調動態 (標題必含機構+民調)</h3>"
    if general_news:
        html_content += "<ul>"
        for news in general_news:
            html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 24 小時內，無符合標題標準的民調發表）</p>"

    html_content += "<h3>🇹🇼🇨🇳 兩岸關係特定機構民調動態 (標題必含該機構+兩岸+民調)</h3>"
    if cross_strait_news:
        html_content += "<ul>"
        for news in cross_strait_news:
            html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 24 小時內，無符合標題標準的兩岸民調發表）</p>"

    send_email(html_content)

if __name__ == "__main__":
    main()
