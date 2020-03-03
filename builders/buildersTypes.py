from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Any

from common.common import FetchRecord, Outcome, Result, str_to_bool


# _____________________________________________________________________________
@dataclass
class BuildersItem(FetchRecord):
    __slots__ = ['filename', 'filepath', 'dateRemote', 'url', 'to_download', 'outcome', 'result',
                'name', 'learningLevel', 'headline', 'dateUpdated', 'dateCreated', 'contentType',
                'downloadUrl', 'videoUrl', 'description']

    name: str
    learningLevel: str
    headline: str
    dateUpdated: date
    dateCreated: date
    contentType: str
    downloadUrl: str
    videoUrl: str
    description: str

    # _____________________________________________________________________________
    def to_list(self) -> List[Any]:
        """Return list of the instance attribute values.
        """
        return [self.filename, self.filepath, self.dateRemote, self.url, self.to_download,
                    self.outcome.name, self.result.name,
                    self.name, self.learningLevel, self.headline, self.dateUpdated, self.dateCreated,
                    self.contentType, self.downloadUrl, self.videoUrl, self.description]

    # _____________________________________________________________________________
    @staticmethod
    def from_string(s: List[str]):
        """Create an instance of the dataclass from a list os strings.  For simplicity, instead of introspecting
         the dataclass for field types, the function is manually synchronized (similar to __slots__).
        """
        return BuildersItem(s[0], Path(s[1]), date.fromisoformat(s[2]), s[3], str_to_bool(s[4]),
                    Outcome[s[5]], Result[s[6]],
                    s[7], s[8], s[9],
                    date.fromisoformat(s[10]) if s[10] else None, date.fromisoformat(s[11]),
                    s[12], s[13], s[14], s[15])
