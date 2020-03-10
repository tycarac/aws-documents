import concurrent.futures
from datetime import datetime, timedelta
import logging.config
import os
from pathlib import Path
import shutil
import time
from typing import List
import urllib3

from common.appConfig import AppConfig
from common.common import url_client
from common.metricPrefix import to_decimal_units
from whitepapers.whitepaperTypes import FetchRecord, Outcome, Result

_logger = logging.getLogger(__name__)
_BUFFER_SIZE = 1024 * 1024   # buffer for downloading remote resource


# _____________________________________________________________________________
class FetchFile(object):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        _logger.debug('__init__')
        self._app_config = app_config

    # _____________________________________________________________________________
    def __fetch_records(self, records: List[FetchRecord]):
        _logger.debug('__fetch')

        record_docs = list(filter(lambda r: r.to_download, records))
        # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_entry = {executor.submit(self.__fetch_record, rec, id) for id, rec in enumerate(record_docs)}
            for future in concurrent.futures.as_completed(future_entry):
                record, id = future.result()

    # _____________________________________________________________________________
    def __fetch_record(self, record: FetchRecord, id: int):
        _logger.debug(f'> {id:4d} __fetch_item')
        record.result = Result.error
        record.outcome = Outcome.nil

        # Check file exists and, if so, if old
        is_file_exists = record.filepath.exists()
        _logger.debug(f'> {id:4d} exists:     {str(is_file_exists):<5s}: "{record.filename}"')
        if is_file_exists:
            # Check file age
            local_date = datetime.date(datetime.fromtimestamp(record.filepath.stat().st_ctime))
            remote_date = record.dateRemote
            _logger.debug(f'> {id:4d} date:       local, remote: {local_date}, {remote_date}')
            if local_date >= remote_date:
                record.result, record.outcome = Result.success, Outcome.cached
                _logger.debug(f'> {id:4d} cached:     "{record.filepath.name}"')
                return record, id

        self.__fetch_file(record, is_file_exists, id)
        return record, id

    # _____________________________________________________________________________
    def __fetch_file(self, record: FetchRecord, is_file_exists: bool, id: int):
        _logger.debug(f'> {id:4d} __fetch_file')

        try:
            output_base_local_path = self._app_config.output_base_local_path
            rel_path = record.filepath.relative_to(output_base_local_path)
            _logger.info(f'> {id:4d} fetching:   "{rel_path.name}" --> "{rel_path.parent}"')
            _logger.debug(f'> {id:4d} GET:        {record.url}')

            rsp_status, fetch_time = FetchFile.__stream_response(record.url, record.filepath, id)
            if rsp_status == 200:
                record.result = Result.success
                record.outcome = Outcome.updated if is_file_exists else Outcome.created
            if record.result == Result.success:
                pub_timestamp = time.mktime(record.dateRemote.timetuple())
                file_path_str = str(record.filepath)
                os.utime(file_path_str, (pub_timestamp, pub_timestamp))

                file_size = record.filepath.stat().st_size
                _logger.debug(f'> {id:4d} fetch time, size: {fetch_time:.2f}s, {to_decimal_units(file_size)}')
            else:
                _logger.error(f'> {id:4d} HTTP code:  {rsp_status}')
                if record.filepath.exists():
                    record.filepath.unlink()
                    _logger.debug(f'> {id:4d} deleting:   "{rel_path}"')
                    record.outcome = Outcome.deleted
        except Exception as ex:
            _logger.exception(f'> {id:4d} generic exception')

    # _____________________________________________________________________________
    @staticmethod
    def __get_response(url: str, filepath: Path, id: int):
        # Must call release_conn() after file copied but opening/writing exception is possible
        rsp = None
        fetch_time = timedelta()
        try:
            start_time = time.time()
            rsp = url_client.request('GET', url)
            _logger.debug(f'> {id:4d} resp code:  {rsp.status}')
            while rsp.status in urllib3.HTTPResponse.REDIRECT_STATUSES:
                if location := rsp.headers.get('location', None):
                    _logger.debug(f'> {id:4d} redirct:      "{url} --> {location}')
                    url = location
                    rsp.release_conn()
                    rsp = url_client.request('GET', url, preload_content=False)
                else:
                    raise RuntimeError('Response header "location" not found')
            if rsp.status == 200:
                _logger.debug(f'> {id:4d} write:      "{filepath.name}"')
                with filepath.open('wb', buffering=_BUFFER_SIZE) as rfp:
                    shutil.copyfileobj(rsp, rfp, length=_BUFFER_SIZE)
            fetch_time = time.time() - start_time
        except urllib3.exceptions.HTTPError as ex:
            _logger.exception(f'> {id:4d} HTTP error')
        except Exception as ex:
            _logger.exception('Unexpected')
            raise ex
        finally:
            if rsp:
                rsp.release_conn()

        return rsp.status, fetch_time

    # _____________________________________________________________________________
    @staticmethod
    def __stream_response(url: str, filepath: Path, id: int):
        # Must call release_conn() after file copied but opening/writing exception is possible
        rsp = None
        start_time, fetch_time = time.time(), timedelta()
        try:
            rsp = url_client.request('GET', url, preload_content=False)
            _logger.debug(f'> {id:4d} resp code:  {rsp.status}')
            if rsp.status == 200:
                _logger.debug(f'> {id:4d} write:      "{filepath.name}"')
                with filepath.open('wb', buffering=_BUFFER_SIZE) as rfp:
                    shutil.copyfileobj(rsp, rfp, length=_BUFFER_SIZE)
            fetch_time = time.time() - start_time
        except urllib3.exceptions.HTTPError as ex:
            _logger.exception(f'> {id:4d} HTTP error')
        finally:
            if rsp:
                rsp.release_conn()

        return rsp.status, fetch_time

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

        self.__fetch_records(records)
