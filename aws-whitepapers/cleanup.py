from datetime import date
import logging.config
import os
from pathlib import Path
from typing import List

from .common import FetchRecord, DeleteRecord, Outcome, Result
from .appConfig import AppConfig


logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class CleanOutput(object):

    # _____________________________________________________________________________
    def __init__(self, paths: AppConfig):
        logger.debug('__init__')
        self._paths = paths

    # _____________________________________________________________________________
    def __delete_empty_files(self) -> List[DeleteRecord]:
        logger.debug('__delete_empty_files')

        # Check for extra or empty files
        file_paths = sorted(self._paths.output_local_path.glob('**/*.*'))
        delete_records = []
        for file_path in file_paths:
            if file_path.stat().st_size == 0:
                logger.warning('- Delete empty file: "%s"'
                            % file_path.relative_to(self._paths.output_base_local_path))
                delete_record = DeleteRecord(file_path.parent.name, date.today(), file_path.name, file_path,
                            Outcome.deleted, Result.error)
                try:
                    os.remove(file_path)
                    delete_record.result = Result.success
                except Exception as ex:
                    logger.exception('Cannot delete empty file: "%s"' % file_path)
                delete_records.append(delete_record)

        return delete_records

    # _____________________________________________________________________________
    def __archive_extra_files(self, record_file_paths: List[Path]) -> List[DeleteRecord]:
        logger.debug('__archive_extra_files')

        # Derive file paths from records and local directory
        local_file_paths = sorted(self._paths.output_local_path.glob('**/*.*'))
        archive_file_path = self._paths.archive_path
        archive_file_paths = []
        logger.debug('Number files: local, remote: %d, %d', len(local_file_paths), len(record_file_paths))

        file_paths = sorted(self._paths.output_local_path.glob('**/*.*'))
        archive_fp = str(self._paths.archive_path)
        delete_records = []
        for file_path in file_paths:
            if file_path not in record_file_paths and not str(file_path).startswith(archive_fp):
                archive_file_paths.append(file_path)

        if archive_file_paths:
            self._paths.archive_path.mkdir(parents=True, exist_ok=True)
            for file_path in archive_file_paths:
                logger.info('- Archive file: "%s"' % file_path.relative_to(self._paths.output_base_local_path))
                delete_record = DeleteRecord(file_path.parent.name, date.today(), file_path.name, file_path,
                            Outcome.archived, Result.error)
                delete_records.append(delete_record)
                try:
                    # Move file to archive
                    os.replace(file_path, Path(archive_file_path, file_path.name))
                    delete_record.result = Result.success
                except OSError as ex:
                    logger.exception('Cannot archive file: "%s"', file_path)

        return delete_records

    # _____________________________________________________________________________
    @staticmethod
    def __delete_empty_directories(parent_dir):
        logger.debug('__delete_empty_directories')
        for root, dirs, _ in os.walk(parent_dir, topdown=False):
            for dir in dirs:
                name = os.path.join(root, dir)
                if not len(os.listdir(name)):
                    logger.info('- Delete empty dir:  "%s"' % name)
                    os.rmdir(name)

    # _____________________________________________________________________________
    def process(self, fetch_records: List[FetchRecord]) -> List[DeleteRecord]:
        logger.debug('process')

        record_file_paths = sorted({r.filepath: r for r in fetch_records})
        delete_records = []
        delete_records.extend(self.__delete_empty_files())
        delete_records.extend(self.__archive_extra_files(record_file_paths))
        self.__delete_empty_directories(self._paths.output_local_path)

        return delete_records
