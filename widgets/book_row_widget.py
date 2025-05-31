from PyQt6.QtWidgets import QWidget, QFrame, QHBoxLayout
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtCore import Qt 

from widgets.book_widget import BookWidget



# 行书架类

class BookRowWidget(QWidget):
    def __init__(self, row_index, books, main_window):
        super().__init__()
        self.row_index = row_index
        self.books = books
        self.main_window = main_window
        self.placeholder = None
        self.dragged_widget = None
        self.setAcceptDrops(True)

        self.insert_line = QFrame(self)
        self.insert_line.setFrameShape(QFrame.Shape.VLine)
        self.insert_line.setFrameShadow(QFrame.Shadow.Sunken)
        self.insert_line.setStyleSheet("background-color: red;")
        self.insert_line.setFixedWidth(3)
        self.insert_line.hide()

        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(15)
        self.h_layout.setContentsMargins(10, 0, 10, 0)
        self.setLayout(self.h_layout)

        self.refresh_row()
        

    # 刷新一行
    def refresh_row(self, books=None):
        if books is None:
            books = self.books

        while self.h_layout.count():
            item = self.h_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for col, book in enumerate(books):
            book_widget = BookWidget(book, self.row_index, col, self.main_window, self)
            self.h_layout.addWidget(book_widget)

        self.h_layout.addStretch()


    # 放置占位符
    def insert_placeholder_at(self, book_widget):
        layout = self.h_layout
        idx = layout.indexOf(book_widget)
        if self.placeholder:
            layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None
        placeholder = QWidget()
        placeholder.setObjectName("placeholder")
        placeholder.setFixedSize(book_widget.size())
        self.placeholder = placeholder
        
        layout.insertWidget(idx, placeholder)
        book_widget.hide()
        self.dragged_widget = book_widget
    
    # 去除占位符
    def remove_placeholder(self):
        if self.placeholder:
            layout = self.layout()
            layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None

    # 处理拖动结果
    def handle_drag_finished(self, drop_action):
        if hasattr(self, 'placeholder') and self.placeholder:
            self.h_layout.removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None

        if drop_action == Qt.DropAction.MoveAction:
            self.main_window.refresh_view()
        else:
            # 拖动取消，恢复隐藏的控件显示
            if hasattr(self, 'dragged_widget') and self.dragged_widget:
                self.dragged_widget.show()
                self.dragged_widget = None

    # （暂无事件）
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    # 鼠标移动事件
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasText():
            x = event.position().x()
            insert_col = self.estimate_insert_col(x)
            self.show_insert_line(insert_col)
            event.acceptProposedAction()
    
    # 鼠标离开事件
    def dragLeaveEvent(self, event):
        self.insert_line.hide()
        event.accept()

    # 鼠标停止按压事件
    def dropEvent(self, event: QDropEvent):
        try:
            from_row, from_col = map(int, event.mimeData().text().split(","))
            to_row = self.row_index

            pos = event.position()
            x = pos.x()

            insert_col = self.estimate_insert_col(x)
            if insert_col == -1:
                self.insert_line.hide()
                return

            self.main_window.insert_book((from_row, from_col), (to_row, insert_col))

            self.insert_line.hide()
            event.acceptProposedAction()
        except Exception as e:
            print("行级 drop 解析错误：", e)

    # 判断插入位置
    def estimate_insert_col(self, x_pos):
        threshold = 10 
        visible_widgets = []
        for i in range(self.h_layout.count()):
            item = self.h_layout.itemAt(i)
            widget = item.widget()
            if widget and widget.objectName() != "placeholder":
                visible_widgets.append(widget)
        for i, widget in enumerate(visible_widgets):
            mid_x = widget.x() + widget.width() / 2
            if mid_x - threshold < x_pos < mid_x + threshold:
                return -1 
            if x_pos < mid_x - threshold:
                return i
        return self.h_layout.count()  
    
    # 显示插入提示线
    def show_insert_line(self, insert_col):
        real_widgets = []
        for i in range(self.h_layout.count()):
            item = self.h_layout.itemAt(i)
            widget = item.widget()
            if widget and widget.objectName() != "placeholder":
                real_widgets.append(widget)

        if not real_widgets:
            self.insert_line.hide()
            return

        insert_col = max(0, min(insert_col, len(real_widgets)))

        if insert_col == len(real_widgets):
            last_widget = real_widgets[-1]
            x = last_widget.x() + last_widget.width()
        else:
            target_widget = real_widgets[insert_col]
            x = target_widget.x()

        self.insert_line.move(x - 8, 0)
        self.insert_line.setFixedHeight(self.height())
        self.insert_line.show()
