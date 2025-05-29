"""image_book_recognizer.py — 使用 **Google Gemini** 的 OpenAI-兼容端点识别书脊书名 + 出版社，并打印每一步的调试信息"""

import os
import re
import json
import base64
from typing import List, Dict

from PIL import Image
import openai  # 使用 openai>=1.0 客户端调用 Gemini 兼容端点

from douban_spider import DoubanBookSpider

# ------------------------------------------------------------------
# 配置区
# ------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("请先设置 GEMINI_API_KEY 环境变量！")

# Gemini OpenAI-compatible 基地址
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
VISION_MODEL    = "gemini-2.0-flash"  # 列表里确认可用后再填
MAX_DOUBAN_RET  = 2                     # 豆瓣每次取前 N 条
# ------------------------------------------------------------------

# 初始化客户端
openai_client = openai.OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL)

# 列出可用模型（调试用）
models = openai_client.models.list()
print("[DEBUG] Available models:", [m.id for m in models.data])


def gemini_vision_books(img_path: str) -> List[Dict[str, str]]:
    """调用 Gemini Vision，返回 [{title, publisher}, …]，并打印调试信息"""
    # 读取并编码图片
    with open(img_path, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode()
    print(f"[DEBUG] 已读取图片 {img_path}, 大小 {len(raw)} bytes")

    # 构造消息
    messages = [{
        "role": "user",
        "content": [
            {"type": "text",  "text": (
                "这是一张书架/书脊照片。请识别每一本书的书名和出版社，"
                "返回 JSON 数组，例如 [{\"title\":\"三体\",\"publisher\":\"重庆出版社\"}, …]。"
                "请只输出纯 JSON，不要任何多余文本。"
            )},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]
    }]
    print(f"[DEBUG] 发送到 Gemini 的消息: {json.dumps(messages, ensure_ascii=False)[:200]}...")

    # 调用 API
    resp = openai_client.chat.completions.create(
        model=VISION_MODEL,
        messages=messages,
    )
    raw_txt = resp.choices[0].message.content.strip()
    print(f"[DEBUG] Gemini 原始输出: {raw_txt}")

    # 清洗并解析
    txt = re.sub(r"^```[a-z]*", "", raw_txt).rstrip("`")
    try:
        data = json.loads(txt)
    except json.JSONDecodeError as e:
        print(f"[ERROR] 解析 JSON 失败: {e}")
        raise
    print(f"[DEBUG] 解析后的 JSON: {data}")
    return data

# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python image_book_recognizer.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    spider = DoubanBookSpider()

    try:
        books_info = gemini_vision_books(img_path)
        print("\n=== Gemini 识别结果 ===")
        for idx, info in enumerate(books_info, 1):
            title = info.get("title", "").strip()
            publisher = info.get("publisher", "").strip()
            print(f"[{idx}] 书名: {title} | 出版社: {publisher}")
    except Exception as e:
        print("Gemini 解析失败:", e)
        books_info = []

    print("\n=== 执行豆瓣搜索 ===")
    for idx, info in enumerate(books_info, 1):
        title = info.get("title", "").strip()
        publisher = info.get("publisher", "").strip()
        query = f"{title} {publisher}".strip()
        print(f"[DEBUG] 查询豆瓣: {query}")
        books = spider.search_books(query)
        print(f"[DEBUG] 搜索到 {len(books)} 条结果 (max {MAX_DOUBAN_RET})")
        if not books:
            books = spider.search_books(title)
            print(f"[DEBUG] 仅用书名搜索，结果数: {len(books)}")

        if books:
            bk = spider.get_book_details(books[0])
            print(f"》{bk.title} | 作者: {bk.author} | 出版社: {bk.publisher} | 评分: {bk.rating}\n")
        else:
            print(f"‼ 未找到: {title}\n")