'''
Lambda Gateway.

Usage:
  lgw lgw-deploy [--verbose] --config-file=<cfg>
  lgw lgw-undeploy [--verbose] --config-file=<cfg>
  lgw add-domain [--verbose] --config-file=<cfg>
  lgw remove-domain [--verbose] --config-file=<cfg>
  lgw lambda-deploy [--verbose] --config-file=<cfg> --lambda-file=<zip>
  lgw lambda-invoke [--verbose] --lambda-name=<name> [--payload=<json>]
  lgw lambda-delete [--verbose] --lambda-name=<name>

Options:
  -h --help             Show this screen.
  --version             Show version.
  --verbose             Enable DEBUG-level logging.
  --config-file=<cfg>   Override defaults with these settings.
  --lambda-file=<zip>   Path to zip file with executable lambda code.
  --lambda-name=<name>  Name of the lambda to invoke or delete.
  --payload=<json>      Path to a file of type json with data to send with the lambda invocation.
'''

from os import path
import json
from logging import info, debug, error
from everett.manager import ConfigManager, ConfigOSEnv, ConfigEnvFileEnv, ConfigDictEnv
from docopt import docopt
from lgw.util import configure_logging
from lgw.version import __version__
from lgw import settings
from lgw.api_gateway import create_rest_api, delete_rest_api
from lgw.api_gateway_domain import add_domain_mapping, remove_domain_mapping
from lgw.lambda_util import deploy_function, invoke_function, delete_function


def handle_deploy_lambda(file, config):
    info('handle_deploy_lambda() called with file [%s]' % file)
    if not path.isfile(file):
        error('ERROR: Lambda zip file not found at location: [%s]' % file)
        return
    if not file.endswith('.zip'):
        error('ERROR: Lambda file expected to be in ZIP format.')
        return

    lambda_arn = deploy_function(
        file,
        config('aws_lambda_name'),
        config('aws_lambda_handler'),
        config('aws_lambda_execution_role_arn'),
        config('aws_lambda_connection_timeout'),
        config('aws_lambda_memory_size'),
        config('aws_lambda_runtime'),
        config('aws_lambda_archive_bucket'),
        config('aws_lambda_archive_key'),
        config('aws_lambda_description'),
        config('aws_lambda_vpc_subnets'),
        config('aws_lambda_vpc_security_groups'),
        config('aws_lambda_environment'),
        config('aws_lambda_tags'),
    )
    print(lambda_arn)
    info('Lambda [%s] created.' % config('aws_lambda_name'))
    return 1


def handle_invoke_lambda(name, payload):
    info('handle_invoke_lambda() called for lambda [%s]' % name)
    if payload:
        result = invoke_function(name, payload)
    else:
        result = invoke_function(name)
    json_result = json.loads(result['Payload'].read().decode('utf-8'))
    print(json_result)
    info('Invocation completed for lambda [%s]' % name)
    return 1


def handle_delete_lambda(name):
    info('handle_delete_lambda() called for lambda [%s]' % name)
    delete_function(name)
    info('Lambda [%s] deleted.' % name)
    return 1


def handle_deploy_api_gateway(config):
    api_url = create_rest_api(
        config('aws_api_name'),
        config('aws_lambda_name'),
        config('aws_api_resource_path'),
        config('aws_api_deploy_stage'),
        config('aws_api_lambda_integration_role'),
    )
    print(api_url)
    info('REST API URL: [%s]' % api_url)
    return 1

def handle_undeploy_api_gateway(config):
    delete_rest_api(config('aws_api_name'))
    info('API Gateway %s deleted.' % config('aws_api_name'))
    return 1

def handle_add_domain(config):
    add_domain_mapping(
        config('aws_api_name'),
        config('aws_api_domain_name'),
        config('aws_api_base_path'),
        config('aws_acm_certificate_arn'),
        config('aws_api_deploy_stage'),
        config('aws_api_domain_wait_until_available'),
    )
    info('Domain name %s mapped to path %s' % (config('aws_api_domain_name'), config('aws_api_base_path')))
    info('HTTPS certificate validation may be pending.  Check here for status: https://console.aws.amazon.com/apigateway/home?region=us-east-1#/custom-domain-names')
    return 1

def handle_remove_domain(config):
    remove_domain_mapping(
        config('aws_api_name'),
        config('aws_api_domain_name'),
        config('aws_api_base_path'),
    )
    info('Domain name %s unmapped from API %s' % (config('aws_api_domain_name'), config('aws_api_name')))
    return 1


def app(args, config):
    if args.get('lgw-deploy'):
        return handle_deploy_api_gateway(config)
    if args.get('lgw-undeploy'):
        return handle_undeploy_api_gateway(config)
    if args.get('add-domain'):
        return handle_add_domain(config)
    if args.get('remove-domain'):
        return handle_remove_domain(config)
    if args.get('lambda-deploy'):
        file = path.abspath(args.get('--lambda-file'))
        return handle_deploy_lambda(file, config)
    if args.get('lambda-invoke'):
        name = args.get('--lambda-name')
        payload = args.get('--payload', None)
        return handle_invoke_lambda(name, payload)
    if args.get('lambda-delete'):
        name = args.get('--lambda-name')
        return handle_delete_lambda(name)

    error('Unrecognized command.')

def main():
    args = docopt(__doc__, version=__version__)
    configure_logging(args.get('--verbose'))
    config_file = args.get('--config-file', None)
    if config_file:
        config_file = path.abspath(config_file)

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
