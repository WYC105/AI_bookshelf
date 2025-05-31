import sys

from PyQt6.QtWidgets import QApplication

from mainwindow import MainWindow



if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = MainWindow()
    win.resize(1300, 1000)
    win.show()
    sys.exit(app.exec())