"""Components used in the Notepad application

The components defined in this module include `MenuBar` and `StatusBar`. 
The menu is configured with a `JSON` file which action slots are defined
in the main application class named `Notepad`.
"""

__all__ = ['MenuBar', 'StatusBar']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import codecs
import json
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QLabel, QMenu, QMenuBar, QStatusBar, QWidget
from .config import readConfig
from .logger import showError, logger

# Configuration
try:
    _config_file = 'config/menubar.json'
    with open(_config_file, 'r') as _menubar_config:
        _menubar = json.load(_menubar_config)
except FileNotFoundError as e:
    showError(f"File {_config_file} not found. {e}")
except PermissionError as e:
    showError(f"Permission denied to open {_config_file}. {e}")
except UnicodeDecodeError as e:
    showError(f"File encoding error while reading file {_config_file}. {e}")
except Exception as e:
    showError(f"Error parsing JSON file {_config_file}. {e}")

class MenuBar(QMenuBar):
    """
    Custom menu bar to build menus and actions dynamically from a configuration.
    """

    def __init__(self, parent):
        """
        Initialize the MenuBar.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self._iconset = _menubar['iconset']
        self.buildMenubar(_menubar['menubar'])

    def buildMenubar(self, menubar_config):
        """
        Build the menubar from a configuration.

        Args:
            menubar_config: The configuration for the menubar.
        """
        for menu_config in menubar_config:
            menu = self.buildMenu(self, menu_config)
            self.addMenu(menu)

    def buildMenu(self, parent: QMenu|QMenuBar, menu_config) -> QMenu:
        """
        Build a menu from a configuration.

        Args:
            parent (QMenu | QMenuBar): The parent menu or menubar.
            menu_config: The configuration for the menu.

        Returns:
            QMenu: The constructed menu.
        """
        menu = QMenu(parent)
        menu.setTitle(menu_config['text'])
        # Optional menu icon
        if 'icon' in menu_config:
            menu.setIcon(QIcon(self._iconset + menu_config['icon']))

        for child_config in menu_config['children']:
            match(child_config['type']):
                case 'separator':
                    menu.addSeparator()
                case 'action':
                    action = self.buildAction(child_config)
                    menu.addAction(action)
                case 'menu':
                    submenu = self.buildMenu(menu, child_config)
                    menu.addMenu(submenu)
                case _:
                    logger.error(f"Unsupported child type {child_config['type']} in menu configuration")
        return menu

    def buildAction(self, action_config) -> QAction:
        """
        Build an action from a configuration.

        Args:
            action_config: The configuration for the action.

        Returns:
            QAction: The constructed action.
        """
        action = QAction(self)
        if 'text' in action_config:
            action.setText(action_config['text'])
        else:
            showError('JSON key "text" is required for child type action in menubar configuration.')
        if 'icon' in action_config:
            action.setIcon(QIcon(self._iconset + action_config['icon']))
        if 'shortcut' in action_config:
            action.setShortcut(action_config['shortcut'])
        if 'status-tip' in action_config:
            action.setStatusTip(action_config['status-tip'])
        if 'slot' in action_config:
            action.triggered.connect(eval(f"self.parent().{action_config['slot']}"))
        else:
            showError('JSON key "slot" is required for child type action in menubar configuration.')
        if 'checkable' in action_config:
            action.setCheckable(action_config['checkable'])
        if 'checked' in action_config:
            action.setChecked(action_config['checked'])
        return action    
        
    def onUndoAvailable(self, available: bool):
        """
        Enable or disable the undo action based on availability.

        Args:
            available (bool): Whether the undo action is available.
        """
        try:
            edit_menu: QMenu = self.actions()[1].menu()
        except KeyError:
            showError('Edit menu not found')
        else:
            try:
                undo_action: QAction = edit_menu.actions()[0]
            except KeyError:
                showError('Undo action not found')
            else:
                undo_action.setEnabled(available)

    def onRedoAvailable(self, available: bool):
        """
        Enable or disable the redo action based on availability.

        Args:
            available (bool): Whether the redo action is available.
        """
        edit_menu: QMenu = self.actions()[1].menu()
        redo_action: QAction = edit_menu.actions()[1]
        redo_action.setEnabled(available)

    def onCopyAvailable(self, textSelected: bool):
        """
        Enable or disable the copy-related actions based on text selection.

        Args:
            textSelected (bool): Whether text is selected.
        """
        edit_menu: QMenu = self.actions()[1].menu()

        cut_action: QAction = edit_menu.actions()[3]
        copy_action: QAction = edit_menu.actions()[4]
        del_action: QAction = edit_menu.actions()[6]

        cut_action.setEnabled(textSelected)
        copy_action.setEnabled(textSelected)
        del_action.setEnabled(textSelected)

    def onTextChanged(self, hasText: bool):
        """
        Enable or disable the find actions based on text presence.

        Args:
            hasText (bool): Whether there is text to find.
        """
        edit_menu: QMenu = self.actions()[1].menu()

        find_action: QAction = edit_menu.actions()[8]
        find_next_action: QAction = edit_menu.actions()[9]
        find_prev_action: QAction = edit_menu.actions()[10]

        find_action.setEnabled(hasText) # Find
        find_next_action.setEnabled(hasText) # Find Next
        find_prev_action.setEnabled(hasText) # Find Previous


class StatusBar(QStatusBar):
    """
    Custom status bar to display position, zoom level, line separator, 
    and encoding information.
    """

    def __init__(self, parent: QWidget):
        """
        Initialize the StatusBar.

        Args:
            parent (QWidget): The parent widget.
        """
        super().__init__(parent)

        # Moves the label border from its default position at the right to the left
        self.setStyleSheet("item { border-left: 1px solid lightgray; }")

        self._position_label = QLabel(self)
        self._position_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._position_label.setFixedWidth(135)
        self._position_label.setContentsMargins(10, 0, 0, 0)
        self._position_label.setTextFormat(Qt.TextFormat.PlainText)
        self.setPosition(1,1)
        self.addPermanentWidget(self._position_label)

        self._zoom_label = QLabel(self)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._zoom_label.setFixedWidth(45)
        self._zoom_label.setContentsMargins(5, 0, 0, 0)
        self.setZoom(100)
        self.addPermanentWidget(self._zoom_label)

        self._linesep_label = QLabel(self)
        self._linesep_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._linesep_label.setFixedWidth(115)
        self._linesep_label.setContentsMargins(5, 0, 0, 0)
        self.setLineSep(os.linesep)
        self.addPermanentWidget(self._linesep_label)

        self._encoding_label = QLabel(self)
        self._encoding_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._encoding_label.setFixedWidth(95)
        self._encoding_label.setContentsMargins(5, 0, 0, 0)
        self.setEncoding('utf-8')
        self.addPermanentWidget(self._encoding_label)

    def setPosition(self, line:int, column:int):
        """
        Set the position label to display the current line and column.

        Args:
            line (int): The current line number.
            column (int): The current column number.

        Raises:
            ValueError: If line or column is less than or equal to 0.
        """
        if line > 0 and column > 0:
            label = f'Ln {line}, Col {column}'
            self._position_label.setText(label)
        else:
            raise ValueError(line, column)

    def setZoom(self, zoom:int):
        """
        Set the zoom label to display the current zoom percentage.

        Args:
            zoom (int): The current zoom level.

        Raises:
            ValueError: If the zoom level is not within the allowed range.
        """
        # zoom-min <= zoom <= zoom-max
        zoom_min = readConfig('zoom-min')
        if zoom_min is None:
            zoom_min = 10
        zoom_max = readConfig('zoom-max')
        if zoom_max is None:
            zoom_max = 500
        if zoom_min <= zoom and zoom <= zoom_max:
            self._zoom_label.setText(f'{zoom}%')
        else:
            raise ValueError(zoom)

    def setLineSep(self, linesep:str):
        """
        Set the line separator label to display the current line separator.

        Args:
            linesep (str): The current line separator.

        Raises:
            ValueError: If the line separator is not recognized.
        """
        match linesep:
            case '\n':
                self._linesep_label.setText('Linux (LF)')
            case '\r':
                self._linesep_label.setText('Mac (CR)')
            case '\r\n':
                self._linesep_label.setText('Windows (CRLF)')
            case _:
                raise ValueError(linesep)

    def setEncoding(self, encoding:str):
        """
        Set the encoding label to display the current encoding.

        Args:
            encoding (str): The encoding to set.

        Raises:
            ValueError: If the encoding is not recognized.
        """
        try:
            info = codecs.lookup(encoding)
        except LookupError:
            raise ValueError(encoding)
        else:
            self._encoding_label.setText(info.name.upper())
