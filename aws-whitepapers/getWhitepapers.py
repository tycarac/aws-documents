from collections import Counter
import csv
from datetime import date, datetime, timedelta
from io import StringIO
import json
import logging.config, logging.handlers
import os
from pathlib import Path
import time
from typing import List

from common import Record, Changed, Result
from fetch import FetchItem
from fetchList import FetchItemList
from logger import NoExceptionFormatter

# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
def export_results(records, paths):
    logger.debug('export_results')

    out_data_path = paths['dataFilePath']
    with out_data_path.open(mode='wt', newline='') as out:
        csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(Record.__slots__)
        for r in records:
            csv_writer.writerow(
                [r.name, r.title, r.category, r.contentType, r.description, r.dateCreated, r.dateUpdated,
                    r.datePublished, r.dateSort, r.url, r.filename, r.filepath, r.changed.name, r.result.name])

    out_report_path = paths['reportFilePath']
    with out_report_path.open(mode='wt', newline='') as out:
        csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['datePublished', 'changed', 'contentType', 'filename'])
        for r in records:
            csv_writer.writerow([r.datePublished, r.changed.name, r.contentType, r.filename])


# _____________________________________________________________________________
def build_summary(records: List[Record]):
    with StringIO() as buf:
        counter_changed = Counter(map(lambda r: r.changed, records))
        counter_result = Counter(map(lambda r: r.result, records))
        buf.write('Records:    %5d\n' % len(records))
        buf.write('- Cached:   %5d\n' % counter_changed[Changed.cached])
        buf.write('- Created:  %5d\n' % counter_changed[Changed.created])
        buf.write('- Updated:  %5d\n' % counter_changed[Changed.updated])
        buf.write('- Deleted:  %5d\n' % counter_changed[Changed.deleted])
        buf.write('- Archived: %5d\n' % counter_changed[Changed.archived])
        buf.write('- Nil:      %5d\n' % counter_changed[Changed.nil])
        buf.write('Results\n')
        buf.write('- Warnings: %5d\n' % counter_result[Result.warning])
        buf.write('- Errors:   %5d\n' % counter_result[Result.error])
        buf.write('- Nil:      %5d\n' % counter_result[Result.nil])
        return buf.getvalue()


# _____________________________________________________________________________
def process(config_settings, paths):
    fdl = FetchItemList(config_settings, paths)
    records = fdl.build_list()
    try:
        fd = FetchItem(config_settings, paths)
        fd.process(records)
    finally:
        export_results(records, paths)
        logger.info('\n' + build_summary(records))


# _____________________________________________________________________________
def derive_paths(config_settings):
    name = Path(__file__).stem

    # Initialize
    cache_settings = config_settings['cache']
    cache_base_path = Path(cache_settings['localPath']).resolve()
    cache_path = Path(cache_base_path, name).resolve()

    output_settings = config_settings['local']
    output_base_local_path = Path(output_settings['localPath']).resolve()
    output_local_path = Path(output_base_local_path, name).resolve()

    paths = {
        'name': Path(__file__).stem,
        # Cache
        'cacheBasePath': cache_base_path,
        'cachePath': Path(cache_base_path, name).resolve(),
        'summaryFilepath': Path(cache_path, name + '.summary.json').resolve(),
        # Output
        'outputBaseLocalPath': output_base_local_path,
        'outputLocalPath': Path(output_base_local_path, name).resolve(),
        # Report
        'dataFilePath': Path(cache_base_path, '%s.data.%s.csv' % (name, date.today().strftime('%y-%m-%d'))).resolve(),
        'reportFilePath': Path(cache_base_path, '%s.report.%s.csv' % (name, date.today().strftime('%y-%m-%d'))).resolve(),
        # Archive
        'archivePath': output_local_path.joinpath(output_settings['archiveName']).resolve()
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