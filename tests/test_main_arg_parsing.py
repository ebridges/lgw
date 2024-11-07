import pytest
from unittest.mock import patch, MagicMock
from lgw import parse_args
from lgw.main import app


def test_gw_deploy():
    with patch("sys.argv", ["lgw", "gw-deploy", "--verbose", "--config-file=config.env"]):
        args = parse_args()
        assert args['command'] == "gw-deploy"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_gw_undeploy():
    with patch("sys.argv", ["lgw", "gw-undeploy", "--verbose", "--config-file=config.env"]):
        args = parse_args()
        assert args['command'] == "gw-undeploy"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_domain_add():
    with patch("sys.argv", ["lgw", "domain-add", "--verbose", "--config-file=config.env"]):
        args = parse_args()
        assert args['command'] == "domain-add"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_lambda_deploy_with_file():
    with patch(
        "sys.argv",
        [
            "lgw",
            "lambda-deploy",
            "--lambda-file=my_lambda.zip",
            "--verbose",
            "--config-file=config.env",
        ],
    ):
        args = parse_args()
        assert args['command'] == "lambda-deploy"
        assert args['lambda_file'] == "my_lambda.zip"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_lambda_invoke_with_payload():
    with patch(
        "sys.argv",
        [
            "lgw",
            "lambda-invoke",
            "--lambda-name=myLambda",
            "--payload=data.json",
            "--verbose",
            "--config-file=config.env",
        ],
    ):
        args = parse_args()
        assert args['command'] == "lambda-invoke"
        assert args['lambda_name'] == "myLambda"
        assert args['payload'] == "data.json"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_lambda_delete():
    with patch(
        "sys.argv",
        ["lgw", "lambda-delete", "--lambda-name=myLambda", "--verbose", "--config-file=config.env"],
    ):
        args = parse_args()
        assert args['command'] == "lambda-delete"
        assert args['lambda_name'] == "myLambda"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


def test_lambda_archive():
    with patch("sys.argv", ["lgw", "lambda-archive", "--verbose", "--config-file=config.env"]):
        args = parse_args()
        assert args['command'] == "lambda-archive"
        assert args['verbose'] is True
        assert args['config_file'] == "config.env"


@pytest.mark.parametrize(
    "test_args, handler_function, config_args",
    [
        ({"command": "gw-deploy"}, "lgw.main.handle_deploy_api_gateway", [MagicMock()]),
        ({"command": "gw-undeploy"}, "lgw.main.handle_undeploy_api_gateway", [MagicMock()]),
        ({"command": "domain-add"}, "lgw.main.handle_add_domain", [MagicMock()]),
        ({"command": "domain-remove"}, "lgw.main.handle_remove_domain", [MagicMock()]),
        ({"command": "lambda-archive"}, "lgw.main.handle_lambda_archive", [MagicMock()]),
        ({"command": "lambda-deploy"}, "lgw.main.handle_deploy_lambda", [MagicMock()]),
    ],
)
def test_command_routing(test_args, handler_function, config_args):
    config = config_args[0]

    if len(config_args) > 1:
        expected_args = tuple(config_args)
    else:
        expected_args = (config,)

    with patch(handler_function) as patched_handler:
        # Run the app function
        app(test_args, config)

        # Check the correct handler was called
        patched_handler.assert_called_once_with(*expected_args)


@pytest.mark.parametrize(
    "test_args, handler_function, config_args",
    [
        (
            {"command": "lambda-deploy", "lambda_file": "/path/to/lambda.zip"},
            "lgw.main.handle_deploy_lambda",
            [MagicMock(), "/path/to/lambda.zip"],
        ),
    ],
)
def test_command_routing_with_config_plus_params(test_args, handler_function, config_args):
    config = config_args[0]

    with patch(handler_function) as patched_handler:
        # Run the app function
        app(test_args, config)

        # Check the correct handler was called
        patched_handler.assert_called_once_with(*config_args)


@pytest.mark.parametrize(
    "test_args, handler_function, expected_args",
    [
        (
            {"command": "lambda-invoke", "lambda_name": "myLambda", "payload": "data.json"},
            "lgw.main.handle_invoke_lambda",
            ("myLambda", "data.json"),
        ),
        (
            {"command": "lambda-delete", "lambda_name": "myLambda"},
            "lgw.main.handle_delete_lambda",
            ("myLambda",),
        ),
    ],
)
def test_command_routing_without_config(test_args, handler_function, expected_args):
    with patch(handler_function) as patched_handler:
        # Run the app function
        app(test_args, MagicMock())

        # Check the correct handler was called
        patched_handler.assert_called_once_with(*expected_args)
