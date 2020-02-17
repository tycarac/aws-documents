import concurrent.futures
from datetime import datetime
import logging.config
import os
from pathlib import Path
import shutil
import time
from typing import List
import urllib3

from common.appConfig import AppConfig
from common.common import url_client
from common.incCounter import IncCounter
from common.metricPrefix import to_decimal_units
from whitepapers.whitepaperTypes import FetchRecord, Outcome, Result

_logger = logging.getLogger(__name__)
_BUFFER_SIZE = 1024 * 1024   # buffer for downloading remote resource


# _____________________________________________________________________________
class FetchItem(object):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        _logger.debug('__init__')
        self._app_config = app_config

    # _____________________________________________________________________________
    def __fetch(self, records: List[FetchRecord]):
        _logger.debug('__fetch')
        counter = IncCounter()

        record_docs = list(filter(lambda r: r.category in ['pdf'], records))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_entry = {executor.submit(self.__fetch_item, rec, counter.inc_value) for rec in record_docs}
            for future in concurrent.futures.as_completed(future_entry):
                record, id = future.result()

    # _____________________________________________________________________________
    def __fetch_item(self, record: FetchRecord, id):
        _logger.debug(f'> {id:4d} __fetch_item')
        record.result = Result.error
        record.outcome = Outcome.nil

        # Check file exists and, if so, if old
        is_file_exists = record.filepath.exists()
        _logger.debug(f'> {id:4d} exists:     {str(is_file_exists):<5s}: "{record.filename}"')
        if is_file_exists:
            # Check file age
            local_date = datetime.date(datetime.fromtimestamp(record.filepath.stat().st_ctime))
            date_sort = record.dateSort
            _logger.debug(f'> {id:4d} date:       local, remote: {local_date}, {date_sort}')
            if local_date >= date_sort:
                record.result, record.outcome = Result.success, Outcome.cached
                _logger.debug(f'> {id:4d} cached:     "{record.filepath.name}"')
                return record, id

        self.__fetch_file(record, is_file_exists, id)
        return record, id

    # _____________________________________________________________________________
    def __fetch_file(self, record: FetchRecord, is_file_exists, id):
        _logger.debug(f'> {id:4d} __fetch_file')

        try:
            output_base_local_path = self._app_config.output_base_local_path
            rel_path = record.filepath.relative_to(output_base_local_path)
            _logger.info(f'> {id:4d} fetching:   "{rel_path.name}" --> "{rel_path.parent}"')
            _logger.debug(f'> {id:4d} GET:        {record.url}')

            # Fetch.  Must call release_conn() after file copied but opening/writing exception is possible
            rsp = None
            start_time = time.time()
            try:
                rsp = url_client.request('GET', record.url, preload_content=False)
                _logger.debug(f'> {id:4d} resp code:  {rsp.status}')
                if rsp.status == 200:
                    _logger.debug(f'> {id:4d} write:      "{record.filename}')
                    with record.filepath.open('wb', buffering=_BUFFER_SIZE) as rfp:
                        shutil.copyfileobj(rsp, rfp, length=_BUFFER_SIZE)
                record.outcome = Outcome.updated if is_file_exists else Outcome.created
                record.result = Result.success
            except urllib3.exceptions.HTTPError as ex:
                _logger.exception(f'> {id:4d} HTTP error')
            finally:
                fetch_time = time.time() - start_time
                if rsp:
                    rsp.release_conn()

            if record.result == Result.success:
                pub_timestamp = time.mktime(record.dateSort.timetuple())
                file_path_str = str(record.filepath)
                os.utime(file_path_str, (pub_timestamp, pub_timestamp))

                file_size = record.filepath.stat().st_size
                _logger.debug(f'> {id:4d} fetch time, size: {fetch_time:.2f}s, {to_decimal_units(file_size)}')
            else:
                _logger.error(f'> {id:4d} HTTP code:  {rsp.status}')
                if record.filepath.exists():
                    record.filepath.unlink()
                    _logger.debug(f'> {id:4d} deleting:   "{rel_path}"')
                    record.outcome = Outcome.deleted
        except Exception as ex:
            _logger.exception(f'> {id:4d} generic exception')

    # _____________________________________________________________________________
    def process(self, records):
        _logger.debug('process')

        # Prepare record data for fetching
        for r in records:
            r.filepath = Path(self._app_config.output_local_path, r.filepath).resolve()

        # Create output directories
        dirs = {r.filepath.parent for r in records}
        for dir in dirs:
            dir.mkdir(parents=True, exist_ok=True)

        self.__fetch(records)
