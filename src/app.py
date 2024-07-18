__all__ = ['Notepad']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import os
import datetime as dt
import webbrowser
from PyQt6.QtGui import QTextOption, QTextCursor, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, 
    QFileDialog, QMessageBox, 
    QFontDialog, QInputDialog
)
from PyQt6.QtPrintSupport import QPrintDialog, QPageSetupDialog, QPrinter
from .config import readConfig
from .logger import showError, logger
from .translation import tr
from .components import MenuBar, StatusBar
from .dialogs import FindDialog, ReplaceDialog, AboutDialog

class Notepad(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self._filename = readConfig('file-name')
        if self._filename is None:
            self._filename = 'Untitled'
        self._zoom = readConfig('zoom-restore')
        if self._zoom is None:
            self._zoom = 100
        self._zoom_factor = readConfig('zoom-factor')
        if self._zoom_factor is None:
            self._zoom_factor = 10
        self._line = 1
        self._col = 1
        self._printer = QPrinter(QPrinter.PrinterMode.PrinterResolution)

        self.setWindowTitle(self.getWindowTitle())
        icon_filename = readConfig('window-icon')
        if icon_filename is None:
            self.setWindowIcon(QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew))
        else: 
            self.setWindowIcon(QIcon(icon_filename))
        self.setMenuBar(MenuBar(self))
 
        self.editor = QTextEdit(self)
        self.editor.setAcceptRichText(False)
        self.setCentralWidget(self.editor)
        self.editor.document().modificationChanged.connect(self.setWindowModified)
        self.editor.undoAvailable.connect(self.menuBar().onUndoAvailable)
        self.editor.redoAvailable.connect(self.menuBar().onRedoAvailable)
        self.editor.copyAvailable.connect(self.menuBar().onCopyAvailable)
        self.editor.textChanged.connect(self.onTextChanged)
        self.editor.cursorPositionChanged.connect(self.onCursorPositionChanged)
        self.editor.setStyleSheet(
            "border: 1px solid lightgray; \
            selection-color: white; \
            selection-background-color: rgb(53, 126, 199);"
        )
        self.setStatusBar(StatusBar(self))

        self._find_dialog = FindDialog(self)
        self._replace_dialog = ReplaceDialog(self)

        logger.info(f"Notepad class initiated")

    # File / New File
    def newFile(self):
        """
        Create a new file, prompting the user to save the current file if it is modified.
        """
        # Check if file is saved
        if self.isWindowModified():
            reply = self.unsavedFileDialog()
            match reply:
                case QMessageBox.StandardButton.Save:
                    self.save()
                case QMessageBox.StandardButton.Discard:
                    self.createNewFile()
                case QMessageBox.StandardButton.Cancel: 
                    pass
        else:
            self.createNewFile()

    def createNewFile(self):
        """
        Create a new file by clearing the editor and resetting the window title and modification status.
        """
        self.editor.clear()
        self.setWindowTitle(self.getWindowTitle())
        self.setWindowModified(False)
        logger.info(f"New file created")

    # File / New Window
    def newWindow(self):
        # How to open a new instance of the application?
        logger.info('New Window - To be implemented')

    # File / Open...
    def open(self):
        """
        Open a file, prompting the user to save the current file if it is modified.
        """
        # Check if file is saved
        if self.isWindowModified():
            reply = self.unsavedFileDialog()
            match reply:
                case QMessageBox.StandardButton.Save:
                    self.save()
                    self.openFile()
                case QMessageBox.StandardButton.Discard:
                    self.openFile()
                case QMessageBox.StandardButton.Cancel:
                    return
        else:
            self.openFile()

    def openFile(self):
        """
        Open a file and load its content into the editor, handling various exceptions.
        """
        # User directory
        user_dir = readConfig('file-dialog-directory')
        if user_dir is None:
            user_dir = '~'
        dir = os.path.expanduser(user_dir)
        # File filter
        file_filter = readConfig('file-dialog-filters')
        if file_filter is None:
            file_filter = 'Text Documents(*.txt);;All Files(*.*)'
        # Show open file dialog
        filename, _ = QFileDialog.getOpenFileName(
            parent = self, 
            caption = tr('Open'), 
            directory = dir, 
            filter = file_filter
        )
        if filename != '':
            # Encoding
            encoding = readConfig('file-encoding')
            if encoding is None:
                encoding = 'utf_8'
            # Open file for reading
            try:
                text = open(filename, 'r', encoding=encoding).read()
            except FileNotFoundError as e:
                showError(f"File {filename} not found. {e}")
            except PermissionError as e:
                showError(f"Permission denied to open {filename}. {e}")
            except UnicodeDecodeError as e:
                showError(f"File encoding error while reading file {filename}. {e}")
            except Exception as e:
                showError(f"Error opening file {filename}. {e}")
            else:
                # Load file content on editor and reset modified flag
                self._filename = filename
                self.editor.setPlainText(text)
                self.setWindowTitle(self.getWindowTitle())
                self.setWindowModified(False)
                logger.info(f"File {filename} opened")
        else:
            logger.info("Open file dialog was cancelled by user")

    # File / Save
    def save(self):
        """
        Save the current file. If the file name matches the default, prompt the user to save as a new file.
        """
        if self._filename == readConfig('file-name'):
            self.saveAs()
        else:
            try:
                with open(self._filename, 'w') as file:
                    file.write(self.editor.toPlainText())
            except FileNotFoundError as e:
                showError(f"File {self._filename} not found. {e}")
            except PermissionError as e:
                showError(f"No write permission for file {self._filename}. {e}")
            except UnicodeDecodeError as e:
                showError(f"File encoding error while writting file {self._filename}. {e}")
            except Exception as e:
                showError(f"Error writting file {self._filename}. {e}")
            else:
                self.setWindowModified(False)
                logger.info(f"File {self._filename} was saved")

    # File / Save As...
    def saveAs(self):
        """
        Save the current file with a new name, prompting the user to choose the location and file name.
        """
        # User directory
        user_dir = readConfig('file-dialog-directory')
        if user_dir is None:
            user_dir = '~'
        dir = os.path.expanduser(user_dir)
        # File extension
        file_extension = readConfig('file-extension')
        if file_extension is None:
            file_extension = "*.txt"
        dir += '/' + file_extension
        # File filter
        file_filter = readConfig('file-dialog-filters')
        if file_filter is None:
            file_filter = 'Text Documents(*.txt);;All Files(*.*)'
        # File Save As dialog
        filename, _ = QFileDialog.getSaveFileName(
            parent = self, 
            caption = tr('Save As'), 
            directory = dir,
            filter = file_filter
        )
        if filename != '':
            # Encoding
            encoding = readConfig('file-encoding')
            if encoding is None:
                encoding = 'utf_8'
            # Write to file
            try:
                with open(filename, 'w', encoding=encoding) as file:
                    file.write(self.editor.toPlainText())
            except FileNotFoundError as e:
                showError(f"File {filename} not found. {e}")
            except PermissionError as e:
                showError(f"No write permission for file {filename}. {e}")
            except UnicodeDecodeError as e:
                showError(f"File encoding error while writting file {filename}. {e}")
            except Exception as e:
                showError(f"Error writting file {filename}. {e}")
            else:
                self._filename = filename
                self.setWindowTitle(self.getWindowTitle())
                self.setWindowModified(False)
                logger.info(f"File {filename} was saved")
        else:
            logger.info("Save As file dialog was cancelled by user")

    # File / Page Setup...
    def showPageSetupDialog(self):
        """
        Creates and displays a page setup dialog in a PyQt application.
        """
        dialog = QPageSetupDialog(self._printer, self)
        reply = dialog.exec()

    # File / Print...
    def showPrintDialog(self):
        """
        Creates and displays a print dialog window in a PyQt application.
        """
        dialog = QPrintDialog(self._printer, self)
        reply = dialog.exec()

    # File / Exit
    def exitApplication(self):
        """
        Prompts the user to save a file if it has been modified before
        closing the application.
        """
        # Show dialog asking user to save file
        if self.isWindowModified():
            reply = self.unsavedFileDialog()
            match reply:
                case QMessageBox.StandardButton.Save:
                    self.save()
                    self.close()
                case QMessageBox.StandardButton.Discard:
                    self.close()
                case QMessageBox.StandardButton.Cancel:
                    pass
        else:
            self.close()
            logger.info(f"Application closed")

    # Edit / Undo
    def undo(self):
        """
        Undoes the last operation.
        """
        self.editor.undo()

    # Edit / Redo
    def redo(self):
        """
        Redoes the last operation.
        """
        self.editor.redo()

    # Edit / Cut
    def cut(self):
        """
        Cuts the selected text in the editor.
        """
        self.editor.cut()

    # Edit / Copy
    def copy(self):
        """
        Copies the content from the editor.
        """
        self.editor.copy()

    # Edit / Paste
    def paste(self):
        """
        Pastes the content from the clipboard into the editor.
        """
        self.editor.paste()

    # Edit / Delete
    def delete(self):
        """
        Deletes the character at the current cursor position in the text editor.
        """
        self.editor.textCursor().deleteChar()

    # Edit / Find
    def showFindDialog(self):
        """
        Displays a Find Dialog window
        """
        self._find_dialog.find_text.setText(self.editor.textCursor().selectedText())
        self._find_dialog.show()

    # Edit / Find Next
    def findNext(self):
        """
        Searches for the next occurrence of a specified text in an editor.
        """
        self._find_dialog.findNext()

    # Edit / Find Previous
    def findPrevious(self) -> bool:
        """
        Searches for the previous occurrence of a specified text in an editor.
        """
        self._find_dialog.findPrevious()

    # Edit / Replace
    def showReplaceDialog(self):
        """
        Creates and displays a replace text dialog window.
        """
        self._replace_dialog.find_text.setText(self.editor.textCursor().selectedText())
        self._replace_dialog.show()

    def replace(self):
        """
        Searches for a specified text in an editor and replaces it with 
        another text if found.
        """
        self._replace_dialog.replace()

    def replaceAll(self):
        """
        Searches for all instances of a specified text in an editor and replaces
        them with another.
        """
        self._replace_dialog.replaceAll()

    # Edit / Go To
    def goTo(self):
        """
        Prompts the user to input a line number and moves the cursor to that 
        line in the editor if the input is valid.
        """
        line, accepted = QInputDialog.getInt(
            self, 
            tr("Go To Line"), 
            tr("Line number:"), 
            self._line
        )
        if accepted and line > 0:
            self.editor.moveCursor(
                QTextCursor.MoveOperation.Start
            )
            current_line = 1
            while(current_line < line):
                self.editor.moveCursor(
                    QTextCursor.MoveOperation.Down
                )
                current_line += 1
                if self.editor.textCursor().atEnd():
                    break
            logger.info(f"Moved cursor to line {line}")

    # Edit / Select All
    def selectAll(self):
        """
        Selects all text in the editor.
        """
        self.editor.selectAll()

    # Edit / Time Date
    def insertDateTime(self):
        """
        Inserts the current date and time into a text editor using a specified
        datetime format.
        """
        now = dt.datetime.now()
        format = readConfig('datetime-format')
        if format is None:
            format = '%I:%M %p %m/%d/%Y'
        dateTime = now.strftime(format)
        self.editor.insertPlainText(dateTime)
        logger.info(f"Inserted date/time {dateTime}")

    # Format / Word Wrap
    def toggleWordWrap(self, enabled:bool):
        """
        Toggles word wrap mode in a text editor based on the `enabled` parameter.

        Args:
            enabled (bool): determines whether word wrap should be enabled or disabled in the editor.
        """
        if enabled:
            self.editor.setWordWrapMode(
                QTextOption.WrapMode.WordWrap
            )
        else:
            self.editor.setWordWrapMode(
                QTextOption.WrapMode.NoWrap
            )

    # Format / Font...
    def showFontDialog(self):
        """
        Creates and displays a font dialog window.
        """
        dialog = QFontDialog(self)
        dialog.show()

    # View / Zoom / Zoom In
    def zoomIn(self):
        """
        Increases the zoom level by zoom factor units if the current zoom 
        level is less than the maximum allowed zoom level.
        """
        # Maximum Zoom
        zoom_max = readConfig('zoom-max')
        if zoom_max is None:
            zoom_max = 500
        # Zoom in until max zoom is reached
        if (self._zoom < zoom_max):
            self.editor.zoomIn()
            self._zoom += self._zoom_factor
            self.statusBar().setZoom(self._zoom)

    # View / Zoom / Zoom Out
    def zoomOut(self):
        """
        Decreases the zoom level by zoom factor if it is greater than the 
        minimum zoom level allowed.
        """
        # Minimum Zoom
        zoom_min = readConfig('zoom-min')
        if zoom_min is None:
            zoom_min = 10
        # Zoom out until min zoom is reached
        if (self._zoom > zoom_min):
            self.editor.zoomOut()
            self._zoom -= self._zoom_factor
            self.statusBar().setZoom(self._zoom)

    # View / Zoom / Restore Default Zoom 
    def restoreZoom(self):
        """
        Adjusts the zoom level of an editor to a default value and updates the
        status bar accordingly.
        """
        # Zoom restore
        zoom_restore = readConfig('zoom-restore')
        if zoom_restore is None:
            zoom_restore = 100
        # Calculate range to restore zoom
        if (self._zoom < zoom_restore):
            range = int((zoom_restore - self._zoom) / self._zoom_factor)
            self.editor.zoomIn(range)
        elif (self._zoom > zoom_restore):
            range = int((self._zoom - zoom_restore) / self._zoom_factor)
            self.editor.zoomOut(range)
        # 
        self._zoom = zoom_restore
        self.statusBar().setZoom(self._zoom)

    # View / Status Bar
    def toggleStatusBar(self, visible:bool):
        """
        Toggles the visibility of the status bar based on the boolean 
        parameter `visible`.

        Args:
            visible (bool): Determines whether the status bar should be shown 
                or hidden.
        """
        self.statusBar().setVisible(visible)

    # Help / View Help
    def viewHelp(self):
        """
        Opens a web page with help about Notepad
        """
        url = readConfig('help-view')
        webbrowser.open(url)

    # Help / About
    def about(self):
        """
        Displays an AboutDialog window.
        """
        dialog = AboutDialog(self)
        dialog.show()

    # HELPER FUNCTIONS    
    def unsavedFileDialog(self) -> QMessageBox.StandardButton:
        """
        Prompts the user to save changes to a file with options to save,
        discard changes, or cancel.
        """
        # Ask the user to save the file
        filename = tr(os.path.basename(self._filename))
        if filename == '':
            filename = readConfig('file-name')
            if filename is None:
                filename = 'Untitled'
        app_name = readConfig('app-name')
        if app_name is None:
            app_name = 'Notepad'
        msgBox = QMessageBox(
            QMessageBox.Icon.NoIcon,
            app_name, 
            tr(f'Do you want to save changes to {filename}?'),
            QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            self
        )
        return msgBox.exec()
    
    def getWindowTitle(self) -> str:
        """
        Retrieves the window title by formatting a template with the filename 
        and application name.

        Returns:
            str: a formatted window title string based on the `filename` and 
                application name stored in the class attributes. 
        """
        filename = self._filename
        default_filename = readConfig('file-name')
        if default_filename is None:
            default_filename = 'Untitled'
        if filename != default_filename:
            filename = os.path.basename(self._filename)

        title_template = readConfig('window-title')
        if title_template is None:
            title_template = '[*]{file} - {app}'

        app_name = readConfig('app-name')
        if app_name is None:
            app_name = 'Notepad'

        window_title = title_template.format(
                file = filename, 
                app = app_name
        )
        return window_title
    
    # EVENTS
    def onTextChanged(self):
        """
        Calculates the length of text in a text editor and then calls a method 
        in the menu bar with that length as an argument.
        """
        length = len(self.editor.toPlainText())
        self.menuBar().onTextChanged(length > 0)

    def onCursorPositionChanged(self):
        """
        Calculates the current line and column position of the cursor
        in a text editor and updates the status bar with this information.
        """
        cursor = self.editor.textCursor()
        currentPosition = cursor.positionInBlock()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        startOfLine = cursor.positionInBlock()
        self._col = currentPosition - startOfLine + 1

        lines = 1
        while(cursor.positionInBlock()>0):
            cursor.movePosition(QTextCursor.MoveOperation.Up)
            lines += 1
        block = cursor.block().previous()

        while(block.isValid()):
            lines+=block.lineCount()
            block = block.previous()
        self._line = lines

        self.statusBar().setPosition(self._line, self._col)
