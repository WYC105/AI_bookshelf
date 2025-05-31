import json
import os
import copy

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon, QFont, QAction
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QScrollArea, QVBoxLayout, QHBoxLayout,
    QFrame, QMenu, QMessageBox, QLineEdit, QFileDialog, QSizePolicy, QToolBar, QToolButton, QInputDialog
)

import utlis
from douban_spider import DoubanBookSpider
from widgets.book_row_widget import BookRowWidget




# 主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的书架")

        self.edit_mode = False
        self.sort_ascending_per_row = {}
        self.spider = DoubanBookSpider()

        # 加载json文件中的书架数据
        try:
            self.books_2d = utlis.load_bookshelf_from_file()
        except FileNotFoundError:
            self.books_2d = []

        pure_data = utlis.books_2d_to_dict(self.books_2d)
        self.original_bookshelf_data = copy.deepcopy(pure_data)

        self.init_ui()
        self.setup_toolbar()
        self.setup_shortcuts()


    def init_ui(self):
        self.scroll = QScrollArea()
        self.container = QWidget()
        self.v_layout = QVBoxLayout(self.container)
        self.v_layout.setSpacing(20)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)
        self.setCentralWidget(self.scroll)

        for row_index, row_data in enumerate(self.books_2d):
            row_name = row_data["row_name"]
            row_books = row_data["books"]
            row_widget = self.create_named_book_row(row_name, row_books, row_index)
            self.v_layout.addWidget(row_widget)

        # 添加“新建书架”按钮
        add_row = QHBoxLayout()
        btn_add_shelf = QPushButton("➕")
        btn_add_shelf.setFixedHeight(40)
        btn_add_shelf.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 8px 20px;
                border: 2px dashed #888;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
        """)
        btn_add_shelf.clicked.connect(self.show_create_bookshelf_dialog)
        add_row.addWidget(btn_add_shelf)
        add_row.addStretch()
        self.v_layout.addLayout(add_row)

        self.v_layout.addStretch(1)
        

    # 编辑行书架名称
    def edit_row_name(self, row_index):
        current_name = self.books_2d[row_index]["row_name"]
        new_name, ok = QInputDialog.getText(self, "修改分类名称", "请输入新名称:", text=current_name)
        if ok and new_name.strip():
            self.books_2d[row_index]["row_name"] = new_name.strip()
            self.refresh_view()
    

    # 工具栏
    def setup_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)

        # 保存按钮
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_bookshelf)

        # 创建搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索书名…")
        self.search_input.setFixedWidth(200)

        # 创建搜索按钮
        search_button = QPushButton("搜索并添加")
        search_button.clicked.connect(self.on_search_book)

        # 创建编辑模式按钮
        self.edit_button = QToolButton()
        self.edit_button.setText("编辑模式")
        self.edit_button.setCheckable(True)
        self.edit_button.setIcon(QIcon.fromTheme("document-edit"))  # 使用系统图标，也可以换成自己的图标
        self.edit_button.setIconSize(QSize(20, 20))
        self.edit_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        font = QFont()
        font.setPointSize(12) 

        self.edit_button.setStyleSheet("""
            QToolButton {
                border: 2px solid gray;
                border-radius: 6px;
                padding: 4px 8px;
            }
            QToolButton:checked {
                background-color: lightgreen;
                border: 2px solid green;
            }
        """)  
        self.edit_button.toggled.connect(self.toggle_edit_mode)

        upload_action = QAction("上传图片识别", self)
        upload_action.triggered.connect(self.upload_image_and_add_book)
        

        # 添加到工具栏
        toolbar.addWidget(save_button)
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(search_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addAction(upload_action)
        

    # 快捷键
    def setup_shortcuts(self):
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_bookshelf)

    # 保存当前书架
    def save_bookshelf(self):
        utlis.save_bookshelf_to_file(self.books_2d)
        print("书架已保存。")
        self.statusBar().showMessage("书架已保存", 3000)


    def is_bookshelf_modified(self):
        """比较内存数据和磁盘数据是否一致，返回True表示有改动"""
        if not os.path.exists('bookshelf.json'):
            return bool(self.books_2d)

        try:
            with open('bookshelf.json', 'r', encoding='utf-8') as f:
                file_data = json.load(f)
        except Exception:
            return True
        pure_data = utlis.books_2d_to_dict(self.books_2d)
        return file_data != self.books_2d


    # 退出程序
    def closeEvent(self, event):
        if self.is_bookshelf_modified():
            reply = QMessageBox.question(
                self,
                "退出确认",
                "是否在退出前保存书架？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_bookshelf()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:  # Cancel
                event.ignore()
        else:
            event.accept()

    # 行书架图形化
    def create_named_book_row(self, row_name, books_1d, row_index):
        # 行容器
        row_widget = QWidget()
        h_layout = QHBoxLayout(row_widget)
        h_layout.setContentsMargins(10, 0, 10, 0)
        h_layout.setSpacing(10)

        # 左侧
        label_layout = QVBoxLayout()
        label_layout.setSpacing(5)

        # 书架名称
        name_label = QLabel(row_name)
        name_label.setFixedWidth(80)
        name_label.setStyleSheet("font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # 书架名称编辑按钮
        edit_button = QPushButton("✎")
        edit_button.setFixedSize(20, 20)
        edit_button.clicked.connect(lambda _, i=row_index: self.edit_row_name(i))

        # 删除书架按钮（小×）
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("""
            QPushButton {
                color: red;
                font-weight: bold;
                font-size: 16px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background-color: #fdd;
            }
        """)
        delete_button.setToolTip("删除当前书架")
        delete_button.clicked.connect(lambda _, i=row_index: self.confirm_delete_bookshelf(i))

        # 排序按钮
        sort_button = QPushButton("排序")
        sort_button.setFixedSize(60, 30)
        sort_button.setCheckable(True)
        sort_button.setStyleSheet("")


        # 升降序切换按钮
        order_button = QPushButton("↑")
        order_button.setFixedSize(30, 30)
        order_button.setCheckable(True)
        order_button.setToolTip("切换升序 / 降序")

        if row_index not in self.sort_ascending_per_row:
            self.sort_ascending_per_row[row_index] = True
        def update_order_button():
            order_button.setText("↑" if self.sort_ascending_per_row[row_index] else "↓")
        update_order_button()
        def toggle_order():
            self.sort_ascending_per_row[row_index] = not self.sort_ascending_per_row[row_index]
            update_order_button()
        order_button.clicked.connect(toggle_order)


        # 排序按钮挂载菜单
        sort_menu = QMenu(sort_button)
        sort_button.setMenu(sort_menu)

        # 排序字段列表
        sort_fields = [
            ("标题", "title"),
            ("作者", "author"),
            ("出版社", "publisher"),
            ("出版日期", "pub_date"),
            ("价格", "price"),
            ("评分", "rating"),
            ("评价人数", "rating_count"),
        ]

        def on_sort_triggered(field_key):
            def sorter():
                try:
                    ascending = self.sort_ascending_per_row.get(row_index, True)
                    reverse = not ascending
                    if field_key in ("rating", "rating_count"):
                        self.books_2d[row_index]["books"].sort(
                            key=lambda b: float(getattr(b, field_key, 0)) if getattr(b, field_key, None) not in (None, '') else 0,
                            reverse=reverse
                        )
                    elif field_key == "pub_date":
                        # 假设日期格式可直接字符串比较
                        self.books_2d[row_index]["books"].sort(
                            key=lambda b: getattr(b, field_key, ""),
                            reverse=reverse
                        )
                    else:
                        self.books_2d[row_index]["books"].sort(
                            key=lambda b: getattr(b, field_key, "").lower() if getattr(b, field_key, None) else "" ,
                            reverse=reverse
                        )
                    self.refresh_view()
                except Exception as e:
                    print("排序出错:", e)
            return sorter

        for label, key in sort_fields:
            action = QAction(label, sort_menu)
            action.triggered.connect(on_sort_triggered(key))
            sort_menu.addAction(action)

        # 控制菜单显示和固定
        def on_menu_about_to_show():
            sort_button.setChecked(True)
        def on_menu_about_to_hide():
            sort_button.setChecked(False)

        sort_menu.aboutToShow.connect(on_menu_about_to_show)
        sort_menu.aboutToHide.connect(on_menu_about_to_hide)

        edit_delete_layout = QHBoxLayout()
        edit_delete_layout.setSpacing(4)
        edit_delete_layout.setContentsMargins(0, 0, 0, 0)
        edit_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)       
        edit_delete_layout.addWidget(edit_button)
        edit_delete_layout.addWidget(delete_button)
        edit_delete_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        edit_delete_widget = QWidget()
        edit_delete_widget.setLayout(edit_delete_layout)

        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(2)
        sort_layout.setContentsMargins(0, 0, 0, 0)
        sort_layout.addWidget(sort_button)
        sort_layout.addWidget(order_button)
        sort_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        sort_widget = QWidget()
        sort_widget.setLayout(sort_layout)

        label_layout.addWidget(name_label)
        label_layout.addWidget(edit_delete_widget)
        label_layout.addWidget(sort_widget)
        label_layout.addStretch()

        # 生成左侧滚动区
        row_scroll = QScrollArea()
        row_scroll.setWidgetResizable(True)
        row_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        row_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        row_scroll.setFixedHeight(220)  

        row_container = BookRowWidget(row_index, books_1d, self)
        row_scroll.setWidget(row_container)
        
        h_layout.addLayout(label_layout)
        h_layout.addWidget(row_scroll)

        return row_widget
            
    # 刷新书架窗口
    def refresh_view(self):
        utlis.clear_layout(self.v_layout)

        for row_index, row_data in enumerate(self.books_2d):
            row_name = row_data["row_name"]
            row_books = row_data["books"]
            row_widget = self.create_named_book_row(row_name, row_books, row_index)
            self.v_layout.addWidget(row_widget)
        self.add_add_shelf_button()


    # 变动书籍位置
    def insert_book(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        # 防止越界
        if not (0 <= from_row < len(self.books_2d)) or not (0 <= to_row < len(self.books_2d)):
            return
        if not (0 <= from_col < len(self.books_2d[from_row]["books"])):
            return

        
        book = self.books_2d[from_row]["books"].pop(from_col)
        if from_row == to_row and from_col < to_col:
            to_col -= 1

        to_col = max(0, min(to_col, len(self.books_2d[to_row]["books"])))
        self.books_2d[to_row]["books"].insert(to_col, book)

        self.refresh_view()


    # 删除书籍
    def remove_book(self, row, col):
        if 0 <= row < len(self.books_2d) and 0 <= col < len(self.books_2d[row]["books"]):
            self.books_2d[row]["books"].pop(col)

            row_widget = self.v_layout.itemAt(row).widget()
            h_layout = row_widget.layout()
            row_scroll = h_layout.itemAt(1).widget() 
            row_container = row_scroll.widget() 
            row_container.refresh_row(self.books_2d[row]["books"])

    # 搜索按钮激活函数
    def on_search_book(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "提示", "请输入关键词")
            return

        # 爬取数据
        books = self.spider.search_books(keyword)
        if not books:
            QMessageBox.information(self, "结果", "未找到相关书籍")
            return

        book = self.spider.get_book_details(books[0])

        # 若没有书架，新建书架
        if not self.books_2d:
            self.books_2d.append({
                "row_name": "默认书架",
                "books": []
            })

        self.books_2d[0]["books"].insert(0, book)
        self.refresh_view()
    
    # 编辑模式
    def toggle_edit_mode(self, checked):
        self.edit_mode = checked

    # 上传图片（demo）
    
    def upload_image_and_add_book(self):
        from image_book_recognizer import gemini_vision_books
        from douban_spider import DoubanBookSpider

        file_path, _ = QFileDialog.getOpenFileName(self, "选择书脊照片", "", "Images (*.png *.jpg *.jpeg)")
        if not file_path:
            return  # 用户取消

        try:
            # 1. 调用 Gemini 获取识别结果
            books_info = gemini_vision_books(file_path)
            if not books_info:
                QMessageBox.warning(self, "识别失败", "没有识别到书籍信息。")
                return

            # 2. 调用豆瓣爬虫获取图书详细信息
            spider = DoubanBookSpider()
            first = books_info[0]
            query = f"{first.get('title', '')} {first.get('publisher', '')}".strip()
            search_results = spider.search_books(query)
            if not search_results:
                search_results = spider.search_books(first.get("title", ""))
            if not search_results:
                QMessageBox.information(self, "未找到", "未找到匹配图书。")
                return

            book = spider.get_book_details(search_results[0])

            # 3. 添加到书架第一排第一个位置
            if self.books_2d:
                self.books_2d[0]["books"].insert(0, book)
                self.refresh_view()
                QMessageBox.information(self, "添加成功", f"已添加图书：{book.title}")
            else:
                QMessageBox.warning(self, "添加失败", "当前书架为空。")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理失败：{e}")

    # 新建书架按钮激活函数
    def show_create_bookshelf_dialog(self):
        text, ok = QInputDialog.getText(self, "新建书架", "请输入书架名称：")
        if ok and text.strip():
            self.add_new_bookshelf(text.strip())

    # 新建书架
    def add_new_bookshelf(self, name):
        new_row_data = {
            "row_name": name,
            "books": []
        }
        self.books_2d.append(new_row_data)
        self.refresh_view()

    def add_add_shelf_button(self):
        add_row = QHBoxLayout()
        btn_add_shelf = QPushButton("➕")
        btn_add_shelf.setFixedHeight(40)
        btn_add_shelf.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 8px 20px;
                border: 2px dashed #888;
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #ddd;
            }
        """)
        btn_add_shelf.clicked.connect(self.show_create_bookshelf_dialog)
        add_row.addWidget(btn_add_shelf)
        add_row.addStretch()
        self.v_layout.addLayout(add_row)

    def confirm_delete_bookshelf(self, row_index):
        total_shelves = len(self.books_2d)
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("删除书架确认")
        msg_box.setText(f"您确定要删除书架【{self.books_2d[row_index]['row_name']}】吗？")

        msg_box.setInformativeText(
            "选择操作：\n"
            "- 点击【合并】，将书籍合并到相邻的另一个书架尾端\n"
            "- 点击【删除】，删除当前书架所有书籍\n"
            "- 点击【取消】，不执行任何操作"
        )

        delete_button = msg_box.addButton("删除", QMessageBox.ButtonRole.DestructiveRole)
        cancel_button = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        if total_shelves > 1:
            merge_button = msg_box.addButton("合并", QMessageBox.ButtonRole.AcceptRole)

        msg_box.exec()

        clicked_button = msg_box.clickedButton()
        if total_shelves > 1 and clicked_button == merge_button:
            self.merge_bookshelf_adjacent(row_index)
        elif clicked_button == delete_button:
            self.delete_bookshelf(row_index)
        elif clicked_button == cancel_button:
            pass
    
    def merge_bookshelf_adjacent(self, row_index):
        total_shelves = len(self.books_2d)
        current_books = self.books_2d[row_index]["books"]

        if row_index == 0:
            # 第一个书架，合并到第二个书架尾端
            target_index = 1
        elif row_index == total_shelves - 1:
            # 最后一个书架，合并到前一个书架尾端
            target_index = row_index - 1
        else:
            # 中间书架，默认合并到前一个书架尾端（你可以改成后一个）
            target_index = row_index - 1

        self.books_2d[target_index]["books"].extend(current_books)
        del self.books_2d[row_index]
        self.refresh_view()
    
    def delete_bookshelf(self, row_index):
        # 删除当前书架
        del self.books_2d[row_index]
        self.refresh_view()

