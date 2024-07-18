__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import sys
from PyQt6.QtWidgets import QApplication
from src.app import Notepad

# Main
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Notepad()
    w.show()
    app.exec()
