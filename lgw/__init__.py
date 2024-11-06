from lgw.version import __version__

import argparse


def parse_args():
    # Parent parser for global options
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--verbose", action="store_true", help="Enable DEBUG-level logging.")
    parent_parser.add_argument("--config-file", help="Override defaults with these settings.")

    # Main parser
    parser = argparse.ArgumentParser(description="Lambda Gateway")
    parser.add_argument("--version", action="version", version=__version__, help="Show version.")

    # Subparsers for each command
    subparsers = parser.add_subparsers(dest="command", required=True)

    # gw-deploy
    subparsers.add_parser("gw-deploy", parents=[parent_parser], help="Deploy the API Gateway")

    # gw-undeploy
    subparsers.add_parser("gw-undeploy", parents=[parent_parser], help="Undeploy the API Gateway")

    # domain-add
    subparsers.add_parser("domain-add", parents=[parent_parser], help="Add a domain mapping")

    # domain-remove
    subparsers.add_parser("domain-remove", parents=[parent_parser], help="Remove a domain mapping")

    # lambda-deploy
    lambda_deploy_parser = subparsers.add_parser(
        "lambda-deploy", parents=[parent_parser], help="Deploy a Lambda function"
    )
    lambda_deploy_parser.add_argument(
        "--lambda-file", help="Path to zip file with executable lambda code."
    )

    # lambda-invoke
    lambda_invoke_parser = subparsers.add_parser(
        "lambda-invoke", parents=[parent_parser], help="Invoke a Lambda function"
    )
    lambda_invoke_parser.add_argument(
        "--lambda-name", required=True, help="Name of the lambda to invoke."
    )
    lambda_invoke_parser.add_argument(
        "--payload", help="Path to a JSON file with data to send with the lambda invocation."
    )

    # lambda-delete
    lambda_delete_parser = subparsers.add_parser(
        "lambda-delete", parents=[parent_parser], help="Delete a Lambda function"
    )
    lambda_delete_parser.add_argument(
        "--lambda-name", required=True, help="Name of the lambda to delete."
    )

    # lambda-archive
    subparsers.add_parser("lambda-archive", parents=[parent_parser], help="Create a Lambda archive")

    args = parser.parse_args()

    return vars(args)
