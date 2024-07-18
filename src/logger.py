__all__ = ['logger', 'showError', 'showWarning']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import logging
import logging.config
from PyQt6.QtWidgets import QMessageBox

# Logging
logging.config.fileConfig('config/logging.conf')
logger = logging.getLogger('notepadLogger')

def showError(error_msg):
    logger.error(error_msg)
    QMessageBox.critical(
        title = 'Error', 
        text = error_msg, 
        buttons = QMessageBox.StandardButton.Ok
    )

def showWarning(warning_msg):
    logger.warn(warning_msg)
    QMessageBox.warning(
        title = 'Warning',
        text = warning_msg,
        buttons = QMessageBox.StandardButton.Ok
    )