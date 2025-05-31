from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QLineEdit, QDialog, QScrollArea
from PyQt6.QtGui import QCursor
from PyQt6.QtCore import Qt, QSize

from utlis import FlowLayout
from douban_spider import Book


# 书籍标签图形类
class TagWidget(QPushButton):
    def __init__(self, text, on_delete):
        super().__init__(f"{text}  ✕")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.setStyleSheet("""
            QPushButton {
                border: 1px solid #aaa;
                border-radius: 5px;
                padding: 2px 6px;
                background-color: #eee;
                color: black;
            }
            QPushButton:hover {
                background-color: #e53935;
                color: white;
            }
        """)
        self.clicked.connect(on_delete)


# 书籍标签编辑器类
class TagEditorDialog(QDialog):
    def __init__(self, book: Book, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle(f"为《{self.book.title}》编辑标签")
        self.setFixedWidth(300)

        self.main_layout = QVBoxLayout(self)
        self.tag_container = QWidget()
        self.tag_layout = FlowLayout(self.tag_container)
        self.tag_container.setLayout(self.tag_layout)
        self.tag_container.setStyleSheet("border: 1px solid gray; padding: 8px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.tag_container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.main_layout.addWidget(scroll)

        input_layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入新标签")
        input_layout.addWidget(self.input)

        self.btn_add = QPushButton("添加标签")
        self.btn_add.clicked.connect(self.add_tag)
        input_layout.addWidget(self.btn_add)

        self.btn_close = QPushButton("退出")
        self.btn_close.clicked.connect(self.accept)
        input_layout.addWidget(self.btn_close)

        self.main_layout.addLayout(input_layout)

        self.refresh_tags()

    # 显示标签图形
    def add_tag_widget(self, tag_text):
        def remove():
            self.book.tags.remove(tag_text)
            self.refresh_tags()

        tag_widget = TagWidget(tag_text, remove)
        self.tag_layout.addWidget(tag_widget)

    # 刷新所有标签图形
    def refresh_tags(self):
        while self.tag_layout.count():
            item = self.tag_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for tag in self.book.tags:
            self.add_tag_widget(tag)

    # 添加标签
    def add_tag(self):
        tag_text = self.input.text().strip()
        if tag_text and tag_text not in self.book.tags:
            self.book.tags.append(tag_text)
            self.input.clear()
            self.refresh_tags()
