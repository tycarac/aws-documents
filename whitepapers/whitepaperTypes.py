from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Any

from common.common import FetchRecord, Outcome, Result, str_to_bool


# _____________________________________________________________________________
@dataclass
class WhitepaperItem(FetchRecord):
    __slots__ = ['filename', 'filepath', 'dateRemote', 'url', 'to_download', 'outcome', 'result',
                'name', 'title', 'category', 'contentType', 'featureFlag', 'description', 'primaryUrl',
                'dateCreated', 'dateUpdated', 'datePublished', 'dateSort']

    name: str
    title: str
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
        return [self.filename, self.filepath, self.dateRemote, self.url, self.to_download,
                    self.outcome.name, self.result.name,
                    self.name, self.title, self.category, self.contentType, self.featureFlag,
                    self.description, self.primaryUrl,
                    self.dateCreated, self.dateUpdated, self.datePublished, self.dateSort]

    # _____________________________________________________________________________
    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return WhitepaperItem(s[0], Path(s[1]), date.fromisoformat(s[2]), s[3], str_to_bool(s[4]),
                    Outcome[s[5]], Result[s[6]],
                    s[7], s[8], s[9], s[10], s[11], s[12], s[13],
                    date.fromisoformat(s[14]), date.fromisoformat(s[15]) if s[15] else None,
                    date.fromisoformat(s[16]), date.fromisoformat(s[17]))
