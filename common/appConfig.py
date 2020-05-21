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
    def __init__(self, app_path: Path, output_root: Path):
        """Initialises the configuration class
        """
        _logger.debug(f'__init__ app_path "{app_path}"')

        # Initialize
        self._name = app_path.stem
        self._output_root = output_root

        # Folders
        self._downloads_path = Path(self._output_root, 'downloads', self._name).resolve()
        self._archive_path = Path(self._output_root, 'archive', self._name).resolve()
        self._cache_root = Path(self._output_root, 'cache')
        self._cache_path = Path(self._cache_root, self._name).resolve()

        # Files
        self._summary_file_path = Path(self._cache_path, self._name + '.summary.json').resolve()
        self._data_file_path = Path(self._cache_root,
                    f'{self._name}.data.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._report_file_path = Path(self._cache_root,
                    f'{self._name}.report.{date.today().strftime("%y-%m-%d")}.csv').resolve()
        self._extras_file_path = Path(self._cache_root, f'{self._name}.extra.csv').resolve()

        # Ensure directories pre-exist
        self._downloads_path.mkdir(parents=True, exist_ok=True)
        self._cache_path.mkdir(parents=True, exist_ok=True)
        _logger.debug(f'cache_path "{self._cache_path}"')
        _logger.debug(f'downloads_path "{self._downloads_path}"')

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
        raise NotImplementedError('cache_age_sec')

    # _____________________________________________________________________________
    @property
    def cache_path(self):
        return self._cache_path

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
