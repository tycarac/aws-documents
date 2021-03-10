from datetime import datetime
from dateutil import parser
import logging
from pathlib import Path
import re

from common.appConfig import AppConfig
from common.common import Result, Outcome
from common.fetchList import FetchList
from answers.answersTypes import AnswersItem

_logger = logging.getLogger(__name__)

_category_re = re.compile(r'(?:<a\s[^>]*>)([^<]*)</a>', re.IGNORECASE)
_desc_re = re.compile(r'(?:</?p>)?([^<]+)</?p>', re.IGNORECASE)


# _____________________________________________________________________________
class FetchAnswersList(FetchList):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        super().__init__(app_config)
        _logger.debug('__init__')

    # _____________________________________________________________________________
    def build_record(self, item):
        adfields = item['additionalFields']
        name = item['name']
        headline = adfields['headline']
        sub_headline = adfields['subHeadline']
        category = adfields.get('category', '').split('|')
        content_type = adfields['contentType']
        feature_flag = adfields.get('featureFlag', None)

        # Extract text up to HTML tag from "description" and normalize whitespacing
        desc = m.group(1) if (m := _desc_re.search(adfields['description'])) else ''
        description = ' '.join(desc.split())

        # Derive date from datetime (not raw from JSON data file)
        date_created = datetime.date(parser.parse(item['dateCreated']))
        date_update_value = item.get('dateUpdated', None)
        date_updated = datetime.date(parser.parse(date_update_value)) if date_update_value else None
        date_sort = datetime.date(parser.parse(adfields['sortDate']))

        # Extract paths
        url = adfields.get('downloadUrl', '').split('?')[0]
        filename = FetchList.build_filename(headline, date_sort, url)
        rel_filepath = Path(content_type, filename) if category else Path(filename)

        # Derived
        to_download = True if url else False

        record = AnswersItem(headline, date_sort, filename, rel_filepath, url, to_download, Outcome.nil, Result.nil,
                    name, category, content_type, feature_flag, sub_headline, description,
                    date_created, date_updated, date_sort)

        _logger.debug(f'build_record "{record.title}"')
        return record

