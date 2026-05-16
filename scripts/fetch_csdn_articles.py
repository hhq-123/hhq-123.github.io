#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSDN博客文章抓取脚本
使用 CSDN API 或 HTML 解析抓取指定博客的所有文章列表并保存为YAML格式
作者: GitHub Actions Bot
"""

import requests
import yaml
import json
from datetime import datetime
import time
import os
from bs4 import BeautifulSoup
import re

# CSDN博客配置
CSDN_USERNAME = "qq_23297513"
CSDN_BLOG_URL = f"https://blog.csdn.net/{CSDN_USERNAME}"
# CSDN 内部 API
CSDN_ARTICLE_LIST_API = "https://blog.csdn.net/community/home-api/v1/get-business-list"
OUTPUT_FILE = "_data/csdn_posts.yml"

# 请求头 - 模拟真实浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://blog.csdn.net/',
}

# API 专用请求头
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': f'https://blog.csdn.net/{CSDN_USERNAME}',
    'Origin': 'https://blog.csdn.net',
}


def fetch_article_list_from_html():
    """
    使用 HTML 解析方式抓取博客文章列表（备用方法）
    
    Returns:
        articles: 文章列表
    """
    articles = []
    
    print(f"🔍 使用 HTML 解析方式抓取CSDN博客: {CSDN_USERNAME}")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    max_retries = 3
    page = 1
    
    while True:
        for retry in range(max_retries):
            try:
                print(f"📡 正在请求第 {page} 页 (尝试 {retry + 1}/{max_retries})...")
                
                # 构建博客列表URL
                url = f"{CSDN_BLOG_URL}/article/list/{page}"
                
                # 发送请求
                response = session.get(url, timeout=15)
                response.raise_for_status()
                
                # 使用 BeautifulSoup 解析 HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找文章列表
                article_items = soup.select('.article-item-box')
                
                if not article_items:
                    print(f"✅ 第 {page} 页无更多文章")
                    break
                
                print(f"✅ 第 {page} 页找到 {len(article_items)} 篇文章")
                
                # 解析每篇文章
                for item in article_items:
                    try:
                        # 获取标题和链接
                        title_elem = item.select_one('h4 a')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        # 确保链接是完整的
                        if link and not link.startswith('http'):
                            link = 'https://blog.csdn.net' + link
                        
                        # 获取日期
                        date_elem = item.select_one('.date')
                        date_str = ''
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            # 尝试提取日期，格式可能是 "2024-01-15" 或其他
                            date_match = re.search(r'\d{4}-\d{2}-\d{2}', date_text)
                            if date_match:
                                date_str = date_match.group()
                        
                        # 获取摘要
                        desc_elem = item.select_one('.content')
                        description = ''
                        if desc_elem:
                            description = desc_elem.get_text(strip=True)
                            if len(description) > 150:
                                description = description[:150] + '...'
                        
                        # 获取阅读量
                        views_elem = item.select_one('.read-num')
                        views = ''
                        if views_elem:
                            views_text = views_elem.get_text(strip=True)
                            # 提取数字
                            views_match = re.search(r'\d+', views_text)
                            if views_match:
                                views = views_match.group()
                        
                        if title and link:
                            article = {
                                'title': title,
                                'link': link,
                                'date': date_str,
                                'excerpt': description,
                                'views': views
                            }
                            articles.append(article)
                        
                    except Exception as e:
                        print(f"⚠️  解析文章时出错: {str(e)}")
                        continue
                
                # 成功获取，跳出重试循环
                break
                
            except Exception as e:
                print(f"❌ 请求失败 (尝试 {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep((retry + 1) * 3)
                else:
                    print(f"⚠️  第 {page} 页获取失败，返回已获取的 {len(articles)} 篇文章")
                    return articles
        else:
            # 重试全部失败
            break
        
        # 检查是否还有文章
        if not article_items or len(article_items) == 0:
            break
        
        # 继续获取下一页
        page += 1
        time.sleep(2)  # 礼貌地等待2秒
    
    print(f"\n✨ 总共抓取到 {len(articles)} 篇文章")
    return articles


def fetch_article_list_from_api():
    """
    使用 CSDN API 抓取博客文章列表
    
    Returns:
        articles: 文章列表
    """
    articles = []
    
    print(f"🔍 开始使用 API 抓取CSDN博客: {CSDN_USERNAME}")
    
    session = requests.Session()
    session.headers.update(API_HEADERS)
    
    max_retries = 3
    page = 1
    page_size = 40  # 每页获取40篇
    
    while True:
        for retry in range(max_retries):
            try:
                print(f"📡 正在请求第 {page} 页 (尝试 {retry + 1}/{max_retries})...")
                
                # 构建 API 请求参数
                params = {
                    'page': page,
                    'size': page_size,
                    'businessType': 'blog',
                    'orderby': '',
                    'noMore': 'false',
                    'year': '',
                    'month': '',
                    'username': CSDN_USERNAME
                }
                
                # 发送请求到 API
                response = session.get(CSDN_ARTICLE_LIST_API, params=params, timeout=15)
                response.raise_for_status()
                
                # 解析 JSON 响应
                data = response.json()
                
                if data.get('code') != 200:
                    print(f"⚠️  API 返回错误: {data.get('message', 'Unknown error')}")
                    if retry < max_retries - 1:
                        time.sleep((retry + 1) * 3)
                        continue
                    else:
                        break
                
                # 获取文章列表
                article_list = data.get('data', {}).get('list', [])
                
                if not article_list:
                    print(f"✅ 第 {page} 页无更多文章，已获取全部")
                    break
                
                print(f"✅ 第 {page} 页找到 {len(article_list)} 篇文章")
                
                # 解析文章信息
                for item in article_list:
                    try:
                        title = item.get('title', '').strip()
                        article_id = item.get('articleId', '')
                        link = f"https://blog.csdn.net/{CSDN_USERNAME}/article/details/{article_id}"
                        
                        # 处理日期 - 转换时间戳
                        post_time = item.get('postTime', '')
                        date_str = ''
                        if post_time:
                            try:
                                # CSDN 返回的时间戳是毫秒级
                                timestamp = int(post_time) / 1000 if len(str(post_time)) > 10 else int(post_time)
                                date_obj = datetime.fromtimestamp(timestamp)
                                date_str = date_obj.strftime('%Y-%m-%d')
                            except:
                                date_str = str(post_time)[:10]
                        
                        # 获取摘要
                        description = item.get('description', '').strip()
                        if len(description) > 150:
                            description = description[:150] + '...'
                        
                        # 获取阅读量
                        view_count = item.get('viewCount', 0)
                        views = str(view_count) if view_count else ''
                        
                        if title and link:
                            article = {
                                'title': title,
                                'link': link,
                                'date': date_str,
                                'excerpt': description,
                                'views': views
                            }
                            articles.append(article)
                        
                    except Exception as e:
                        print(f"⚠️  解析文章时出错: {str(e)}")
                        continue
                
                # 成功获取，跳出重试循环
                break
                
            except requests.RequestException as e:
                print(f"❌ 请求失败 (尝试 {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep((retry + 1) * 5)
                else:
                    # 最后一次重试也失败了，返回已获取的文章
                    print(f"⚠️  第 {page} 页获取失败，返回已获取的 {len(articles)} 篇文章")
                    return articles
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析错误 (尝试 {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep((retry + 1) * 3)
                else:
                    return articles
            except Exception as e:
                print(f"❌ 处理时出错 (尝试 {retry + 1}/{max_retries}): {str(e)}")
                if retry < max_retries - 1:
                    time.sleep((retry + 1) * 3)
                else:
                    return articles
        else:
            # 重试全部失败
            break
        
        # 检查是否还有更多文章
        if len(article_list) < page_size:
            print(f"✅ 已获取所有文章")
            break
        
        # 继续获取下一页
        page += 1
        time.sleep(2)  # 礼貌地等待2秒再请求下一页
    
    print(f"\n✨ 总共抓取到 {len(articles)} 篇文章")
    return articles


def save_to_yaml(articles):
    """
    将文章列表保存为YAML文件
    
    Args:
        articles: 文章列表
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 添加元数据
    data = {
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(articles),
        'articles': articles
    }
    
    # 保存为YAML
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    print(f"💾 文章列表已保存到: {OUTPUT_FILE}")


def load_existing_data():
    """
    加载现有的文章数据
    
    Returns:
        dict: 现有数据，如果文件不存在则返回 None
    """
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict) and 'articles' in data:
                    print(f"📂 已加载现有数据: {data.get('total_count', 0)} 篇文章")
                    return data
        except Exception as e:
            print(f"⚠️  读取现有数据失败: {str(e)}")
    return None


def main():
    """主函数"""
    print("=" * 60)
    print("CSDN博客文章同步工具 (本地执行版)")
    print("=" * 60)
    
    # 加载现有数据，以便在抓取失败时保留
    existing_data = load_existing_data()
    existing_count = existing_data.get('total_count', 0) if existing_data else 0
    
    try:
        # 首先尝试使用 API 方法
        print("\n方法1: 尝试使用 API...")
        articles = fetch_article_list_from_api()
        
        # 如果 API 失败，使用 HTML 解析方法
        if not articles:
            print("\n⚠️  API 方法失败，切换到 HTML 解析方法...")
            print("方法2: 使用 HTML 解析...")
            articles = fetch_article_list_from_html()
        
        if articles:
            # 保存到YAML
            save_to_yaml(articles)
            print("\n🎉 同步完成！")
            print(f"📊 共获取 {len(articles)} 篇文章")
            return 0
        else:
            # 抓取失败，保护原有数据
            print("\n⚠️  未抓取到任何文章")
            if existing_data and existing_count > 0:
                print(f"🛡️  保留原有 {existing_count} 篇文章数据，不进行覆盖")
                print("\n💡 提示：本地执行通常不会被拦截，请检查网络连接")
            else:
                print("⚠️  没有现有数据可保留")
            return 0
            
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 发生异常时也保留原有数据
        if existing_data and existing_count > 0:
            print(f"\n🛡️  发生异常，保留原有 {existing_count} 篇文章数据")
        
        return 1


if __name__ == '__main__':
    exit(main())