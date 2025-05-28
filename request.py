import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
from dataclasses import dataclass
from typing import List, Optional

@dataclass
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
    info: str = ""
    summary: str = ""
    tags: List[str] = None
    rating_count: int = 0

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class DoubanBookSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.base_url = "https://search.douban.com/book/subject_search"
        
    def search_books(self, keyword: str, start: int = 0) -> List[Book]:
        """搜索豆瓣书籍，返回Book对象列表"""
        params = {
            'search_text': keyword,
            'cat': '1001',
            'start': start
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            books = self._parse_html(soup)

            script_data = self._extract_script_data(response.text)
            if script_data and 'items' in script_data:
                books.extend(self._parse_script_data(script_data['items']))
                
            return books
            
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return []
    
    def _parse_html(self, soup: BeautifulSoup) -> List[Book]:
        """解析HTML中的书籍信息，返回Book对象列表"""
        books = []
        items = soup.select('.sc-bZQynM')
        
        for item in items:
            title_elem = item.select_one('.title-text')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            
            rating_elem = item.select_one('.rating_nums')
            rating = float(rating_elem.get_text(strip=True)) if rating_elem else 0.0
            
            author_pub_elem = item.select_one('.meta.abstract')
            author_pub = author_pub_elem.get_text('|', strip=True).split('|') if author_pub_elem else []
            author = author_pub[0].strip() if len(author_pub) > 0 else ''
            pub_info = author_pub[1].strip() if len(author_pub) > 1 else ''
            
            cover_elem = item.select_one('.cover img')
            cover_url = cover_elem.get('src', '') if cover_elem else ''
            
            books.append(Book(
                title=title,
                url=url,
                rating=rating,
                author=author,
                publisher=pub_info,
                cover_url=cover_url,
                source='html'
            ))
            
        return books
    
    def _extract_script_data(self, html: str) -> Optional[dict]:
        """从JavaScript中提取数据"""
        pattern = re.compile(r'window\.__DATA__\s*=\s*({.*?});', re.DOTALL)
        match = pattern.search(html)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None
    
    def _parse_script_data(self, items: List[dict]) -> List[Book]:
        """解析JavaScript中的书籍数据，返回Book对象列表"""
        books = []
        
        for item in items:
            if item.get('tpl_name') != 'search_subject':
                continue
                
            title = item.get('title', '')
            url = item.get('url', '')
            
            rating_info = item.get('rating', {})
            rating = float(rating_info.get('value', 0)) if rating_info else 0.0
            
            abstract = item.get('abstract', '')
            author_pub = abstract.split(' / ')
            author = author_pub[0] if len(author_pub) > 0 else ''
            publisher = author_pub[1] if len(author_pub) > 1 else ''
            pub_date = author_pub[2] if len(author_pub) > 2 else ''
            price = author_pub[3] if len(author_pub) > 3 else ''
            
            cover_url = item.get('cover_url', '')
            
            books.append(Book(
                title=title,
                url=url,
                rating=rating,
                author=author,
                publisher=publisher,
                pub_date=pub_date,
                price=price,
                cover_url=cover_url,
                source='script'
            ))
            
        return books
    
    def get_book_details(self, book: Book) -> Book:
        """获取书籍详细信息并更新Book对象"""
        try:
            response = requests.get(book.url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            info = soup.select_one('#info')
            info_text = info.get_text('|', strip=True) if info else ''
            
            summary = soup.select_one('.intro')
            summary_text = summary.get_text(strip=True) if summary else ''
            
            # 提取标签
            tags = [tag.get_text(strip=True) for tag in soup.select('.tags a')]
            
            # 提取评分人数
            rating_people = soup.select_one('.rating_people span')
            rating_count = int(rating_people.get_text(strip=True)) if rating_people else 0
            
            # 更新Book对象
            book.info = info_text
            book.summary = summary_text
            book.tags = tags
            book.rating_count = rating_count
            
            return book
            
        except requests.RequestException as e:
            print(f"获取书籍详情失败: {e}")
            return book

if __name__ == "__main__":
    spider = DoubanBookSpider()
    
    keyword = "三体"
    print(f"正在搜索豆瓣书籍: {keyword}")
    
    books = spider.search_books(keyword)
    
    print(f"\n找到 {len(books)} 本相关书籍:")
    for i, book in enumerate(books, 1):
        print(f"\n{i}. {book.title}")
        print(f"   作者: {book.author}")
        print(f"   评分: {book.rating}")
        print(f"   出版社: {book.publisher}")
        print(f"   封面: {book.cover_url}")
        print(f"   链接: {book.url}")
    
    if books:
        first_book = books[0]
        print(f"\n获取第一本书的详细信息: {first_book.url}")
        detailed_book = spider.get_book_details(first_book)
        
        print("\n详细信息:")
        print(f"基本信息: {detailed_book.info}")
        print(f"简介: {detailed_book.summary[:100]}...")
        print(f"标签: {', '.join(detailed_book.tags)}")
        print(f"评分人数: {detailed_book.rating_count}")