from dataclasses import dataclass
from enum import Enum
from datetime import date
import tzlocal
from pathlib import Path
import urllib3


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


@dataclass
class DeleteRecord:
    __slots__ = ['contentType', 'dateDeleted', 'filename', 'filepath', 'outcome', 'result']
    contentType: str
    dateDeleted: date
    filename: str
    filepath: Path
    outcome: Outcome
    result: Result


# URL variables
# HTTP headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
url_headers = urllib3.make_headers(keep_alive=True, accept_encoding=True)
url_retries = urllib3.Retry(total=3, backoff_factor=5, status_forcelist=[500, 502, 503, 504])
url_client = urllib3.PoolManager(timeout=urllib3.Timeout(total=15.0), retries=url_retries, block=True,
                                 headers=url_headers)


# Date time
local_tz = tzlocal.get_localzone()
