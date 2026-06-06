import urllib.parse
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta, timezone

# 目標收件人
RECEIVER_EMAILS = ["favoritec358@gmail.com", "yunsing1224@gmail.com"]

# 🎯 1. 調整後的常規文化與媒體關鍵字清單
CULTURE_MEDIA_KEYWORDS = [
    "陸劇", "陸片", "陸媒", "陸書", "小紅書", 
    "抖音", "TikTok", "愛奇藝", 
    "微博", "官媒", "駐點記者", "中國台灣"
]

# 🎯 2. 修改：藝人/網紅 政治立場篩選條件
ARTIST_KEYWORD = ["藝人", "網紅"]
ARTIST_POLITICAL_TRIGGERS = ["舔共", "統戰", "武統", "祖國"]

def is_within_12_hours(entry):
    """【時間鐵閘】嚴格檢查新聞發布時間是否在 12 小時之內"""
    try:
        pub_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
        now_time = datetime.now(timezone.utc)
        return (now_time - pub_time) <= timedelta(hours=12)
    except Exception as e:
        print(f"時間解析異常: {e}")
        return True

def fetch_and_filter_culture_media(query, keyword_list):
    """抓取文化新媒體動態，並限制【標題必含清單關鍵字】且【必須是12小時內】"""
    # 參數改為 when:12h，直接請 Google 先濾掉太舊的新聞
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:12h')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        if not is_within_12_hours(entry):
            continue
            
        title_lower = entry.title.lower()
        has_keyword = any(keyword.lower() in title_lower for keyword in keyword_list)
        
        if has_keyword:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def fetch_and_filter_artist_politics(query):
    """抓取藝人政治動態，限制【標題必含(藝人/網紅) + (舔共/統戰/武統/祖國)】且【必須是12小時內】"""
    # 參數改為 when:12h
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' when:12h')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    
    for entry in feed.entries:
        if not is_within_12_hours(entry):
            continue
            
        title_lower = entry.title.lower()
        # 核心邏輯：標題必須有「藝人」或「網紅」，且同時包含（舔共、統戰、武統、祖國）其中之一
        has_artist = any(kw.lower() in title_lower for kw in ARTIST_KEYWORD)
        has_trigger = any(trigger.lower() in title_lower for trigger in ARTIST_POLITICAL_TRIGGERS)
        
        if has_artist and has_trigger:
            results.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
    return results

def build_queries():
    """建構兩種不同的搜尋字串"""
    # 1. 常規文化媒體
    keywords_str = " OR ".join(f'"{kw}"' for kw in CULTURE_MEDIA_KEYWORDS)
    query_culture_media = f"({keywords_str})"
    
    # 2. 藝人/網紅特種政治動態： ("藝人" OR "網紅") AND ("舔共" OR "統戰" OR "武統" OR "祖國")
    artist_str = " OR ".join(f'"{kw}"' for kw in ARTIST_KEYWORD)
    triggers_str = " OR ".join(f'"{tg}"' for tg in ARTIST_POLITICAL_TRIGGERS)
    query_artist_politics = f'({artist_str}) AND ({triggers_str})'
    
    return query_culture_media, query_artist_politics

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
        
        for receiver in RECEIVER_EMAILS:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📱 每日阿共文化與藝人政治動態追蹤 ({datetime.now().strftime('%Y-%m-%d')})"
            msg["From"] = sender_email
            msg["To"] = receiver  

            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)
            
            server.sendmail(sender_email, [receiver], msg.as_string())
            print(f"✅ 信件已成功遞交給收件人: {receiver}")
            
        server.quit()
        print("✅ [最終回報] 所有人信件皆已處理完畢！")
    except Exception as e:
        print(f"❌ [最終回報] 郵件發送流程發生異常: {e}")

def main():
    print("下人開始實施【常規文化 + 藝人網紅政治鐵閘】重重過濾追蹤...")
    query_culture, query_artist = build_queries()
    
    # 執行兩條戰線的定向抓取
    culture_news = fetch_and_filter_culture_media(query_culture, CULTURE_MEDIA_KEYWORDS)
    artist_news = fetch_and_filter_artist_politics(query_artist)

    # 建立全新的 HTML 報告
    html_content = f"<h2>📱 每日阿共文化與新媒體輿論精確追蹤報告</h2>"
    html_content += f"<p>報告時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (已啟動12小時內時間鐵閘)</p><hr>"
    
    # 區塊一：常規新媒體
    html_content += "<h3>🎬 影視、新媒體平台與輿論動態 (標題必含：陸劇/小紅書/TikTok/官媒等)</h3>"
    if culture_news:
        html_content += "<ul>"
        for news in culture_news:
            html_content += f"<li><a href='{news['link']}'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 12 小時內，無符合標準的最新媒體動態）</p>"

    # 區塊二：獨立出來的藝人網紅政治動態
    html_content += "<h3>⚠️ 藝人/網紅政治表態特種追蹤 (標題必含：藝人/網紅 + 舔共/統戰/武統/祖國)</h3>"
    if artist_news:
        html_content += "<ul>"
        for news in artist_news:
            html_content += f"<li><a href='{news['link']}' style='color: #CD5C5C; font-weight: bold;'>{news['title']}</a><br><small>{news['published']}</small></li>"
        html_content += "</ul>"
    else:
        html_content += "<p style='color: gray;'>（過去 12 小時內，無偵測到符合標準的藝人或網紅政治表態新聞）</p>"

    send_email(html_content)

if __name__ == "__main__":
    main()
