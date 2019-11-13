import csv
from datetime import datetime, timedelta
import json
import logging.config, logging.handlers
import os
from pathlib import Path
import time

from common import Record
from fetch import FetchItem
from fetchList import FetchItemList
from logger import NoExceptionFormatter
import os
from typing import List


# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
def export_results(records, paths):
    out_path = paths['reportFilePath']
    logger.info('Report:        %s' % out_path)
    with out_path.open(mode='wt', newline='') as out:
        csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(Record.__slots__)
        for r in records:
            csv_writer.writerow(
                [r.name, r.title, r.category, r.contentType, r.description,
                    r.dateCreated, r.dateUpdated, r.datePublished, r.dateSort, r.dateTimeCreated, r.dateTimeUpdated,
                    r.url, r.filename, r.filepath, r.changed, r.result])


# _____________________________________________________________________________
def process(config_settings, paths):
    fdl = FetchItemList(config_settings, paths)
    records = fdl.build_list()
    try:
        fd = FetchItem(config_settings, paths)
        fd.process(records)
    finally:
        export_results(records, paths)


# _____________________________________________________________________________
def derive_paths(config_settings):
    name = Path(__file__).stem

    # Cache list
    cache_settings = config_settings['cache']
    cache_base_path = Path(cache_settings['localPath']).resolve()
    cache_path = Path(cache_base_path, name).resolve()

    # Output
    output_settings = config_settings['local']
    output_base_local_path = Path(output_settings['localPath']).resolve()
    output_local_path = Path(output_base_local_path, name).resolve()

    paths = {
        'name': Path(__file__).stem,
        # Fetch list
        'cacheBasePath': cache_base_path,
        'cachePath': Path(cache_base_path, name).resolve(),
        'summaryFilepath': Path(cache_path, name + '.summary.json').resolve(),
        # Fetch
        'outputBaseLocalPath': output_base_local_path,
        'outputLocalPath': output_local_path,
        # Report
        'reportFilePath': Path(output_base_local_path, name + '.csv').resolve()
    }

    return paths


# _____________________________________________________________________________
def main():
    start_time = time.time()
    try:
        # Configure logging
        logging.captureWarnings(True)
        with Path(__file__).with_suffix('.logging.json') as p:
            logging.config.dictConfig(json.loads(p.read_text()))
        start_datetime = datetime.fromtimestamp(start_time)
        logger.info('Now: %s' % start_datetime.strftime('%a  %d-%b-%y  %I:%M:%S %p'))
        logger.debug('CPU count: %s' % os.cpu_count())

        # Run application
        with Path(__file__).with_suffix('.config.json') as f:
            config_settings = json.loads(f.read_text())

        paths = derive_paths(config_settings)
        process(config_settings, paths)
    except Exception as ex:
        logger.exception('Catch all exception')
    finally:
        run_timedelta = timedelta(seconds=time.time() - start_time)
        logger.info('Run time: %02d:%02d' % (divmod(run_timedelta.total_seconds(), 60)))


# _____________________________________________________________________________
if __name__ == '__main__':
    main()