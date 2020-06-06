from os import stat
import boto3
import json
from logging import debug, info
from lgw.s3 import upload_file

MAX_LAMBDA_SIZE = 50000000


def deploy_function(
    archive,
    lambda_name,
    handler_name,
    execution_role,
    connection_timeout,
    memory_size,
    runtime,
    s3_bucket,
    s3_key,
    description,
    vpc_subnets,
    vpc_security_groups,
    environment,
    tags,
):

    env = {}
    if environment:
        env = dict(item.split('=') for item in environment.split(';'))

    t = {}
    if tags:
        t = dict(item.split('=') for item in tags.split(';'))

    vpc_config = {}
    if vpc_subnets and vpc_security_groups:
        subnets = vpc_subnets.split(',')
        sec_grps = vpc_security_groups.split(',')
        vpc_config = {'SubnetIds': subnets, 'SecurityGroupIds': sec_grps}

    if archive:
        sz = stat(archive).st_size
    else:
        sz = MAX_LAMBDA_SIZE + 1

    if sz < MAX_LAMBDA_SIZE:
        assert archive is not None
        return deploy_function_from_zip(
            archive,
            lambda_name,
            handler_name,
            execution_role,
            connection_timeout,
            memory_size,
            runtime,
            description,
            vpc_config,
            env,
            t,
        )
    else:
        if archive:
            upload_file(s3_bucket, s3_key, archive)

        return deploy_function_from_s3(
            lambda_name,
            s3_bucket,
            s3_key,
            handler_name,
            execution_role,
            connection_timeout,
            memory_size,
            runtime,
            description,
            vpc_config,
            env,
            t,
        )


def deploy_function_from_s3(
    lambda_name,
    s3_bucket,
    s3_key,
    handler_name,
    execution_role,
    connection_timeout,
    memory_size,
    runtime,
    description=None,
    vpc_config=None,
    environment=None,
    tags=None,
):
    code = {'S3Bucket': s3_bucket, 'S3Key': s3_key}
    return create_or_replace_function(
        lambda_name,
        code,
        handler_name,
        execution_role,
        connection_timeout,
        memory_size,
        runtime,
        description,
        vpc_config,
        environment,
        tags,
    )


def deploy_function_from_zip(
    archive,
    lambda_name,
    handler_name,
    execution_role,
    connection_timeout,
    memory_size,
    runtime,
    description=None,
    vpc_config=None,
    environment=None,
    tags=None,
):
    with open(archive, 'rb') as binaryfile:
        zipfile = bytearray(binaryfile.read())
        code = {'ZipFile': zipfile}
        return create_or_replace_function(
            lambda_name,
            code,
            handler_name,
            execution_role,
            connection_timeout,
            memory_size,
            runtime,
            description,
            vpc_config,
            environment,
            tags,
        )


def create_or_replace_function(
    lambda_name,
    code,
    handler_name,
    execution_role,
    connection_timeout,
    memory_size,
    runtime,
    description=None,
    vpc_config=None,
    environment=None,
    tags=None,
):
    '''
    Deploys a lambda function to AWS Lambda.  If a function already exists under the given
    `lambda_name` then this will delete it.

    :param lambda_name: Name for the Lambda function
    :param code: Config for location of executable code for the function.
    :param handler_name: Name of the entry point of the function.
    :param execution_role: Name of a role with execute permissions.
    :param vpc_config: Optional VPC config where the function should execute.
                      SubnetIds: [string], SecurityGroupIds: [string].
    :param runtime: Language runtime of the function. Default: python3.7
    :param environment: Environment variables to be available at runtime to the function.
    :param tags: Tags to identify the function.
    :return: ARN of deployed function.
    '''

    delete_function(lambda_name)

    lambda_client = boto3.client('lambda')

    env = {}
    if environment:
        env = {'Variables': environment}

    tracing_config = {'Mode': 'PassThrough'}

    info('Creating a lambda function with name: [%s]' % lambda_name)
    response = lambda_client.create_function(
        FunctionName=lambda_name,
        Runtime=runtime,
        Role=execution_role,
        Handler=handler_name,
        Code=code,
        Description=description,
        Timeout=int(connection_timeout),
        MemorySize=int(memory_size),
        Publish=True,
        VpcConfig=vpc_config,
        Environment=env,
        TracingConfig=tracing_config,
        Tags=tags,
    )

    return response['FunctionArn']


def delete_function(lambda_name):
    '''
    Deletes a lambda function.

    :param lambda_name: Name or ARN of the Lambda function to be deleted.
    :return: None
    '''
    lambda_client = boto3.client('lambda')
    response = lambda_client.list_functions()
    for f in response['Functions']:
        if f['FunctionName'] == lambda_name:
            debug('Found existing function [%s].' % f['FunctionName'])
            lambda_client.delete_function(FunctionName=lambda_name)
            info('Existing function [%s] deleted.' % f['FunctionName'])
            return
    info('No lambda named [%s] found to delete.' % lambda_name)


def invoke_function(lambda_name, payload):
    '''
    Invokes a lambda function.

    :param lambda_name: Name or ARN of the Lambda function to invoke.
    :param payload: File of JSON to send along with invocation.
    :return: None
    '''
    log_type = 'Tail'
    invocation_type = 'RequestResponse'  # or 'Event', or 'DryRun'

    with open(payload, 'r') as file:
        input_payload = bytearray(file)

        lambda_client = boto3.client('lambda')

        res = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType=invocation_type,
            LogType=log_type,
            Payload=input_payload,
        )

    return res


def invoke_function(lambda_name):
    '''
    Invokes a lambda function.

    :param lambda_name: Name or ARN of the Lambda function to invoke.
    :return: None
    '''
    log_type = 'Tail'
    invocation_type = 'RequestResponse'  # or 'Event', or 'DryRun'

    lambda_client = boto3.client('lambda')
    res = lambda_client.invoke(
        FunctionName=lambda_name, InvocationType=invocation_type, LogType=log_type
    )

    return res


def get_lambda_info(lambda_name):
    lambda_client = boto3.client('lambda')
    response = lambda_client.get_function(FunctionName=lambda_name)
    lambda_arn = response['Configuration']['FunctionArn']

    sections = lambda_arn.split(':')
    region = sections[3]
    account_id = sections[4]

    # Construct the Lambda function's URI
    lambda_uri = (
        f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
    )

    return lambda_arn, lambda_uri, region, account_id


def grant_permission_to_api_resource(api_id, region, account_id, lambda_arn, resource_path):
    '''
    Grant invoke permissions on the Lambda function so it can be called by API Gateway.
    If it exists already then remove so it can be recreated.
    '''
    lambda_client = boto3.client('lambda')
    lambda_name = lambda_arn.split(':')[6]
    statement_id = f'{lambda_name}-invoke'
    action = 'lambda:InvokeFunction'

    info(f'Loading policies related to lambda: {lambda_arn}')
    policy = None
    try:
        policy = lambda_client.get_policy(FunctionName=lambda_arn)
    except lambda_client.exceptions.ResourceNotFoundException:
        info(f'No policy associated with {lambda_arn}')

    if policy and 'Policy' in policy:
        stmts = json.loads(policy['Policy'])
        for stmt in stmts['Statement']:
            if stmt['Action'] == action and stmt['Resource'] == lambda_arn:
                info(f'removing permission [{statement_id}] for lambda: [{lambda_arn}]')
                try:
                    lambda_client.remove_permission(
                        FunctionName=lambda_arn, StatementId=statement_id
                    )
                except lambda_client.exceptions.ResourceNotFoundException:
                    info(
                        f'No permission found for StatementId: {statement_id}, FunctionName: {lambda_arn}'
                    )

    info(f'adding permission [{statement_id}] for lambda: [{lambda_arn}]')
    source_arn = f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/*/'
    lambda_client.add_permission(
        FunctionName=lambda_arn,
        StatementId=statement_id,
        Action=action,
        Principal='apigateway.amazonaws.com',
        SourceArn=source_arn,
    )
