from logging import info, warn
import boto3
from tld import get_fld


def update_dns_a_record(domain_name, alias_target_dns_name):
    '''
    Updates the A record for the given domain name with a new alias target.
    Assumes that the hosted zone that hosts the domain name is public, and that
    that the domain name is the apex for this hosted zone.
    '''
    r53_client = boto3.client('route53')

    apex_domain = get_fld(domain_name, fix_protocol=True)

    zone_id = get_hosted_zone_id_for_domain(r53_client, apex_domain)
    info(f'located {zone_id} as zone id for {apex_domain}')

    record_set = {
        'Name': domain_name,
        'Type': 'A',
        'AliasTarget': {
            'HostedZoneId': 'Z2FDTNDATAQYW2',  # This is a magic value that means 'CloudFront'
            'DNSName': alias_target_dns_name,
            'EvaluateTargetHealth': False,
        },
    }

    response = r53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={'Changes': [{'Action': 'UPSERT', 'ResourceRecordSet': record_set}]},
    )

    if response:
        change_info = response.get('ChangeInfo')
        info('Resource record change submitted: status of change is: [%s]' % change_info['Status'])
        if change_info['Status'] == 'PENDING':
            waiter = r53_client.get_waiter('resource_record_sets_changed')
            waiter.wait(Id=change_info['Id'], WaiterConfig={'Delay': 30, 'MaxAttempts': 60})
        return change_info['Id']
    else:
        warn('Empty response returned from record change submission.')
        return None


def get_hosted_zone_id_for_domain(route53_client, domain_name):
    '''
    List public zones -- more robust implementation linked below that considers
    - larger number of hosted zones
    - more diverse pool of domain names
    - non-public hosted zones
    cf.: https://github.com/Miserlou/Zappa/blob/master/zappa/core.py#L3087
    '''
    public_zones = []

    zones = route53_client.list_hosted_zones(MaxItems='25')

    for hosted_zone in zones['HostedZones']:
        if not hosted_zone['Config']['PrivateZone']:
            public_zones += zones['HostedZones']

    for zone in public_zones:
        if zone['Name'][:-1] == domain_name:
            return zone['Id']

    return None
