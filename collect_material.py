#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材收集自动化脚本
用于自动收集网页内容并保存到 collection 目录
"""

import os
import re
import time
import urllib.parse
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def save_to_collection(content, title):
    """保存内容到 collection 目录"""
    # 创建 collection 目录（如果不存在）
    collection_dir = "/home/leo/.openclaw/workspace/collection"
    os.makedirs(collection_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_title = sanitize_filename(title)
    
    # 确保文件名长度合理
    if len(safe_title) > 100:
        safe_title = safe_title[:100]
    
    filename = f"{timestamp}_{safe_title}.md"
    file_path = os.path.join(collection_dir, filename)
    
    # 保存内容
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"内容已保存到: {file_path}")
        return file_path
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return None


def sanitize_filename(filename):
    """清理文件名，去除非法字符"""
    # 替换非法字符
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    return filename


def get_web_content(url):
    """获取网页内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = response.apparent_encoding
        
        return response.text
    except Exception as e:
        print(f"获取网页内容时出错: {e}")
        return None


def extract_wechat_article(html):
    """提取微信文章内容"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title = soup.find('h1', id='activity-name')
        if not title:
            title = soup.find('title')
        title_text = title.get_text().strip() if title else '无标题'
        
        # 提取正文
        content_div = soup.find('div', id='js_content')
        if content_div:
            content = content_div.get_text().strip()
        else:
            content = '未找到正文内容'
        
        # 格式化内容
        formatted_content = f"# {title_text}\n\n{content}"
        
        return formatted_content, title_text
    except Exception as e:
        print(f"解析微信文章时出错: {e}")
        return None, None


def main(url):
    """主函数"""
    print("素材收集自动化工具")
    print("==================")
    print(f"正在收集: {url}")
    
    # 获取网页内容
    html = get_web_content(url)
    if not html:
        return
    
    # 识别页面类型并提取内容
    if 'mp.weixin.qq.com' in url:
        content, title = extract_wechat_article(html)
    else:
        # 默认处理
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        title_text = title.get_text().strip() if title else '无标题'
        content = f"# {title_text}\n\n{html[:2000]}"  # 只保存前2000字符
    
    if content:
        save_to_collection(content, title)
    else:
        print("未成功提取内容")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("用法: python collect_material.py <url>")
        print("示例: python collect_material.py 'https://mp.weixin.qq.com/s/914w3MWqnEGTBkkzv-oGuA'")
