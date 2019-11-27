import json
from logging import info
import boto3
from botocore.exceptions import ClientError
from lgw.lambda_util import get_lambda_info, grant_permission_to_api_resource

def create_rest_api(api_name, lambda_name, resource_path, deploy_stage):
    '''
    Creates & deploys a REST API that proxies to a Lambda function, returning the URL
    pointing to this API.

    :param api_name: Name of the REST API
    :param lambda_name: Name of an existing Lambda function
    :param resource_path: The resource path that points to the lambda.
    :param deploy_stage: The name of the deployment stage.

    :return: URL of API. If error, returns None.
    '''

    api_client = boto3.client('apigateway')

    api_id = create_api_gateway(api_client, api_name)

    (lambda_arn, lambda_uri, region, account_id) = get_lambda_info(lambda_name)

    root_resource_id = get_root_resource_id(api_client, api_id)
    create_method(api_client, api_id, root_resource_id, 'ANY')
    create_lambda_integration(api_client, api_id, root_resource_id, lambda_uri)

    child_resource_id = create_resource(api_client, api_id, root_resource_id, resource_path)
    create_method(api_client, api_id, child_resource_id, 'ANY')
    create_lambda_integration(api_client, api_id, child_resource_id, lambda_uri)

    deploy_to_stage(api_client, api_id, deploy_stage)

    grant_permission_to_api_resource(api_id, region, account_id, lambda_arn, resource_path)

    return f'https://{api_id}.execute-api.{region}.amazonaws.com/{deploy_stage}'


def delete_rest_api(api_name):
    api_client = boto3.client('apigateway')
    delete_api_gateway(api_client, api_name)


def deploy_to_stage(api_client, api_id, deploy_stage):
    return api_client.create_deployment(restApiId=api_id, stageName=deploy_stage)


def create_lambda_integration(api_client, api_id, root_resource_id, lambda_uri, role_arn=None):
    '''
    Set the Lambda function as the destination for the ANY method
    Extract the Lambda region and AWS account ID from the Lambda ARN
    ARN format="arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"
    '''
    api_client.put_integration(
        restApiId=api_id,
        resourceId=root_resource_id,
        httpMethod='ANY',
        type='AWS_PROXY',
        integrationHttpMethod='POST',
        uri=lambda_uri,
    )


def create_method(api_client, api_id, resource_id, http_method):
    try:
        response = api_client.get_method(restApiId=api_id, resourceId=resource_id, httpMethod=http_method)
        if response and response.get('httpMethod'):
            info(f'{http_method} method already exists for resource {resource_id}')
            return
    except api_client.exceptions.NotFoundException:
        info(f'{http_method} method does not exist for resource {resource_id}, adding it.')

    api_client.put_method(
        resourceId=resource_id,
        restApiId=api_id,
        httpMethod=http_method,
        authorizationType='NONE',
    )

    # Set the content-type of the method response to JSON
    content_type = {'application/json': 'Empty'}
    api_client.put_method_response(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        statusCode='200',
        responseModels=content_type,
    )


def create_resource(api_client, api_id, parent_id, resource_path):
    resources = api_client.get_resources(restApiId=api_id)
    if 'items' in resources:
        for resource in resources['items']:
            if resource.get('parentId') == parent_id and resource.get('pathPart') == resource_path:
                info('Found existing resource for %s' % resource['parentId'])
                return resource['id']

    info(f'No existing resource found for {parent_id}/{resource_path}, creating a new one')
    result = api_client.create_resource(restApiId=api_id, parentId=parent_id, pathPart=resource_path)
    return result['id']


def get_root_resource_id(api_client, api_id):
    result = api_client.get_resources(restApiId=api_id)

    root_id = None
    for item in result['items']:
        if item['path'] == '/':
            root_id = item['id']

    if root_id is None:
        raise ClientError(
            'Could not retrieve the ID of the API root resource using api_id [%s]' % api_id
        )

    return root_id


def delete_api_gateway(api_client, api_name):
    api_id = lookup_api_gateway(api_client, api_name)
    if api_id:
        info(f'Deleting API with ID: {api_id}')
        api_client.delete_rest_api(restApiId=api_id)


def create_api_gateway(api_client, api_name):
    api_id = lookup_api_gateway(api_client, api_name)
    if api_id:
        return api_id
    info(f'No existing API account found for {api_name}, creating it.')
    result = api_client.create_rest_api(name=api_name)
    return result['id']


def lookup_api_gateway(api_client, api_name):
    apis = api_client.get_rest_apis()
    if 'items' in apis:
        for api in apis['items']:
            if api['name'] == api_name:
                info('Found existing API account for %s' % api['name'])
                return api['id']
    info(f'No API gateway found with name {api_name}')
    return None
