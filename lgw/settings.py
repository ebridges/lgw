def defaults():
    return {
        'aws_region': 'us-east-1',
        'aws_api_name': '',
        'aws_api_description': '',
        'aws_api_resource_path': '{proxy+}',
        'aws_api_deploy_stage': '',
        'aws_api_lambda_integration_role': '',
        'aws_api_domain_name': '',
        'aws_api_base_path': '(none)',
        'aws_api_domain_wait_until_available': 'true',
        'aws_api_response_models': 'application/json=Empty',
        'aws_api_binary_types': '',
        'aws_acm_certificate_arn': '',
        'aws_lambda_name': '',
        'aws_lambda_description': '',
        'aws_lambda_handler': '',
        'aws_lambda_runtime': 'python3.7',
        'aws_lambda_connection_timeout': 30,
        'aws_lambda_memory_size': 3000,
        'aws_lambda_archive_bucket': '',
        'aws_lambda_archive_key': '',
        'aws_lambda_execution_role_arn': '',
        'aws_lambda_vpc_subnets': '',
        'aws_lambda_vpc_security_groups': '',
        'aws_lambda_environment': '',
        'aws_lambda_tags': '',
        'aws_lambda_archive_context_dir': '.',
        'aws_lambda_archive_bundle_dir': './build',
        'aws_lambda_archive_bundle_name': 'lambda-bundle.zip',
        'aws_lambda_archive_addl_files': '',
        'aws_lambda_archive_addl_packages': '',
    }


def dump(config):
    for key in sorted(defaults().keys()):
        print('    %s => %s' % (key, config(key)))
