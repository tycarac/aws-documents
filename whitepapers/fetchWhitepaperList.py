from datetime import datetime
from dateutil import parser
import logging
from pathlib import Path
import re

from common.appConfig import AppConfig
from common.common import Result, Outcome
from common.fetchList import FetchList
from whitepapers.whitepaperTypes import WhitepaperItem

_logger = logging.getLogger(__name__)

_category_re = re.compile(r'(?:<a\s[^>]*>)([^<]*)</a>', re.IGNORECASE)
_desc_re = re.compile(r'(?:</?p>)?([^<]+)<p>', re.IGNORECASE)


# _____________________________________________________________________________
class FetchWhitepaperList(FetchList):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        super().__init__(app_config)
        _logger.debug('__init__')

    # _____________________________________________________________________________
    def build_record(self, item):
        adfields = item['additionalFields']
        name = item['name']
        title = adfields['docTitle']
        category = m.group(1).lower() if (m := _category_re.search(adfields['description'])) else None
        content_type = adfields['contentType']
        feature_flag = adfields.get('featureFlag', None)

        # Extract text up to HTML tag from "description" and normalize whitespacing
        desc = m.group(1) if (m := _desc_re.search(adfields['description'])) else ''
        description = ' '.join(desc.split())

        # Derive date from datetime (not raw from JSON data file)
        date_created = datetime.date(parser.parse(item['dateCreated']))
        date_update_value = adfields.get('updateDate', None)
        date_updated = datetime.date(parser.parse(date_update_value)) if date_update_value else None
        date_published = datetime.date(parser.parse(adfields['datePublished']))
        date_sort = datetime.date(parser.parse(adfields['sortDate']))

        # Extract paths
        url = adfields['primaryURL'].split('?')[0]
        filename = FetchList.build_filename(title, date_sort, url)
        rel_filepath = Path(content_type, filename) if category else Path(filename)

        # Derived
        to_download = category in ['pdf']

        record = WhitepaperItem(filename, rel_filepath, date_sort, url, to_download, Outcome.nil, Result.nil,
                    name, title, category, content_type, feature_flag, description,
                    date_created, date_updated, date_published, date_sort)

        _logger.debug(f'build_record "{record.title}"')
        return record

