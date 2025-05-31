from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QDesktopServices, QGuiApplication
from PyQt6.QtCore import Qt, QUrl, QPoint




# 书籍详情卡类
class BookInfoPopup(QWidget):
    def __init__(self, book, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.book = book
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.init_ui()

    def init_ui(self):
        v_layout = QVBoxLayout()
        v_layout.setContentsMargins(8, 8, 8, 8)
        v_layout.setSpacing(6)
        self.setLayout(v_layout)

        # 关闭按钮
        btn_close = QPushButton('✕')
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("border:none; font-weight:bold;")

        title_label = QLabel(f"<b>{self.book.title}</b>")
        title_label.setWordWrap(True)

        h_title_layout = QHBoxLayout()
        h_title_layout.addWidget(title_label)
        h_title_layout.addStretch()  
        h_title_layout.addWidget(btn_close)
        v_layout.addLayout(h_title_layout)

        # 显示信息文本（除了 url、cover_url、source）
        info_text =(
            f"作者: {self.book.author}<br>"
            f"出版社: {self.book.publisher}<br>"
            f"出版日期: {self.book.pub_date}<br>"
            f"价格: {self.book.price}<br>"
            f"评分: {self.book.rating} ({self.book.rating_count}人评价)<br>"
            f"简介: {self.book.summary}"
        )
        text_label = QLabel(info_text)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v_layout.addWidget(text_label)

        if self.book.tags:
            tag_layout = QHBoxLayout()
            tag_label = QLabel("标签:")
            tag_layout.addWidget(tag_label)

            tags_text = ", ".join(self.book.tags)
            tags_label = QLabel(tags_text)
            tags_label.setStyleSheet("color: gray;")
            tags_label.setWordWrap(False)
            tags_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            tags_label.setMaximumHeight(20)
            tags_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            tags_label.setToolTip(tags_text)  # 鼠标悬停可查看完整标签

            tag_layout.addWidget(tags_label)
            v_layout.addLayout(tag_layout)

        # 访问链接按钮
        btn_visit = QPushButton("访问书籍链接")
        btn_visit.clicked.connect(self.open_url)
        v_layout.addWidget(btn_visit)

        self.setFixedWidth(300)
    
    def adjust_position(self, pos: QPoint):
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        popup_width = self.width()
        popup_height = self.height()

        x = pos.x()
        y = pos.y()

        # 如果超出右边界
        if x + popup_width > screen_geometry.right():
            x = screen_geometry.right() - popup_width
        # 如果超出下边界
        if y + popup_height > screen_geometry.bottom():
            y = screen_geometry.bottom() - popup_height
        # 如果弹出位置太靠左/上，也要处理
        x = max(screen_geometry.left(), x)
        y = max(screen_geometry.top(), y)

        return QPoint(x, y)

    # 访问链接
    def open_url(self):
        if self.book.url:
            QDesktopServices.openUrl(QUrl(self.book.url))

    def enterEvent(self, event):
        event.accept()

    def leaveEvent(self, event):
        # 鼠标离开时关闭详情卡
        self.close()
