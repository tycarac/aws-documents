import json
import logging.handlers
from pathlib import Path

from common.appConfig import AppConfig

# Common variables
_logger = logging.getLogger(__name__)


# _____________________________________________________________________________
class BuildersAppConfig(AppConfig):

    # _____________________________________________________________________________
    def __init__(self, main_path: Path):
        super().__init__(main_path)

        # Run application
        config_file_path = main_path.with_suffix('.config.json')
        _logger.debug(f'Config file: {config_file_path}')
        with config_file_path as f:
            config_settings = json.loads(f.read_text())

        remote_settings = config_settings['remote']

        # Remote URL
        self._source_url = remote_settings['urlLoc']
        self._source_parameters = remote_settings['urlParameters']

    # _____________________________________________________________________________
    @property
    def source_url(self):
        return self._source_url

    # _____________________________________________________________________________
    @property
    def source_parameters(self):
        return self._source_parameters
