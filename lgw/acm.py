from logging import debug, info
import boto3

DEFAULT_DELAY=60 #secs
DEFAULT_ATTEMPT_COUNT=40

def wait_for_certificate_validation(certificate_arn, wait_for):
    acm_client = boto3.client('acm')

    waiter_config={
        'Delay': DEFAULT_DELAY,
        'MaxAttempts': DEFAULT_ATTEMPT_COUNT,
    }

    if wait_for:
        waiter_config['MaxAttempts'] = wait_for

    wait_time = waiter_config['Delay'] * waiter_config['MaxAttempts']
    info(f'Waiting for certificate to complete validation for at most {wait_time} minutes.')

    waiter = acm_client.get_waiter('certificate_validated')
    waiter.wait(
        CertificateArn=certificate_arn,
        WaiterConfig=waiter_config,
    )
