from datetime import datetime, timedelta
import logging.handlers
from pathlib import Path
import time
from typing import List

from common.appConfig import AppConfig
from common.cleanup import CleanOutput
from common.common import initialize_logger
from common.reporting import Reporting
from common.logTools import MessageFormatter, PathFileHandler
from common.fetchFiles import FetchFiles

from whitepapers.fetchWhitepaperList import FetchWhitepaperList
from whitepapers.whitepaperAppConfig import WhitepaperAppConfig
from whitepapers.whitepaperTypes import WhitepaperItem

# Common variables
_logger = logging.getLogger(__name__)
_CSV_BACKUP_SUFFIX = '.bak.csv'


# _____________________________________________________________________________
def clean_output(fetch_records: List[WhitepaperItem], app_config: AppConfig):
    _logger.debug('clean_output')

    co = CleanOutput(app_config)
    fetch_paths = {r.filepath for r in fetch_records}
    delete_records = co.process(fetch_paths)
    return delete_records


# _____________________________________________________________________________
def fetch_files(fetch_records: List[WhitepaperItem], app_config: AppConfig):
    _logger.debug('fetch_files')

    fd = FetchFiles(app_config)
    fd.process(fetch_records)


# _____________________________________________________________________________
def build_record_list(app_config: AppConfig):
    _logger.debug('build_record_list')

    fdl = FetchWhitepaperList(app_config)
    return fdl.build_list()


# _____________________________________________________________________________
def process(app_config: AppConfig):
    _logger.debug('process')
    _logger.info(f'Output path: "{app_config.downloads_path}"')

    fetch_records = build_record_list(app_config)
    delete_records = []
    try:
        fetch_files(fetch_records, app_config)
        delete_records = clean_output(fetch_records, app_config)
    finally:
        reporting = Reporting(fetch_records, WhitepaperItem, delete_records, app_config)
        reporting.export_fetch_results()
        reporting.export_extras_results()
        _logger.info('\n' + reporting.build_summary())


# _____________________________________________________________________________
def main():
    start_time = time.time()
    app_path = Path(__file__)
    try:
        # Configure logging
        start_datetime = datetime.fromtimestamp(start_time)
        initialize_logger(app_path, start_datetime)

        # Run application
        process(WhitepaperAppConfig(app_path, app_path.parents[1]))
    except Exception as ex:
        _logger.exception('Catch all exception')
    finally:
        mins, secs = divmod(timedelta(seconds=time.time() - start_time).total_seconds(), 60)
        _logger.info(f'Run time: {int(mins)}:{secs:0.1f}s')


# _____________________________________________________________________________
if __name__ == '__main__':
    main()
