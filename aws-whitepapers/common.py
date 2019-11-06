from dataclasses import dataclass
from enum import Enum
from datetime import date, datetime
import tzlocal
from pathlib import Path
import urllib3


# Enums
class Changed(Enum):
    nil = 'Nil',
    cached = 'Cached',
    created = 'Created',
    updated = 'Updated',
    deleted = 'Deleted',
    removed = 'Removed'


class Result(Enum):
    nil = 'Nil',
    success = 'Success',
    warning = 'Warning',
    error = 'Error'


@dataclass()
class Record(object):
    __slots__ = ['name', 'title', 'category', 'contentType', 'description', 'dateCreated', 'dateUpdated',
                'datePublished', 'dateTimeCreated', 'dateTimeUpdated', 'url', 'filename', 'filepath',
                'changed', 'result']
    name: str
    title: str
    category: str
    contentType: str
    description: str
    dateCreated: date
    dateUpdated: date
    datePublished : date
    dateTimeCreated: datetime
    dateTimeUpdated: datetime
    url: str
    filename: str
    filepath: Path
    changed: Changed
    result: Result


# URL variables
url_headers = urllib3.make_headers(keep_alive=True, accept_encoding=True)
url_retries = urllib3.Retry(total=2, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
url_client = urllib3.PoolManager(timeout=urllib3.Timeout(total=15.0), retries=url_retries, block=True,
                                 headers=url_headers)


# Date time
local_tz = tzlocal.get_localzone()
