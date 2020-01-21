from datetime import date
import json
import logging.handlers
from pathlib import Path

# Common variables
logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class AppConfig:
    _base_url = 'https://docs.aws.amazon.com/'

    # _____________________________________________________________________________
    def __init__(self, main_path: Path):

        # Run application
        with Path(main_path.with_suffix('.config.json')) as f:
            config_settings = json.loads(f.read_text())

        # Initialize
        self._name = main_path.stem
        cache_settings = config_settings['cache']
        output_settings = config_settings['local']
        remote_settings = config_settings['remote']

        # Cache
        self._cache_base_path = Path(cache_settings['localPath']).resolve()
        self._cache_path = Path(self._cache_base_path, self._name).resolve()
        self._cache_age_sec = int(cache_settings.get('age', 300))

        # Output
        self._output_base_local_path = Path(output_settings['localPath']).resolve()
        self._output_local_path = Path(self._output_base_local_path, self._name).resolve()

        # Archive
        self._archive_path = self._output_local_path.joinpath(output_settings['archiveName']).resolve()

        # Files
        self._summary_file_path = Path(self._cache_path, self._name + '.summary.json').resolve()
        self._data_file_path = Path(self._cache_base_path,
                    f'{self._name}.data.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._report_file_path = Path(self._cache_base_path,
                    f'{self._name}.report.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._extras_file_path = Path(self._cache_base_path, f'{self._name}.extra.csv').resolve()

        # Remote URL
        self._source_url = remote_settings['urlLoc']
        self._source_parameters = remote_settings['urlParameters']

    # _____________________________________________________________________________
    @property
    def name(self):
        return self._name

    # _____________________________________________________________________________
    @property
    def source_url(self):
        return self._source_url

    # _____________________________________________________________________________
    @property
    def source_parameters(self):
        return self._source_parameters

    # _____________________________________________________________________________
    @property
    def cache_age_sec(self):
        return self._cache_age_sec

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

    # _____________________________________________________________________________
    @property
    def extras_file_path(self):
        return self._extras_file_path
