from abc import ABC, abstractmethod
from datetime import date
import json
import logging.handlers
from pathlib import Path

# Common variables
_logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class AppConfig(ABC):
    _base_url = 'https://docs.aws.amazon.com/'

    # _____________________________________________________________________________
    def __init__(self, app_path: Path, output_path: Path):
        """Initialises the configuration class
        """
        _logger.debug(f'__init__ app_path "{app_path}"')

        # Initialize
        self._name = app_path.stem
        self._base_path = output_path

        # Load common App config file
        config_file_path = Path(__file__).with_suffix('.config.json')
        _logger.debug(f'Config file: "{config_file_path}"')
        with config_file_path as fp:
            config_settings = json.loads(fp.read_text())
        cache_settings = config_settings['cache']
        output_settings = config_settings['local']

        # Cache
        self._cache_base_path = Path(self._base_path, cache_settings['localPath']).resolve()
        self._cache_path = Path(self._cache_base_path, self._name).resolve()
        self._cache_age_sec = int(cache_settings.get('age', 300))

        # Output
        self._downloads_base_path = Path(self._base_path, output_settings['localPath']).resolve()
        self._downloads_path = Path(self._downloads_base_path, self._name).resolve()

        # Archive
        self._archive_path = Path(self._downloads_path, output_settings['archiveName']).resolve()

        # Files
        self._summary_file_path = Path(self._cache_path, self._name + '.summary.json').resolve()
        self._data_file_path = Path(self._cache_base_path,
                    f'{self._name}.data.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._report_file_path = Path(self._cache_base_path,
                    f'{self._name}.report.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._extras_file_path = Path(self._cache_base_path, f'{self._name}.extra.csv').resolve()

    # _____________________________________________________________________________
    @property
    def name(self):
        return self._name

    # _____________________________________________________________________________
    @property
    @abstractmethod
    def source_url(self):
        raise NotImplementedError('source_url')

    # _____________________________________________________________________________
    @property
    @abstractmethod
    def source_parameters(self):
        raise NotImplementedError('source_parameters')

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
    def downloads_base_path(self):
        return self._downloads_base_path

    # _____________________________________________________________________________
    @property
    def downloads_path(self):
        return self._downloads_path

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
