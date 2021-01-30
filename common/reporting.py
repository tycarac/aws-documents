from collections import Counter
import csv
from io import StringIO
import logging.config
from operator import attrgetter
from typing import List, Type

from common.appConfig import AppConfig
from common.common import DeleteRecord, Outcome, Result, FetchItem

# Common variables
_logger = logging.getLogger(__name__)
_CSV_BACKUP_SUFFIX = '.bak.csv'


class Reporting:
    # _____________________________________________________________________________
    def __init__(self, frecs: List[FetchItem], cls, drecs: List[DeleteRecord],
                app_config: AppConfig):
        self._frecs = frecs
        self._cls = cls
        self._drecs = drecs
        self._app_config = app_config

    # _____________________________________________________________________________
    def __merge_fetch_results(self):
        _logger.debug('__merge_fetch_results')

        data_path = self._app_config.data_file_path
        if data_path.exists() and data_path.stat().st_size > 0:
            with data_path.open(mode='r', newline='') as rp:
                csv_reader = csv.reader(rp)
                next(csv_reader, None)  # skip csv header
                rows = {r.filename: r for r in [self._cls.from_string(line) for line in csv_reader]}
            for rec in self._frecs:
                if rec.outcome != Outcome.cached or rec.result != Result.success:
                    _logger.debug(f'Rec org|new: {rows.get(rec.filename, "")} | {rec}')
                    rows[rec.filename] = rec
            results = rows.values()
        else:
            results = self._frecs

        # Sort report (but only use fields from base class)
        results = sorted(results, key=attrgetter('contentType', 'dateRemote', 'title'), reverse=True)

        return results

    # _____________________________________________________________________________
    def export_fetch_results(self):
        _logger.debug('export_fetch_results')

        data_path = self._app_config.data_file_path
        merged_records = self.__merge_fetch_results()

        # Write data
        if data_path.exists():
            try:
                data_path.with_suffix(_CSV_BACKUP_SUFFIX).write_text(data_path.read_text())
            except Exception as ex:
                _logger.exception(f'Error backing up data file: "{data_path}"')
        try:
            with data_path.open(mode='w', newline='') as out:
                csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(self._cls.__slots__)
                for mr in merged_records:
                    csv_writer.writerow(mr.to_list())

        except Exception as ex:
            _logger.exception(f'Error writing report file: "{data_path}"')

    # _____________________________________________________________________________
    def export_extras_results(self):
        _logger.debug('export_extras_results')

        if not self._drecs:
            return

        extras_path = self._app_config.extras_file_path
        has_extras_path = extras_path.exists() and extras_path.stat().st_size > 0
        if has_extras_path:
            try:
                extras_path.with_suffix(_CSV_BACKUP_SUFFIX).write_text(extras_path.read_text())
            except Exception as ex:
                _logger.exception(f'Error backing up extras file: "{extras_path}"')
        try:
            with extras_path.open(mode='a', newline='') as out:
                csv_writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
                if not has_extras_path:
                    csv_writer.writerow(DeleteRecord.__slots__)
                for r in self._drecs:
                    csv_writer.writerow(
                        [r.contentType, r.dateDeleted, r.filename, r.filepath, r.outcome.name, r.result.name])
        except Exception as ex:
            _logger.exception(f'Error writing extras file: "{extras_path}"')

    # _____________________________________________________________________________
    def build_summary(self):
        _logger.debug('build_summary')

        counter_outcome = Counter(map(lambda r: r.outcome, self._frecs))
        counter_outcome += Counter(map(lambda r: r.outcome, self._drecs))
        counter_result = Counter(map(lambda r: r.result, self._frecs))
        counter_result += Counter(map(lambda r: r.result, self._drecs))

        with StringIO() as buf:
            buf.write(f'Records:    {len(self._frecs):5d}\n')
            buf.write(f'- Cached:   {counter_outcome[Outcome.cached]:5d}\n')
            buf.write(f'- Created:  {counter_outcome[Outcome.created]:5d}\n')
            buf.write(f'- Updated:  {counter_outcome[Outcome.updated]:5d}\n')
            buf.write(f'- Nil:      {counter_outcome[Outcome.nil]:5d}\n')
            buf.write(f'  Archived: {counter_outcome[Outcome.archived]:5d}\n')
            buf.write(f'  Deleted:  {counter_outcome[Outcome.deleted]:5d}\n')
            buf.write(f'Results\n')
            buf.write(f'- Warnings: {counter_result[Result.warning]:5d}\n')
            buf.write(f'- Errors:   {counter_result[Result.error]:5d}\n')
            buf.write(f'- Nil:      {counter_result[Result.nil]:5d}\n')
            return buf.getvalue()
