from logging import info, warn
import boto3


def update_dns_a_record(domain_name, alias_target_dns_name):
    '''
    Updates the A record for the given domain name with a new alias target.
    Assumes that the hosted zone that hosts the domain name is public, and that
    that the domain name is the apex for this hosted zone.
    '''
    r53_client = boto3.client('route53')

    zone_id = get_hosted_zone_id_for_domain(r53_client)
    record_set = {
        'Name': domain_name,
        'Type': 'A',
        'AliasTarget': {
            'HostedZoneId': 'Z2FDTNDATAQYW2', # This is a magic value that means 'CloudFront'
            'DNSName': alias_target_dns_name,
            'EvaluateTargetHealth': False,
        }
    }

    response = r53_client.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': record_set
                }
            ]
        }
    )

    if response:
        change_info = response.get('ChangeInfo')
        info('Resource record change submitted: status of change is: [%s]' % change_info['Status'])
        return change_info['Id']
    else:
        warn('Empty response returned from record change submission.')
        return None



def get_hosted_zone_id_for_domain(route53_client, domain_name):
    '''
    List public host zones, while transparently handling pagination.
    cf.: https://github.com/Miserlou/Zappa/blob/master/zappa/core.py#L3087
    '''
    public_zones = list_public_hosted_zones(route53_client)

    zones = {zone['Name'][:-1]: zone['Id'] for zone in public_zones if zone['Name'][:-1] in domain_name}
    if zones:
        keys = max(zones.keys(), key=lambda a: len(a))  # get longest key -- best match.
        return zones[keys]
    else:
        return None


def list_public_hosted_zones(route53_client):
    public_zones = {'HostedZones': []}

    new_zones = route53_client.list_hosted_zones(MaxItems='100')
    while new_zones['IsTruncated']:
        if not new_zones['Config']['PrivateZone']:
            public_zones['HostedZones'] += new_zones['HostedZones']
        new_zones = route53_client.list_hosted_zones(Marker=new_zones['NextMarker'], MaxItems='100')

    if not new_zones['Config']['PrivateZone']:
        public_zones['HostedZones'] += new_zones['HostedZones']

    return public_zones
