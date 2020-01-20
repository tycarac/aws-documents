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

from .appConfig import AppConfig
from .common import FetchRecord, DeleteRecord, Outcome, Result
from .fetch import FetchItem
from .fetchList import FetchItemList
from .cleanup import CleanOutput
from .logTools import MessageFormatter

# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
def merge_fetch_results(records: List[FetchRecord], data_path: Path):
    logger.debug('merge_fetch_results')

    if data_path.exists() and data_path.stat().st_size > 0:
        with data_path.open(mode='r', newline='') as rp:
            csv_reader = csv.reader(rp)
            next(csv_reader, None)  # skip csv header
            rows = {rec.filename: rec for rec in [FetchRecord.from_string(rec) for rec in csv_reader]}
        for rec in records:
            if rec.outcome != Outcome.cached or rec.result != Result.success:
                logger.debug('Rec org|new: %s | %s' % (rows.get('filename', ''), rec))
                rows['filename'] = rec
        results = rows.values()
    else:
        results = records
    sorted(results, key=attrgetter('contentType', 'datePublished', 'filename'), reverse=True)

    return results


# _____________________________________________________________________________
def export_fetch_results(records: List[FetchRecord], app_config: AppConfig):
    logger.debug('export_fetch_results')

    data_path = app_config.data_file_path
    merged_records = merge_fetch_results(records, data_path)

    # Write data
    if data_path.exists():
        try:
            data_path.with_suffix('.bak.csv').write_text(data_path.read_text())
        except Exception as ex:
            logger.exception('Error backing up data file: "%s"' % data_path)
    try:
        with data_path.open(mode='w', newline='') as out:
            csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(FetchRecord.__slots__)
            for r in merged_records:
                csv_writer.writerow(
                    [r.name, r.title, r.category, r.contentType, r.featureFlag, r.description,
                        r.dateCreated, r.dateUpdate, r.datePublished, r.dateSort, r.publishedDateText,
                        r.url, r.filename, r.filepath, r.outcome.name, r.result.name])
    except Exception as ex:
        logger.exception('Error writing report file: "%s"' % data_path)

    # Write report
    report_path = app_config.report_file_path
    if report_path.exists():
        try:
            report_path.with_suffix('.bak.csv').write_text(report_path.read_text())
        except Exception as ex:
            logger.exception('Error backing up report file: "%s"' % report_path)
    try:
        with report_path.open(mode='w', newline='') as out:
            csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['datePublished', 'dateSort', 'dateUpdate', 'featureFlag', 'changed',
                        'contentType', 'filename'])
            for r in merged_records:
                csv_writer.writerow([r.datePublished, r.dateSort, r.dateUpdate, r.featureFlag, r.outcome.name,
                            r.contentType, r.filename])
    except Exception as ex:
        logger.exception('Error writing report file: "%s"' % report_path)


# _____________________________________________________________________________
def export_extras_results(records: List[DeleteRecord], app_config: AppConfig):
    logger.debug('export_extras_results')

    if not records:
        return

    extras_path = app_config.extras_file_path
    has_extras_path = extras_path.exists() and extras_path.stat().st_size > 0
    if has_extras_path:
        try:
            extras_path.with_suffix('.bak.csv').write_text(extras_path.read_text())
        except Exception as ex:
            logger.exception('Error backing up extras file: "%s"' % extras_path)
    try:
        with extras_path.open(mode='a', newline='') as out:
            csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
            if not has_extras_path:
                csv_writer.writerow(DeleteRecord.__slots__)
            for r in records:
                csv_writer.writerow(
                    [r.contentType, r.dateDeleted, r.filename, r.filepath, r.outcome.name, r.result.name])
    except Exception as ex:
        logger.exception('Error writing extras file: "%s"' % extras_path)


# _____________________________________________________________________________
def build_summary(fetch_records: List[FetchRecord], delete_records: List[FetchRecord]):
    logger.debug('build_summary')

    counter_outcome = Counter(map(lambda r: r.outcome, fetch_records))
    counter_outcome += Counter(map(lambda r: r.outcome, delete_records))
    counter_result = Counter(map(lambda r: r.result, fetch_records))
    counter_result += Counter(map(lambda r: r.result, delete_records))

    with StringIO() as buf:
        buf.write('Records:    %5d\n' % len(fetch_records))
        buf.write('- Cached:   %5d\n' % counter_outcome[Outcome.cached])
        buf.write('- Created:  %5d\n' % counter_outcome[Outcome.created])
        buf.write('- Updated:  %5d\n' % counter_outcome[Outcome.updated])
        buf.write('- Nil:      %5d\n' % counter_outcome[Outcome.nil])
        buf.write('  Archived: %5d\n' % counter_outcome[Outcome.archived])
        buf.write('  Deleted:  %5d\n' % counter_outcome[Outcome.deleted])
        buf.write('Results\n')
        buf.write('- Warnings: %5d\n' % counter_result[Result.warning])
        buf.write('- Errors:   %5d\n' % counter_result[Result.error])
        buf.write('- Nil:      %5d\n' % counter_result[Result.nil])

        return buf.getvalue()


# _____________________________________________________________________________
def process(app_config: AppConfig):
    logger.debug('process')
    logger.info('Output path: %s' % app_config.output_local_path)

    fdl = FetchItemList(app_config)
    fetch_records = fdl.build_list()

    delete_records = []
    try:
        fd = FetchItem(app_config)
        fd.process(fetch_records)

        co = CleanOutput(app_config)
        delete_records = co.process(fetch_records)
    finally:
        export_fetch_results(fetch_records, app_config)
        export_extras_results(delete_records, app_config)
        logger.info('\n' + build_summary(fetch_records, delete_records))


# _____________________________________________________________________________
def main():
    start_time = time.time()
    try:
        main_path = Path(__file__)

        # Configure logging
        logging.captureWarnings(True)
        with main_path.with_suffix('.logging.json') as p:
            logging.config.dictConfig(json.loads(p.read_text()))
        start_datetime = datetime.fromtimestamp(start_time)
        logger.info('Now: %s' % start_datetime.strftime('%a  %d-%b-%y  %I:%M:%S %p'))
        logger.debug('CPU count: %s' % os.cpu_count())

        process(AppConfig(main_path))
    except Exception as ex:
        logger.exception('Catch all exception')
    finally:
        run_timedelta = timedelta(seconds=time.time() - start_time)
        logger.info('Run time: %02d:%02d' % (divmod(run_timedelta.total_seconds(), 60)))


# _____________________________________________________________________________
if __name__ == '__main__':
    main()