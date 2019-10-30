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
from dynaconf import settings
from docopt import docopt
from lgw.util import configure_logging
from lgw.version import __version__

def app(args):
  info('Hello World!')
  info('Port: %d' % settings.PORT)

def main():
  args = docopt(__doc__, version=__version__)
  configure_logging(args.get('--verbose'))
  app(args)

if __name__== '__main__':
  main()
