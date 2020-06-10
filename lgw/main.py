'''
Lambda Gateway.

Usage:
  lgw gw-deploy [--verbose] [--config-file=<cfg>]
  lgw gw-undeploy [--verbose] [--config-file=<cfg>]
  lgw domain-add [--verbose] [--config-file=<cfg>]
  lgw domain-remove [--verbose] [--config-file=<cfg>]
  lgw lambda-deploy [--verbose] [--config-file=<cfg>] [--lambda-file=<zip>]
  lgw lambda-invoke [--verbose] --lambda-name=<name> [--payload=<json>]
  lgw lambda-delete [--verbose] --lambda-name=<name>
  lgw lambda-archive [--verbose] [--config-file=<cfg>]

Options:
  -h --help             Show this screen.
  --version             Show version.
  --verbose             Enable DEBUG-level logging.
  --config-file=<cfg>   Override defaults with these settings.
  --lambda-file=<zip>   Path to zip file with executable lambda code.
  --lambda-name=<name>  Name of the lambda to invoke or delete.
  --payload=<json>      Path to a file of type json with data to send with the lambda invocation.
'''

from os import path, makedirs
from sys import argv
import json
from logging import info, debug, error
from everett.manager import ConfigManager, ConfigOSEnv, ConfigDictEnv
from docopt import docopt
from dotenv import dotenv_values, find_dotenv
from lgw.util import configure_logging
from lgw.version import __version__
from lgw import settings
from lgw.api_gateway import create_rest_api, delete_rest_api
from lgw.api_gateway_domain import add_domain_mapping, remove_domain_mapping
from lgw.lambda_util import deploy_function, invoke_function, delete_function
from lgw.lambda_bundle import build_lambda_archive
from lgw.settings import dump


def handle_deploy_lambda(config):
    return handle_deploy_lambda(None, config)


def handle_deploy_lambda(file, config):
    if file:
        info(f'handle_deploy_lambda() called with file [{file}]')
    else:
        info(
            'handle_deploy_lambda() called with s3://%s/%s'
            % (config('aws_lambda_archive_bucket'), config('aws_lambda_archive_key'))
        )

    if file:
        if not path.isfile(file):
            raise FileNotFoundError('ERROR: Lambda zip file not found at location: [%s]' % file)

        if not file.endswith('.zip'):
            raise FileNotFoundError('ERROR: Lambda file expected to be in ZIP format.')

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


def handle_lambda_archive(config):
    info(f'handle_lambda_archive() called.')
    addl_files = []
    if config('aws_lambda_archive_addl_files'):
        addl_files = [
            (x, y)
            for x, y in (
                line.split(',') for line in config('aws_lambda_archive_addl_files').split(';')
            )
        ]

    addl_packages = []
    if config('aws_lambda_archive_addl_packages'):
        addl_packages = config('aws_lambda_archive_addl_packages').split(',')

    context_dir = config('aws_lambda_archive_context_dir')
    if context_dir == '.':
        context_dir = path.abspath(context_dir)
        context_dir = f'{context_dir}/'

    if not path.exists(context_dir):
        raise FileNotFoundError(f'context dir not found: [context_dir]')

    bundle_dir = path.abspath(config('aws_lambda_archive_bundle_dir'))
    if not path.exists(bundle_dir):
        makedirs(bundle_dir)

    path_to_archive = build_lambda_archive(
        context_dir, bundle_dir, config('aws_lambda_archive_bundle_name'), addl_files, addl_packages
    )
    print(path_to_archive)
    info(f'lambda archive location: [{path_to_archive}]')


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
    binary_types = []
    if config('aws_api_binary_types'):
        binary_types = config('aws_api_binary_types').split(',')

    response_models = {}
    if config('aws_api_response_models'):
        response_models = dict(
            item.split('=') for item in config('aws_api_response_models').split(';')
        )

    api_url = create_rest_api(
        config('aws_api_name'),
        config('aws_api_description'),
        binary_types,
        config('aws_lambda_name'),
        config('aws_api_resource_path'),
        config('aws_api_deploy_stage'),
        config('aws_api_lambda_integration_role'),
        response_models,
    )
    print(api_url)
    info('REST API URL: [%s]' % api_url)
    return 1


def handle_undeploy_api_gateway(config):
    delete_rest_api(config('aws_api_name'))
    info('API Gateway %s deleted.' % config('aws_api_name'))
    return 1


def handle_add_domain(config):
    api_name = config('aws_api_name')
    domain_name = config('aws_api_domain_name')
    base_path = config('aws_api_base_path')
    cert_arn = config('aws_acm_certificate_arn')
    deploy_stage = config('aws_api_deploy_stage')
    wait_until = config('aws_api_domain_wait_until_available')

    add_domain_mapping(api_name, domain_name, base_path, cert_arn, deploy_stage, wait_until)

    info(f'Domain name {domain_name} mapped to path {base_path}')
    info('HTTPS certificate validation may still be pending. Check here for status:')
    info('https://console.aws.amazon.com/apigateway/home?region=us-east-1#/custom-domain-names')

    return 1


def handle_remove_domain(config):
    api_name = config('aws_api_name')
    domain_name = config('aws_api_domain_name')
    base_path = config('aws_api_base_path')

    remove_domain_mapping(api_name, domain_name, base_path)

    info(f'Domain name {domain_name} unmapped from API {api_name}')
    return 1


def app(args, config):
    if args.get('gw-deploy'):
        return handle_deploy_api_gateway(config)
    if args.get('gw-undeploy'):
        return handle_undeploy_api_gateway(config)
    if args.get('domain-add'):
        return handle_add_domain(config)
    if args.get('domain-remove'):
        return handle_remove_domain(config)
    if args.get('lambda-deploy'):
        file_arg = args.get('--lambda-file')
        if file_arg:
            file = path.abspath(file_arg)
            return handle_deploy_lambda(file, config)
        else:
            return handle_deploy_lambda(config)
    if args.get('lambda-invoke'):
        name = args.get('--lambda-name')
        payload = args.get('--payload', None)
        return handle_invoke_lambda(name, payload)
    if args.get('lambda-delete'):
        name = args.get('--lambda-name')
        return handle_delete_lambda(name)
    if args.get('lambda-archive'):
        return handle_lambda_archive(config)

    error('Unrecognized command.')


def load_config(config_file):
    # python-dotenv enables interpolation of values in config file
    # from the environment or elsewhere in the config file using
    # POSIX variable expansion

    config_wrappers = []
    config_wrappers.append(ConfigOSEnv())

    local_conf = dotenv_values(find_dotenv())
    config_wrappers.append(ConfigDictEnv(local_conf))

    if config_file:
        config_file_path = path.abspath(config_file)
        project_conf = dotenv_values(dotenv_path=config_file_path)
        config_wrappers.append(ConfigDictEnv(project_conf))

    config_wrappers.append(ConfigDictEnv(settings.defaults()))

    config = ConfigManager(config_wrappers)

    return config


def main():
    args = docopt(__doc__, version=__version__)
    configure_logging(args.get('--verbose'))
    config_file = args.get('--config-file', None)
    if config_file:
        debug(f'Reading config from file {config_file}')

    config = load_config(config_file)
    if args.get('--verbose'):
        debug(f'All config values:')
        dump(config)

    app(args, config)


if __name__ == '__main__':
    if '--verbose' in argv:
        print(argv)
    main()
