from logging import debug, info, warn
import boto3
from lgw.api_gateway import lookup_api_gateway
from lgw.route53 import update_dns_a_record


def add_domain_mapping(
    api_name, domain_name, base_path, https_certificate_arn, deploy_stage, wait_for_completion
):
    api_client = boto3.client('apigateway')

    api_id = lookup_api_gateway(api_client, api_name)

    created = create_custom_domain_name(api_client, domain_name, https_certificate_arn)
    if wait_for_completion:
        while True:
            created = create_custom_domain_name(api_client, domain_name, https_certificate_arn)
            if created:
                break

    if created:
        debug(f'Adding base path mapping for {deploy_stage}')
        configure_base_path_mapping(api_client, api_id, domain_name, deploy_stage, base_path)

        cf_distribution = created['distributionDomainName']
        debug(f'Updating A record for {domain_name} with CF distribution {cf_distribution}')
        update_dns_a_record(domain_name, cf_distribution)


def remove_domain_mapping(api_name, domain_name, base_path):
    api_client = boto3.client('apigateway')

    api_id = lookup_api_gateway(api_client, api_name)

    response = api_client.get_base_path_mappings(domainName=domain_name)
    if response:
        for item in response['items']:
            print(item)

    api_client.delete_base_path_mapping(domainName=domain_name, basePath=base_path)

    api_client.delete_domain_name(domainName=domain_name)


def configure_base_path_mapping(api_client, api_id, domain_name, deploy_stage, base_path):
    response = None
    try:
        response = api_client.get_base_path_mapping(domainName=domain_name, basePath=base_path)
    except api_client.exceptions.NotFoundException:
        info(f'Base path mapping for {domain_name}:{base_path} does not exist.')

    if response:
        info(f'Base path mapping {domain_name}:{base_path} already exists.')
        api_client.delete_base_path_mapping(domainName=domain_name, basePath=base_path)

    response = api_client.create_base_path_mapping(
        domainName=domain_name, basePath=base_path, restApiId=api_id, stage=deploy_stage
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 201:
        info(f'Base path mapping created for {domain_name}:{base_path}')
    else:
        warn(f'Unable to create base path mapping for {domain_name}:{base_path}')


def create_custom_domain_name(api_client, domain_name, certificate_arn):
    response = None
    try:
        response = api_client.get_domain_name(domainName=domain_name)
    except api_client.exceptions.NotFoundException:
        info(f'Custom domain name {domain_name} does not exist.')

    if response:
        if response.get('domainNameStatus') == 'AVAILABLE':
            info(f'Domain name {domain_name} exists and is available.')
            return response

        if response.get('domainNameStatus') in ('UPDATING', 'PENDING'):
            info(
                'Domain name %s is in process: [%s] %s'
                % (
                    domain_name,
                    response.get('domainNameStatus'),
                    response.get('domainNameStatusMessage'),
                )
            )
            return

    response = api_client.create_domain_name(
        domainName=domain_name, certificateName=domain_name, certificateArn=certificate_arn
    )
    if response:
        cloudfront_distribution = response.get('distributionDomainName')
        info(f'domain name {domain_name} created, pointing at: {cloudfront_distribution}')
        return response
