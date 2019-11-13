import concurrent.futures
from collections import Counter
from datetime import datetime, timedelta
import logging.config
import os
from pathlib import Path
from io import StringIO
import shutil
import time
from typing import List
import urllib3

from common import Record, Changed, Result, url_client, local_tz
from incCounter import IncCounter

logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class FetchItem(object):

    # _____________________________________________________________________________
    def __init__(self, config_settings, paths):
        self._paths = paths

    # _____________________________________________________________________________
    @staticmethod
    def __report_output(records: List[Record]):
        with StringIO() as buf:
            counter_changed = Counter(map(lambda r: r.changed, records))
            counter_result = Counter(map(lambda r: r.result, records))
            buf.write('Records:    %5d\n' % len(records))
            buf.write('- Cached:   %5d\n' % counter_changed[Changed.cached])
            buf.write('- Created:  %5d\n' % counter_changed[Changed.created])
            buf.write('- Updated:  %5d\n' % counter_changed[Changed.updated])
            buf.write('- Removed:  %5d\n' % counter_changed[Changed.removed])
            buf.write('- Deleted:  %5d\n' % counter_changed[Changed.deleted])
            buf.write('- Nil:      %5d\n' % counter_changed[Changed.nil])
            buf.write('Results\n')
            buf.write('- Warnings: %5d\n' % counter_result[Result.warning])
            buf.write('- Errors:   %5d\n' % counter_result[Result.error])
            buf.write('- Nil:      %5d\n' % counter_result[Result.nil])
            return buf.getvalue()

    # _____________________________________________________________________________
    def __fetch(self, records: List[Record]):
        logger.debug('__fetch')
        counter = IncCounter()

        record_docs = list(filter(lambda r: r.category in ['pdf'], records))
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_entry = {executor.submit(self.__fetch_item, rec, counter.inc_value) for rec in record_docs}
            for future in concurrent.futures.as_completed(future_entry):
                record, id = future.result()

    # _____________________________________________________________________________
    def __fetch_item(self, record: Record, id):
        logger.debug('> %4d __fetch_item' % id)
        start_time = time.time()
        record.result = Result.error
        record.changed = Changed.nil

        # Check file exists and, if so, if old
        is_file_exists = record.filepath.exists()
        logger.debug('> %4d Exists:     %-5s: "%s"' % (id, is_file_exists, record.filename))
        if is_file_exists:
            # Check file age
            local_date = datetime.date(datetime.fromtimestamp(record.filepath.stat().st_mtime))
            date_sort = record.dateSort
            logger.debug('> %4d date:       local, remote: %s, %s' % (id, local_date, date_sort))
            if local_date >= date_sort:
                record.result, record.changed = Result.success, Changed.cached
                logger.debug('> %4d Cached:     "%s"' % (id, record.filepath.name))
                return record, id

        # Fetch document
        try:
            output_base_local_path = self._paths['outputBaseLocalPath']
            rel_path = record.filepath.relative_to(output_base_local_path)
            logger.info('> %4d Fetching:   %s --> %s' % (id, rel_path.name, rel_path.parent))
            logger.debug('> %4d GET:        %s' % (id, record.url))

            rsp = None
            try:
                rsp = url_client.request('GET', record.url, preload_content=False)
                logger.debug('> %4d resp code:  %d' % (id, rsp.status))
                if rsp.status == 200:
                    logger.debug('> %4d Write:      "%s"' % (id, record.filename))
                    with record.filepath.open('wb', buffering=2**18) as rfp:
                        shutil.copyfileobj(rsp, rfp)
                    record.changed = Changed.updated if is_file_exists else Changed.created
                    record.result = Result.success
                    mins, secs = divmod(timedelta(seconds=time.time() - start_time).total_seconds(), 60)
                    logger.debug('> %4d Run time: %02d:%02d, File size %d' % (id, mins, secs, record.filepath.stat().st_size))
                else:
                    logger.error('> %4d HTTP code:  %d' % (id, rsp.status))
                    if is_file_exists:
                        record.filepath.unlink()
                        logger.debug('> %4d Deleting:   "%s"' % (id, rel_path))
                        record.changed = Changed.deleted
            except urllib3.exceptions.HTTPError as ex:
                logger.exception('> %4d HTTP error' % id)
            finally:
                if rsp:
                    rsp.release_conn()
        except Exception as ex:
            logger.exception('> %4d Generic exception' % id)
        return record, id

    # _____________________________________________________________________________
    def __remove_unwanted_files(self, records: List[Record]):
        logger.debug('__delete_bad_documents')
        output_base_local_path = self._paths['outputBaseLocalPath']
        output_local_path = self._paths['outputLocalPath']

        # Derive filepaths from records and local directory
        file_paths = sorted({r.filepath: r for r in records})
        local_file_paths = sorted(output_local_path.glob('**/*.*'))
        logger.debug('Number files: local, remote: %d, %d', len(local_file_paths), len(file_paths))

        # Check for extra or empty files
        for local_file_path in local_file_paths:
            if local_file_path.stat().st_size == 0:
                logger.info('- Empty file: "%s"' % local_file_path.relative_to(output_base_local_path))
                local_file_path.unlink()
                if local_file_path in file_paths:
                    fp = file_paths[local_file_path]
                    fp.changed = Changed.removed
                    fp.result = Result.warning
            elif local_file_path not in file_paths:
                logger.info('- Extra file: "%s"' % local_file_path.relative_to(output_base_local_path))
                records.append(Record(None, None, None, None, None,
                    None, None, None, None,
                    None, local_file_path.name, local_file_path, Changed.removed, Result.warning))
                local_file_path.unlink()

        # Delete empty folders
        for root, dirs, _ in os.walk(output_local_path, topdown=False):
            for dir in dirs:
                name = os.path.join(root, dir)
                if not len(os.listdir(name)):
                    logger.info('- Empty dir:  "%s"' % dir)
                    os.rmdir(name)

    # _____________________________________________________________________________
    def process(self, records):
        logger.debug('process')
        output_local_path = self._paths['outputLocalPath']
        logger.info('Output path: %s' % output_local_path)
        for r in records:
            r.filepath = Path(output_local_path, r.filepath).resolve()
        for dir in {r.filepath.parent for r in records}:
            dir.mkdir(parents=True, exist_ok=True)

        try:
            self.__fetch(records)
            self.__remove_unwanted_files(records)
        finally:
            logger.info(self.__report_output(records))

