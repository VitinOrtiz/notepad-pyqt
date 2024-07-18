"""
Dialog windows used in the Notepad application
"""

__all__ = ['FindDialog', 'ReplaceDialog', 'AboutDialog']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import os
import platform
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QTextDocument, QTextCursor
from PyQt6.QtWidgets import (
    QDialog, QFrame, QLabel, QMessageBox,
    QLineEdit, QGroupBox, QRadioButton, 
    QCheckBox, QPushButton, QGridLayout, 
    QHBoxLayout, QSpacerItem, QSizePolicy
)
from .config import readConfig
from .logger import logger
from .translation import tr

_families = readConfig('font-ui-families')
if _families is None:
    _families = 'Arial'
_size = readConfig('font-ui-size')
if _size is None:
    _size = 10
_ui_font = QFont(_families, _size)

def _showNotFoundDialog_(text):
    app_name = readConfig('app-name')
    if app_name is None:
        app_name = 'Notepad'
    QMessageBox.information(
        None,
        app_name, 
        tr(f'Cannot find "{text}"'), 
        buttons=QMessageBox.StandardButton.Ok
    )

class FindDialog (QDialog):
    """Dialog for finding text in text editor."""

    def __init__(self, parent):
        """
        Initialize the FindDialog.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle(tr('Find'))
        self.setFont(_ui_font)

        # Input field
        find_label = QLabel(tr('Find what:'))
        find_label.setFont(_ui_font)
        self.find_text = QLineEdit(self)
        self.find_text.setFont(_ui_font)
        self.find_text.focusWidget()

        # Buttons
        findNext_button = QPushButton(tr('&Find Next'), self)
        findNext_button.setDefault(True)
        cancel_button = QPushButton(tr('Cancel'), self)

        # Radio buttons
        direction_group = QGroupBox(tr('Direction'), self)
        self.up_radio_buttton = QRadioButton(tr('Up'), direction_group)
        self.up_radio_buttton.setFont(_ui_font)
        self.down_radio_buttton = QRadioButton(tr('Down'), direction_group)
        self.down_radio_buttton.setFont(_ui_font)
        self.down_radio_buttton.setChecked(True)

        # Check boxes
        self.match_case_checkbox = QCheckBox(tr('Match &case'), self)
        self.wrap_around_checkbox = QCheckBox(tr('W&rap around'), self)

        # Button actions
        findNext_button.clicked.connect(self.onFindNextClicked)
        cancel_button.clicked.connect(self.close)

        grid = QGridLayout(self)
        grid.setSpacing(5)
        grid.addWidget(find_label, 0, 0)
        grid.addWidget(self.find_text, 0, 1, 1, 2)
        grid.addWidget(findNext_button, 0, 3)
        grid.addWidget(direction_group, 1, 2, 2, 1)
        grid.addWidget(cancel_button, 1, 3)
        grid.addWidget(self.match_case_checkbox, 2, 0)
        grid.addWidget(self.wrap_around_checkbox, 3, 0)
        self.setLayout(grid)
        
        hbox = QHBoxLayout(direction_group)
        hbox.addWidget(self.up_radio_buttton)
        hbox.addWidget(self.down_radio_buttton)
        direction_group.setLayout(hbox)

    def onFindNextClicked(self):
        """
        Handle the Find Next button click event to find the next or previous occurrence of the search text.
        """
        self._options: QTextDocument.FindFlag = None
        if self.match_case_checkbox.isChecked():
            self._options = QTextDocument.FindFlag.FindCaseSensitively
        if self.up_radio_buttton.isChecked():
            self.findPrevious()
        if self.down_radio_buttton.isChecked():
            self.findNext()

    def find(self, findBackward: bool = False) -> bool:
        """
        Find the next or previous occurrence of the search text.

        Args:
            findBackward (bool): Whether to search backwards.

        Returns:
            bool: True if the text was found, False otherwise.
        """
        if self._options is None:
            if findBackward:
                found = self.parent().editor.find(
                    self.find_text.text(), 
                    QTextDocument.FindFlag.FindBackward
                )
            else:
                found = self.parent().editor.find(self.find_text.text())
        else:
            if findBackward:
                found = self.parent().editor.find(
                    self.find_text.text(), 
                    self._options | QTextDocument.FindFlag.FindBackward
                )
            else:
                found = self.parent().editor.find(self.find_text.text(), self._options)
        return found
    
    def findNext(self):
        """
        Find the next occurrence of the search text, with optional wrap around.
        """
        found = self.find(False)
        if not found:
            if self.wrap_around_checkbox.isChecked():
                self.parent().editor.moveCursor(QTextCursor.MoveOperation.Start)
                found = self.find()
                if not found:
                    _showNotFoundDialog_(self.find_text.text())
            else:
                _showNotFoundDialog_(self.find_text.text())

    def findPrevious(self):
        """
        Find the previous occurrence of the search text, with optional wrap around.
        """
        found = self.find(True)
        if not found:
            if self.wrap_around_checkbox.isChecked():
                self.parent().editor.moveCursor(QTextCursor.MoveOperation.End)
                found = self.find(True)
                if not found:
                    _showNotFoundDialog_(self.find_text.text())
            else:
                _showNotFoundDialog_(self.find_text.text())

class ReplaceDialog (QDialog):
    """
    Dialog for finding and replacing text in a parent editor.
    """

    def __init__(self, parent):
        """
        Initialize the ReplaceDialog.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle(tr('Replace'))
        self.setFont(_ui_font)
        self.parent = parent

        # Text input
        find_label = QLabel(tr('Find what:'))
        find_label.setFont(_ui_font)
        self.find_text = QLineEdit(self)
        self.find_text.setFont(_ui_font)
        self.find_text.focusWidget()
        replace_label = QLabel(tr('Replace with:'))
        replace_label.setFont(_ui_font)
        self.replace_text = QLineEdit(self)
        self.replace_text.setFont(_ui_font)

        # Buttons
        findNext_button = QPushButton(tr('&Find Next'), self)
        replace_button = QPushButton(tr('&Replace'), self)
        replaceAll_button = QPushButton(tr('Replace &All'), self)
        cancel_button = QPushButton(tr('Cancel'), self)
        cancel_button.setDefault(True)

        # Check boxes
        self.match_case_checkbox = QCheckBox(tr('Match &case'), self)
        self.wrap_around_checkbox = QCheckBox(tr('W&rap around'), self)

        findNext_button.clicked.connect(self.findNext)
        replace_button.clicked.connect(self.replace)
        replaceAll_button.clicked.connect(self.replaceAll)
        cancel_button.clicked.connect(self.close)

        grid = QGridLayout(self)
        grid.setSpacing(5)
        grid.addWidget(find_label, 0, 0)
        grid.addWidget(self.find_text, 0, 1, 1, 2)
        grid.addWidget(findNext_button, 0, 3)
        grid.addWidget(replace_label, 1, 0)
        grid.addWidget(self.replace_text, 1, 1, 1, 2)
        grid.addWidget(replace_button, 1, 3)
        grid.addWidget(replaceAll_button, 2, 3)
        grid.addWidget(cancel_button, 3, 3)
        grid.addWidget(self.match_case_checkbox, 3, 0)
        grid.addWidget(self.wrap_around_checkbox, 4, 0)
        self.setLayout(grid)
        
    def find(self) -> bool:
        """
        Find the next occurrence of the search text.

        Returns:
            bool: True if the text was found, False otherwise.
        """
        if self.match_case_checkbox.isChecked():
            found = self.parent().editor.find(
                self.find_text.text(),
                QTextDocument.FindFlag.FindCaseSensitively
            )
        else:
            found = self.parent().editor.find(self.find_text.text())
        return found
    
    def findNext(self):
        """
        Find the next occurrence of the search text, with optional wrap around.
        """
        found = self.find()
        if not found:
            if self.wrap_around_checkbox.isChecked():
                self.parent().editor.moveCursor(QTextCursor.MoveOperation.Start)
                found = self.find()
                if not found:
                    _showNotFoundDialog_(self.find_text.text())
            else:
                _showNotFoundDialog_(self.find_text.text())

    def replace(self):
        """
        Replace the current occurrence of the search text with the replacement text, 
        with optional wrap around.
        """
        cursor: QTextCursor = self.parent().editor.textCursor()
        found = self.find()
        if not found:
            if self.wrap_around_checkbox.isChecked():
                self.parent().editor.moveCursor(QTextCursor.MoveOperation.Start)
                found = self.find()
                if found:
                    if cursor.hasSelection():
                        cursor.insertText(self.replace_text.text())
                        self.parent().editor.setTextCursor(cursor)
                else:
                    _showNotFoundDialog_(self.find_text.text())
        else:
            if cursor.hasSelection():
                cursor.insertText(self.replace_text.text())
                self.parent().editor.setTextCursor(cursor)

    def replaceAll(self):
        """
        Replace all occurrences of the search text with the replacement text.
        """
        cursor: QTextCursor = self.parent().editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.parent().editor.setTextCursor(cursor)

        while (self.find()):
            cursor.removeSelectedText()
            cursor.insertText(self.replace_text.text())
            self.parent().editor.setTextCursor(cursor)


class AboutDialog (QDialog):
    """
    This class defines an AboutDialog window in a PyQt application that 
    displays information about the Notepad application, including logos, 
    text content, and an OK button.
    """
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle(tr('About Notepad'))
        self.setFont(_ui_font)
        self.setFixedWidth(450)

        # Logo
        logo_label = QLabel(self)
        logo = QPixmap()
        logo_filename = readConfig('about-logo')
        if logo_filename is None:
            logo_filename = 'img/windows-logo-300.png'
        logo.load(logo_filename)
        logo_label.setPixmap(logo)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Horizontal Ruler
        hr = QFrame(self)
        hr.setFrameShape(QFrame.Shape.HLine)
        hr.setFrameShadow(QFrame.Shadow.Sunken)

        # Icon
        icon_label = QLabel(self)
        icon = QPixmap()
        icon_filename = readConfig('about-icon')
        if icon_filename is None:
            icon_filename = 'img/notepad-icon-32.png'
        icon.load(icon_filename)
        icon_label.setPixmap(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Platform
        os_name = f"{platform.system()} {platform.release()}"
        os_version = f"Version {platform.win32_ver()[1]} ({platform.architecture()[0]})"
        os_label = QLabel(os_name + os.linesep + os_version + os.linesep)

        vertical_space = QSpacerItem(50, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # Credits
        license = tr('This application is licensed under the MIT License')
        author = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'
        credits_label = QLabel(license + os.linesep + tr('Author: ') + author)

        # OK Button
        ok_button = QPushButton('OK', self)
        ok_button.setFixedWidth(75)
        ok_button.clicked.connect(self.close)

        grid = QGridLayout(self)
        grid.addWidget(logo_label, 0, 0, 1, 3) # Logo
        grid.addWidget(hr, 1, 0, 1, 3) # HR
        grid.addWidget(icon_label, 2, 0, 8, 1) # App Icon
        grid.setColumnMinimumWidth(0, 32)
        grid.addWidget(os_label, 2, 1, 1, 2)
        grid.addItem(vertical_space, 5, 1)
        grid.addWidget(credits_label, 6, 1, 1, 2)
        grid.addWidget(ok_button, 8, 2)
        
        self.setLayout(grid)
