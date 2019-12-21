import concurrent.futures
from datetime import datetime
import logging.config
import os
from pathlib import Path
import shutil
import time
from typing import List
import urllib3

from common import FetchRecord, Changed, Result, url_client
from appPaths import AppPaths
from incCounter import IncCounter

logger = logging.getLogger(__name__)
buffer_size = 1024 * 1024


# _____________________________________________________________________________
class FetchItem(object):

    # _____________________________________________________________________________
    def __init__(self, paths: AppPaths):
        logger.debug('__init__')
        self._paths = paths

    # _____________________________________________________________________________
    def __fetch(self, records: List[FetchRecord]):
        logger.debug('__fetch')
        counter = IncCounter()

        record_docs = list(filter(lambda r: r.category in ['pdf'], records))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_entry = {executor.submit(self.__fetch_item, rec, counter.inc_value) for rec in record_docs}
            for future in concurrent.futures.as_completed(future_entry):
                record, id = future.result()

    # _____________________________________________________________________________
    def __fetch_item(self, record: FetchRecord, id):
        logger.debug('> %4d __fetch_item' % id)
        record.result = Result.error
        record.changed = Changed.nil

        # Check file exists and, if so, if old
        is_file_exists = record.filepath.exists()
        logger.debug('> %4d Exists:     %-5s: "%s"' % (id, is_file_exists, record.filename))
        if is_file_exists:
            # Check file age
            local_date = datetime.date(datetime.fromtimestamp(record.filepath.stat().st_ctime))
            date_sort = record.dateSort
            logger.debug('> %4d date:       local, remote: %s, %s' % (id, local_date, date_sort))
            if local_date >= date_sort:
                record.result, record.changed = Result.success, Changed.cached
                logger.debug('> %4d Cached:     "%s"' % (id, record.filepath.name))
                return record, id

        self.__fetch_file(record, is_file_exists, id)
        return record, id

    # _____________________________________________________________________________
    def __fetch_file(self, record: FetchRecord, is_file_exists, id):
        try:
            output_base_local_path = self._paths.output_base_local_path
            rel_path = record.filepath.relative_to(output_base_local_path)
            logger.info('> %4d Fetching:   %s --> %s' % (id, rel_path.name, rel_path.parent))
            logger.debug('> %4d GET:        %s' % (id, record.url))

            pub_timestamp = time.mktime(record.datePublished.timetuple())
            file_path_str = str(record.filepath)

            # Fetch.  Must call release_conn() after file copied but opening/writing exception is possible
            rsp = None
            start_time = time.time()
            try:
                rsp = url_client.request('GET', record.url, preload_content=False)
                logger.debug('> %4d resp code:  %d' % (id, rsp.status))
                if rsp.status == 200:
                    logger.debug('> %4d Write:      "%s"' % (id, record.filename))
                    with record.filepath.open('wb', buffering=buffer_size) as rfp:
                        shutil.copyfileobj(rsp, rfp, length=buffer_size)
                record.changed = Changed.updated if is_file_exists else Changed.created
                record.result = Result.success
            except urllib3.exceptions.HTTPError as ex:
                logger.exception('> %4d HTTP error' % id)
            finally:
                fetch_time = time.time() - start_time
                if rsp:
                    rsp.release_conn()

            if record.result == Result.success:
                os.utime(file_path_str, (pub_timestamp, pub_timestamp))
                file_size = record.filepath.stat().st_size
                fs_str = str(bytes) if file_size <= 10000 else str(file_size // 1024) + 'k'
                logger.debug('> %4d Fetch time: %.2fs, File size %s' % (id, fetch_time, fs_str))
            else:
                logger.error('> %4d HTTP code:  %d' % (id, rsp.status))
                if record.filepath.exists():
                    record.filepath.unlink()
                    logger.debug('> %4d Deleting:   "%s"' % (id, rel_path))
                    record.changed = Changed.deleted
        except Exception as ex:
            logger.exception('> %4d Generic exception' % id)

    # _____________________________________________________________________________
    def process(self, records):
        logger.debug('process')
        logger.info('Output path: %s' % self._paths.output_local_path)

        # Prepare record data for fetching
        for r in records:
            r.filepath = Path(self._paths.output_local_path, r.filepath).resolve()

        # Create output directories
        dirs = {r.filepath.parent for r in records}
        for dir in dirs:
            dir.mkdir(parents=True, exist_ok=True)

        self.__fetch(records)
