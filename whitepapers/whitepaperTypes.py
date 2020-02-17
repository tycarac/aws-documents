from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List

from common.common import Outcome, Result


@dataclass
class FetchRecord:
    __slots__ = ['name', 'title', 'category', 'contentType', 'featureFlag', 'description',
                'dateCreated', 'dateUpdate', 'datePublished', 'dateSort', 'publishedDateText',
                'url', 'filename', 'filepath', 'outcome', 'result']
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
    outcome: Outcome
    result: Result

    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return FetchRecord(s[0], s[1], s[2], s[3], s[4], s[5],
            date.fromisoformat(s[6]), date.fromisoformat(s[7]) if s[7] else None,
            date.fromisoformat(s[8]), date.fromisoformat(s[9]),
            s[10], s[11], s[12], Path(s[13]), Outcome[s[14]], Result[s[15]])
