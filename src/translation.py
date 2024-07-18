import gettext
from .config import readConfig

__all__ = ['tr']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

# Localization
gettext.bindtextdomain(
    readConfig('app-name'), 
    'locales/' + readConfig('app-locale')
)
gettext.textdomain(readConfig('app-name'))
tr = gettext.gettext
