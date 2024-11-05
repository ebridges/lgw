import pytest
from unittest.mock import patch, MagicMock
from lgw import parse_args
from lgw.main import app

def test_gw_deploy():
    with patch("sys.argv", ["lgw", "gw-deploy", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "gw-deploy"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_gw_undeploy():
    with patch("sys.argv", ["lgw", "gw-undeploy", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "gw-undeploy"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_domain_add():
    with patch("sys.argv", ["lgw", "domain-add", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "domain-add"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_lambda_deploy_with_file():
    with patch("sys.argv", ["lgw", "lambda-deploy",
                            "--lambda-file=my_lambda.zip", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "lambda-deploy"
        assert args.lambda_file == "my_lambda.zip"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_lambda_invoke_with_payload():
    with patch("sys.argv", ["lgw", "lambda-invoke", "--lambda-name=myLambda",
                            "--payload=data.json", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "lambda-invoke"
        assert args.lambda_name == "myLambda"
        assert args.payload == "data.json"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_lambda_delete():
    with patch("sys.argv", ["lgw", "lambda-delete", "--lambda-name=myLambda",
                            "--verbose", "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "lambda-delete"
        assert args.lambda_name == "myLambda"
        assert args.verbose is True
        assert args.config_file == "config.env"


def test_lambda_archive():
    with patch("sys.argv", ["lgw", "lambda-archive", "--verbose",
                            "--config-file=config.env"]):
        args = parse_args()
        assert args.command == "lambda-archive"
        assert args.verbose is True
        assert args.config_file == "config.env"


@pytest.mark.parametrize(
    "args, expected_mock, expected_args",
    [
        # gw-deploy should call handle_deploy_api_gateway with config
        ({"gw-deploy": True}, "lgw.main.handle_deploy_api_gateway",
         (MagicMock(),)),

        # gw-undeploy should call handle_undeploy_api_gateway with config
        ({"gw-undeploy": True}, "lgw.main.handle_undeploy_api_gateway",
         (MagicMock(),)),

        # domain-add should call handle_add_domain with config
        ({"domain-add": True}, "lgw.main.handle_add_domain", (MagicMock(),)),

        # domain-remove should call handle_remove_domain with config
        ({"domain-remove": True}, "lgw.main.handle_remove_domain",
         (MagicMock(),)),

        # lambda-deploy with file should call handle_deploy_lambda with file
        # and config
        ({"lambda-deploy": True, "--lambda-file": "/path/to/lambda.zip"},
         "lgw.main.handle_deploy_lambda", ("/path/to/lambda.zip", MagicMock())),

        # lambda-deploy without --lambda-file should call handle_deploy_lambda
        # with config only
        ({"lambda-deploy": True}, "lgw.main.handle_deploy_lambda",
         (MagicMock(),)),

        # lambda-invoke should call handle_invoke_lambda with name and payload
        ({"lambda-invoke": True, "--lambda-name": "myLambda",
          "--payload": "data.json"},
         "lgw.main.handle_invoke_lambda", ("myLambda", "data.json")),

        # lambda-delete should call handle_delete_lambda with name
        ({"lambda-delete": True, "--lambda-name": "myLambda"},
         "lgw.main.handle_delete_lambda", ("myLambda",)),

        # lambda-archive should call handle_lambda_archive with config
        ({"lambda-archive": True}, "lgw.main.handle_lambda_archive",
         (MagicMock(),)),
    ]
)
def test_app_routing(args, expected_mock, expected_args):
    with patch("lgw.main.handle_deploy_api_gateway") as \
            mock_deploy_api_gateway, \
         patch("lgw.main.handle_undeploy_api_gateway") as \
            mock_undeploy_api_gateway, \
         patch("lgw.main.handle_add_domain") as \
            mock_add_domain, \
         patch("lgw.main.handle_remove_domain") as \
            mock_remove_domain, \
         patch("lgw.main.handle_deploy_lambda") as \
            mock_deploy_lambda, \
         patch("lgw.main.handle_invoke_lambda") as \
            mock_invoke_lambda, \
         patch("lgw.main.handle_delete_lambda") as \
            mock_delete_lambda, \
         patch("lgw.main.handle_lambda_archive") as \
            mock_lambda_archive:

        # Map mock names to mock objects
        mock_map = {
            "lgw.main.handle_deploy_api_gateway": mock_deploy_api_gateway,
            "lgw.main.handle_undeploy_api_gateway": mock_undeploy_api_gateway,
            "lgw.main.handle_add_domain": mock_add_domain,
            "lgw.main.handle_remove_domain": mock_remove_domain,
            "lgw.main.handle_deploy_lambda": mock_deploy_lambda,
            "lgw.main.handle_invoke_lambda": mock_invoke_lambda,
            "lgw.main.handle_delete_lambda": mock_delete_lambda,
            "lgw.main.handle_lambda_archive": mock_lambda_archive,
        }

        # Prepare config and expected mock
        config = (expected_args[-1] if isinstance(expected_args[-1], MagicMock)
                  else MagicMock())
        expected_args = tuple(
            config if arg == MagicMock() else arg for arg in expected_args
        )

        # Reset all mocks
        for mock in mock_map.values():
            mock.reset_mock()

        # Run the app function
        app(args, config)

        # Verify the correct handler was called with expected arguments
        mock_map[expected_mock].assert_called_once_with(*expected_args)

        # Ensure all other mocks were not called
        for name, mock in mock_map.items():
            if name != expected_mock:
                mock.assert_not_called()
