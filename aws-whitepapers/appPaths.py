from datetime import date
import logging.handlers
from pathlib import Path

# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class AppPaths:
    _base_url = 'https://docs.aws.amazon.com/'

    # _____________________________________________________________________________
    def __init__(self, name, config_settings):
        # Initialize
        self._name = name
        cache_settings = config_settings['cache']
        output_settings = config_settings['local']

        # Cache
        self._cache_base_path = Path(cache_settings['localPath']).resolve()
        self._cache_path = Path(self._cache_base_path, name).resolve()

        # Output
        self._output_base_local_path = Path(output_settings['localPath']).resolve()
        self._output_local_path = Path(self._output_base_local_path, name).resolve()

        # Archive
        self._archive_path = self._output_local_path.joinpath(output_settings['archiveName']).resolve()

        # Files
        self._summary_file_path = Path(self._cache_path, name + '.summary.json').resolve()
        self._data_file_path = Path(self._cache_base_path, '%s.data.%s.csv'
                    % (name, date.today().strftime('%y-%m-%d'))).resolve()
        self._report_file_path = Path(self._cache_base_path, '%s.report.%s.csv'
                    % (name, date.today().strftime('%y-%m-%d'))).resolve()

    # _____________________________________________________________________________
    @property
    def name(self):
        return self._name

    # _____________________________________________________________________________
    @property
    def cache_base_path(self):
        return self._cache_base_path

    # _____________________________________________________________________________
    @property
    def cache_path(self):
        return self._cache_path

    # _____________________________________________________________________________
    @property
    def output_base_local_path(self):
        return self._output_base_local_path

    # _____________________________________________________________________________
    @property
    def output_local_path(self):
        return self._output_local_path

    # _____________________________________________________________________________
    @property
    def archive_path(self):
        return self._archive_path

    # _____________________________________________________________________________
    @property
    def summary_file_path(self):
        return self._summary_file_path

    # _____________________________________________________________________________
    @property
    def data_file_path(self):
        return self._data_file_path

    # _____________________________________________________________________________
    @property
    def report_file_path(self):
        return self._report_file_path
