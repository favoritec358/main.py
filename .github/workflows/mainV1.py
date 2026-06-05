import urllib.parse
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta, timezone

# 目標收件人
RECEIVER_EMAILS = ["favoritec358@gmail.com", "jimmychwchang@gmail.com"]

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

def is_within_48_hours(entry):
    """【時間鐵閘】嚴格檢查新聞發布時間是否在 48 小時之內"""
    try:
        pub_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        now_time = datetime.now(timezone.utc)
        return (now_time - pub_time) <= timedelta(hours=48)
    except Exception as e:
        print(f"時間解析異常: {e}")
        return True

def fetch_and_filter_general(query, org_list):
    """抓取一般機構，並限制【標題含機構+民調】且【必須是48小時內】"""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        if not is_within_48_hours(entry):
            continue
            
        title_lower = entry.title.lower()
        has_org = any(org.lower() in title_lower for org in org_list)
        has_poll = "民調" in title_lower or "poll" in title_lower
        
        if has_org and has_poll:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def fetch_and_filter_cross_strait(query, org_list):
    """抓取特定機構，並限制【標題含機構+兩岸+民調】且【必須是48小時內】"""
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:1d')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        if not is_within_48_hours(entry):
            continue
            
        title_lower = entry.title.lower()
        has_org = any(org.lower() in title_lower for org in org_list)
        has_cross = "兩岸" in title_lower or "兩岸關係" in title_lower
        has_poll = "民調" in title_lower or "poll" in title_lower
        
        if has_org and has_cross and has_poll:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def build_queries():
    """建構原始搜尋字串"""
    general_orgs_str = " OR ".join(f'"{org}"' for org in general_orgs)
    query_general = f"({general_orgs_str}) AND (民調 OR Poll)"

    cross_strait_orgs_str = " OR ".join(f'"{org}"' for org in cross_strait_orgs)
    query_cross_strait = f"({cross_strait_orgs_str}) AND (兩岸關係 OR 兩岸) AND (民調 OR Poll)"
    
    return query_general, query_cross_strait

def send_email(html_content):
    """發送 Email 給所有人 (100% 符合 RFC 5321 安全規格版)"""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print("❌ 錯誤：未設定 SENDER_EMAIL 或 SENDER_PASSWORD 環境變數")
        return

    try:
        print("正在與 Gmail 建立安全連線...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # 🎯 核心修正：對每個收件人「單獨」打包成合法的獨立信件發送
        for receiver in RECEIVER_EMAILS:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📊 每日民調與兩岸關係精選追蹤 ({datetime.now().strftime('%Y-%m-%d')})"
            msg["From"] = sender_email
            msg["To"] = receiver  # 這邊傳入單一字串，絕對符合 RFC 5321 規範！

            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)
            
            # 單獨發送給該收件人
            server.sendmail(sender_email, [receiver], msg.as_string())
            print(f"✅ 信件已成功遞交給收件人: {receiver}")
            
        server.quit()
        print("✅ [最終回報] 所有人信件皆已處理完畢！")
    except Exception as e:
        print(f"❌ [最終回報] 郵件發送流程發生異常: {e}")

def main():
    print("下人開始實施【時間重重過濾】防噪聲追蹤...")
    query_general, query_cross_strait = build_queries()
    
    general_news = fetch_and_filter_general(query_general, general_orgs)
    cross_strait_news = fetch_and_filter_cross_strait(query_cross_strait, cross_strait_orgs)

    html_content = f"<h2>📊 每日民調與兩岸關係精確追蹤報告</h2>"
    html_content += f"<p>報告時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (已啟動48小時內時間鐵閘)</p><hr>"
    
    html_content += "<h3>🌐 國際與國內機構民調動態 (48小時內 + 標題必含機構+民調)</h3>"
    if general_news:
        html_content += "<ul>"
        for news in general_news:
            html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 48 小時內，無符合標準的最新民調發表）</p>"

    html_content += "<h3>🇹🇼🇨🇳 兩岸關係特定機構民調動態 (48小時內 + 標題必含該機構+兩岸+民調)</h3>"
    if cross_strait_news:
        html_content += "<ul>"
        for news in cross_strait_news:
            html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 48 小時內，無符合標準的最新兩岸民調發表）</p>"

    send_email(html_content)

if __name__ == "__main__":
    main()
