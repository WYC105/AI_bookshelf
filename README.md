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
