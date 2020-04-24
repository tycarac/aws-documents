from datetime import date
import logging.config
import os
from pathlib import Path
from typing import List, Set

from common.common import DeleteRecord, Outcome, Result
from common.appConfig import AppConfig
from common.pathTools import is_parent

_logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class CleanOutput:

    # _____________________________________________________________________________
    def __init__(self, app_config: AppConfig):
        _logger.debug('__init__')
        self._app_config = app_config

    # _____________________________________________________________________________
    def __delete_empty_files(self) -> List[DeleteRecord]:
        _logger.debug('__delete_empty_files')

        # Check for extra or empty files
        file_paths = sorted(self._app_config.output_local_path.glob('**/*.*'))
        delete_records = []
        for file_path in file_paths:
            if file_path.stat().st_size == 0:
                _logger.warning(f'- Delete empty file: "{file_path.relative_to(self._app_config.output_base_local_path)}"')
                delete_record = DeleteRecord(file_path.parent.name, date.today(), file_path.name, file_path,
                            Outcome.deleted, Result.error)
                try:
                    os.remove(file_path)
                    delete_record.result = Result.success
                except (PermissionError, OSError):
                    _logger.exception(f'Cannot delete empty file: "{file_path}"')
                delete_records.append(delete_record)

        return delete_records

    # _____________________________________________________________________________
    def __archive_extra_files(self, fetch_paths: Set[Path]) -> List[DeleteRecord]:
        _logger.debug('__archive_extra_files')

        # Derive file paths from records and local directory
        local_file_paths = sorted(self._app_config.output_local_path.rglob('*.*'))
        _logger.debug(f'Number files: local, remote: {len(local_file_paths)}, {len(fetch_paths)}')

        archive_file_path = self._app_config.archive_path
        archive_file_paths = []
        for file_path in local_file_paths:
            if file_path not in fetch_paths and not is_parent(self._app_config.archive_path, file_path):
                archive_file_paths.append(file_path)

        delete_records = []
        if archive_file_paths:
            self._app_config.archive_path.mkdir(parents=True, exist_ok=True)
            for file_path in archive_file_paths:
                _logger.info(f'-      archiving: "{file_path.relative_to(self._app_config.output_base_local_path)}"')
                delete_record = DeleteRecord(file_path.parent.name, date.today(), file_path.name, file_path,
                            Outcome.archived, Result.error)
                delete_records.append(delete_record)
                try:
                    # Move file to archive
                    os.replace(file_path, Path(archive_file_path, file_path.name))
                    delete_record.result = Result.success
                except (PermissionError, OSError):
                    _logger.exception(f'Cannot archive file: "{file_path}"')

        return delete_records

    # _____________________________________________________________________________
    @staticmethod
    def __delete_empty_directories(parent_dir):
        _logger.debug('__delete_empty_directories')
        for root, dirs, _ in os.walk(parent_dir, topdown=False):
            for dr in dirs:
                name = os.path.join(root, dr)
                if not len(os.listdir(name)):
                    _logger.info(f'- Delete empty dir:  "{name}"')
                    os.rmdir(name)

    # _____________________________________________________________________________
    def process(self, fetch_paths: Set[Path]) -> List[DeleteRecord]:
        _logger.debug('process')

        delete_records = []
        delete_records.extend(self.__delete_empty_files())
        delete_records.extend(self.__archive_extra_files(fetch_paths))
        self.__delete_empty_directories(self._app_config.output_local_path)

        return delete_records
