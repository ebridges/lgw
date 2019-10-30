'''
Lambda Gateway.

Usage:
  lgw deploy-api --config-file=<cfg>

Options:
  -h --help             Show this screen.
  --version             Show version.
  --config-file=<cfg>   Override defaults with these settings.
'''

from logging import info, debug, error
from docopt import docopt
from .util import configure_logging
from . import __version__

def app():
  info('Hello World!')

def main():
  args = docopt(__doc__, version=__version__)
  configure_logging(args.get('--verbose'))

if __name__== '__main__':
  main()
