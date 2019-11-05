import boto3
from botocore.exceptions import ClientError


def create_rest_api(api_name, lambda_name, resource_path, deploy_stage):
    '''
    Creates & deploys a REST API that proxies to a Lambda function, returning the URL
    pointing to this API.

    :param api_name: Name of the REST API
    :param lambda_name: Name of an existing Lambda function
    :param resource_path: The resource path that pointsto the lambda.
    :param deploy_stage: The name of the deployment stage.

    :return: URL of API. If error, returns None.
    '''

    api_client = boto3.client('apigateway')
    lambda_client = boto3.client('lambda')

    api_id = create_api_gateway_account(api_client, api_name)

    root_resource_id = get_root_resource_id(api_client, api_id)

    create_any_method(api_client, api_id, root_resource_id)

    child_resource_id = create_child_resource(api_client, api_id, root_resource_id, resource_path)

    create_any_method(api_client, api_id, child_resource_id)

    (lambda_arn, lambda_uri, region, account_id) = get_lambda_info(lambda_client, lambda_name)

    link_lambda_with_gateway(api_client, api_id, root_resource_id, lambda_uri)

    deploy_to_stage(api_client, api_id, deploy_stage)

    grant_lambda_permission_to_resource(
        lambda_client, api_id, region, account_id, lambda_name, resource_path
    )

    return f'https://{api_id}.execute-api.{region}.amazonaws.com/{deploy_stage}/{resource_path}'


def grant_lambda_permission_to_resource(
    lambda_client, api_id, region, account_id, lambda_name, resource_path
):
    '''
        Grant invoke permissions on the Lambda function so it can be called by API Gateway.
        Note: To retrieve the Lambda function's permissions, call `lambda_client.get_policy()`
    '''
    source_arn = f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/{resource_path}'
    lambda_client.add_permission(
        FunctionName=lambda_name,
        StatementId=f'{lambda_name}-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=source_arn,
    )


def deploy_to_stage(api_client, api_id, deploy_stage):
    return api_client.create_deployment(restApiId=api_id, stageName=deploy_stage)


def link_lambda_with_gateway(api_client, api_id, root_resource_id, lambda_uri):
    '''
        Set the Lambda function as the destination for the ANY method
        Extract the Lambda region and AWS account ID from the Lambda ARN
        ARN format="arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"
    '''
    api_client.put_integration(
        restApiId=api_id,
        resourceId=root_resource_id,
        httpMethod='ANY',
        type='AWS',
        integrationHttpMethod='POST',
        uri=lambda_uri,
    )

    # Set the content-type of the Lambda function to JSON
    content_type = {'application/json': ''}
    api_client.put_integration_response(
        restApiId=api_id,
        resourceId=root_resource_id,
        httpMethod='ANY',
        statusCode='200',
        responseTemplates=content_type,
    )


def get_lambda_info(lambda_client, lambda_name):
    response = lambda_client.get_function(FunctionName=lambda_name)
    lambda_arn = response['Configuration']['FunctionArn']

    sections = lambda_arn.split(':')
    region = sections[3]
    account_id = sections[4]

    # Construct the Lambda function's URI
    lambda_uri = (
        f'arn:aws:apigateway:{region}:lambda:path' f'/2015-03-31/functions/{lambda_arn}/invocations'
    )

    return lambda_arn, lambda_uri, region, account_id


def create_any_method(api_client, api_id, root_resource_id):
    api_client.put_method(
        restApiId=api_id, resourceId=root_resource_id, httpMethod='ANY', authorizationType='NONE'
    )

    # Set the content-type of the ANY method response to JSON
    content_type = {'application/json': 'Empty'}
    api_client.put_method_response(
        restApiId=api_id,
        resourceId=root_resource_id,
        httpMethod='ANY',
        statusCode='200',
        responseModels=content_type,
    )


def create_child_resource(api_client, api_id, root_id, resource_path):
    # Define a child resource called /example under the root resource
    result = api_client.create_resource(restApiId=api_id, parentId=root_id, pathPart=resource_path)
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

def create_api_gateway_account(api_client, api_name):
    # Create initial REST API
    result = api_client.create_rest_api(name=api_name)
    return result['id']
