[![PyPi License](https://img.shields.io/pypi/l/lgw?color=blue)](https://github.com/ebridges/lgw/blob/master/LICENSE)
[![PyPi](https://img.shields.io/pypi/v/lgw.svg?style=flat-square)](https://pypi.org/project/lgw/)

# Lambda Gateway

Configure an AWS Gateway in front of a Lambda function.

## Usage

```
Lambda Gateway.

Usage:
  lgw gw-deploy [--verbose] [--config-file=<cfg>]
  lgw gw-undeploy [--verbose] [--config-file=<cfg>]
  lgw domain-add [--verbose] [--config-file=<cfg>]
  lgw domain-remove [--verbose] [--config-file=<cfg>]
  lgw lambda-deploy [--verbose] [--config-file=<cfg>] [--lambda-file=<zip>]
  lgw lambda-invoke [--verbose] --lambda-name=<name> [--payload=<json>]
  lgw lambda-delete [--verbose] --lambda-name=<name>
  lgw lambda-archive [--verbose] [--config-file=<cfg>]

Options:
  -h --help             Show this screen.
  --version             Show version.
  --verbose             Enable DEBUG-level logging.
  --config-file=<cfg>   Override defaults with these settings.
  --lambda-file=<zip>   Path to zip file with executable lambda code.
  --lambda-name=<name>  Name of the lambda to invoke or delete.
  --payload=<json>      Path to a file of type json with data to send with the lambda invocation.
```

## Configuration Parameters

Configuration params are read in the following order, with the first read of it overriding subsequent configs:

1. Read from environment.
2. Read from `.env` file in current folder.
3. Read from flat file named via `--config-file` CLI param.
4. Read from `lgw.settings.defaults()`

Defaults are configured in `lgw.settings`.

<table>
<tr>
<th>Related Task(s)</th>
<th>Key</th>
<th>Description</th>
<th>Default</th>
</tr>
<tr>
<td><ul><li>All</li></ul></td>
<td><code>AWS_REGION</code></td>
<td>AWS region.</td>
<td><tt>us-east-1</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
  <li><tt>gw-undeploy</tt></li>
  <li><tt>domain-add</tt></li>
  <li><tt>domain-remove</tt></li>
</ul>
</td>
<td><code>AWS_API_NAME</code></td>
<td>Name for the created API gateway.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_DESCRIPTION</code></td>
<td>Description of the created API gateway.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_RESOURCE_PATH</code></td>
<td>Resource path for the API. By default it's a greedy path to proxy all requests.</td>
<td><tt>{proxy+}</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_DEPLOY_STAGE</code></td>
<td>Name for the stage that the API gets deployed to. E.g. "production"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_BINARY_TYPES</code></td>
<td>Listing of binary media types to configure the gateway as handling.  Example: <tt>image/jpeg,image/png</tt></td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_RESPONSE_MODELS</code></td>
<td>Response content-type: model mapping of the response body.  Typically used for mapping binary content-types.  For binary types specify: <tt>image/*=Empty</tt></td>
<td><tt>application/json=Empty</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
</ul>
</td>
<td><code>AWS_API_LAMBDA_INTEGRATION_ROLE</code></td>
<td>ARN of a role that grants permission to the API gateway to invoke a lambda.  Should have <tt>AmazonAPIGatewayPushToCloudWatchLogs</tt> and <tt>AWSLambdaRole</tt> managed roles as permissions, and <tt>apigateway.amazonaws.com</tt> as a trusted entity.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>domain-add</tt></li>
</ul>
</td>
<td><code>AWS_API_DOMAIN_NAME</code></td>
<td>A domain name configured in Route 53 that the API gateway can be mapped to.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>domain-add</tt></li>
</ul>
</td>
<td><code>AWS_API_BASE_PATH</code></td>
<td>Base path mapping to connect the domain name's CF distribution to the gateway.</td>
<td><tt>(none)</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>domain-add</tt></li>
</ul>
</td>
<td><code>AWS_API_DOMAIN_WAIT_UNTIL_AVAILABLE</code></td>
<td>Waits until the custom domain name has been created.</td>
<td>true, set to undefined to disable.</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>domain-add</tt></li>
</ul>
</td>
<td><code>AWS_ACM_CERTIFICATE_ARN</code></td>
<td>ARN of an HTTPS certificate to use for securing API requests.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>gw-deploy</tt></li>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_NAME</code></td>
<td>Name for the created Lambda.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_DESCRIPTION</code></td>
<td>Description for the created Lambda</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_HANDLER</code></td>
<td>Name of the handler function. e.g. "module.function"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_RUNTIME</code></td>
<td>Lambda runtime environment.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_CONNECTION_TIMEOUT</code></td>
<td>Connection timeout in seconds.</td>
<td><tt>30</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_MEMORY_SIZE</code></td>
<td>Amount of memory to allocate to the Lambda.</td>
<td><tt>3000</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_BUCKET</code></td>
<td>S3 bucket to store lambda if zip file exceeds maximum upload size.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_KEY</code></td>
<td>Key of the lambda archive in the configured bucket.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_EXECUTION_ROLE_ARN</code></td>
<td>ARN of a role with permissions to execute the Lambda.  Should have <tt>AWSXrayWriteOnlyAccess</tt> and <tt>AWSLambdaBasicExecutionRole</tt> managed roles as permissions, and <tt>lambda.amazonaws.com</tt> as a trusted entity.</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_VPC_SUBNETS</code></td>
<td>List of subnets that the Lambda should run in. Format: "subnetA,subnetB,subnetC,...</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_VPC_SECURITY_GROUPS</code></td>
<td>List of security groups that control the Lambda's access. Format: "<tt>secgrpA,secgrpB,secgrpC,...</tt>"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ENVIRONMENT</code></td>
<td>Variables to inject into the Lambda's environment.  Format: "<tt>varA=valA;varB=valB;...</tt>"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-deploy</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_TAGS</code></td>
<td>List of tags to categorize this Lambda.  Format: "<tt>tagA=valA;tagB=valB;...</tt>"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-archive</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_CONTEXT_DIR</code></td>
<td>Root directory of the project that will provide files to be copied into the Docker image.  If the directory ends with a trailing slash, then the root of the context will be the contents of the directory; otherwise the leaf directory will be at the root of the context.</td>
<td><tt>.</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-archive</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_BUNDLE_DIR</code></td>
<td>Destination directory to write Lambda archive zipfile. </td>
<td><tt>./build</tt></td>
</tr>
<tr>
<tr>
<td>
<ul>
  <li><tt>lambda-archive</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_BUNDLE_NAME</code></td>
<td>Filename of Lambda archive zipfile. </td>
<td><tt>lambda-bundle.zip</tt></td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-archive</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_ADDL_FILES</code></td>
<td>List of 2-tuples of files to copy into the context directory from the local computer. Format: "<tt>srcA,desA;srcB,desB;srcC,desC;...</tt>"</td>
<td>N/A</td>
</tr>
<tr>
<td>
<ul>
  <li><tt>lambda-archive</tt></li>
</ul>
</td>
<td><code>AWS_LAMBDA_ARCHIVE_ADDL_PACKAGES</code></td>
<td>List of <tt>yum</tt> packages to install in the Docker image.  Format: "<tt>packageA,packageB,packageC,...</tt>"</td>
<td>
Default installed by this script:
<ul>
<li><tt>gcc</tt></li>
<li><tt>openssl-devel</tt></li>
<li><tt>bzip2-devel</tt></li>
<li><tt>libffi-devel</tt></li>
<li><tt>python37-pip</tt></li>
</ul>
</td>
</tr>
</table>


## Releasing

```
git flow release start x.y.z
# bump version
vi pyproject.toml lgw/version.py
git add pyproject.toml lgw/version.py
git commit -m 'bump version'
dephell deps convert
poetry publish --build
git flow release finish x.y.z
```
