from botocore.vendored import requests


def handler(event, context):
    response = requests.get('https://reqres.in/api/users/2')
    print(response.json())
