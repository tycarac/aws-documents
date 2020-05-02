from datetime import datetime
from dateutil import parser
import logging
from pathlib import Path
import re

from common.appConfig import AppConfig
from common.fetchList import FetchList
from builders.buildersTypes import BuildersItem, Outcome, Result

_logger = logging.getLogger(__name__)
_desc_re = re.compile(r'(?:</?p>)?([^<]+)<p>', re.IGNORECASE)


# _____________________________________________________________________________
class FetchBuildersList(FetchList):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        super().__init__(app_config)
        _logger.debug('__init__')

    # _____________________________________________________________________________
    def build_record(self, item):
        adfields = item['additionalFields']
        name = item['name']
        learning_level = adfields['learningLevel']
        headline = adfields['headline']
        content_type = adfields['contentType']
        download_url = adfields.get('downloadUrl', '').split('?')[0]
        video_url = adfields.get('videoUrl', '')

        # Extract text up to HTML tag from "description" and normalize whitespacing
        desc = m.group(1) if (m := _desc_re.search(adfields['description'])) else ''
        description = ' '.join(desc.split())

        # Derive date from datetime (not raw from JSON data file)
        date_created = datetime.date(parser.parse(item['dateCreated']))
        date_update_value = adfields.get('updateDate', None)
        date_updated = datetime.date(parser.parse(date_update_value)) if date_update_value else None

        # Extract paths
        filename_date = date_updated if date_updated else date_created
        filename = FetchList.build_filename(headline, filename_date, download_url)
        rel_filepath = Path(content_type, filename) if content_type else Path(filename)

        # Derived
        to_download = True if download_url else False
        date_remote = date_updated if date_updated else date_created

        record = BuildersItem(headline, date_remote, filename, rel_filepath, download_url, to_download,
                    Outcome.nil, Result.nil,
                    name, learning_level, date_updated, date_created, content_type,
                    download_url, video_url, description)

        _logger.debug(f'build_record "{record.title}"')
        return record
