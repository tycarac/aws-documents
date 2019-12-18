from collections import Counter
import csv
from datetime import datetime, timedelta
from io import StringIO
import json
import logging.config, logging.handlers
from operator import attrgetter
import os
from pathlib import Path
import time
from typing import List

from appPaths import AppPaths
from common import Record, Changed, Result
from fetch import FetchItem
from fetchList import FetchItemList
from logger import NoExceptionFormatter

# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
def export_results(records: List[Record], paths: AppPaths):
    logger.debug('export_results')

    results_path = paths.data_file_path
    out_report_path = paths.report_file_path

    # Read and update
    has_existing_results = results_path.exists() and results_path.stat().st_size > 0
    if has_existing_results:
        with results_path.open(mode='r', newline='') as rp:
            csv_reader = csv.reader(rp)
            next(csv_reader, None)  # skip csv header
            rows = {rec.filename: rec for rec in [Record.from_string(rec) for rec in csv_reader]}
        for rec in records:
            if rec.changed != Changed.cached or rec.result != Result.success:
                logger.debug('Rec org|new: %s | %s' % (rows.get('filename', ''), rec))
                rows['filename'] = rec
        results = rows.values()
    else:
        results = records
    sorted(results, key=attrgetter('contentType', 'datePublished', 'filename'))

    # Write
    try:
        try:
            results_path.with_suffix('.bak.csv').write_text(results_path.read_text())
        except Exception as ex:
            logger.exception('Error backing up data file')
        with results_path.open(mode='w', newline='') as out:
            csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(Record.__slots__)
            for r in results:
                csv_writer.writerow(
                    [r.name, r.title, r.category, r.contentType, r.description, r.dateCreated, r.dateUpdated,
                        r.datePublished, r.dateSort, r.url, r.filename, r.filepath, r.changed.name, r.result.name])

        try:
            out_report_path.with_suffix('.bak.csv').write_text(out_report_path.read_text())
        except Exception as ex:
            logger.exception('Error backing up data file')
        with out_report_path.open(mode='w', newline='') as out:
            csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['datePublished', 'changed', 'contentType', 'filename'])
            for r in results:
                csv_writer.writerow([r.datePublished, r.changed.name, r.contentType, r.filename])
    except Exception as ex:
        logger.exception('Error writing files')
        raise ex


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
def process(config_settings, paths: AppPaths):
    fdl = FetchItemList(config_settings, paths)
    records = fdl.build_list()
    try:
        fd = FetchItem(paths)
        fd.process(records)
    finally:
        export_results(records, paths)
        logger.info('\n' + build_summary(records))


# _____________________________________________________________________________
def main():
    start_time = time.time()
    main_path = Path(__file__)
    try:
        # Configure logging
        logging.captureWarnings(True)
        with main_path.with_suffix('.logging.json') as p:
            logging.config.dictConfig(json.loads(p.read_text()))
        start_datetime = datetime.fromtimestamp(start_time)
        logger.info('Now: %s' % start_datetime.strftime('%a  %d-%b-%y  %I:%M:%S %p'))
        logger.debug('CPU count: %s' % os.cpu_count())

        # Run application
        with main_path.with_suffix('.config.json') as f:
            config_settings = json.loads(f.read_text())

        paths = AppPaths(main_path.stem, config_settings)
        process(config_settings, paths)
    except Exception as ex:
        logger.exception('Catch all exception')
    finally:
        run_timedelta = timedelta(seconds=time.time() - start_time)
        logger.info('Run time: %02d:%02d' % (divmod(run_timedelta.total_seconds(), 60)))


# _____________________________________________________________________________
if __name__ == '__main__':
    main()