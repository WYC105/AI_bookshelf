from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mainwindow import MainWindow

import hashlib
from pathlib import Path
import requests
from PyQt6 import sip

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu, QMessageBox, QDialog
from PyQt6.QtGui import QPixmap, QDrag, QMouseEvent, QContextMenuEvent, QGuiApplication, QAction
from PyQt6.QtCore import Qt, QMimeData, QPoint, QTimer

from widgets.book_info_popup import BookInfoPopup
from widgets.tag_editor import TagEditorDialog


# 书籍图形类
class BookWidget(QWidget):
    def __init__(self, book,row, col, main_window: 'MainWindow', parent=None):
        super().__init__(parent)
        self.book = book
        self.row = row
        self.col = col
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setFixedWidth(120)
        self.init_ui()

#       self.scroll_timer = QTimer(self)
#       self.scroll_timer.timeout.connect(self.auto_scroll)
#       self.scroll_direction = None  # 'left' 或 'right'


    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0,0,0,0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        # 1. 书封面
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cover_label)
        
        self.load_cover(self.book.cover_url)
        
        # 2. 书名
        self.title_label = QLabel(self.book.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label)
        
        # 3. 作者
        self.author_label = QLabel(self.book.author)
        self.author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.author_label)

    # 双击事件(暂无事件)
    def mouseDoubleClickEvent(self, event):
        event.accept()

    # 点击/长按事件
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            
            if not self.window().edit_mode:
                # 非编辑模式下，弹出详情卡
                global_pos = self.mapToGlobal(event.pos())
                popup = BookInfoPopup(self.book)
                popup.adjustSize()
                popup.move(popup.adjust_position(global_pos)-QPoint(5,5))  # 自动修正位置
                popup.show()
                self.info_popup = popup 

            else:
                self.setWindowOpacity(0.4)  

                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText(f"{self.row},{self.col}")
                drag.setMimeData(mime_data)

                self.hide()
                parent = self.parentWidget()
                self.parentWidget().insert_placeholder_at(self)

                pixmap = self.grab()   
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.pos())  
                

                drop_action = drag.exec(Qt.DropAction.MoveAction)
                if not sip.isdeleted(parent):
                    parent.handle_drag_finished(drop_action)

    def load_cover(self, url):
        if url:
            try:
                cache_dir = Path("cache")
                cache_dir.mkdir(exist_ok=True)

                # 用 url 的哈希值作为文件名
                filename = hashlib.md5(url.encode("utf-8")).hexdigest() + ".jpg"
                filepath = cache_dir / filename

                if filepath.exists():
                    # 如果缓存存在，直接加载本地文件
                    pixmap = QPixmap(str(filepath))
                else:
                    # 下载图片并缓存
                    headers = {
                        "User-Agent": "Mozilla/5.0"
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    filepath.write_bytes(response.content)
                    pixmap = QPixmap(str(filepath))
                pixmap = pixmap.scaledToWidth(100, Qt.TransformationMode.SmoothTransformation)
                self.cover_label.setPixmap(pixmap)
            except Exception as e:
                print("加载封面失败:", e)
                self.cover_label.setText("封面加载失败")
        else:
            self.cover_label.setText("无封面")

    # 右键挂载菜单
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = menu.addAction("删除")

        menu.addSeparator()

        action_edit_tag = QAction("编辑标签", self)

        def open_tag_editor():
            dialog = TagEditorDialog(self.book, self)
            if dialog.exec():
                print(f"已更新《{self.book.title}》的标签为: {self.book.tags}")
                self.main_window.refresh_view()

        action_edit_tag.triggered.connect(open_tag_editor)
        menu.addAction(action_edit_tag)

        action = menu.exec(event.globalPos())
        
        if action == delete_action:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除《{self.book.title}》吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.remove_book(self.row, self.col)
