from logging import debug, info
import boto3
from boto3.s3.transfer import S3Transfer


def upload_file(archive_bucket, artifact_name, file):
    debug(
        'Uploading artifact [%s] to bucket [%s] using archive [%s]'
        % (artifact_name, archive_bucket, file)
    )
    s3 = boto3.client('s3')
    client = S3Transfer(client=s3)
    client.upload_file(file, archive_bucket, artifact_name)
    info('File [%s] uploaded to bucket [%s]' % (artifact_name, archive_bucket))
