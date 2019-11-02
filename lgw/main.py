'''
Lambda Gateway.

Usage:
  lgw deploy-api [--verbose] --config-file=<cfg>

Options:
  -h --help             Show this screen.
  --version             Show version.
  --verbose             Enable DEBUG-level logging.
  --config-file=<cfg>   Override defaults with these settings.
'''

from os import path
from logging import info, debug, error
from everett.manager import ConfigManager, ConfigOSEnv, ConfigEnvFileEnv, ConfigDictEnv
from docopt import docopt
from lgw.util import configure_logging
from lgw.version import __version__
from lgw import settings
from lgw.api_gateway import create_rest_api


def app(args, config):
    if args.get('deploy-api'):
        api_url = create_rest_api(
          config('aws_api_name'),
          config('aws_lambda_name'),
          config('aws_api_resource_path'),
          config('aws_api_deploy_stage')
        )
        info('REST API URL: [%s]' % api_url)


def main():
    args = docopt(__doc__, version=__version__)
    configure_logging(args.get('--verbose'))
    config_file = args.get('--config-file')

    config = ConfigManager(
        [
            ConfigOSEnv(),
            ConfigEnvFileEnv('.env'),
            ConfigEnvFileEnv(config_file),
            ConfigDictEnv(settings.defaults()),
        ]
    )

    app(args, config)


if __name__ == '__main__':
    main()
