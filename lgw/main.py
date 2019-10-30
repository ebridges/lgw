'''
Lambda Gateway.

Usage:
  lgw deploy-api --config-file=<cfg>

Options:
  -h --help             Show this screen.
  --version             Show version.
  --config-file=<cfg>   Override defaults with these settings.
'''

from docopt import docopt


def main(args):
  print('Hello World!')
  
if __name__== '__main__':
  args = docopt(__doc__, version=__version__)
  main(args)
