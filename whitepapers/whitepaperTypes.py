from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Any

from common.common import FetchItem, Outcome, Result, str_to_bool


# _____________________________________________________________________________
@dataclass
class WhitepaperItem(FetchItem):
    __slots__ = ['title', 'dateRemote', 'filename', 'filepath', 'url', 'to_download', 'outcome', 'result',
                'name', 'category', 'contentType', 'featureFlag', 'description', 'primaryUrl',
                'dateCreated', 'dateUpdated', 'datePublished', 'dateSort']

    name: str
    category: str
    contentType: str
    featureFlag: str
    description: str
    primaryUrl: str
    dateCreated: date
    dateUpdated: date
    datePublished: date
    dateSort: date

    # _____________________________________________________________________________
    def to_list(self) -> List[Any]:
        """Return list of the instance attribute values.
        """
        return [self.title, self.dateRemote, self.filename, self.filepath, self.url, self.to_download,
                    self.outcome.name, self.result.name,
                    self.name, self.category, self.contentType, self.featureFlag,
                    self.description, self.primaryUrl,
                    self.dateCreated, self.dateUpdated, self.datePublished, self.dateSort]

    # _____________________________________________________________________________
    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return WhitepaperItem(s[0], date.fromisoformat(s[1]), s[2], Path(s[3]), s[4], str_to_bool(s[5]),
                    Outcome[s[6]], Result[s[7]],
                    s[8], s[9], s[10], s[11], s[12], s[13],
                    date.fromisoformat(s[14]), date.fromisoformat(s[15]) if s[15] else None,
                    date.fromisoformat(s[16]), date.fromisoformat(s[17]))
