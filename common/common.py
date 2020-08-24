from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from datetime import date
import logging.config, logging.handlers
import os
from pathlib import Path
import time
from typing import List, Any, Union
import tzlocal

from common.logTools import MessageFormatter, PathFileHandler

local_tz = tzlocal.get_localzone()
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
class FetchItem(ABC):
    __slots__ = ['title', 'dateRemote', 'filename', 'filepath', 'url', 'to_download', 'outcome', 'result']

    title: str
    dateRemote: date
    filename: str
    filepath: Path
    url: str
    to_download: bool
    outcome: Outcome
    result: Result

    # _____________________________________________________________________________
    @abstractmethod
    def to_list(self) -> List[Any]:
        """Return list of the instance attribute values.
        """
        return [self.title, self.dateRemote, self.filename, self.filepath, self.url, self.to_download,
                    self.outcome.name, self.result.name]

    # _____________________________________________________________________________
    @staticmethod
    @abstractmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return FetchItem(s[0], date.fromisoformat(s[1]), s[2], Path(s[3]), s[4], str_to_bool(s[5]),
                    Outcome[s[6]], Result[s[7]])


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
def initialize_logger(app_path: Path, start_datetime: datetime = None):
    if not start_datetime:
        start_datetime = datetime.fromtimestamp(time.time())

    # Load log configuration
    logger_config_path = app_path.with_suffix('.logging.json')
    with logger_config_path as p:
        import json
        logging.captureWarnings(True)
        logging.config.dictConfig(json.loads(p.read_text()))

    _logger.info(f'Now: {start_datetime.strftime("%a  %d-%b-%y  %I:%M:%S %p")}')
    _logger.debug(f'Config file: "{logger_config_path}"')
    _logger.debug(f'CPU count: {os.cpu_count()}')


# _____________________________________________________________________________
def str_to_bool(s: Union[str, bool]) -> bool:
    return s if type(s) is bool else s.lower() in ('true', 't', 'yes', '1')

