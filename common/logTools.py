"""

Notes:
- The logging Formatter formats an exception as a string and caches it.  The first Logging handler does the exception
formating and caching.  Subsequent calls to logging handlers use the same cached exception text.  The cached exception
string is stored in LogRecord record.exec_text and must be cleared if a different exception format is required.  Thus
custom logging formatters should be added after standard Logging formatters.
"""
from logging import LogRecord, Formatter, FileHandler
from pathlib import Path
from sys import exc_info


# _____________________________________________________________________________
class NoExceptionFormatter(Formatter):
    """Remove exception details from logger formatter so to declutter log downloads
    """
    def format(self, record: LogRecord):
        record.exc_text = ''
        return super().format(record)

    def formatException(self, ei: exc_info):
        return ''


# _____________________________________________________________________________
class MessageFormatter(Formatter):
    """Remove all exception details from logger formatter except for message so to declutter log downloads
    """
    def format(self, record: LogRecord):
        record.exc_text = ''
        return super().format(record)

    def formatException(self, ei: exc_info):
        lei = (ei[0], ei[1], None)
        return repr(super().formatException(lei))


# _____________________________________________________________________________
class OneLineFormatter(Formatter):
    """Covert exception details to single line to simplify log downloads processing
    """
    def format(self, record: LogRecord):
        if text := super().format(record):
            text = text.strip().replace('\n', '|')
        return text


# _____________________________________________________________________________
class PathFileHandler(FileHandler):
    """Extends FileHandler to create the directory, if required, for the log file.

    Note this has some security risk as the file path is arbitrary and could be any location.
    """
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        Path.mkdir(Path(filename).parent, parents=True, exist_ok=True)
        super().__init__(filename, mode, encoding, delay)
