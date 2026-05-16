import requests
import yaml
import time
from datetime import datetime
from pathlib import Path

# ================== 请修改这里的配置 ==================
CSDN_USERNAME = "qq_23297513"  # 改成你的 CSDN ID
OUTPUT_FILE = "_data/csdn_posts.yml"
# ==================================================

def fetch_articles():
    """获取CSDN博客文章列表"""
    base_url = "https://blog.csdn.net/community/home-api/v1/get-business-list"
    params = {
        "page": 1,
        "size": 20,
        "businessType": "blog",
        "noMore": "false",
        "username": CSDN_USERNAME
    }
    articles = []
    while True:
        response = requests.get(base_url, params=params)
        if response.status_code != 200:
            break
        data = response.json().get("data", {})
        article_list = data.get("list", [])
        if not article_list:
            break
        for item in article_list:
            articles.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "date": item.get("publishTime", "").split(" ")[0]
            })
        if data.get("page", {}).get("isLast"):
            break
        params["page"] += 1
        time.sleep(0.5)   # 避免请求过快
    return articles

def main():
    print(f"Fetching CSDN articles for user: {CSDN_USERNAME}")
    articles = fetch_articles()
    if not articles:
        print("No articles fetched")
        return
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(articles, f, allow_unicode=True, default_flow_style=False)
    print(f"Saved {len(articles)} articles to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()