"""

Notes:
- The logging Formatter formats an exception as a string and caches it.  The first Logging handler does the exception
formating and caching.  Subsequent calls to logging handlers use the same cached exception text.  The cached exception
string is stored in LogRecord record.exec_text and must be cleared if a different exception format is required.  Thus
custom logging formatters should be added after standard Logging formatters.
"""
from logging import LogRecord, Formatter
from sys import exc_info
from string import whitespace


# _____________________________________________________________________________
class NoExceptionFormatter(Formatter):
    """Remove exception details from logger formatter so to declutter log output
    """
    def format(self, record: LogRecord):
        record.exc_text = ''
        return super().format(record)

    def formatException(self, ei: exc_info):
        return ''


# _____________________________________________________________________________
class MessageFormatter(Formatter):
    """Remove all exception details from logger formatter except for message so to declutter log output
    """
    def format(self, record: LogRecord):
        record.exc_text = ''
        return super().format(record)

    def formatException(self, ei: exc_info):
        lei = (ei[0], ei[1], None)
        return repr(super().formatException(lei))


# _____________________________________________________________________________
class OneLineFormatter(Formatter):
    """Covert exception details to single line to simplify log output processing
    """
    def format(self, record: LogRecord):
        if text := super().format(record):
            text = text.rstrip(whitespace + '\n').replace('\n', '|')
        return text
