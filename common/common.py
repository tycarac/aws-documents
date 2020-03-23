from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from datetime import date
import logging.config, logging.handlers
import os
from pathlib import Path
from typing import List, Any
import tzlocal
import urllib3

from common.logTools import MessageFormatter, PathFileHandler

# _____________________________________________________________________________
# URL variables
# Reference HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
# Note urllib3:
#   1. A redirect, HTTP status 3xx, is handled as a retry can counts towards the connection retry count.  Thus
#      redirects will exhaust retries (default: 3).
url_headers = urllib3.make_headers(keep_alive=True, accept_encoding=True)
url_retries = urllib3.Retry(total=4, backoff_factor=5, status_forcelist=[500, 502, 503, 504])
url_client = urllib3.PoolManager(timeout=urllib3.Timeout(total=15.0), retries=url_retries, block=True, maxsize=10,
                                 headers=url_headers)

# Date time
local_tz = tzlocal.get_localzone()

# Logging
_logger = logging.getLogger(__name__)


# _____________________________________________________________________________
# Enums
class Outcome(Enum):
    nil = 'Nil',
    cached = 'Cached',
    created = 'Created',
    updated = 'Updated',
    deleted = 'Deleted',
    archived = 'Archived'


class Result(Enum):
    nil = 'Nil',
    success = 'Success',
    warning = 'Warning',
    error = 'Error'


# _____________________________________________________________________________
# Data classes
@dataclass
class FetchRecord(ABC):
    __slots__ = ['filename', 'filepath', 'dateRemote', 'url', 'to_download', 'outcome', 'result']
    filename: str
    filepath: Path
    dateRemote: date
    url: str
    to_download: bool
    outcome: Outcome
    result: Result

    # _____________________________________________________________________________
    @abstractmethod
    def to_list(self) -> List[Any]:
        """Return list of the instance attribute values.
        """
        return [self.filename, self.filepath, self.dateRemote, self.url, self.to_download,
                    self.outcome.name, self.result.name]

    # _____________________________________________________________________________
    @staticmethod
    @abstractmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return FetchRecord(s[0], Path(s[1]), date.fromisoformat(s[2]), s[3], str_to_bool(s[4]),
                    Outcome[s[5]], Result[s[6]])


# _____________________________________________________________________________
@dataclass
class DeleteRecord:
    __slots__ = ['contentType', 'dateDeleted', 'filename', 'filepath', 'outcome', 'result']
    contentType: str
    dateDeleted: date
    filename: str
    filepath: Path
    outcome: Outcome
    result: Result


# _____________________________________________________________________________
def initialize_logger(main_path: Path):
    logger_config_path = main_path.with_suffix('.logging.json')
    _logger.debug(f'Config file: {logger_config_path}')
    with logger_config_path as p:
        import json
        logging.captureWarnings(True)
        logging.config.dictConfig(json.loads(p.read_text()))
    _logger.debug(f'CPU count: {os.cpu_count()}')


# _____________________________________________________________________________
def str_to_bool(s: str) -> bool:
    return s.lower() in ('true', 't', 'yes', '1')
