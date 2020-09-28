from abc import ABC, abstractmethod
from datetime import datetime, date
from dataclasses import dataclass
import logging
import json
from pathlib import Path
import pytz
import time
from typing import List, Any, Mapping
from urllib import parse
from urllib3 import exceptions, make_headers, Retry, PoolManager, Timeout

from common.appConfig import AppConfig
from common.common import local_tz
from common.pathTools import sanitize_filename

_logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class FetchList(ABC):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        _logger.debug('__init__')
        self._app_config = app_config

        url_headers = make_headers(keep_alive=True, accept_encoding=True)
        url_headers.update({'Accept': 'text/*', 'Accept-Charset': 'utf-8'})
        url_retries = Retry(total=4, backoff_factor=3, status_forcelist=[500, 502, 503, 504])
        self.url_client = PoolManager(timeout=Timeout(total=15.0), retries=url_retries, block=True, headers=url_headers)

    # _____________________________________________________________________________
    @abstractmethod
    def build_record(self, item) -> dataclass:
        raise NotImplementedError('build_record')

    # _____________________________________________________________________________
    @staticmethod
    def build_filename(fname: str, fdate: date, url: str) -> str:
        """Build a filename to be retrieved from the URL.  The filename has a base of name and date
        and file suffix from the URL.
        """
        url_path = parse.urlparse(url).path
        loc = url_path.rfind('.')
        fname = f'{sanitize_filename(fname)} - {fdate.strftime("%Y-%m-%d")}'
        return (fname + url_path[loc:]) if loc >= 0 else fname

    # _____________________________________________________________________________
    def __process_list(self, list_pages) -> List[Any]:
        _logger.debug('__process_list')
        records = []
        for page in list_pages:
            for grp in page['items']:
                item = grp['item']
                record = self.build_record(item)
                records.append(record)
        _logger.info(f'Number items: {len(records)}')
        return records

    # _____________________________________________________________________________
    def __fetch_list_page(self, page_num: int, fields: Mapping[str, str]):
        _logger.info(f'  fetch list: page {page_num:3d}')
        list_page, cache_pf = None, None
        hits_total, count = 0, 0

        try:
            rsp = self.url_client.request('GET', self._app_config.source_url, fields=fields)
            _logger.debug(f'> {page_num:4d} response status  {rsp.status}')
            if rsp.status == 200:
                # extract data
                list_page = json.loads(rsp.data.decode('utf-8'))
                metadata = list_page['metadata']
                count = int(metadata['count'])
                hits_total = int(metadata['totalHits'])

                # Write list page to cache
                if count > 1:
                    fname = f'{self._app_config.name}.{page_num:03d}.json'
                    cache_pf = Path(self._app_config.cache_path, fname).resolve()
                    _logger.debug(f'> {page_num:4d} write {fname}')
                    cache_pf.write_text(json.dumps(list_page, indent=2))
        except exceptions.MaxRetryError as ex:
            _logger.exception(f'> {page_num:4d} Maximum reties exceeded')
            raise
        except exceptions.HTTPError as ex:
            _logger.exception(f'> {page_num:4d} HTTPError')
            raise

        return list_page, count, hits_total, cache_pf

    # _____________________________________________________________________________
    def __fetch_list(self):
        _logger.debug('__fetch_list')
        _logger.info(f'URL: {self._app_config.source_url}')

        list_pages, cache_files = [], []
        hits_count, page_num = 0, 0
        fields = self._app_config.source_parameters.copy()
        while True:
            list_page, count, hits_total, cache_pf = self.__fetch_list_page(page_num, fields)
            _logger.debug(f'> {page_num:4d} hits total, hits count, count: {hits_total}, {hits_count}, {count}')
            if count < 1:
                break
            list_pages.append(list_page)
            hits_count += count
            cache_files.append(cache_pf)
            if hits_count >= hits_total:
                break
            page_num += 1
            fields['page'] = page_num

        # Write summary file
        now_dt = datetime.utcnow()
        summary = f'{{"written":{{"utc":"{pytz.UTC.localize(now_dt)}","local":"{local_tz.localize(now_dt)}"}}' \
                f',"count":"{hits_count}","pages":"{len(cache_files)}"}}'
        summary_filepath = self._app_config.summary_file_path
        summary_filepath.write_text(json.dumps(json.loads(summary), indent=2))
        cache_files.append(summary_filepath)

        # Remove superfluous cache files
        cache_path = self._app_config.cache_path
        deleted_files = [p.unlink() for p in cache_path.glob('*.*') if p not in cache_files]

        return list_pages

    # _____________________________________________________________________________
    def build_list(self):
        _logger.debug('build_list')
        cache_path = self._app_config.cache_path
        _logger.debug(f'Cache path: {cache_path}')

        # Test local cached age
        is_use_cache = False
        summary_filepath = self._app_config.summary_file_path
        if self._app_config.cache_age_sec > 0 and summary_filepath.exists():
            is_use_cache = summary_filepath.stat().st_mtime > (time.time() - self._app_config.cache_age_sec)

        # Build list
        _logger.info(f'Use cached list: {is_use_cache}')
        list_pages = []
        if is_use_cache:
            [list_pages.append(json.loads(p.read_text())) for p in cache_path.glob('*.*') if
                not p.samefile(summary_filepath)]
        else:
            cache_path.mkdir(parents=True, exist_ok=True)
            list_pages = self.__fetch_list()
        records = self.__process_list(list_pages)

        return records
