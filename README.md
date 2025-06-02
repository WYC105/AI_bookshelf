# AI_bookshelf
class Book:
    """书籍信息类"""

    title: str
    
    url: str
    
    rating: float
       
    author: str
       
    publisher: str
       
    cover_url: str
    
    source: str
    
    pub_date: str = ""
    
    price: str = ""
    
    info: str = ""     ##基本信息
    
    summary: str = ""  ##简介
    
    tags: List[str] = None  
    
    rating_count: int = 0  ##评分人数
为每一个对象





# Image Book Recognizer

`image_book_recognizer.py` 是一个使用 **Google Gemini** OpenAI-兼容端点识别书架/书脊照片中书名和出版社的脚本，并结合豆瓣搜索打印每本书的详细信息。

## 功能

1. 调用 Gemini Vision 模型识别书籍书脊中的书名和出版社
2. 打印完整的调试信息（可用模型、图片尺寸、请求与回复等）
3. 使用 `douban_spider.py` 对识别结果在豆瓣进行搜索，并输出作者、评分、出版社等详情

## 环境依赖

- Python 3.8+
- [openai](https://pypi.org/project/openai/) >=1.0
- pillow
- requests
- beautifulsoup4

```
pip install openai pillow requests beautifulsoup4 
```

## 配置

1. 在环境变量中设置 API Key：

   ```
   export GEMINI_API_KEY="YOUR_GEMINI_STUDIO_KEY"
   ```

2. 脚本顶部可以调整：

   ```
   GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
   VISION_MODEL    = "gemini-2.0-flash"  # 可选: gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash 等
   MAX_DOUBAN_RET  = 2                     # 豆瓣每次取前 N 条
   ```

## 使用方法

```
python image_book_recognizer.py <image_path>
```

示例：

```
python image_book_recognizer.py "/path/to/截屏2025-05-28 15.14.22.png"
```

脚本执行后会依次打印：

1. 可用 Gemini 模型列表
2. 图片读取信息
3. 发送到 Gemini 的请求摘要
4. Gemini 返回的原始 JSON
5. 清洗并解析后的书名/出版社列表
6. 对每本书在豆瓣的搜索查询及结果数
7. 若找到书目，输出作者、出版社、评分；否则提示未找到
