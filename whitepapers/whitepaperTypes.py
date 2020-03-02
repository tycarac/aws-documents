from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Any

from common.common import FetchRecord, Outcome, Result

__slots__ = ['filename', 'filepath', 'url', 'outcome', 'result']


# _____________________________________________________________________________
@dataclass
class WhitepaperItem(FetchRecord):
    __slots__ = ['filename', 'filepath', 'remoteDate', 'url', 'outcome', 'result',
                'name', 'title', 'category', 'contentType', 'featureFlag', 'description',
                'dateCreated', 'dateUpdated', 'datePublished', 'dateSort']

    name: str
    title: str
    category: str
    contentType: str
    featureFlag: str
    description: str
    dateCreated: date
    dateUpdated: date
    datePublished: date
    dateSort: date

    # _____________________________________________________________________________
    def to_list(self) -> List[Any]:
        """Return list of the instance attribute values.
        """
        return [self.filename, self.filepath, self.remoteDate, self.url, self.outcome.name, self.result.name,
                    self.name, self.title, self.category, self.contentType, self.featureFlag,
                    self.description, self.dateCreated, self.dateUpdated, self.datePublished, self.dateSort]

    # _____________________________________________________________________________
    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return WhitepaperItem(s[0], Path(s[1]), date.fromisoformat(s[2]), s[3], Outcome[s[4]], Result[s[5]],
            s[6], s[7], s[8], s[9], s[10], s[11],
            date.fromisoformat(s[12]), date.fromisoformat(s[13]) if s[13] else None,
            date.fromisoformat(s[14]), date.fromisoformat(s[15]))

