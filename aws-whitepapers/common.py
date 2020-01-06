from dataclasses import dataclass
from enum import Enum
from datetime import date
import tzlocal
from pathlib import Path
from typing import List
import urllib3


# Enums
class Changed(Enum):
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
class FetchRecord:
    __slots__ = ['name', 'title', 'category', 'contentType', 'featureFlag', 'description',
                'dateCreated', 'dateUpdate', 'datePublished', 'dateSort', 'publishedDateText',
                'url', 'filename', 'filepath', 'changed', 'result']
    name: str
    title: str
    category: str
    contentType: str
    featureFlag: str
    description: str
    dateCreated: date
    dateUpdate: date
    datePublished: date
    dateSort: date
    publishedDateText: str
    url: str
    filename: str
    filepath: Path
    changed: Changed
    result: Result

    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return FetchRecord(s[0], s[1], s[2], s[3], s[4], s[5],
            date.fromisoformat(s[6]), date.fromisoformat(s[7]) if s[7] else None,
            date.fromisoformat(s[8]), date.fromisoformat(s[9]),
            s[10], s[11], s[12], Path(s[13]), Changed[s[14]], Result[s[15]])


@dataclass
class DeleteRecord:
    __slots__ = ['contentType', 'dateDeleted', 'filename', 'filepath', 'changed', 'result']
    contentType: str
    dateDeleted: date
    filename: str
    filepath: Path
    changed: Changed
    result: Result


# URL variables
url_headers = urllib3.make_headers(keep_alive=True, accept_encoding=True)
url_retries = urllib3.Retry(total=3, backoff_factor=5, status_forcelist=[500, 502, 503, 504])
url_client = urllib3.PoolManager(timeout=urllib3.Timeout(total=15.0), retries=url_retries, block=True,
                                 headers=url_headers)


# Date time
local_tz = tzlocal.get_localzone()
