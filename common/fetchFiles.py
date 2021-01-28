import concurrent.futures
from datetime import datetime, timedelta
import logging.config
import os
from pathlib import Path
import shutil
import time
from typing import List
from urllib3 import exceptions, make_headers, HTTPResponse, Retry, PoolManager, Timeout

from common.appConfig import AppConfig
from common.common import local_tz
from common.metricPrefix import to_decimal_units
from whitepapers.whitepaperTypes import FetchItem, Outcome, Result

_logger = logging.getLogger(__name__)
_BUFFER_SIZE = 1024 * 1024   # buffer for downloading remote resource


# _____________________________________________________________________________
class FetchFiles(object):

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        _logger.debug('__init__')
        self._app_config = app_config

        url_headers = make_headers(keep_alive=True, accept_encoding=True)
        url_retries = Retry(total=4, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
        self.url_client = PoolManager(timeout=Timeout(total=15.0), retries=url_retries, block=True, headers=url_headers)

    # _____________________________________________________________________________
    def __fetch_records(self, records: List[FetchItem]):
        _logger.debug(f'__fetch {len(records)} records')

        record_docs = list(filter(lambda r: r.to_download, records))
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_entries = {executor.submit(self.__fetch_record, rec, i) for i, rec in enumerate(record_docs, 1)}
            for future in concurrent.futures.as_completed(future_entries):
                record, i = future.result()

    # _____________________________________________________________________________
    def __fetch_record(self, record: FetchItem, i: int):
        is_file_exists = record.filepath.exists()
        _logger.debug(f'> {i:4d} exists:    {str(is_file_exists):<5s}: "{record.filename}"')

        record.result = Result.error
        record.outcome = Outcome.nil
        try:
            if is_file_exists:
                # Check file age
                local_date = datetime.date(datetime.fromtimestamp(record.filepath.stat().st_ctime, local_tz))
                remote_date = record.dateRemote
                _logger.debug(f'> {i:4d} date:      local, remote: {local_date}, {remote_date}')
                if local_date >= remote_date:
                    record.result, record.outcome = Result.success, Outcome.cached
                    _logger.debug(f'> {i:4d} cached:    "{record.filepath.name}"')
                    return record, i

            self.__fetch_file(record, is_file_exists, i)
        except Exception as ex:
            _logger.exception(f'> {i:4d} {record.title}')

        return record, i

    # _____________________________________________________________________________
    def __fetch_file(self, record: FetchItem, is_file_exists: bool, i: int):
        downloads_path = self._app_config.downloads_path
        rel_path = record.filepath.relative_to(downloads_path)
        _logger.info(f'> {i:4d} fetching:  "{rel_path.name}" --> "{rel_path.parent}"')
        _logger.debug(f'> {i:4d} GET:       {record.url}')

        try:
            rsp_status, fetch_time = self.__stream_response(record.url, record.filepath, i)
            if rsp_status == 200:
                record.result = Result.success
                record.outcome = Outcome.updated if is_file_exists else Outcome.created

                # Update file datetime stamp
                pub_timestamp = time.mktime(record.dateRemote.timetuple())
                file_path_str = str(record.filepath)
                os.utime(file_path_str, (pub_timestamp, pub_timestamp))

                # Derive file size
                file_size = record.filepath.stat().st_size
                _logger.debug(f'> {i:4d} fetch time, size: {fetch_time:.2f}s, {to_decimal_units(file_size)}')
            else:
                _logger.error(f'> {i:4d} HTTP code: {rsp_status}')
                if record.filepath.exists():
                    record.filepath.unlink()
                    _logger.debug(f'> {i:4d} deleting:  "{rel_path}"')
                    record.outcome = Outcome.deleted
        except Exception as ex:
            _logger.exception(f'> {i:4d} generic exception')

    # _____________________________________________________________________________
    def __get_response(self, url: str, filepath: Path, i: int):
        # Must call release_conn() after file copied but opening/writing exception is possible
        rsp = None
        fetch_time = timedelta()
        try:
            redirect_count = 3
            start_time = time.time()
            rsp = self.url_client.request('GET', url, preload_content=False)
            _logger.debug(f'> {i:4d} resp code: {rsp.status}')
            while rsp.status in HTTPResponse.REDIRECT_STATUSES and redirect_count > 0:
                if location := rsp.headers.get('location', None):
                    _logger.debug(f'> {i:4d} redirct:   {url} --> {location}')
                    url = location
                    rsp.release_conn()
                    rsp = self.url_client.request('GET', location, preload_content=False)
                else:
                    raise RuntimeError('Response header "location" not found')
            if rsp.status == 200:
                _logger.debug(f'> {i:4d} write:     "{filepath.name}"')
                with filepath.open('wb', buffering=_BUFFER_SIZE) as rfp:
                    shutil.copyfileobj(rsp, rfp, length=_BUFFER_SIZE)
            fetch_time = time.time() - start_time
        except exceptions.HTTPError as ex:
            _logger.exception(f'> {i:4d} HTTP error')
        except Exception as ex:
            _logger.exception('Unexpected')
            raise ex
        finally:
            if rsp:
                rsp.release_conn()

        return rsp.status, fetch_time

    # _____________________________________________________________________________
    def __stream_response(self, url: str, filepath: Path, i: int):
        # Must call release_conn() after file copied but opening/writing exception is possible
        rsp = None
        start_time, fetch_time = time.time(), timedelta()
        try:
            rsp = self.url_client.request('GET', url, preload_content=False)
            _logger.debug(f'> {i:4d} resp code: {rsp.status}')
            while rsp.status in HTTPResponse.REDIRECT_STATUSES:
                if location := rsp.headers.get('location', None):
                    _logger.debug(f'> {i:4d} redirct:   {url} --> "{location}"')
                    url = location
                    rsp.release_conn()
                    rsp = self.url_client.request('GET', url, preload_content=False)
                    _logger.debug(f'> {i:4d} resp code: {rsp.status}')
                else:
                    raise RuntimeError('Response header "location" not found')
            if rsp.status == 200:
                _logger.debug(f'> {i:4d} write:     "{filepath.name}"')
                with filepath.open('wb', buffering=_BUFFER_SIZE) as rfp:
                    shutil.copyfileobj(rsp, rfp, length=_BUFFER_SIZE)
            fetch_time = time.time() - start_time
        except exceptions.HTTPError as ex:
            _logger.exception(f'> {i:4d} HTTP error')
        finally:
            if rsp:
                rsp.release_conn()

        return rsp.status, fetch_time

    # _____________________________________________________________________________
    def process(self, records):
        _logger.debug('process')

        # Prepare record data for fetching
        for r in records:
            if r.to_download:
                r.filepath = Path(self._app_config.downloads_path, r.filepath).resolve()

        # Create downloads directories
        dirs = {r.filepath.parent for r in records if r.to_download}
        for dir in dirs:
            dir.mkdir(parents=True, exist_ok=True)

        self.__fetch_records(records)
