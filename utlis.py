import json

from PyQt6.QtWidgets import QLayout
from PyQt6.QtCore import QSize, QPoint, QRect, Qt

from douban_spider import Book


# 类型转换
def book_to_dict(book):
    return {
        "title": book.title,
        "author": book.author,
        "publisher": book.publisher,
        "pub_date": book.pub_date,
        "price": book.price,
        "rating": book.rating,
        "rating_count": book.rating_count,
        "summary": book.summary,
        "url": book.url,
        "cover_url": book.cover_url,
        "source": book.source,
        "tags": getattr(book, "tags", []),  # 如果没有 tags 则为空列表
    }

def books_2d_to_dict(books_2d):
    result = []
    for row in books_2d:
        new_row = {
            "row_name": row["row_name"],
            "books": [book_to_dict(book) for book in row["books"]]
        }
        result.append(new_row)
    return result

def book_from_dict(data):
    return Book(
        title=data.get("title", ""),
        author=data.get("author", ""),
        publisher=data.get("publisher", ""),
        pub_date=data.get("pub_date", ""),
        price=data.get("price", ""),
        rating=data.get("rating", ""),
        rating_count=data.get("rating_count", 0),
        summary=data.get("summary", ""),
        url=data.get("url", ""),
        cover_url=data.get("cover_url", ""),
        source=data.get("source", ""),
        tags=data.get("tags", []),
    )


# 清除全部布局
def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                clear_layout(child_layout)



# 保存至json
def save_bookshelf_to_file(bookshelf=[], filename="bookshelf.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([
            {
                "row_name": row["row_name"],
                "books": [book_to_dict(book) for book in row["books"]]
            } for row in bookshelf
        ], f, ensure_ascii=False, indent=2)


# 读取json
def load_bookshelf_from_file(filename="bookshelf.json"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [
        {
            "row_name": row["row_name"],
            "books": [book_from_dict(book) for book in row["books"]]
        } for row in data
    ]



# 自定义布局类
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.item_list = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        width = self.parentWidget().width() if self.parentWidget() else 300
        height = self.do_layout(QRect(0, 0, width, 0), True)
        size.setHeight(height)
        size.setWidth(width)
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self.item_list:
            widget = item.widget()
            space_x = self.spacing()
            space_y = self.spacing()
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()