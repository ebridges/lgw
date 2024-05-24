import os
from logging import info
import boto3
from botocore.exceptions import ClientError

import pytest
from moto import mock_aws
from assertpy import assert_that

from lgw.util import configure_logging
from lgw.api_gateway import (
    create_api_gateway,
    get_root_resource_id,
    create_resource,
    create_method,
)

configure_logging()

DEFAULT_REGION = 'us-east-1'


@pytest.fixture(scope='function')
def aws_credentials():
    '''
    Mocked AWS Credentials for moto.
    '''
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ["AWS_DEFAULT_REGION"] = 'us-east-1'


@pytest.fixture(scope='function')
def lambda_client(aws_credentials):
    with mock_aws():
        yield boto3.client('lambda', region_name=DEFAULT_REGION)


@pytest.fixture(scope='function')
def api_client(aws_credentials):
    with mock_aws():
        yield boto3.client('apigateway', region_name=DEFAULT_REGION)


def create_mock_api_gateway(api_client):
    api_name = 'mock_api_name'
    api_description = 'mock_api_description'
    binary_types = ['image/jpeg']
    api_id = create_api_gateway(api_client, api_name, api_description=api_description, binary_types=binary_types)
    info('api_id [%s]' % api_id)
    return api_id


def create_mock_root_resource(api_client, api_id):
    root_id = get_root_resource_id(api_client, api_id)
    info('root_id: [%s]' % root_id)
    return root_id


def test_create_api_gateway(api_client):
    api_id = create_mock_api_gateway(api_client)
    assert_that(api_id).is_not_none()
    assert_that(api_id).is_not_empty()


def test_get_root_resource_id(api_client):
    api_id = create_mock_api_gateway(api_client)
    root_resource_id = create_mock_root_resource(api_client, api_id)
    assert_that(root_resource_id).is_not_none()
    assert_that(root_resource_id).is_not_empty()


def test_create_resource(api_client):
    api_id = create_mock_api_gateway(api_client)
    root_id = get_root_resource_id(api_client, api_id)

    resource_path = 'mock-resource-path'

    actual_resource_id = create_resource(api_client, api_id, root_id, resource_path)

    info('actual_resource_id: [%s]' % actual_resource_id)
    assert_that(actual_resource_id).is_not_none()
    assert_that(actual_resource_id).is_not_empty()


def test_create_method(api_client):
    api_id = create_mock_api_gateway(api_client)
    root_id = get_root_resource_id(api_client, api_id)

    create_method(api_client, api_id, root_id, 'GET')

    method = api_client.get_method(restApiId=api_id, resourceId=root_id, httpMethod='GET')

    assert_that(method).is_not_none()
    assert_that(method).contains('httpMethod')
    assert_that(method).has_httpMethod('GET')

    method_response = api_client.get_method_response(
        restApiId=api_id, resourceId=root_id, httpMethod='GET', statusCode='200'
    )

    assert_that(method_response).contains('statusCode')
    assert_that(method_response).has_statusCode('200')


# def test_link_lambda_with_gateway(api_client, api_id, root_resource_id, lambda_uri):
# 	pass


DISABLED = [
    '''
def test_deploy_to_stage(api_client, sts_client):
    account_id = sts_client.get_caller_identity().get('Account')
    api_id = create_mock_api_gateway(api_client)
    root_id = get_root_resource_id(api_client, api_id)
    create_method(api_client, api_id, root_id, 'GET')

    deploy_stage = 'mock_deploy_stage'
    result = deploy_to_stage(api_client, api_id, deploy_stage)
    assert_that(result).is_not_none()


def test_get_lambda_info(lambda_client):
    lambda_name = 'mock_lambda_name'
    (lambda_arn, lambda_uri, region, account_id) = get_lambda_info(lambda_client, lambda_name)

def test_grant_lambda_permission_to_resource(lambda_client):
  api_id = 'a1b2c3d4e5'
  region = DEFAULT_REGION
  account_id = '012345678912'
  lambda_name = 'mock_lambda_name'
  resource_path = 'mock_resource_path'
  grant_lambda_permission_to_resource(
    lambda_client,
    api_id,
    region,
    account_id,
    lambda_name,
    resource_path
  )
  policy = lambda_client.get_policy()
  info(policy)
'''
]
